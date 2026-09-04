using System;
using XRL.World.AI;

namespace XRL.World.Parts.Skill
{
    /// <summary>
    /// Take the Measure: reading a person's regard for you off their examine text — their people's
    /// standing, and whatever they hold against you personally, in Freehold's own words.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The gap is resolution, not absence.</b> Qud does report regard:
    /// <c>Description.GetFeelingDescription</c> renders <c>Friendly</c> / <c>Neutral</c> /
    /// <c>Hostile</c> off the full <c>Brain.GetFeelingLevel</c>, and Look shows it on both UIs. But
    /// <c>Reputation.GetFeeling</c> collapses the ±600 reputation scale to five values — −100, −50,
    /// 0, +50, +100 — before <c>Brain</c> ever sees it, and <c>GetFeelingLevel</c> then bands at −10
    /// and +50. So the whole ±249 reputation range, where ordinary play lives, is one word. See #836.
    /// </para>
    /// <para>
    /// <b>Freehold wrote the readout and left it behind a debug flag.</b>
    /// <c>Brain.BuildChronology</c> is complete — leader, allegiances dated by the in-world calendar,
    /// then per-observer opinions with authored prose and value — reached by a <i>Show Attitude</i>
    /// inventory action gated on <c>Options.DebugInternals || Options.DebugAttitude</c>, and
    /// <c>OptionDebugAttitude</c> is <c>Category="Debug" Requires="OptionShowAdvancedOptions==Yes"</c>.
    /// <c>IOpinion</c>'s own doc comment says it: <i>"As of yet only for hostility debugging purposes,
    /// may be leveraged somewhere player-facing in the future."</i> This is that, narrowed.
    /// </para>
    /// <para>
    /// <b>It is not <c>BuildChronology</c> verbatim, which would be wrong twice.</b> That dumps
    /// opinions about <em>everyone</em> the creature has an opinion of — a lore leak — with raw
    /// values and calendar dates, which is a debug panel wearing a skill's name. This filters to the
    /// player and keeps only the authored text.
    /// </para>
    /// <para>
    /// <b>The hook is <c>OwnerGetShortDescriptionEvent</c>, and it reaches the player rather than an
    /// owner.</b> <c>Description.GetDescription</c> builds an object's short description and then
    /// runs <c>OE.Process(IComponent&lt;GameObject&gt;.ThePlayer, E)</c> — for <em>any</em> object,
    /// not just equipment. <c>IShortDescriptionEvent.Process</c> calls
    /// <c>ParentEvent.ApplyTo(this)</c> before dispatching, which copies <c>E.Object</c> across, and
    /// its <c>finally</c> copies the builders back — so appending to <c>Postfix</c> reaches the
    /// description. That puts this in the place a player already looks, with no inventory action, no
    /// activated ability and no blueprint merges.
    /// </para>
    /// <para>
    /// <b><c>Brain.TryGetOpinions</c> is not a read-only accessor and is deliberately not used
    /// here.</b> When no list exists it writes one —
    /// <c>Opinions[Subject.BaseID] = (List = new OpinionList())</c> — so a readout calling it would
    /// add an empty <c>OpinionList</c> to every creature examined, mutating save state from a look.
    /// <c>Opinions</c> is a public field and <c>Dictionary.TryGetValue</c> creates nothing.
    /// </para>
    /// <para>
    /// <b>A led creature answers with its leader's regard, so this says so rather than passing it
    /// off.</b> <c>Brain.GetFeeling</c> early-returns
    /// <c>GetFinalLeaderBrain().GetFeeling(Target)</c> before it reads any opinion map, so a
    /// bodyguard's feeling <em>is</em> their captain's and its own <c>Opinions</c> are never
    /// consulted. Reporting the captain's view as the bodyguard's would be a quiet lie; naming the
    /// leader and stopping is the honest answer.
    /// </para>
    /// <para>
    /// <b>Decay is not surfaced per creature, deliberately.</b> Grudges lapse after 16,800 turns and
    /// kindnesses never do — <c>IOpinion.Duration</c> returns 0 for <c>BaseValue &gt;= 0</c>, which
    /// nothing overrides — and a per-creature countdown would be the same debug precision this power
    /// exists to avoid. The power's own description carries it instead.
    /// </para>
    /// <para>
    /// <b>The <c>scholarship</c> element is the tree's idiom</b>, not decoration: both
    /// <c>Customs_Tactful</c> and <c>Customs_TrashDivining</c> add exactly this on
    /// <c>GetItemElementsEvent</c>, and a third power in the tree that did not would be the odd one.
    /// </para>
    /// <para>
    /// Charter rule 5: no instance state, two event handlers, public members only, no Harmony and no
    /// reflection.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_CustomsRegard : BaseSkill
    {
        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade)
                || ID == PooledEvent<GetItemElementsEvent>.ID
                || ID == OwnerGetShortDescriptionEvent.ID;
        }

        public override bool HandleEvent(GetItemElementsEvent E)
        {
            if (E.IsRelevantCreature(ParentObject))
            {
                E.Add("scholarship", 3);
            }
            return base.HandleEvent(E);
        }

        public override bool HandleEvent(OwnerGetShortDescriptionEvent E)
        {
            Describe(E);
            return base.HandleEvent(E);
        }

        /// <summary>
        /// Vanilla's own five bands for how a people regard somebody, in its own vocabulary.
        /// </summary>
        /// <remarks>
        /// The words are <c>Faction.GetFeelingText</c>'s — despise, dislike, don't care, favor,
        /// revere — so a player reading this beside the faction screen sees the same escalation mean
        /// the same thing. The cut points are <c>Reputation.GetFeeling</c>'s own outputs: it maps
        /// reputation to exactly −100, −50, 0, +50 and +100, and an allegiance across several
        /// factions is a weighted mean of those, so the ranges below cover every value that can
        /// arrive.
        /// </remarks>
        private static string FactionPhrase(int Feeling)
        {
            if (Feeling <= -100) return "{{R|despise}}";
            if (Feeling <= -50) return "{{r|dislike}}";
            if (Feeling < 50) return "{{y|have no strong feeling about}}";
            if (Feeling < 100) return "{{g|favour}}";
            return "{{G|revere}}";
        }

        private void Describe(OwnerGetShortDescriptionEvent E)
        {
            GameObject subject = E.Object;
            if (subject == null || subject == ParentObject)
            {
                return;
            }

            // Vanilla suppresses its own Friendly/Neutral/Hostile line on these, in
            // Description.GetFeelingDescription. Anything it will not report, this does not either.
            if (subject.HasProperty("HideCon"))
            {
                return;
            }

            Brain brain = subject.Brain;
            if (brain == null || !ParentObject.HasID)
            {
                return;
            }

            GameObject leader = brain.GetFinalLeader();
            if (leader != null && leader != subject)
            {
                E.Postfix.Append("\nTakes their bearing from {{C|")
                    .Append(leader.BaseDisplayNameStripped)
                    .Append("}}, whose regard is the one that counts.");
                return;
            }

            E.Postfix.Append("\nTheir people ")
                .Append(FactionPhrase(brain.GetBaseFactionFeeling(ParentObject)))
                .Append(" you.");

            if (brain.Opinions.TryGetValue(ParentObject.BaseID, out OpinionList held) && held.Count > 0)
            {
                E.Postfix.Append("\nOf you they remember:");
                for (int i = 0; i < held.Count; i++)
                {
                    string line = held[i]?.GetText(subject);
                    if (!string.IsNullOrEmpty(line))
                    {
                        E.Postfix.Append("\n  ").Append(line);
                    }
                }
            }
            else
            {
                E.Postfix.Append("\nThey hold nothing against you personally.");
            }
        }
    }
}
