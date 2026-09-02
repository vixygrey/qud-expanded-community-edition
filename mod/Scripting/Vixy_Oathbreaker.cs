using System;
using QudExpandedCE;

namespace XRL.World.Parts
{
    /// <summary>
    /// Makes killing a water-sibling cost everything, rather than a hundred off every ledger.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Part of #753. Vanilla already punishes this heavily and I want to be accurate about how
    /// heavily, because the change here is smaller than it sounds. <c>GivesRep</c>'s death handler
    /// checks <c>wasParleyed</c> and then walks <em>every visible faction that does not already hate
    /// me</em>, taking about a hundred from each:
    /// </para>
    /// <para>
    /// <code>
    /// foreach (Faction item in Factions.Loop())
    ///     if (item.Visible &amp;&amp; !item.HatesPlayer)
    ///         PlayerReputation.Modify(item, VaryRep(-100), …, "WaterRitualCurse", …);
    /// </code>
    /// </para>
    /// <para>
    /// Seventy visible factions, so roughly <b>seven thousand reputation</b> destroyed in one act,
    /// plus another two hundred with the victim's own people from the ordinary legendary-kill
    /// penalty. It is one of the harshest events in the game already.
    /// </para>
    /// <para>
    /// <b>The flaw is that it is flat.</b> At 700 with a faction I drop to 600 and am still
    /// <em>loved</em> — the bands are 250 for liked and 600 for loved. So the people who knew me best
    /// forgive me most easily, which is precisely backwards for this crime. A curse that leaves me
    /// with friends is not a curse.
    /// </para>
    /// <para>
    /// <b>So standing falls to nothing first, and then the curse lands.</b> Anyone who was above
    /// neutral ends at about -100 regardless of how far above they were; anyone at or below neutral
    /// is untouched by this and takes vanilla's hundred exactly as before. Nobody who hears of it
    /// still likes me, which is the whole of the rule and the whole of the change.
    /// </para>
    /// <para>
    /// <b>One line does it, because the amount is a delta.</b> Subtracting the current standing makes
    /// the result land on the penalty itself: <c>standing + (amount - standing) == amount</c>. The
    /// variance vanilla rolls into <c>VaryRep</c> is preserved rather than replaced by a number of
    /// mine.
    /// </para>
    /// <para>
    /// <b>Left alone deliberately: the curse reaches mollusks and fish.</b> #190's reasoning about
    /// which peoples can hear about a thing would exclude them, and I have not applied it, because
    /// here it would <em>soften</em> the punishment. Tightening that fiction is a separate argument
    /// from making the sentence bite, and it pulls the other way.
    /// </para>
    /// <para>
    /// <c>ReputationChangeEvent</c> is vanilla's own hook — <c>Reputation.Modify</c> routes every
    /// change through <c>GetFor</c> before it lands, and it dispatches to <c>The.Player</c>.
    /// <c>CyberneticsSocialCoprocessor</c> is the shipped precedent for reading <c>E.Type</c> and
    /// scaling <c>E.Amount</c>. Charter rule 5: no I/O, no network, no reflection, no Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Oathbreaker : IPart
    {
        /// <summary>The type vanilla tags the water-ritual curse with.</summary>
        public const string CurseType = "WaterRitualCurse";

        public override bool SameAs(IPart p) => true;

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == ReputationChangeEvent.ID;
        }

        public override bool HandleEvent(ReputationChangeEvent E)
        {
            if (!Raven_Options.Oathbreaker || E.Faction == null || E.Type != CurseType)
            {
                return base.HandleEvent(E);
            }

            // Prospective changes are answered too, so anything asking what this would cost is told
            // the truth rather than vanilla's flat hundred.
            int standing = The.Game.PlayerReputation.Get(E.Faction);
            if (standing > 0) E.Amount -= standing;

            return base.HandleEvent(E);
        }
    }
}
