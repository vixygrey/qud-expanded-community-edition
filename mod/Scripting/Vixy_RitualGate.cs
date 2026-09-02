using System;
using QudExpandedCE;
using XRL.World.Parts;

namespace XRL.World.Conversations.Parts
{
    /// <summary>
    /// Decides whether vanilla's water-ritual choice is offered at all, on both sides of the ritual.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Part of #753, added to vanilla's own <c>WaterRitualChoice</c> by <c>Load="Add"</c>. It answers
    /// two complaints found in play, which turn out to be the same question asked before and after:
    /// <em>should this choice be here right now?</em>
    /// </para>
    /// <para>
    /// <b>Before the ritual: not until we have exchanged names.</b> You could share water with a
    /// legendary who had never heard your name, which is a strange thing for the game's central
    /// gesture of trust. See <see cref="Vixy_Introduce"/>, which also had to be written, because on
    /// the population that offers the ritual there was no introduction available at all.
    /// </para>
    /// <para>
    /// <b>After the ritual: not unless the bond can actually deepen.</b> Re-entering the node is
    /// vanilla behaviour and does nothing — <c>PerformRitual()</c> is gated on
    /// <c>!HasIntProperty("WaterRitualed")</c> — but it is not free: <c>WaterRitualBegin</c> charges
    /// a dram on every entry, because the branch that calls <c>UseDrams(1, …)</c> sits outside the
    /// first-time check. So the shipped behaviour is that you pay water to open a menu that cannot
    /// do anything. Hiding it unless <see cref="Vixy_WaterMemory"/> has something to give retires
    /// that.
    /// </para>
    /// <para>
    /// <b>The gate falls open rather than shut when it cannot decide.</b> A creature who cannot be
    /// introduced to would otherwise lose the ritual permanently, and quests route through it. Every
    /// unknown here resolves to <em>visible</em>. That is deliberate: the worst outcome of showing a
    /// choice too often is a wasted dram, and the worst outcome of hiding it is a dead questline.
    /// </para>
    /// <para>
    /// Charter rule 5: no I/O, no network, no reflection, no Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_RitualGate : IConversationPart
    {
        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == IsElementVisibleEvent.ID;
        }

        public override bool HandleEvent(IsElementVisibleEvent E)
        {
            // Off means vanilla, including vanilla's dead repeat choice.
            if (!Raven_Options.WaterBond) return base.HandleEvent(E);

            GameObject speaker = The.Speaker;
            if (speaker == null) return base.HandleEvent(E);

            if (speaker.HasIntProperty("WaterRitualed"))
            {
                // Already done. Only worth offering again if there is something to gain by it.
                return Vixy_WaterMemory.CanDeepen(speaker) ? base.HandleEvent(E) : false;
            }

            // Not yet done. Hide only when a name could have passed between us and has not.
            if (Vixy_Introduce.Possible(speaker) && !Vixy_Introduce.Done(speaker)) return false;

            return base.HandleEvent(E);
        }
    }
}
