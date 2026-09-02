using System;
using System.Collections.Generic;
using QudExpandedCE;
using XRL.UI;

namespace XRL.World.Conversations.Parts
{
    /// <summary>
    /// Notices when I give somebody my name, whoever wrote the words.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Part of #753, and the piece that makes <see cref="Vixy_RitualGate"/> safe. Vanilla already
    /// has hand-written introductions in twenty-six conversations, seven of them on people who can
    /// perform a water ritual — Agyra, Une, Miryam, Tzedech, Tikva, Thicksalt and Tammuz. Without
    /// this, using vanilla's introduction would leave the gate shut for ever, because only
    /// <see cref="Vixy_Introduce"/> was setting the marker. Introducing yourself and then being told
    /// you may not share water is a dead end that looks exactly like a bug.
    /// </para>
    /// <para>
    /// <b>There was no hook to attach to.</b> <c>GenericAskNameOption</c> is a template nobody
    /// inherits, five of the seven route through <c>GotoID="Name"</c> but Agyra and Une do not, and
    /// none of them carries a part. A list of seven conversation IDs would have been exact today and
    /// would rot silently as Qud adds people, with nothing in the validator able to notice.
    /// </para>
    /// <para>
    /// <b>So this watches instead, from the conversation level.</b> Events bubble upward — a choice
    /// is handled by parts on itself, then its node, then its conversation — so one part on
    /// <c>BaseConversation</c> sees every choice taken in every conversation in the game. It needs
    /// <c>Register="Listener"</c> in the XML: a conversation-level part would otherwise register for
    /// the Speaker perspective and never see a choice, which is mine to speak.
    /// </para>
    /// <para>
    /// <b>The test is on the raw text, before substitution.</b> Every introduction — vanilla's, this
    /// fork's, and any mod's following the same convention — contains the literal <c>=name=</c>
    /// token. Measured across all 2,375 choices in vanilla's <c>Conversations.xml</c>, the three
    /// phrasings below match <b>32 introductions and nothing else</b>; the six other choices
    /// containing <c>=name=</c> are greetings and speeches, and none of them matches.
    /// </para>
    /// <para>
    /// <b>It fails in the safe direction.</b> A phrasing this misses simply does not set the marker,
    /// which leaves <see cref="Vixy_Introduce"/> visible and able to set it — so a miss costs a
    /// duplicate choice in one menu, never a blocked ritual. That asymmetry is the same one that
    /// makes the gate itself open rather than close when it cannot decide.
    /// </para>
    /// <para>
    /// Charter rule 5: no I/O, no network, no reflection, no Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Introductions : IConversationPart
    {
        /// <summary>
        /// The phrasings that count as giving my name, matched against unsubstituted text.
        /// </summary>
        public static readonly string[] Phrasings =
        {
            "i am =name=", "my name is =name=", "call me =name=",
        };

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == EnterElementEvent.ID;
        }

        public override bool HandleEvent(EnterElementEvent E)
        {
            if (Raven_Options.WaterBond && IsIntroduction(E.Element))
            {
                The.Speaker?.SetIntProperty(Vixy_Introduce.Marker, 1);
            }
            return base.HandleEvent(E);
        }

        /// <summary>Whether this element's words are me giving my name.</summary>
        public static bool IsIntroduction(IConversationElement element)
        {
            if (element == null) return false;

            if (Matches(element.Text)) return true;

            if (element.Texts != null)
            {
                foreach (ConversationText text in element.Texts)
                {
                    if (Matches(text?.Text)) return true;
                }
            }
            return false;
        }

        private static bool Matches(string raw)
        {
            if (raw.IsNullOrEmpty()) return false;

            string lower = raw.ToLowerInvariant();
            foreach (string phrase in Phrasings)
            {
                if (lower.Contains(phrase)) return true;
            }
            return false;
        }

        /// <summary>
        /// Whether the conversation I am in already offers an introduction of its own.
        /// </summary>
        /// <remarks>
        /// Read by <see cref="Vixy_Introduce"/> so it does not stand next to vanilla's version of
        /// itself. Its own choice is excluded by ID, since it would otherwise always find itself.
        /// </remarks>
        public static bool AlreadyOffered()
        {
            Node start = ConversationUI.StartNode;
            if (start?.Elements == null) return false;

            foreach (IConversationElement element in start.Elements)
            {
                if (element is Choice && element.ID != "Vixy_Introduce" && IsIntroduction(element))
                {
                    return true;
                }
            }
            return false;
        }
    }
}
