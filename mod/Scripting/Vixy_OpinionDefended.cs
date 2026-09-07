using XRL.World;
using XRL.World.Parts;

namespace XRL.World.AI
{
    /// <summary>
    /// What somebody remembers about having been fought for. #921.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The mirror vanilla only built one side of.</b> <c>OpinionKilledAlly</c> is −200 and
    /// <c>OpinionAttackAlly</c> −75, both formed in <c>Brain.HandleEvent(AIHelpBroadcastEvent)</c>
    /// — so the game already believes that what you do to somebody a person cares about is personal.
    /// Kill the thing that was <em>hunting</em> them and nothing is recorded at all. This is that
    /// entry.
    /// </para>
    /// <para>
    /// <b>10 × 5 is five defences on five separate days, ending at +50.</b> The same ceiling
    /// <c>Vixy_OpinionGift</c> reaches, at twice the rate per act, because standing between somebody
    /// and a thing trying to kill them is not handing them a waterskin. <c>AddOpinion</c> renews
    /// <c>Magnitude</c> by 1 behind the inherited <c>Cooldown</c> of 1200 turns, so defending the
    /// same person twice in one fight counts once — which is correct, and is also most of what keeps
    /// this rare.
    /// </para>
    /// <para>
    /// <b>Built on <c>OpinionBeguile</c>'s shape, exactly as <c>Vixy_OpinionGift</c> is</b> — small
    /// <c>BaseValue</c>, raised <c>Limit</c>, and <b>no <c>Initialize</c></b>. See
    /// <c>docs/FEATURES.md</c> §62.4 for why <c>OpinionMollify</c> is the trap rather than the
    /// template: its <c>Initialize</c> re-runs on every renewal and cancels the target's whole
    /// negative feeling in one act.
    /// </para>
    /// <para>
    /// <b>No <c>Duration</c> override, so this never expires</b> — the same decision, and the same
    /// reasoning, as the gift. <c>Limit</c> bounds the total, so permanence creates no faucet.
    /// </para>
    /// <para>
    /// The namespace is part of the save format and must never change; see
    /// <see cref="Vixy_OpinionGift"/>, which records why and what uninstalling costs.
    /// </para>
    /// <para>
    /// Charter rule 5: two properties, a two-field serialiser and a string.
    /// </para>
    /// </remarks>
    public class Vixy_OpinionDefended : IOpinionSubject
    {
        public override bool WantFieldReflection => false;

        /// <summary>The most defences that can ever count. See <see cref="Vixy_OpinionGift.Ceiling"/>.</summary>
        public const float Ceiling = 5f;

        public override int BaseValue => 10;

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
        /// Three bands cut at thirds of <c>Limit</c>, the same way the gift's are, so the two read
        /// as one system rather than two.
        /// </remarks>
        public override string GetText(GameObject Actor)
        {
            if (Magnitude >= Limit * 2f / 3f) return "Has stood between me and death.";
            if (Magnitude >= Limit / 3f) return "Has come to my aid more than once.";
            return "Fought something off me.";
        }
    }
}
