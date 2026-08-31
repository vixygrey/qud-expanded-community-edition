using System;
using QudExpandedCE;
using XRL.Messages;
using XRL.World.Effects;

namespace XRL.World.Parts
{
    /// <summary>
    /// Applies a <see cref="Vixy_Wound"/> when a single blow takes off half of my hit points.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>One handler sees both of the things a wound trigger needs.</b> <c>Physics</c> sends
    /// <c>BeforeTookDamageEvent</c>, then moves hit points, then sends <c>TookDamageEvent</c> — so
    /// by the time this runs, <c>E.Damage.Amount</c> is the <em>final post-mitigation damage
    /// actually taken</em>, after AV, resistances and every <c>BeforeApplyDamageEvent</c> reduction,
    /// and the hit points are already spent. See #192.
    /// </para>
    /// <para>
    /// <b>The threshold is a proportion, and it is vanilla's own.</b> Immediately above that send
    /// site, the floating combat text scales itself by <c>damage.Amount / stat.BaseValue</c> in five
    /// bands — 0.1, 0.2, 0.3, 0.4, 0.5. **Freehold already classifies how big a hit was as a
    /// fraction of maximum hit points**, and has trained the player on it for the whole game: the
    /// number gets visibly bigger at exactly these steps. This fires at the top band.
    /// </para>
    /// <para>
    /// A proportional threshold is also what closes #192's last checkbox. This fork adds +4 to the
    /// maximum weapon die at tier 5 and nothing at the other eight tiers, but that only matters to an
    /// absolute number: a fraction of maximum hit points is invariant to weapon tier, character
    /// level, Strength and every multiplier at once, and never needs re-deriving.
    /// </para>
    /// <para>
    /// <b>Damage over time cannot wound.</b> <c>IDamageEvent.Indirect</c> is passed
    /// <c>Indirect: true</c> by <c>Poisoned</c>, <c>PhasePoisoned</c>, <c>PoisonGasPoison</c>,
    /// <c>SporeCloudPoison</c>, <c>AshPoison</c>, <c>Bleeding</c>, <c>Burning</c>,
    /// <c>GasDamaging</c> and <c>LifeDrain</c> — every damage-over-time source — and it reaches
    /// <c>TookDamageEvent</c>. So the *"generous thresholds"* worry is mostly answered by a flag
    /// that already exists rather than by tuning. A wound should come from being hit hard once, not
    /// from standing in gas.
    /// </para>
    /// <para>
    /// <b>The player only.</b> §B1's framing is that Part B removes free resources from the player
    /// rather than adding opposition, and wounding every creature in the world would be a balance
    /// change of a different kind and size than the one this issue argues for.
    /// </para>
    /// <para>
    /// Charter rule 5: no instance state, one event handler, no Harmony, no reflection, and no
    /// vanilla record touched.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Wounding : IPart
    {
        /// <summary>
        /// Fraction of maximum hit points, in percent, that one blow must take to wound.
        /// </summary>
        /// <remarks>
        /// The top of vanilla's own five-band severity scale. Worth being honest about what that
        /// does and does not license: those bands are read from a *presentation* path — how large to
        /// draw the floating number — so they are good evidence of how Freehold thinks about blow
        /// severity, and are not a balance figure anybody tuned for consequences. The shape is well
        /// founded; the number wants play.
        /// </remarks>
        public const int ThresholdPercent = 50;

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == TookDamageEvent.ID;
        }

        public override bool HandleEvent(TookDamageEvent E)
        {
            if (Raven_Options.Wounds && !E.Indirect && ParentObject.IsPlayer())
            {
                Statistic hitpoints = ParentObject.GetStat("Hitpoints");
                int amount = E.Damage?.Amount ?? 0;

                if (hitpoints != null
                    && amount > 0
                    && amount * 100 >= hitpoints.BaseValue * ThresholdPercent
                    && !ParentObject.HasEffect<Vixy_Wound>()
                    && ParentObject.ApplyEffect(new Vixy_Wound(Vixy_Wound.UntreatedDuration)))
                {
                    ParentObject.ParticleText("*wounded*", 'R');
                    MessageQueue.AddPlayerMessage(
                        "{{R|That one will not simply mend. You are wounded.}}");
                }
            }

            return base.HandleEvent(E);
        }
    }
}
