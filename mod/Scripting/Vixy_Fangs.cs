using System;
using XRL.World.Anatomy;

namespace XRL.World.Parts.Mutation
{
    /// <summary>
    /// Long teeth on the Face, which bite alongside whatever the character is wielding.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>This class exists because it has to.</b> Every <c>&lt;mutation&gt;</c> node needs a
    /// <c>Class</c>, and <c>MutationEntry.MutationType</c> resolves it as
    /// <c>"XRL.World.Parts.Mutation." + Class</c> — so the namespace above is fixed, and a
    /// mutation cannot be added in XML alone. Pointing <c>Class</c> at vanilla's <c>Horns</c>
    /// instead is not an option: two entries sharing a class collide, and whichever sorts first
    /// by display name swallows the other. See <c>mod/Core/Mutations.xml</c> and #589.
    /// </para>
    /// <para>
    /// <b>Modelled on <c>Beak</c>, not on <c>Horns</c>.</b> Horns looked like the closer parent —
    /// it is variant-general and its <c>RegrowHorns</c> already reads a blueprint's slot and grows
    /// the thing. But <c>RegrowHorns</c>, <c>GetAV</c> and <c>GetBaseDamage</c> are all
    /// non-virtual, while the three methods that call <c>RegrowHorns</c> are virtual — so a
    /// subclass overriding <c>ChangeLevel</c> still runs the parent's regrow through
    /// <c>base.ChangeLevel</c>, which force-equips at <c>MaxStrengthBonus = 100</c>,
    /// <c>2d3</c> and <c>AV = 1</c>. All four of the things a fangs subclass would exist to
    /// change, and C# has no <c>base.base</c>. <c>docs/LESSONS.md</c> records it.
    /// </para>
    /// <para>
    /// <b>Default behaviour, never force-equip.</b> <c>BodyPart.GetFirstValidWeapon</c> checks the
    /// part's <c>DefaultBehavior</c> for a <c>MeleeWeapon</c> first and only returns
    /// <c>Equipped</c> when that also has one. A gas mask has none — so setting default behaviour
    /// leaves the player their Face slot and the bite at the same time, where force-equipping
    /// would block all 34 <c>WornOn="Face"</c> items in the game.
    /// </para>
    /// <para>
    /// <b>The bite rides along with the real weapon.</b> <c>Combat.MeleeAttackWithWeapon</c>
    /// collects every body part holding a valid weapon, attacks with the primary at 100%, and
    /// rolls the rest through <c>GetMeleeAttackChanceEvent</c> with <c>Intrinsic</c> set. The
    /// engine default is 15, and <see cref="Vixy_FangsProperties"/> runs it from 20 untrained to 40
    /// fully trained, or 100 while Charging. So
    /// fangs never compete with a better weapon, which is what keeps them worth having.
    /// </para>
    /// <para>
    /// <b>Damage is flat and the bleed is what scales.</b> <c>1d6</c> is vanilla's own figure for
    /// fangs — <c>BaseFangs</c> and both its variants — and it lives in the blueprint rather than
    /// here, because nothing about it varies. Rank moves the bleed instead, through
    /// <see cref="Vixy_FangsProperties"/>: save difficulty <c>20 + 2 × rank</c>, and bleed damage <c>1</c>
    /// rising to <c>1d2</c> and beyond past rank 4.
    /// </para>
    /// <para>
    /// <b>Carries no instance state, so nothing is added to the save.</b> <c>Beak</c> keeps a
    /// <c>GameObject BeakObject</c> field for cleanup; copying that would be the first instance
    /// field on a <c>[Serializable]</c> type in this mod, which <c>serializable-shape</c> flags
    /// and charter rule 5 asks be a considered decision rather than a side effect. The object is
    /// found again from the body instead — it is the Face part's default behaviour, and its
    /// blueprint names it.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Fangs : BaseDefaultEquipmentMutation
    {
        private const string SlotType = "Face";

        private const string DefaultVariant = "Vixy_Fangs";

        /// <summary>The blueprint this rank's fangs are grown from.</summary>
        private string Blueprint => Variant.IsNullOrEmpty() ? DefaultVariant : Variant;

        public override bool GeneratesEquipment()
        {
            return true;
        }

        public override string GetDescription()
        {
            return "Long teeth crowd your mouth, and they are not for eating.";
        }

        public override string GetLevelText(int Level)
        {
            string text = "20% chance on melee attack to bite your opponent\n";
            text += "Damage increment: {{rules|1d6}}\n";
            text += "To-hit bonus: {{rules|" + (Level / 2 + 1) + "}}\n";
            text +=
                (Level == base.Level)
                    ? "Bites may cause bleeding\n"
                    : "{{rules|Increased bleeding save difficulty}}\n";
            text += "Fangs are a short-blade class natural weapon.\n";
            return text + "Leaves your face free for a mask or goggles";
        }

        /// <summary>
        /// Grow the fangs onto the Face and hand the bleed its rank.
        /// </summary>
        /// <remarks>
        /// The slot is registered so a character who loses and regrows the part gets them back on
        /// the same one. Slot and WornOn are written from the part rather than trusted from the
        /// blueprint, because an anatomy may name its face something other than "Face".
        /// </remarks>
        public override void OnRegenerateDefaultEquipment(Body body)
        {
            if (!TryGetRegisteredSlot(body, SlotType, out BodyPart part))
            {
                part = body.GetFirstPart(SlotType);
                if (part != null)
                {
                    RegisterSlot(SlotType, part);
                }
            }

            if (part != null)
            {
                GameObject fangs = GameObjectFactory.Factory.CreateObject(Blueprint);
                fangs.GetPart<MeleeWeapon>().Slot = part.Type;

                Armor armor = fangs.GetPart<Armor>();
                armor.WornOn = part.Type;
                armor.AV = 0;

                SyncBleedRank(fangs, base.Level);
                part.DefaultBehavior = fangs;
                ResetDisplayName();
            }

            base.OnRegenerateDefaultEquipment(body);
        }

        public override bool ChangeLevel(int NewLevel)
        {
            SyncBleedRank(FindFangs(ParentObject), NewLevel);
            return base.ChangeLevel(NewLevel);
        }

        public override bool Unmutate(GameObject GO)
        {
            CleanUpMutationEquipment(GO, FindFangs(GO));
            return base.Unmutate(GO);
        }

        /// <summary>
        /// Tell Vixy_FangsProperties which rank to bleed at.
        /// </summary>
        /// <remarks>
        /// Its own GetHornLevel() asks the wearer for a mutation named "Horns" and this one is
        /// named Vixy_Fangs, so the lookup misses and it falls back to this field. Writing it is
        /// what makes the bleed scale at all.
        /// </remarks>
        private static void SyncBleedRank(GameObject fangs, int rank)
        {
            Vixy_FangsProperties.SetRank(fangs, rank);
        }

        /// <summary>
        /// The fangs currently on this body, or null.
        /// </summary>
        /// <remarks>
        /// <para>
        /// Asked of the body rather than remembered in a field, so this class adds nothing to the
        /// save. The blueprint comparison is what stops it picking up somebody else's bite.
        /// </para>
        /// <para>
        /// The registered slot is asked first and the anatomy's own only as a fallback, because
        /// those two can differ: OnRegenerateDefaultEquipment registers whichever part it actually
        /// grew on, and an anatomy may name its face something other than "Face". Looking up the
        /// wrong part would silently leave the fangs' rank unsynced and their object un-obliterated
        /// on unmutate.
        /// </para>
        /// </remarks>
        private GameObject FindFangs(GameObject who)
        {
            BodyPart part =
                GetRegisteredSlot(SlotType, evenIfDismembered: true)
                ?? who?.Body?.GetFirstPart(SlotType);
            GameObject behavior = part?.DefaultBehavior;
            return (behavior != null && behavior.Blueprint == Blueprint) ? behavior : null;
        }
    }
}
