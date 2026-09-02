using System;
using QudExpandedCE;
using XRL.UI;

namespace XRL.World.Conversations.Parts
{
    /// <summary>
    /// Lets me give my name to somebody whose name I already know.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Part of #753. The gap was found in play: you can share water with a legendary before either of
    /// you has said a name, and — worse — there was no way to introduce yourself at all.
    /// <c>Vixy_AskName</c> hides itself when <c>speaker.HasProperName</c>, which is correct (you can
    /// already see what they are called), but the water ritual requires <c>GivesRep</c>, and the
    /// people who have that are overwhelmingly the people who have proper names. <c>ElderBob</c> and
    /// <c>Mehmet</c> both carry <c>GivesRep</c> <em>and</em> <c>&lt;xtagGrammar Proper="true" /&gt;</c>.
    /// So on exactly the population that can perform the ritual, no naming exchange existed.
    /// </para>
    /// <para>
    /// <b>This is the complement rather than a duplicate.</b> <c>Vixy_AskName</c> covers creatures
    /// with no proper name — <em>what is your name?</em> This covers creatures who have one —
    /// <em>I am so-and-so.</em> Between them every creature I can hold a conversation with has
    /// exactly one naming exchange available, and neither ever appears beside the other.
    /// </para>
    /// <para>
    /// <b>The marker is set from both paths</b>, so <see cref="Vixy_RitualGate"/> does not care which
    /// happened. It lives on the speaker as an int property, the same shape as vanilla's own
    /// <c>WaterRitualed</c>, so it persists with them and costs no save-layout change.
    /// </para>
    /// <para>
    /// Charter rule 5: no I/O, no network, no reflection, no Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Introduce : IConversationPart
    {
        /// <summary>Set on somebody once a name has passed between us, either way round.</summary>
        public const string Marker = "Vixy_Introduced";

        /// <summary>Whether a naming exchange is available with this speaker at all.</summary>
        /// <remarks>
        /// <para>
        /// <b>The gate has to be able to fall open, which is the whole reason this is a separate
        /// test.</b> Some creatures can be talked to but cannot be introduced to — tagged
        /// <c>NoAskName</c>, or reached through a start node that does not allow escape. If the water
        /// ritual were simply hidden until introduced, it would be hidden from those creatures
        /// <em>for ever</em>. The rule is therefore "hide only when an introduction is possible and
        /// has not happened", not "hide until introduced". #190's envoy filter was the same shape of
        /// mistake caught the same way.
        /// </para>
        /// <para>
        /// A creature with a proper name is reachable through this part; one without is reachable
        /// through <c>Vixy_AskName</c>, which has its own option — so if that option is off, an
        /// unnamed creature genuinely cannot be introduced to, and the gate must open.
        /// </para>
        /// </remarks>
        public static bool Possible(GameObject speaker)
        {
            if (speaker == null || !speaker.IsCreature) return false;
            if (speaker.HasPropertyOrTag("NoAskName")) return false;
            if (ConversationUI.StartNode == null || !ConversationUI.StartNode.AllowEscape) return false;

            // Vanilla's own introduction counts. Vixy_Introductions is what notices one being
            // used, so a conversation carrying its own can be introduced to whatever this fork
            // offers - which is what stops the gate dead-ending the seven ritual-capable people
            // vanilla already wrote one for.
            if (Vixy_Introductions.AlreadyOffered()) return true;

            return speaker.HasProperName ? Raven_Options.WaterBond : Raven_Options.AskName;
        }

        /// <summary>Whether a name has already passed between us.</summary>
        public static bool Done(GameObject speaker) =>
            speaker != null && speaker.HasIntProperty(Marker);

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade)
                || ID == IsElementVisibleEvent.ID
                || ID == EnterElementEvent.ID;
        }

        public override bool HandleEvent(IsElementVisibleEvent E)
        {
            GameObject speaker = The.Speaker;

            if (!Raven_Options.WaterBond || speaker == null) return false;
            if (ConversationUI.StartNode == null || !ConversationUI.StartNode.AllowEscape) return false;

            // The mirror of Vixy_AskName's test: it takes the nameless, this takes the named.
            if (!speaker.IsCreature || !speaker.HasProperName) return false;

            if (speaker.HasPropertyOrTag("NoAskName")) return false;
            if (Done(speaker)) return false;

            // Vanilla writes its own introductions into twenty-six conversations. Where one is
            // already on offer, mine would stand beside it saying the same thing.
            if (Vixy_Introductions.AlreadyOffered()) return false;

            return base.HandleEvent(E);
        }

        /// <summary>Remembers that I gave my name, the moment the words are chosen.</summary>
        public override bool HandleEvent(EnterElementEvent E)
        {
            The.Speaker?.SetIntProperty(Marker, 1);
            return base.HandleEvent(E);
        }
    }
}
