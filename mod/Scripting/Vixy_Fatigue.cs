using System;
using QudExpandedCE;
using XRL.Messages;
using XRL;
using XRL.Core;
using XRL.Rules;
using XRL.World.Effects;

namespace XRL.World.Parts
{
    /// <summary>
    /// Fatigue: a third survival timer, and a reason to choose where you sleep.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Modelled on <c>Stomach</c>, which is vanilla's own survival timer</b>, and follows it on
    /// every structural question rather than inventing answers. It accrues on
    /// <c>BeginTakeActionEvent</c> (not <c>EndTurnEvent</c>, which <c>docs/DESIGN_sleep.md</c> §7
    /// recommended before there was a benchmark) because that is the hook vanilla charges hunger and
    /// thirst on; it gates on <c>IsPlayer()</c>, which is why companions are exempt without a special
    /// case; and it skips accrual while <c>Asleep</c>, as <c>Stomach</c> does.
    /// </para>
    /// <para>
    /// <b>The world map is handled the way <c>Stomach</c> handles it</b>, which answers §6's overland
    /// checkbox with a vanilla pattern instead of a guess. A world-map step is many turns, so accruing
    /// per action there would make the map nearly free. Instead the turn count is stamped on entry and
    /// the debt is paid on return, capped, exactly as <c>Stomach</c> does with
    /// <c>OnWorldMapSince</c>.
    /// </para>
    /// <para>
    /// <b>State lives in the object's property bag rather than in a field on this part.</b> That is a
    /// deliberate choice under charter rule 5, not a way round <c>serializable-shape</c>: a
    /// <c>[Serializable]</c> field's layout is written into every save and renaming one can break
    /// saves that exist, while a property key that goes missing simply reads as its default. The mod
    /// already stores persistent state this way in <c>Vixy_OnsetWarning</c>, and vanilla does the same
    /// for the closest analogue — <c>Stomach</c> keeps its counters in fields but puts
    /// <c>OnWorldMapSince</c> in a property.
    /// </para>
    /// <para>
    /// <b>No attribute penalties anywhere.</b> §3.2 was rewritten in #762 against what vanilla's own
    /// timers cost: thirst charges no attribute at all and hunger charges one, and both otherwise
    /// express themselves as capability consequences — you cannot heal, and you cannot travel. The
    /// consequences here are a travel refusal following <c>Famished</c>, and eventually collapse.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Fatigue : IPart
    {
        public const string FatigueProperty = "Vixy_Fatigue";
        public const string OnMapSinceProperty = "Vixy_FatigueOnWorldMapSince";
        public const string SleepCommand = "Vixy_CommandSleep";

        public const int Max = 1000;
        public const int Tired = 400;
        public const int Weary = 600;
        public const int Exhausted = 800;
        public const int Collapsing = 950;

        /// <summary>
        /// A sanity bound on the world-map catch-up, not a balance lever.
        /// </summary>
        /// <remarks>
        /// <b>This was 1,200 turns and that made the world map nearly free</b>, which is the exact
        /// hole §6 warned about — *"a world-map step is many turns. Accrue proportionally or the map
        /// becomes a fatigue-free zone."* One parasang costs 300 ticks across ordinary ground and
        /// 1,200 across North Sheva, so a 1,200-turn cap meant a twenty-parasang haul cost the same
        /// as one bad parasang: half the meter, and never more.
        ///
        /// The cap does not need to do balance work, because <see cref="Set"/> already clamps to
        /// <see cref="Max"/>. Travel far enough without resting and you arrive with the meter full,
        /// which is the correct outcome and the player's own choice. So this is only here to stop a
        /// stale property producing a nonsense number, and it takes `Stomach`'s own bound for the
        /// same job.
        /// </remarks>
        public const int MaxWorldMapCatchUp = 100000;

        public static int Get(GameObject Object)
        {
            return Object?.GetIntProperty(FatigueProperty) ?? 0;
        }

        public static void Set(GameObject Object, int Value)
        {
            Object?.SetIntProperty(FatigueProperty, Math.Max(0, Math.Min(Max, Value)));
        }

        /// <summary>The band a fatigue value falls in, as a threshold constant.</summary>
        public static int BandFor(int Fatigue)
        {
            if (Fatigue >= Collapsing) return Collapsing;
            if (Fatigue >= Exhausted) return Exhausted;
            if (Fatigue >= Weary) return Weary;
            if (Fatigue >= Tired) return Tired;
            return 0;
        }

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade)
                || ID == SingletonEvent<BeginTakeActionEvent>.ID
                || ID == PooledEvent<CanTravelEvent>.ID
                || ID == GetInventoryActionsEvent.ID
                || ID == InventoryActionEvent.ID;
        }

        public override bool HandleEvent(BeginTakeActionEvent E)
        {
            if (!Raven_Options.Fatigue || !ParentObject.IsPlayer())
            {
                return base.HandleEvent(E);
            }

            if (ParentObject.OnWorldMap())
            {
                // Stamp the crossing and charge it on return, as Stomach does. Accruing per action
                // out here would make the world map a fatigue-free zone.
                if (ParentObject.GetIntProperty(OnMapSinceProperty) == 0)
                {
                    ParentObject.SetIntProperty(OnMapSinceProperty, (int)XRLCore.CurrentTurn);
                }
                return base.HandleEvent(E);
            }

            int since = ParentObject.GetIntProperty(OnMapSinceProperty);
            if (since > 0)
            {
                ParentObject.SetIntProperty(OnMapSinceProperty, 0);
                int crossed = (int)Math.Min(XRLCore.CurrentTurn - since, MaxWorldMapCatchUp);
                if (crossed > 0)
                {
                    // Overland travel is strain 1.5 per §3.1, in the same hundredths.
                    Accrue(crossed * BaseAccrual * 3 / 2);
                }
            }

            if (ParentObject.HasEffect<Asleep>())
            {
                Rest();
            }
            else
            {
                Accrue(Strain());
                Announce();
                Collapse();
            }

            return base.HandleEvent(E);
        }

        /// <summary>
        /// Baseline accrual, in hundredths of a fatigue point per action.
        /// </summary>
        /// <remarks>
        /// <b>`Calendar.TurnsPerDay` is 1200</b>, which is the number §3.1 needed and did not have.
        /// The spec put accrual at 1 per action and called 1000 actions "roughly two in-game days";
        /// it is 0.83 of one. Reaching <see cref="Max"/> in three days means 3,600 actions, so the
        /// baseline is 1000/3600 — 0.28 a turn, carried in hundredths so the multipliers below stay
        /// exact integers.
        /// </remarks>
        public const int BaseAccrual = 28;

        /// <summary>
        /// §3.1's strain multiplier, in hundredths so it stays integer arithmetic.
        /// </summary>
        /// <remarks>
        /// Fatigue is a consequence of what the character did, not only of elapsed time — which is
        /// the design's main lever, since it rewards the careful play Qud already rewards. Three days
        /// is the unhurried figure; a character who fights for it arrives much sooner.
        /// </remarks>
        private int Strain()
        {
            int rate = BaseAccrual;
            if (ParentObject.IsInCombat()) rate *= 2;
            if (ParentObject.HasEffect("Bleeding")
                || ParentObject.HasEffect("Poisoned")
                || ParentObject.HasEffect("Burning"))
            {
                rate += BaseAccrual / 2;
            }
            return rate;
        }

        private void Accrue(int Hundredths)
        {
            int carried = ParentObject.GetIntProperty("Vixy_FatigueRemainder") + Hundredths;
            Set(ParentObject, Get(ParentObject) + carried / 100);
            ParentObject.SetIntProperty("Vixy_FatigueRemainder", carried % 100);
        }

        private void Rest()
        {
            // Only voluntary sleep rests. Asleep.Voluntary is false at every involuntary call site -
            // GasSleep, Narcolepsy, CrungleGaze, ModFatecaller, PaxKlanqMadness - and true at every
            // voluntary one, so the gas-grenade exploit closes on one field read. #179.
            Asleep asleep = ParentObject.GetEffect<Asleep>();
            if (asleep == null || !asleep.Voluntary) return;

            Set(ParentObject, Get(ParentObject) - 4 * Vixy_Sleep.RestQuality(ParentObject) / 10);

            if (Get(ParentObject) <= 0)
            {
                ParentObject.RemoveEffect(asleep);
                MessageQueue.AddPlayerMessage("{{G|You wake rested.}}");
                return;
            }

            Vixy_Sleep.RollAmbush(ParentObject);
        }

        /// <summary>
        /// One message per band crossed, carrying `=WEIRDMARKOVSENTENCE=` from Weary upward.
        /// </summary>
        /// <remarks>
        /// The replacer runs a Markov sentence through `Grammar.Weirdify`, which is §1's "make the
        /// world stranger" register available as authored data rather than as code. §4 originally
        /// proposed routing the telepathy sleep display here; that display never reaches the player
        /// and is not a dream system. See #762.
        /// </remarks>
        private void Announce()
        {
            int band = BandFor(Get(ParentObject));
            if (band == ParentObject.GetIntProperty("Vixy_FatigueBandSeen")) return;
            ParentObject.SetIntProperty("Vixy_FatigueBandSeen", band);

            string text = band switch
            {
                Tired => "{{y|You could do with some rest.}}",
                Weary => "{{y|Your eyes are heavy, and the edges of things will not hold still.}}\n{{c|=WEIRDMARKOVSENTENCE=}}",
                Exhausted => "{{r|You are exhausted. You cannot keep this up.}}\n{{c|=WEIRDMARKOVSENTENCE=}}",
                Collapsing => "{{R|You are going to fall down.}}\n{{c|=WEIRDMARKOVSENTENCE=}}",
                _ => null,
            };
            if (text != null)
            {
                MessageQueue.AddPlayerMessage(GameText.VariableReplace(text, ParentObject));
            }
        }

        /// <summary>At Collapsing, a rising per-turn chance of dropping where you stand.</summary>
        private void Collapse()
        {
            int fatigue = Get(ParentObject);
            if (fatigue < Collapsing) return;
            // 1% at 950 climbing to 25% at 1000, per §3.2.
            int chance = 1 + (fatigue - Collapsing) * 24 / (Max - Collapsing);
            if (chance.in100())
            {
                MessageQueue.AddPlayerMessage("{{R|You collapse.}}");
                ParentObject.ForceApplyEffect(new Asleep(Stat.Random(40, 80), forced: true, quicksleep: true, Voluntary: true));
            }
        }

        /// <summary>
        /// Exhaustion refuses world-map travel, following `Famished`.
        /// </summary>
        /// <remarks>
        /// `Stomach.HandleEvent(CanTravelEvent)` is the model, down to the shape of the refusal.
        /// `CanTravelEvent` carries one field and fires before a destination exists, so an outright
        /// refusal is the only thing it can express - which is exactly what this wants. Anything
        /// conditioned on *where* the player is going would need `ObjectLeavingCellEvent` instead;
        /// see docs/LESSONS.md.
        /// </remarks>
        public override bool HandleEvent(CanTravelEvent E)
        {
            if (Raven_Options.Fatigue
                && E.Object == ParentObject
                && ParentObject.IsPlayer()
                && Get(ParentObject) >= Exhausted
                && !The.Core.IDKFA)
            {
                return E.Object.ShowFailure("You're too exhausted to travel long distances.");
            }
            return base.HandleEvent(E);
        }

        public override bool HandleEvent(GetInventoryActionsEvent E)
        {
            if (Raven_Options.Fatigue && E.Object == ParentObject && ParentObject.IsPlayer())
            {
                E.AddAction("Sleep", "sleep", SleepCommand, null, 'S', FireOnActor: true);
            }
            return base.HandleEvent(E);
        }

        public override bool HandleEvent(InventoryActionEvent E)
        {
            if (E.Command == SleepCommand)
            {
                Vixy_Sleep.Attempt(ParentObject);
                return false;
            }
            return base.HandleEvent(E);
        }
    }
}
