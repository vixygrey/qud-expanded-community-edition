using System;

namespace XRL.World.Parts
{
    /// <summary>
    /// The implant half of the sleep suppressor: grants <see cref="Vixy_Sleepless"/> while worn.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>What it refuses, and what it deliberately does not.</b> `Asleep` line 116 ends its whole
    /// refusal chain with <c>|| forced</c>, so anything constructed <c>forced: true</c> goes through
    /// regardless. That is the line between the two halves of this item, and it falls in exactly the
    /// right place without anything being written to put it there:
    /// </para>
    /// <list type="bullet">
    /// <item><description><b>Refused</b> — sleep gas (`GasSleep` line 163), a cudgel to the head
    /// (`Cudgel_Bludgeon`), crungle gaze, Pax Klanq's madness, the fatecaller, `DeepDream`.</description></item>
    /// <item><description><b>Not refused</b> — narcolepsy, which is `ForceApplyEffect(new Asleep(...,
    /// forced: true))`. So this does not cancel a defect somebody took points for at chargen, which
    /// was the one real cost when this was proposed, and it turns out not to exist.</description></item>
    /// <item><description><b>Not refused</b> — my own collapse from exhaustion, also `forced: true`.
    /// Correct: the implant should slow the clock, not let me buy my way out of the end of
    /// it.</description></item>
    /// <item><description><b>Not refused</b> — lying down on purpose, which is `Voluntary: true` and
    /// short-circuits the chain before it starts.</description></item>
    /// </list>
    /// <para>
    /// <b>The fatigue half is a second clause, not the point.</b> `Vixy_Fatigue.Strain` halves while
    /// this is installed. Fatigue is off by default under charter rule 6, so an item whose only
    /// effect were fatigue-shaped would sit in three vanilla implant tables doing nothing for most
    /// players. Refusing involuntary sleep is worth having on its own terms, and nothing in vanilla
    /// grants it: `Wakeful` is applied from one place, `Asleep` line 180, as a three-to-five turn
    /// grace after waking.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_SleepSuppressor : IPart
    {
        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade)
                || ID == ImplantedEvent.ID
                || ID == UnimplantedEvent.ID;
        }

        public override bool HandleEvent(ImplantedEvent E)
        {
            E.Implantee?.RequirePart<Vixy_Sleepless>();
            return base.HandleEvent(E);
        }

        public override bool HandleEvent(UnimplantedEvent E)
        {
            E.Implantee?.RemovePart<Vixy_Sleepless>();
            return base.HandleEvent(E);
        }
    }
}
