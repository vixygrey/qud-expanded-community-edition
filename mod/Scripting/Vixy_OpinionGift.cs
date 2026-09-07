using XRL.World;
using XRL.World.Parts;

namespace XRL.World.AI
{
    /// <summary>
    /// What somebody remembers about having been given something. #634.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The ledger is 22 opinions and 17 of them are grievances.</b> The five positives are
    /// <c>OpinionSummon</c> (+50), <c>OpinionProselytize</c> (+25), <c>OpinionBeguile</c> (+5),
    /// <c>OpinionMollify</c> (+1) and <c>OpinionRebuke</c> — earned by summoning, converting,
    /// beguiling, or being calmed. So the only reliable way to be thought well of by an individual
    /// in Qud is to override their will. This is the entry that is neither a grievance nor a
    /// compulsion.
    /// </para>
    /// <para>
    /// <b>Modelled on <c>OpinionBeguile</c>, not <c>OpinionMollify</c>.</b> Both are
    /// <c>IOpinionSubject</c> with a small <c>BaseValue</c> and a raised <c>Limit</c>, but Mollify
    /// also overrides <c>Initialize</c> — and <c>Brain.AddOpinion</c> calls that again on
    /// <em>every</em> renewal, where it raises <c>Magnitude</c> to cancel the target's entire
    /// current negative feeling. One waterskin handed to somebody whose faction sits at −100 would
    /// wipe the whole deficit in a single act, which is the <i>murder becomes an accounting
    /// problem</i> failure #634 was filed to avoid. Beguile is that same shape with the trap already
    /// absent, so it is the one to copy.
    /// </para>
    /// <para>
    /// <b>5 × 10 is ten gifts over ten days, ending at +50.</b> <c>AddOpinion</c> starts
    /// <c>Magnitude</c> at 1 and renews it as
    /// <c>Magnitude = min(Limit, Magnitude + 1)</c> behind the inherited <c>Cooldown</c> of 1200
    /// turns — one game day — and <c>Value</c> is <c>BaseValue * Magnitude</c>. So the second gift
    /// inside a day counts for nothing and the tenth on the tenth day brings the total to
    /// <b>+50</b>, which is exactly <c>Brain.GetFeelingLevel</c>'s Allied threshold. That is the
    /// point of the number: a full course of gifts crosses a band the player can see, twice over
    /// the five values faction feeling actually takes — a neutral person reaches Allied and a
    /// disliked one reaches Neutral. A ceiling of +40 was the first proposal and would have changed
    /// what a player can observe in one case out of five.
    /// </para>
    /// <para>
    /// <b>No <c>Duration</c> override, so this never expires.</b> <c>IOpinion.Duration</c> returns 0
    /// for a non-negative <c>BaseValue</c> and 16,800 turns otherwise, which nothing overrides — so
    /// vanilla's ledger is asymmetric in a second way beyond the 17-to-5 count: the grievances are
    /// the ones that heal. Left alone deliberately. <c>Limit</c> already bounds the total, so
    /// permanence creates no faucet, and requiring the player to top a friendship up would turn a
    /// gesture into a chore.
    /// </para>
    /// <para>
    /// <b>The namespace is now part of the save format and must never change.</b>
    /// <c>SerializationWriter.WriteDirect(Type)</c> writes <c>Type.FullName</c> for any type whose
    /// assembly is in <c>LocalAssemblies</c>, and <c>SerializationWriter.Init</c> adds every mod
    /// assembly to that set — so saves record <c>XRL.World.AI.Vixy_OpinionGift</c> in full, and
    /// <c>ModManager.ResolveType</c> finds it again through <c>modAssembly.GetType(fullName)</c>.
    /// Moving this class to another namespace would orphan every opinion already written.
    /// </para>
    /// <para>
    /// <b>Uninstalling the mod costs the whole ledger of any creature holding one of these, and
    /// nothing else.</b> <c>ReadTokenizedType</c> throws on a type it cannot resolve,
    /// <c>DeserializeComposite</c> catches and returns null, and <c>OpinionList.Read</c>
    /// dereferences it with no guard — unlike <c>GameObject.Load</c> and <c>Effect.Load</c>, which
    /// both check. But <c>Brain.Read</c> reaches it through <c>ReadComposite&lt;OpinionMap&gt;()</c>,
    /// which opens its own length-prefixed block and catches, and <c>SkipBlock</c> repositions the
    /// stream cleanly. So a creature that remembered a gift forgets its ledger — gratitude and
    /// grudges alike — while its Brain, faction, AI and conversation all survive. Written up in
    /// <c>docs/FEATURES.md</c>, because it is the first time this fork has put a type of its own
    /// into a vanilla collection.
    /// </para>
    /// <para>
    /// <c>Write</c> and <c>Read</c> are hand-written. Vanilla's opinions carry
    /// <c>[GenerateSerializationPartial]</c> and have these generated for them, which a mod cannot
    /// use — so they are copied verbatim from <c>OpinionBeguile</c>'s generated pair, and
    /// <c>WantFieldReflection</c> is turned off to match. Leaving it on would serialise the same two
    /// fields a second way.
    /// </para>
    /// <para>
    /// Charter rule 5: two properties, a two-field serialiser and a string. No I/O, no reflection,
    /// no Harmony.
    /// </para>
    /// </remarks>
    public class Vixy_OpinionGift : IOpinionSubject
    {
        public override bool WantFieldReflection => false;

        /// <summary>
        /// The most gifts that can ever count, and the one place the ceiling is written.
        /// </summary>
        /// <remarks>
        /// A constant rather than a literal on <see cref="Limit" />, because
        /// <see cref="Familiar" /> needs the same number and a static cannot read an instance
        /// property without allocating an opinion to ask.
        /// </remarks>
        public const float Ceiling = 10f;

        public override int BaseValue => 5;

        public override float Limit => Ceiling;

        public override void Write(SerializationWriter Writer)
        {
            Writer.Write(Magnitude);
            Writer.WriteOptimized(Time);
        }

        public override void Read(SerializationReader Reader)
        {
            Magnitude = Reader.ReadSingle();
            Time = Reader.ReadOptimizedInt64();
        }

        /// <summary>
        /// What <c>Vixy_CustomsRegard</c> prints under <i>"Of you they remember:"</i>.
        /// </summary>
        /// <remarks>
        /// Three bands rather than vanilla's one fixed line. Vanilla's opinions say the same
        /// sentence whatever their magnitude because nothing player-facing ever read them —
        /// <c>IOpinion</c>'s own doc comment says so. Take the Measure does read them, and
        /// <i>"Gave me something."</i> repeated identically after ten gifts would report a
        /// relationship that has visibly gone nowhere. The cuts are at a third and two thirds of
        /// <c>Limit</c>, so they move with the ceiling rather than being pinned to it.
        /// </remarks>
        public override string GetText(GameObject Actor)
        {
            if (Magnitude >= Limit * 2f / 3f) return "Has given me much.";
            if (Magnitude >= Limit / 3f) return "Has been generous with me.";
            return "Gave me something.";
        }

        /// <summary>
        /// How much <paramref name="Speaker" /> has been given by <paramref name="Subject" />, as a
        /// count of gifts that counted. Zero when there is no such opinion.
        /// </summary>
        /// <remarks>
        /// <b><c>Brain.TryGetOpinions</c> is deliberately not used.</b> It is not a read-only
        /// accessor — where no list exists it writes one,
        /// <c>Opinions[Subject.BaseID] = (List = new OpinionList())</c> — so asking this question
        /// through it would add an empty <c>OpinionList</c> to every creature asked about, mutating
        /// save state from a read. <c>Opinions</c> is a public field and
        /// <c>Dictionary.TryGetValue</c> creates nothing. <c>Vixy_CustomsRegard</c> avoids the same
        /// trap for the same reason.
        /// </remarks>
        public static float Given(GameObject Speaker, GameObject Subject)
        {
            Brain brain = Speaker?.Brain;
            if (brain == null || Subject == null || !Subject.HasID) return 0f;
            if (!brain.Opinions.TryGetValue(Subject.BaseID, out OpinionList held)) return 0f;
            for (int i = 0; i < held.Count; i++)
            {
                if (held[i] is Vixy_OpinionGift gift) return gift.Magnitude;
            }
            return 0f;
        }

        /// <summary>
        /// Whether giving has gone on long enough to stop being remarkable.
        /// </summary>
        /// <remarks>
        /// <b>The same cut as <see cref="GetText" />'s top band, and that is the point.</b> The
        /// examine line reads <i>"Has given me much."</i> from exactly here, so the two surfaces a
        /// player can see — the ledger and the reply in the moment — change together rather than at
        /// two thresholds nobody could line up. One number, expressed once: two thirds of
        /// <c>Limit</c>, which is the seventh gift of ten and moves if the ceiling ever does.
        /// </remarks>
        public static bool Familiar(GameObject Speaker, GameObject Subject)
        {
            return Given(Speaker, Subject) >= Ceiling * 2f / 3f;
        }
    }
}
