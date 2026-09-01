using System;
using QudExpandedCE;

namespace XRL.World.Parts
{
    /// <summary>
    /// Scales experience by the gap between my tier and what I killed: less for punching down,
    /// more for punching up.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The design is Mura's, from the Experience Curve sub-mod. The implementation is not, and
    /// could not be.</b> That mod declared a class called <c>XRL.World.Parts.Experience</c> — the
    /// exact name vanilla uses — and relied on type resolution preferring the mod's. It does not:
    /// <c>ModManager.ResolveType</c> calls <c>Type.GetType</c> first, which searches
    /// <c>Assembly-CSharp</c>, so vanilla's type is found and the mod assemblies are never
    /// consulted. That C# has never run for anybody. #775 has the measurement, and
    /// <c>docs/LESSONS.md</c> the trap.
    /// </para>
    /// <para>
    /// <b>This is the supported shape instead.</b> <c>IXPEvent.TierScaling</c> is a public flag that
    /// vanilla's own <c>Experience</c> part gates its tier scaling on, and that <b>nothing in the
    /// game ever sets false</b> — an unwired switch whose single purpose is disabling exactly the
    /// behaviour being replaced here. So this part rewrites <c>E.Amount</c>, turns that flag off,
    /// and hands back. Vanilla still does the clamping, the global multiplier, the award, the
    /// write-back and the party pass-down. Only the curve is ours, and everything around it keeps
    /// tracking upstream.
    /// </para>
    /// <para>
    /// <b><c>Priority</c> is load-bearing.</b> Part order is dispatch order, this has to run before
    /// vanilla's <c>Experience</c>, and a higher priority is the only thing that moves a part
    /// earlier. <c>Experience</c> does not override <c>Priority</c>, so it sits at <c>IPart</c>'s
    /// default 45000; 90000 is vanilla's own value for parts that must go first — <c>Combat</c>,
    /// <c>Render</c>, <c>Body</c>, <c>Inventory</c> and <c>Brain</c> all use it. The alternative,
    /// <c>RegisterEvent</c>'s <c>Order</c> parameter, dispatches ahead of the parts list entirely
    /// and has <b>zero callers in the whole assembly</b>, so it was left alone.
    /// </para>
    /// <para>
    /// <b>Vanilla's zero floor is kept, and Mura's curve did not keep it.</b> His formula is
    /// <c>Amount / (gap + 1)</c> at every positive gap, which never reaches zero — so a level-30
    /// character farming trivia would keep earning. Vanilla stops paying at three tiers up and that
    /// is deliberate, so it stands. What is adopted is the middle: two tiers up pays a third rather
    /// than vanilla's tenth.
    /// </para>
    /// <para>
    /// <b>The bonus is x1.6 at three tiers up, and Mura's own comment says x1.3.</b> The comment
    /// describes increments of 0.05; the code is <c>i * -0.1</c>, giving 1 + (0.1 + 0.2 + 0.3). The
    /// code is what shipped and what he tuned against, so the code is what is ported. Written down
    /// because the annotation is the more persuasive of the two and reads as authoritative.
    /// </para>
    /// <para>
    /// Charter rule 5: no I/O, no network, no reflection, no Harmony. This reads two public fields
    /// on an event and writes one of them.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_XPCurve : IPart
    {
        /// <summary>Ahead of vanilla's <c>Experience</c> at 45000. See the remarks.</summary>
        public override int Priority => 90000;

        /// <summary>
        /// What the award was worth before this part touched it, kept only long enough for the
        /// annotation on the way out.
        /// </summary>
        /// <remarks>
        /// <c>[NonSerialized]</c> because it is transient by construction — it is written and read
        /// within a single award and means nothing across a save. Charter rule 5's obligation is
        /// that a <c>[Serializable]</c> type's layout is an identifier; this field stays out of it.
        /// </remarks>
        [NonSerialized]
        private int Base;

        /// <summary>Whether the award in flight was actually adjusted.</summary>
        [NonSerialized]
        private bool Adjusted;

        public override bool SameAs(IPart p) => true;

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade)
                || ID == AwardXPEvent.ID
                || ID == AwardedXPEvent.ID;
        }

        public override bool HandleEvent(AwardXPEvent E)
        {
            Adjusted = false;

            // Read live, so the option is genuinely a toggle in both directions: off, this part
            // leaves TierScaling alone and vanilla's own curve applies unchanged.
            if (!Raven_Options.XPCurve || E.Tier < 0)
            {
                return base.HandleEvent(E);
            }

            int before = E.Amount;
            int gap = (ParentObject.HasStat("Level") ? ParentObject.Stat("Level") / 5 : 1) - E.Tier;
            int amount = before;

            if (gap > 2)
            {
                // Vanilla's floor, kept deliberately: three tiers up is worth nothing.
                amount = 0;
            }
            else if (gap > 0)
            {
                // Mura's softening, inside the range vanilla still pays for: a half, then a third.
                amount = before / (gap + 1);
            }
            else if (gap < 0)
            {
                // 1 + 0.05 * g * (g + 1) is the closed form of Mura's accumulating loop:
                // one tier up 1.1, two 1.3, three 1.6.
                // Deliberately uncapped: x2.0 four tiers up, x4.6 at eight. The gap is
                // self-limiting, because the thing has to be killed first.
                int g = -gap;
                amount = (int)(before * (1.0 + 0.05 * g * (g + 1)));
            }

            E.Amount = amount;
            E.TierScaling = false;

            Base = before;
            Adjusted = amount != before;
            return base.HandleEvent(E);
        }

        /// <summary>
        /// Says why the number differed, after vanilla has said what it was.
        /// </summary>
        /// <remarks>
        /// Vanilla prints <c>You gain N XP!</c> and then sends this event, so an annotation here
        /// lands in the right order with nothing suppressed and no vanilla code replaced. Mura
        /// folded both into one line, which is not available without owning the award.
        /// </remarks>
        public override bool HandleEvent(AwardedXPEvent E)
        {
            if (Adjusted && ParentObject != null && ParentObject.IsPlayer())
            {
                int difference = E.Amount - Base;
                string label = difference > 0 ? "Bonus" : "Penalty";
                IComponent<GameObject>.AddPlayerMessage(
                    "(Base: {{C|" + Base + "}} | " + label + ": {{C|" + difference + "}})");
            }
            Adjusted = false;
            return base.HandleEvent(E);
        }
    }
}
