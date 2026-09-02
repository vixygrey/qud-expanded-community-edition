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
    /// <b>The test is the bare <c>=name=</c> token in a choice's unsubstituted text</b>, and it took
    /// two corrections to arrive at something that simple. A choice is what <em>I</em> say and
    /// <c>=name=</c> is <em>my</em> name, so a choice carrying it is me naming myself. Parsed and
    /// tested per text exactly as this does, <b>35 choice texts in vanilla contain the token and all
    /// 35 are introductions</b> — no false positive to defend against.
    /// </para>
    /// <para>
    /// <b>I first wrote a list of three phrasings, and it was wrong in both directions.</b> The
    /// false positives it was guarding against — <em>"Live and drink, =name="</em> and its kin — are
    /// <c>&lt;text&gt;</c> on nodes, which is the speaker's words and never reaches this. Meanwhile
    /// it missed <c>MehmetIntroduce</c>, whose line is <em>"I am called =name="</em> and matches none
    /// of the three. So the ritual stayed locked for anybody who introduced themselves to Mehmet the
    /// way the game offers, which is the exact dead end this part exists to prevent. I had built the
    /// list by eye off a regex that concatenated sibling elements, rather than by parsing at the
    /// granularity the runtime uses.
    /// </para>
    /// <para>
    /// <b>It still fails in the safe direction.</b> A false positive sets the marker without a real
    /// introduction, which opens the gate early; a miss leaves <see cref="Vixy_Introduce"/> visible
    /// and able to set it. Neither locks the ritual, which is the same asymmetry that makes the gate
    /// open rather than close when it cannot decide.
    /// </para>
    /// <para>
    /// Charter rule 5: no I/O, no network, no reflection, no Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Introductions : IConversationPart
    {
        /// <summary>The token that carries my own name into a line of dialogue.</summary>
        /// <remarks>
        /// <b>Matched bare, against a choice's unsubstituted text, and that is the whole test.</b>
        /// A choice is what <em>I</em> say and <c>=name=</c> is <em>my</em> name, so a choice
        /// carrying it is me naming myself. Measured against every choice in vanilla's
        /// <c>Conversations.xml</c>, parsed and tested per text exactly as this does: <b>35 choice
        /// texts contain the token and all 35 are introductions.</b> Not one false positive.
        /// </remarks>
        public const string NameToken = "=name=";

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

        private static bool Matches(string raw) =>
            !raw.IsNullOrEmpty() && raw.Contains(NameToken);

        /// <summary>This fork's own naming choices, which are never "somebody else's".</summary>
        /// <remarks>
        /// <b>Both of them, and forgetting the second one broke the whole feature.</b>
        /// <c>Vixy_AskName</c>'s pool contains <em>"I am =name=, … What is your name?"</em> — it is
        /// an introduction as well as a question — and it is distributed to the start node of every
        /// conversation in the game. So <see cref="AlreadyOffered"/> found it everywhere, concluded
        /// the game already had an introduction everywhere, hid <c>Vixy_Introduce</c> everywhere,
        /// and left <see cref="Vixy_RitualGate"/> shut on everyone. Excluding only
        /// <c>Vixy_Introduce</c> was not enough; a choice of mine is a choice of mine.
        /// </remarks>
        public static readonly string[] Mine = { "Vixy_Introduce", "Vixy_AskName" };

        /// <summary>
        /// Whether this conversation already offers an introduction that is not one of mine.
        /// </summary>
        /// <remarks>
        /// <para>
        /// Read by <see cref="Vixy_Introduce"/> so it does not stand beside vanilla's version of
        /// itself, and by <see cref="Vixy_Introduce.Possible"/> so the gate knows a name can pass
        /// here by some route.
        /// </para>
        /// <para>
        /// <b>This asks what is <em>present</em>, not what is visible</b>, and the distinction is
        /// worth stating because presence is the cheaper question and the wrong one twice over.
        /// <c>Elements</c> holds every choice the node was built with, including ones hidden by
        /// their own parts — so a choice that no player will ever see still counts here. That is
        /// tolerable for vanilla's introductions, which are visible wherever they are declared, and
        /// it is exactly what made this fork's own distributed choices poison.
        /// </para>
        /// </remarks>
        public static bool AlreadyOffered()
        {
            Node start = ConversationUI.StartNode;
            if (start?.Elements == null) return false;

            foreach (IConversationElement element in start.Elements)
            {
                if (!(element is Choice)) continue;
                if (Array.IndexOf(Mine, element.ID) >= 0) continue;
                if (IsIntroduction(element)) return true;
            }
            return false;
        }
    }
}
