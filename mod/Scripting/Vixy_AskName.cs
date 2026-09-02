using System;
using System.Text;
using QudExpandedCE;
using XRL.UI;
using XRL.World.Parts;

namespace XRL.World.Conversations.Parts
{
    /// <summary>
    /// Lets the player ask a nameless creature what it is called, and be told.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Vanilla wrote this and switched it off.</b> `XRL.World.Conversations.Parts.AskName` is
    /// complete — six question variants, a four-variant `TellName` node, `GiveProperName`, the
    /// `TitleIfNamed` handling, and a `NoAskName` opt-out — and its visibility handler opens with
    /// <c>if (!GlobalConfig.GetBoolSetting("GeneralAskName")) return false;</c>. That key appears
    /// nowhere under `Base/` and <c>GetBoolSetting</c> returns false for a key it cannot find, so
    /// the choice never renders. `docs/LESSONS.md` records it as the most complete instance yet of
    /// vanilla building a mechanism it never wires up.
    /// </para>
    /// <para>
    /// <b>Why this is a new part rather than that flag.</b> Only a mod can supply
    /// `GeneralAskName`, through the <c>ModManager.ForEachFile("GlobalConfig.json", …)</c> call at
    /// the end of <c>LoadGlobalConfig</c> — and that call passes <c>Recursive: false</c>, so it
    /// matches <c>ModFile.RelativeName</c> and the file has to sit at the mod root. Root files are
    /// never registered here: <c>ModInfo.InitializeFiles</c> walks only the paths named in
    /// `manifest.json`'s <c>Directories</c> when that array is non-empty, and declaring the root to
    /// fix it would swallow `Optional/JoppaBuilding` — the dedup loop drops any racked directory
    /// nested inside a newly added one, so the Joppa building would load unconditionally and its
    /// option would stop meaning anything. Reaching vanilla's flag costs an existing opt-out, so
    /// this declares its own choice instead and leaves the flag alone.
    /// </para>
    /// <para>
    /// <b>The answer is still vanilla's.</b> The choice targets `TellName`, which lives in
    /// `BaseConversation` and is inherited everywhere, so what a creature says back — <i>You may
    /// call me …</i>, <i>They call me …</i> — is Freehold's text and not mine. Charter rule 2 for
    /// free: only the question is new, and half of it is copied from the six vanilla already wrote.
    /// </para>
    /// <para>
    /// <b>The gates are vanilla's too</b>, minus the config check: a creature, without a proper
    /// name already, not carrying `NoAskName`, in a conversation the player can leave. Asking is
    /// pointless where any of those fail, and `NoAskName` is the hook an author uses to say <i>this
    /// one does not answer</i>.
    /// </para>
    /// <para>
    /// <b>Asking forecloses renaming, and that is the point.</b> `GameObject.HandleRename` refuses
    /// when <c>HasProperName &amp;&amp; GetIntProperty("Renamed") != 1</c> — <i>"doesn't want a new
    /// name."</i> — and nothing here sets `Renamed`. So a creature that has told me its name cannot
    /// afterwards be given one by me. That is a real trade and it is deliberate: asking who someone
    /// is and deciding who they are should not be the same act, and the player picks which one they
    /// are doing. `docs/FEATURES.md` says so plainly, because there is no helptext to carry it.
    /// </para>
    /// <para>
    /// Charter rule 5: one conversation part, two event handlers. No I/O, no reflection, no
    /// Harmony.
    /// </para>
    /// </remarks>
    public class Vixy_AskName : IConversationPart
    {
        public override bool WantEvent(int ID, int Propagation)
        {
            return base.WantEvent(ID, Propagation)
                || ID == EnteredElementEvent.ID
                || ID == IsElementVisibleEvent.ID;
        }

        /// <summary>They answer, and the name sticks.</summary>
        /// <remarks>
        /// Also marks that a name has passed between us, which <see cref="Vixy_RitualGate"/> reads
        /// to decide whether the water ritual should be offered yet. Asking somebody's name and
        /// giving them mine are the two halves of the same exchange — <see cref="Vixy_Introduce"/>
        /// covers the other — so both set the one marker and the gate need not care which happened.
        /// </remarks>
        public override bool HandleEvent(EnteredElementEvent E)
        {
            GameObject speaker = The.Speaker;
            speaker?.SetIntProperty(Vixy_Introduce.Marker, 1);

            if (speaker != null && !speaker.HasProperName)
            {
                speaker.GiveProperName();

                string title = speaker.GetPropertyOrTag("TitleIfNamed");
                if (!title.IsNullOrEmpty())
                {
                    speaker.RequirePart<Titles>().AddTitle(title);
                }
            }

            return base.HandleEvent(E);
        }

        /// <summary>Offered only where asking makes sense.</summary>
        public override bool HandleEvent(IsElementVisibleEvent E)
        {
            GameObject speaker = The.Speaker;

            if (!Raven_Options.AskName || speaker == null)
            {
                return false;
            }

            if (ConversationUI.StartNode == null || !ConversationUI.StartNode.AllowEscape)
            {
                return false;
            }

            if (!speaker.IsCreature || speaker.HasProperName)
            {
                return false;
            }

            if (speaker.HasPropertyOrTag("NoAskName"))
            {
                return false;
            }

            if (SaysNothing(ConversationUI.StartNode))
            {
                return false;
            }

            return base.HandleEvent(E);
        }

        /// <summary>
        /// True when this conversation is made entirely of emotes, so nobody is speaking.
        /// </summary>
        /// <remarks>
        /// <para>
        /// <c>IsCreature</c> is not the test the question needs, and vanilla's own part stops
        /// there. A giant dragonfly is a creature: <c>BaseAnimal</c> carries
        /// <c>ConversationScript ConversationID="Animals"</c> and insects, birds and reptiles all
        /// inherit it, so chatting with one is possible and answers
        /// <c>{{emote|*soft growling*}}</c>. A choice offering to be told a name, under that,
        /// answered in words, is worse than no feature.
        /// </para>
        /// <para>
        /// <b>Measured rather than listed.</b> 25 of vanilla's 164 conversations with a start node
        /// say nothing that is not an emote — and the interesting entries are not the animals.
        /// <c>Sparafucile</c> has 23 emote lines, <c>Oboroqoru</c> and <c>Warden 1-FF</c> have
        /// their own, and the apple farmer's daughter has hers. Those are people who deliberately
        /// do not speak, and a hardcoded list of animal blueprints would have missed every one of
        /// them while pretending to be thorough.
        /// </para>
        /// <para>
        /// <b>Asked of the conversation rather than the creature</b>, so it needs no data and does
        /// not rot. A future Qud patch that adds a chittering thing gets the right answer without
        /// this fork noticing, and so does another mod's. The alternative was tagging 29 blueprints
        /// with vanilla's <c>NoAskName</c> and clearing it again on the six <c>Sapient*</c> plants
        /// that inherit from tagged bases — correct today and wrong at the next patch.
        /// </para>
        /// <para>
        /// A node with no text at all reads as <em>not</em> silent, deliberately: emptiness here
        /// means the text is built somewhere this cannot see, and hiding the question on a vacuous
        /// truth would suppress it wherever a conversation is assembled at runtime.
        /// </para>
        /// </remarks>
        private static bool SaysNothing(Node Start)
        {
            if (Start?.Texts == null)
            {
                return false;
            }

            bool said = false;

            foreach (ConversationText text in Start.Texts)
            {
                string raw = text?.Text;
                if (raw.IsNullOrEmpty())
                {
                    continue;
                }

                foreach (string fragment in raw.Split('~'))
                {
                    if (fragment.Trim().Length == 0)
                    {
                        continue;
                    }

                    said = true;
                    if (WithoutEmotes(fragment).Trim().Length > 0)
                    {
                        return false;
                    }
                }
            }

            return said;
        }

        /// <summary>
        /// The line with every <c>{{emote|…}}</c> span removed, leaving whatever was actually said.
        /// </summary>
        /// <remarks>
        /// Testing that a line <em>starts</em> with an emote is not enough, and the data says so:
        /// Tillifergaewicz opens <c>{{emote|*aloud, in a high-pitched buzzing voice*}}</c> and then
        /// talks, Vivira beeps and then greets you by name, and Geeub croaks before speaking. All
        /// three would have been silenced by the simpler test. Only what is left after the emotes
        /// come out decides it.
        ///
        /// Depth-counted rather than matched by pattern, because an emote can carry colour markup
        /// inside it and the closing braces of a nested span are not the end of the emote.
        /// </remarks>
        private static string WithoutEmotes(string Line)
        {
            const string OPEN = "{{emote|";

            int start = Line.IndexOf(OPEN, StringComparison.Ordinal);
            if (start < 0)
            {
                return Line;
            }

            StringBuilder said = new StringBuilder(Line.Length);
            int at = 0;

            while (start >= 0)
            {
                said.Append(Line, at, start - at);

                int depth = 1;
                int scan = start + OPEN.Length;
                while (scan < Line.Length && depth > 0)
                {
                    if (scan + 1 < Line.Length && Line[scan] == '{' && Line[scan + 1] == '{')
                    {
                        depth++;
                        scan += 2;
                    }
                    else if (scan + 1 < Line.Length && Line[scan] == '}' && Line[scan + 1] == '}')
                    {
                        depth--;
                        scan += 2;
                    }
                    else
                    {
                        scan++;
                    }
                }

                at = scan;
                start = Line.IndexOf(OPEN, at, StringComparison.Ordinal);
            }

            if (at < Line.Length)
            {
                said.Append(Line, at, Line.Length - at);
            }

            return said.ToString();
        }
    }
}
