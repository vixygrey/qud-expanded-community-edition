using System;

namespace XRL.World.Parts
{
    /// <summary>
    /// Refuses involuntary sleep, for as long as it is present.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Granted and removed by <see cref="Vixy_SleepSuppressor"/></b> rather than declared in any
    /// blueprint. It exists as a separate part because <c>CanApplyInvoluntarySleep</c> is a legacy
    /// string event, and those reach the parts of the object they are fired on — they do not cascade
    /// out to equipment the way the modern pooled events do. `GasMask` can sit on an implant and read
    /// `E.Object == ParentObject.Equipped` because `GetRespiratoryAgentPerformanceEvent` cascades;
    /// this one cannot, so the capability has to live on the body itself.
    /// </para>
    /// <para>
    /// <b>The two events are `Wakeful`'s, and they are the only two fired.</b> `GasSleep` line 130
    /// checks `CanApplyInvoluntarySleep` before applying, and `Asleep` line 116 checks both on the
    /// way in. Nothing else in the assembly fires either.
    /// </para>
    /// <para>
    /// <b>`ImmuneToSleepGas` looks like the part for this job and is inert.</b> It registers
    /// <c>CanApplySleepGas</c>; `GasSleep` fires <c>CanApplySleegas</c>, missing the p. The two
    /// occurrences of the correct-looking spelling in the whole assembly are both inside
    /// `ImmuneToSleepGas` itself, and no blueprint declares the part. See docs/LESSONS.md.
    /// </para>
    /// <para>
    /// Charter rule 5: no instance state, two string-event handlers, no Harmony and no reflection.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Sleepless : IPart
    {
        public override void Register(GameObject Object, IEventRegistrar Registrar)
        {
            Registrar.Register("CanApplyInvoluntarySleep");
            Registrar.Register("ApplyInvoluntarySleep");
            base.Register(Object, Registrar);
        }

        public override bool FireEvent(Event E)
        {
            if (E.ID == "CanApplyInvoluntarySleep" || E.ID == "ApplyInvoluntarySleep")
            {
                return false;
            }
            return base.FireEvent(E);
        }
    }
}
