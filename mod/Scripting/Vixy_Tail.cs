using System;
using XRL.World.Anatomy;

namespace XRL.World.Parts.Mutation
{
    /// <summary>
    /// A tail. It grants a little dodge and helps you keep your feet, and it never attacks.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>It does not level, because it costs one point.</b> All four of vanilla's 1-point physical
    /// mutations — <c>Beak</c>, <c>ThickFur</c>, <c>DarkVision</c>, <c>SlimeGlands</c> — return false
    /// from <c>CanLevel</c> and an empty string from <c>GetLevelText</c>. A point buys one or two
    /// flat effects, permanently, and this follows that shape rather than inventing a curve for a
    /// price that has never had one.
    /// </para>
    /// <para>
    /// <b>Which is why footing is a save rather than a percentage.</b> A flat chance on a mutation
    /// that never ranks is the same number at level 1 and level 30. An Agility save lets the
    /// mutation grow with the character instead, which is the only growth a 1-point mutation can
    /// have — and it is the right stat: how well you catch your balance should depend on how nimble
    /// you are. <c>KnockdownSaveDifficulty</c> is vanilla's own figure for being knocked over,
    /// used by <c>RocketSkates</c> and <c>EelSpawn</c>.
    /// </para>
    /// <para>
    /// <b>The gate is <c>CanChangeBodyPosition</c>, not the obvious event.</b>
    /// <c>ObjectGoingProneEvent</c> is a notification — <c>Prone.Apply</c> sends it after the
    /// "knocked prone" message, too late to refuse. <c>ApplyProne</c> is a real gate but carries no
    /// parameters, so a handler on it would also stop the player lying down to sleep.
    /// <c>CanChangeBodyPosition</c> carries an <c>Involuntary</c> flag, which is exactly the
    /// distinction needed; <c>Burrowed</c> reads the same flag for the opposite purpose.
    /// </para>
    /// <para>
    /// <b>The part is added at runtime and marked as ours.</b> <c>Stinger.RequireTail</c> is the
    /// model: claim an unmanaged tail if the creature has one, otherwise add a part carrying this
    /// mutation's <c>ManagerID</c>. That marking is what lets removal tell "the tail I grew" from
    /// "the tail a snake was born with". Merging a <c>Tail</c> into the <c>Humanoid</c> anatomy
    /// would instead give one to every humanoid in the game.
    /// </para>
    /// <para>
    /// <b>Losing the tail loses the benefits.</b> A tail is <c>Appendage="true"</c>, so an axe can
    /// take it, and a severed tail granting dodge would be free defence. Both the stat shift and the
    /// save are conditioned on the part actually being attached.
    /// </para>
    /// <para>
    /// <b>Carries no instance state, so nothing is added to the save.</b> The manager id is derived
    /// from the parent object rather than stored, the way <c>Stinger</c> derives its own.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Tail : BaseDefaultEquipmentMutation
    {
        private const string SlotType = "Tail";

        private const string DefaultVariant = "Vixy_FoxTail";

        /// <summary>Vanilla's own Agility save for being knocked over — RocketSkates, EelSpawn.</summary>
        private const int KnockdownSaveDifficulty = 16;

        private const int DodgeValueBonus = 1;

        private string ManagerID => ParentObject.ID + "::Vixy_Tail";

        private string Blueprint => Variant.IsNullOrEmpty() ? DefaultVariant : Variant;

        public override bool CanLevel()
        {
            return false;
        }

        public override bool GeneratesEquipment()
        {
            return true;
        }

        public override string GetDescription()
        {
            return "You have a tail.";
        }

        public override string GetLevelText(int Level)
        {
            return "+{{rules|" + DodgeValueBonus + " DV}}\n"
                + "When something would knock you down, an {{rules|Agility}} save to keep your feet\n"
                + "Does not attack, and holds nothing";
        }

        public override void Register(GameObject Object, IEventRegistrar Registrar)
        {
            Registrar.Register("CanChangeBodyPosition");
            base.Register(Object, Registrar);
        }

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == AfterDismemberEvent.ID;
        }

        /// <summary>Losing the tail takes the dodge with it.</summary>
        public override bool HandleEvent(AfterDismemberEvent E)
        {
            if (E.Object == ParentObject)
            {
                SyncDodgeValue();
            }

            return base.HandleEvent(E);
        }

        /// <summary>
        /// Refuse an involuntary knockdown when the save succeeds.
        /// </summary>
        /// <remarks>
        /// Returning false from this event is what stops <c>Prone.Apply</c>. The Involuntary check
        /// is load-bearing: without it this would also refuse lying down to sleep or sitting.
        /// </remarks>
        public override bool FireEvent(Event E)
        {
            if (
                E.ID == "CanChangeBodyPosition"
                && E.HasFlag("Involuntary")
                && E.GetStringParameter("To") == "Prone"
                && HasTail()
                && ParentObject.MakeSave(
                    "Agility",
                    KnockdownSaveDifficulty,
                    null,
                    null,
                    "Vixy_Tail Knockdown"
                )
            )
            {
                if (E.HasFlag("ShowMessage") && ParentObject.IsPlayer())
                {
                    IComponent<GameObject>.EmitMessage(
                        ParentObject,
                        "You swing your tail and keep your feet."
                    );
                }

                return false;
            }

            return base.FireEvent(E);
        }

        public override bool Mutate(GameObject GO, int Level)
        {
            Stinger.AddTail(GO, ManagerID, UseUnmanaged: true);
            SyncDodgeValue();
            return base.Mutate(GO, Level);
        }

        public override bool Unmutate(GameObject GO)
        {
            CleanUpMutationEquipment(GO, FindTailObject(GO));
            Stinger.RemoveTail(GO, ManagerID);
            base.StatShifter.RemoveStatShifts(GO);
            return base.Unmutate(GO);
        }

        /// <summary>
        /// Hang the chosen tail on the part, as its default behaviour rather than as equipment.
        /// </summary>
        /// <remarks>
        /// The object carries no MeleeWeapon part, so <c>GetFirstValidWeapon</c> passes it over and
        /// the tail never attacks. It is here to be seen and to be chosen between.
        /// </remarks>
        public override void OnRegenerateDefaultEquipment(Body body)
        {
            BodyPart part =
                ParentObject.GetBodyPartByManager(ManagerID) ?? body.GetFirstPart(SlotType);
            if (part != null && part.DefaultBehavior?.Blueprint != Blueprint)
            {
                part.DefaultBehavior = GameObjectFactory.Factory.CreateObject(Blueprint);
                ResetDisplayName();
            }

            SyncDodgeValue();
            base.OnRegenerateDefaultEquipment(body);
        }

        /// <summary>Whether a tail is actually attached right now.</summary>
        private bool HasTail()
        {
            return ParentObject?.GetBodyPartByManager(ManagerID) != null
                || ParentObject?.Body?.GetFirstPart(SlotType) != null;
        }

        /// <summary>Match the dodge bonus to whether the tail is there, rather than toggling it.</summary>
        private void SyncDodgeValue()
        {
            if (HasTail())
            {
                base.StatShifter.SetStatShift(
                    ParentObject,
                    "DV",
                    DodgeValueBonus,
                    baseValue: true
                );
            }
            else
            {
                base.StatShifter.RemoveStatShifts(ParentObject);
            }
        }

        /// <summary>The cosmetic tail currently hanging on the part, or null.</summary>
        private GameObject FindTailObject(GameObject who)
        {
            BodyPart part =
                who?.GetBodyPartByManager(ManagerID) ?? who?.Body?.GetFirstPart(SlotType);
            GameObject behavior = part?.DefaultBehavior;
            return (behavior != null && behavior.Blueprint == Blueprint) ? behavior : null;
        }
    }
}
