using System;
using QudExpandedCE;
using XRL.World.Parts;

namespace XRL.World.Conversations.Parts
{
    /// <summary>
    /// Lets somebody I have shared water with say what they have heard of me since.
    /// </summary>
    /// <remarks>
    /// <para>
    /// The speaking half of #753's first checkbox; <c>Vixy_WaterMemory</c> is the half that records.
    /// The choice appears only on somebody I actually completed a ritual with, <em>and</em> only once
    /// my standing with their own people has moved by fifty either way since that day. Their reply
    /// turns on which way it went.
    /// </para>
    /// <para>
    /// <b>The choice appearing is itself the signal.</b> It would have been easier to offer it after
    /// every ritual and answer "I have heard little of you" when nothing had changed, and that is
    /// what this did first. But it puts a permanent extra line on every legendary I have ever shared
    /// water with, and a line that is always there tells me nothing by being there. Gated on the
    /// movement, its presence means there is something to hear.
    /// </para>
    /// <para>
    /// <b>Their own faction, not their related ones, and that is a design choice rather than the
    /// easy one.</b> #753's other half is that a legendary's related factions are <em>rolled</em> —
    /// uniform across the visible factions at 10% friend, 45% dislike, 45% hate — so a line about
    /// what the Girsh think of me, delivered by a Joppa villager, would read as noise until that
    /// half is constrained. Their own faction is the one relationship the ritual definitely
    /// established, so it is the only axis that cannot produce a sentence the player finds absurd.
    /// </para>
    /// <para>
    /// <b>Detecting a past ritual costs nothing.</b> <c>WaterRitual.PerformRitual</c> sets
    /// <c>WaterRitualed</c> on the speaker, and that property is read by nothing in the game —
    /// zero uses across vanilla's own <c>Conversations.xml</c>. A canonical marker, already
    /// persisted, going spare.
    /// </para>
    /// <para>
    /// <b>Why the direction arrives as a token rather than as three nodes.</b>
    /// <c>IConversationElement</c> collapses a <c>~</c> pool with
    /// <c>GetRandomSubstring('~')</c> <em>before</em> <c>PrepareTextEvent</c> fires, so a part
    /// cannot steer which line was drawn — by the time it is asked, the choice is made. But
    /// <c>PrepareTextEvent</c> hands over the <c>StringBuilder</c> and runs <em>before</em> vanilla's
    /// own <c>=variable=</c> substitutions, so a token planted in the text can be filled and the
    /// result still goes through normal processing. That buys one node, one pool of framings in the
    /// XML where the prose belongs, and the direction supplied here.
    /// </para>
    /// <para>
    /// Charter rule 5: no I/O, no network, no reflection, no Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_WaterRemembers : IConversationPart
    {
        /// <summary>The token every line in the pool carries. Filled in <c>PrepareTextEvent</c>.</summary>
        public const string Token = "=Vixy_ritualreport=";

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade)
                || ID == IsElementVisibleEvent.ID
                || ID == PrepareTextEvent.ID;
        }

        public override bool HandleEvent(IsElementVisibleEvent E)
        {
            // Past the threshold, not merely measurable. The choice appearing at all is the signal
            // that there is something to hear - offering it after every ritual and answering "little"
            // would put a permanent extra line on every legendary I have ever shared water with, and
            // would make its presence mean nothing.
            return Shift(out int moved) && Math.Abs(moved) >= Vixy_WaterMemory.Threshold
                ? base.HandleEvent(E)
                : false;
        }

        public override bool HandleEvent(PrepareTextEvent E)
        {
            if (Shift(out int moved))
            {
                // "little" should be unreachable, because the choice that leads here is hidden
                // below the threshold. It stays as the fallback so that no path can ever render the
                // raw token to a player, which is the one failure worth being paranoid about.
                E.Text.Replace(
                    Token,
                    moved >= Vixy_WaterMemory.Threshold ? "good report"
                        : moved <= -Vixy_WaterMemory.Threshold ? "ill report"
                        : "little");
            }
            return base.HandleEvent(E);
        }

        /// <summary>
        /// How far my standing with the speaker's people has moved since we shared water, and
        /// whether there is a reading at all.
        /// </summary>
        /// <remarks>
        /// Cheapest tests first, because this runs for every conversation in the game and almost
        /// nobody qualifies: the option, then the speaker, then the ritual marker, and only then the
        /// record and its attribute. <c>TryGetAttribute</c> rather than <c>GetAttribute</c> — the
        /// latter is inverted in vanilla, as <c>Vixy_WaterMemory</c>'s remarks record.
        /// </remarks>
        private static bool Shift(out int moved)
        {
            moved = 0;
            if (!Raven_Options.WaterMemory) return false;

            GameObject speaker = The.Speaker;
            if (speaker == null || !speaker.HasIntProperty("WaterRitualed")) return false;

            WaterRitualRecord record = speaker.GetPart<WaterRitualRecord>();
            if (record == null || record.faction.IsNullOrEmpty()) return false;

            if (!record.TryGetAttribute(Vixy_WaterMemory.Key, out string stored)) return false;
            if (!int.TryParse(stored, out int then)) return false;

            moved = The.Game.PlayerReputation.Get(record.faction) - then;
            return true;
        }
    }
}
