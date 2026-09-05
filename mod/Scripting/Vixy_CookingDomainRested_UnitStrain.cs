using System;
using QudExpandedCE;
using XRL.World.Parts;

namespace XRL.World.Effects
{
    /// <summary>
    /// The dunelace dish: while it is metabolising, I tire half as fast.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The proactive half of #843, where wakebriar is the reactive one.</b> The tonic is what I
    /// drink when the meter is already at the top and I need to reach the stairs; this is what I eat
    /// before setting out, so the meter climbs slower all day. They cannot collide:
    /// <c>ProceduralCookingEffect</c> does not override <c>IsTonic()</c>, so a meal never counts
    /// toward tonic capacity, and preparing does not cost me the emergency dose.
    /// </para>
    /// <para>
    /// <b>A property rather than a call.</b> <c>Vixy_Fatigue.Strain</c> is private and this is an
    /// effect unit, not a part, so it has no handle on the meter. It writes
    /// <c>Vixy_Fatigue.RestedProperty</c> in <see cref="Apply"/> and clears it in
    /// <see cref="Remove"/>, and <c>Strain</c> reads it — the same shape the sleep suppressor's
    /// <c>HasInstalledCybernetics</c> check already has beside it.
    /// </para>
    /// <para>
    /// <b>Nothing here owns the lifetime.</b> <c>ProceduralCookingEffect</c> zeroes itself on
    /// <c>BecameHungry</c>, <c>BecameFamished</c> and <c>ApplyWellFed</c>, so the dish lasts until I
    /// am hungry again and any other meal ends it. That is the bound <i>and</i> the cost: carrying
    /// this means giving up the regeneration or strength dish.
    /// </para>
    /// <para>
    /// <b>It does not stack with the sleep suppressor</b>, and the reason is in <c>Strain</c>:
    /// <c>BaseAccrual</c> is 22 hundredths, so halving twice is 5, and a meter that takes 20,000
    /// actions to fill is the system switched off. Two investments should not disable a system.
    /// </para>
    /// <para>
    /// <b>With fatigue off this does nothing, and the description says so rather than lying.</b>
    /// <c>Vixy_SleepSuppressor</c> had to answer this differently because it sits in three vanilla
    /// implant tables and displaces something useful; this domain carries <c>RandomWeight="0"</c> and
    /// is reachable only through dried dunelace, so nothing is displaced. A dud meal is not a stolen
    /// slot, and buying it out with a second unrelated effect would have cost more than it bought.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_CookingDomainRested_UnitStrain : ProceduralCookingEffectUnit
    {
        public override string GetDescription()
        {
            return Raven_Options.Fatigue
                ? "You tire half as quickly."
                : "{{K|Nothing, while fatigue is switched off.}}";
        }

        public override void Apply(GameObject go, Effect parent)
        {
            go?.SetIntProperty(Vixy_Fatigue.RestedProperty, 1);
        }

        public override void Remove(GameObject go, Effect parent)
        {
            go?.RemoveIntProperty(Vixy_Fatigue.RestedProperty);
        }
    }
}
