using System;

namespace XRL.World.Effects
{
    /// <summary>
    /// Wakebriar: for a short window you do not fall down, however tired you are. The meter keeps
    /// climbing the whole time.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The case this exists for is a delve that went wrong.</b> An unexpected heavy fight deep in
    /// a dungeon, the meter near the top, and a level and a half between me and anywhere safe to lie
    /// down. Measured against <see cref="XRL.World.Parts.Vixy_Fatigue"/>'s own numbers, that
    /// situation is unsurvivable: once fatigue reaches <c>Collapsing</c> the per-action drop chance
    /// runs 1% at 950 to 25% at 1000, and the meter is still rising, so the race lasts about
    /// <b>36 actions</b> from 950 and <b>four to nine</b> past 970. A Qud zone is 80×25. You cannot
    /// cross one. See #843.
    /// </para>
    /// <para>
    /// <b>200 turns buys roughly two crossings</b> — enough to walk out of a shallow delve, not
    /// enough to rescue a deep one. It is a sixth of a game day, and the same order as
    /// <c>Vixy_Gutter.Cost</c>.
    /// </para>
    /// <para>
    /// <b>It defers the collapse and never touches the meter.</b> <c>Accrue(Strain())</c> runs
    /// throughout, so the debt is not merely still owed, it grows while it is being spent: the window
    /// lapses further up the meter than it started and the collapse roll resumes at the higher rate.
    /// That is the whole balance argument, and it needs no number beyond stating it.
    /// </para>
    /// <para>
    /// <b>Guttering is deliberately left alone.</b> Suppressing <c>Vixy_Gutter.Slip</c> as well would
    /// make this strictly better and hide the cost entirely. Abilities failing while I run for the
    /// stairs is the tell that I am upright on borrowed time rather than actually well.
    /// </para>
    /// <para>
    /// <b>It refreshes rather than accumulating, which is the opposite of vanilla's own
    /// <c>Wakeful</c>.</b> That effect's <c>Apply</c> does <c>Effect.Duration += Duration</c> and
    /// returns false, uncapped — so ten doses would be ten windows, and building on it would have
    /// inherited an unbounded window by construction. This takes the longer of the two instead.
    /// </para>
    /// <para>
    /// <b>The rebound is vanilla's, not invented.</b> <c>Tonic.CausesOverdose</c> defaults true and
    /// base tonic capacity is 1, so a second concurrent tonic effect is a Toughness save at
    /// <c>16 + 3 × (count − capacity)</c>, escalating, with mutants carrying a flat 5% on top and 33%
    /// under <c>TonicAllergy</c>. The <c>Overdose</c> event fires on every effect that fails and does
    /// nothing unless the effect registers for it — so this one ends. Reaching for a second dose to
    /// extend the window closes it instead, with the meter wherever it has climbed to.
    /// </para>
    /// <para>
    /// <b>It also refuses involuntary sleep, which is what makes it worth carrying with fatigue
    /// switched off.</b> <c>Vixy_SleepSuppressor</c>'s docstring names the trap: an item whose only
    /// effect is fatigue-shaped sits in the loot tables doing nothing for most players, because
    /// fatigue is off by default. These are the same two string events <c>Vixy_Sleepless</c> refuses
    /// and the only two fired — sleep gas, a cudgel to the head, crungle gaze, Pax Klanq's madness,
    /// the fatecaller, <c>DeepDream</c>. It does <em>not</em> refuse a fatigue collapse that way:
    /// <c>Asleep.Apply</c> ends its chain with <c>|| forced</c>, so the guard for that lives in
    /// <c>Vixy_Fatigue.Collapse</c> where this fork owns the code.
    /// </para>
    /// <para>
    /// Charter rule 5: no instance fields beyond the ones <c>Effect</c> already carries, so the save
    /// shape is unchanged; no Harmony and no reflection.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Wakebriar : ITonicEffect
    {
        /// <summary>Turns the window lasts, before any tonic-duration modifier.</summary>
        public const int BaseDuration = 200;

        public Vixy_Wakebriar()
        {
            DisplayName = "{{W|wakebriar}}";
        }

        public Vixy_Wakebriar(int Duration)
            : this()
        {
            base.Duration = Duration;
        }

        public override bool SameAs(Effect e)
        {
            return false;
        }

        public override bool UseStandardDurationCountdown()
        {
            return true;
        }

        public override string GetDescription()
        {
            return "{{W|wakebriar}}";
        }

        /// <summary>
        /// What the window costs and what it does not do.
        /// </summary>
        /// <remarks>
        /// Overridden because <c>Effect.GetDetails</c> returns the literal <c>[effect details]</c>
        /// and Show Effects prints it — the defect #841 fixed on <c>Vixy_Fatigued</c>, which shipped
        /// that placeholder from the day the readout arrived.
        /// </remarks>
        public override string GetDetails()
        {
            return "You will not collapse from exhaustion.\n"
                + "You cannot be put to sleep against your will.\n"
                + "Tiredness still climbs, and abilities still gutter out.";
        }

        /// <summary>
        /// Refresh to the longer window rather than adding to it.
        /// </summary>
        /// <remarks>
        /// Returning false leaves the effect already on the object in place — the same shape
        /// <c>Wakeful.Apply</c> uses, with the accumulation taken out.
        /// </remarks>
        public override bool Apply(GameObject Object)
        {
            if (Object.TryGetEffect<Vixy_Wakebriar>(out var Existing))
            {
                if (Duration > Existing.Duration)
                {
                    Existing.Duration = Duration;
                }
                return false;
            }
            return true;
        }

        public override void Register(GameObject Object, IEventRegistrar Registrar)
        {
            Registrar.Register("CanApplyInvoluntarySleep");
            Registrar.Register("ApplyInvoluntarySleep");
            Registrar.Register("Overdose");
            base.Register(Object, Registrar);
        }

        public override bool FireEvent(Event E)
        {
            if (E.ID == "CanApplyInvoluntarySleep" || E.ID == "ApplyInvoluntarySleep")
            {
                return false;
            }
            if (E.ID == "Overdose")
            {
                if (Object != null && Object.IsPlayer())
                {
                    IComponent<GameObject>.AddPlayerMessage(
                        "{{R|The second dose turns on you, and the wakebriar lets go all at once.}}");
                }
                Duration = 0;
            }
            return base.FireEvent(E);
        }

        /// <summary>
        /// Nothing, as <c>Salve_Tonic</c>'s is nothing.
        /// </summary>
        /// <remarks>
        /// <c>ITonicEffect</c> declares this abstract so it has to be written. It is only ever
        /// called from <c>TonicAllergy.SalveOverdose</c>, which draws from a hard-coded array of
        /// seven vanilla tonic effects — a mod's effect is not in it, so this cannot currently be
        /// reached. Left empty rather than invented, because a mutant-allergy reaction nothing calls
        /// is a behaviour nobody could ever review.
        /// </remarks>
        public override void ApplyAllergy(GameObject subject)
        {
        }
    }
}
