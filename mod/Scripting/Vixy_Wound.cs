using System;
using QudExpandedCE;
using XRL.World.Parts.Mutation;

namespace XRL.World.Effects
{
    /// <summary>
    /// A wound: a slice of hit points that natural regeneration will not return. Rest carries you
    /// back to *almost* whole, and the last part needs treating.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Why the late game is easy.</b> Natural healing is
    /// <c>(20 + 2×ToughnessMod + 2×WillpowerMod)</c> per turn into a counter paying 1 HP per 100 —
    /// slow, but turns are cheap, so hit points are very nearly a renewable resource. This is item
    /// B1 of <c>docs/DESIGN_difficulty_systems.md</c>, whose framing is that Part A adds opposition
    /// and Part B removes free resources. **It adds no enemy hit points at all.** See #192.
    /// </para>
    /// <para>
    /// <b>The mechanism is vanilla's, down to a six-line precedent.</b>
    /// <c>Stomach.ProcessNaturalHealing</c> fires <c>Regenerating</c> and then <c>Regenerating2</c>
    /// as ordinary string events carrying a mutable <c>Amount</c>, and
    /// <c>XRL.World.Parts.DisabledNaturalHealing</c> already exists to zero it. This does the same
    /// thing conditionally rather than absolutely.
    /// </para>
    /// <para>
    /// <b>And the arithmetic is vanilla's too.</b> <c>Penalty</c> on the Hitpoints stat <em>is</em>
    /// the damage store — <c>Stomach</c> heals by <c>Penalty -= num</c> — so "hit points a wound
    /// holds back" needs no new bookkeeping. It is a floor below which natural healing may not
    /// lower <c>Penalty</c>.
    /// </para>
    /// <para>
    /// <b>Treatment passes straight through, and nothing had to be changed to allow it.</b>
    /// <c>GameObject.Heal</c> writes <c>stat.Penalty -= num2</c> directly and never fires
    /// <c>Regenerating</c>, so every bandage, salve, injector, <c>Physic</c> use and regeneration
    /// tank already heals through a wound. The treatment economy becomes load-bearing without a
    /// single item being touched — <c>#640</c> counted 11 restorative blueprints, four cooking
    /// domains, Convalessence and the skill tree, and closed as *deliberate, not a gap*.
    /// </para>
    /// <para>
    /// <b>Any healing clears it.</b> <c>Heal</c> fires a <c>Healing</c> event before applying, so
    /// the wound removes itself on being treated at all, rather than requiring you to be healed past
    /// the reserve. That is the gentler of the two readings and a deliberate choice: the bite is the
    /// interruption and the consumable, not the arithmetic. §B1's own risk note calls this the item
    /// most likely to feel bad, and a wound you cannot clear without the right supplies is how that
    /// happens.
    /// </para>
    /// <para>
    /// <b>Blunting the Regeneration mutation rather than exempting it.</b> The mutation registers
    /// <c>Regenerating</c>; this clamps on <c>Regenerating2</c>, which <c>ProcessNaturalHealing</c>
    /// fires second, so the clamp lands last whatever the mutation did to <c>Amount</c>. Rather than
    /// a wound-specific exemption bolted on top, the reserve itself shrinks 10% per mutation level
    /// and is gone at 10 — the existing lever, as #192's second checkbox asked.
    /// </para>
    /// <para>
    /// <b>Never permanent, two ways.</b> Any treatment removes it, and failing that it expires on
    /// its own. Both are required: the first makes the treatment economy matter, the second means
    /// a player with nothing left is delayed rather than stranded.
    /// </para>
    /// <para>
    /// <b>No instance state.</b> The reserve is computed from the object's own maximum hit points
    /// each time it is asked for, so this effect adds no fields to save layout — <c>Duration</c> is
    /// the base class's. Charter rule 5 and <c>validate_mod.py</c>'s <c>serializable-shape</c>
    /// check both stay satisfied without the question arising.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Wound : Effect
    {
        /// <summary>Percent of maximum hit points a wound holds back from natural healing.</summary>
        public const int ReservePercent = 25;

        /// <summary>
        /// Turns a wound lasts if it is never treated.
        /// </summary>
        /// <remarks>
        /// Long enough that treating it is the sensible answer and short enough that it is never a
        /// dead end. Natural healing runs at roughly 0.2 HP a turn, so this is the same order as
        /// simply resting the damage off would have been.
        /// </remarks>
        public const int UntreatedDuration = 1500;

        public Vixy_Wound()
        {
            DisplayName = "{{R|wounded}}";
        }

        public Vixy_Wound(int Duration)
            : this()
        {
            base.Duration = Duration;
        }

        public override bool UseStandardDurationCountdown()
        {
            return true;
        }

        /// <summary>Structural, negative, and removable by ordinary means.</summary>
        public override int GetEffectType()
        {
            return TYPE_STRUCTURAL | TYPE_NEGATIVE | TYPE_REMOVABLE;
        }

        public override string GetDescription()
        {
            return "{{R|wounded}}";
        }

        public override string GetDetails()
        {
            return "Rest will not close this. It needs treating.";
        }

        public override bool SameAs(Effect e)
        {
            return false;
        }

        public override bool Apply(GameObject Object)
        {
            return !Object.HasEffect<Vixy_Wound>();
        }

        public override void Register(GameObject Object, IEventRegistrar Registrar)
        {
            Registrar.Register("Regenerating2");
            Registrar.Register("Healing");
            base.Register(Object, Registrar);
        }

        public override bool FireEvent(Event E)
        {
            if (E.ID == "Regenerating2")
            {
                // Missing hit points, which is what Penalty holds. Natural healing may close the
                // gap down to the reserve and no further.
                if (Object != null && Object.GetStat("Hitpoints")?.Penalty <= ReserveFor(Object))
                {
                    E.SetParameter("Amount", 0);
                }
            }
            else if (E.ID == "Healing")
            {
                // Fired by GameObject.Heal before it applies, so any treatment at all clears this -
                // an item, a Physic use, a regeneration tank or a meal.
                Object?.RemoveEffect(this);
            }

            return base.FireEvent(E);
        }

        /// <summary>
        /// Hit points this wound holds back from <paramref name="Object"/>.
        /// </summary>
        /// <remarks>
        /// Proportional rather than absolute, which is what keeps it invariant to weapon tier,
        /// character level, Strength and every damage multiplier at once — #192's last checkbox
        /// worried that nine tiers of melee weapons move the goalposts, and against a fraction of
        /// maximum hit points they cannot.
        /// </remarks>
        public static int ReserveFor(GameObject Object)
        {
            int max = Object?.GetStat("Hitpoints")?.BaseValue ?? 0;
            int reserve = max * ReservePercent / 100;

            // The mutation blunts the wound instead of ignoring it: a tenth off per level, nothing
            // left at 10.
            Regeneration regeneration = Object?.GetPart<Regeneration>();
            if (regeneration != null)
            {
                int level = Math.Min(10, Math.Max(0, regeneration.Level));
                reserve = reserve * (10 - level) / 10;
            }

            return reserve;
        }
    }
}
