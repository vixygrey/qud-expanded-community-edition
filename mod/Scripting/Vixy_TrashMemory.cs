using System;
using QudExpandedCE;
using XRL.World.Parts.Skill;

namespace XRL.World.Parts
{
    /// <summary>
    /// Remembers how much of a zone's trash has already been gone through, so the eightieth
    /// pile in a room has less to say than the first.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The headline rate was never the problem.</b> Trash Divining rolls a flat 5% per pile and
    /// says so, which reads as a trickle. Pile counts are what turn it into a salary: vanilla's
    /// <c>CatacombsGlobals</c> lays down 80-100 piles per zone, so one catacombs zone pays roughly
    /// four or five secrets. A player who spent 150 points and reached Intelligence 21 bought that
    /// skill, so the 5% stays exactly where it is — the first pile in any zone pays full price, and
    /// what falls away is the twentieth and the fiftieth. See #605.
    /// </para>
    /// <para>
    /// <b>Modelled on <c>TrashOracle</c>, which vanilla wrote and never wired up.</b> That part
    /// exists to do this exact job — it guards on <c>E.Skill is Customs_TrashDivining</c> and
    /// rewrites <c>E.Chance</c> — and no blueprint in the game carries it, the same shape
    /// <c>docs/LESSONS.md</c> records for hidden mutations. It could not be used as-is: its
    /// <c>Bonus</c> and <c>Magnitude</c> are flat, with nowhere to put a per-zone count, and
    /// <c>IActivePart</c> brings charge, power and breakage semantics that mean nothing on a
    /// player. Its guard clause is copied exactly, because that is the intended idiom.
    /// </para>
    /// <para>
    /// <b>Counts piles rifled, not secrets found.</b> The event fires <em>before</em> the roll and
    /// never learns its outcome, so successes are not observable from here. Piles are: this handler
    /// is called once per rifle, which makes the count exact rather than inferred. It is also the
    /// better fiction — a picked-over room has run out of things to tell you whether or not you
    /// understood them.
    /// </para>
    /// <para>
    /// <b>Integer bands, not halving.</b> <c>GetSkillEffectChanceEvent.GetFor</c> runs with
    /// <c>ConstrainToPercentage</c>, so the chance is a whole percent and 2.5% cannot be said.
    /// Halving 5 by integer division gives 5, 2, 1, 0 — far steeper than intended, and it switches
    /// a bought skill off entirely in a dense zone. The band table never reaches zero for that
    /// reason.
    /// </para>
    /// <para>
    /// The bands leave thin zones alone, which is the point: at 20-33 piles a rustwell paid about
    /// 1.3 secrets before and about 1.2 after, while the catacombs fall from about 4.5 to about
    /// 2.3. Density was the fault and density is what is corrected.
    /// </para>
    /// <para>
    /// <b>Scales <c>E.Chance</c> rather than assigning it</b>, so anything else that has already
    /// spoken — a <c>TrashOracle</c> on some future item, another mod — is scaled with it instead
    /// of being silently discarded. <c>E.BaseChance</c> is the divisor because it is the untouched
    /// figure the call started from.
    /// </para>
    /// <para>
    /// <b>The count lives on the zone, so nothing is added to the save.</b>
    /// <c>Zone.SetZoneProperty</c> is vanilla's own mechanism for exactly this, and there is a use
    /// of it on the trash blueprint already: <c>BurnGenerateObjectInCell</c> with
    /// <c>PerZone="true"</c> remembers its rolled result under a namespaced key the same way. It is
    /// string-typed, hence the parse. An instance field here would instead be frozen into every
    /// save's layout in the sense of <c>docs/STYLEGUIDE.md</c> §1, which
    /// <c>validate_mod.py</c>'s <c>serializable-shape</c> asks be a decision rather than an
    /// accident.
    /// </para>
    /// <para>
    /// <b>The count accrues even while the option is off</b>, and only the adjustment is
    /// conditional. Otherwise switching it off in a rich zone and back on afterwards would hand
    /// back a fresh 5%, which makes the off-switch a lever rather than a preference.
    /// </para>
    /// <para>
    /// <b>Followers keep vanilla's rate.</b> The event fires on whoever is rifling, and this part
    /// is on the player, so a follower's rifling neither decays this counter nor is decayed by it.
    /// Vanilla gates the whole secret branch on the rifler holding Trash Divining itself, with
    /// <c>IsPlayerLed()</c> and the player's own skill checked on top, so a follower who qualifies
    /// at all is rare. Leaving that case at vanilla rates is the conservative reading of #605.
    /// </para>
    /// <para>
    /// Charter rule 5: one event handler, one integer on a zone. No I/O, no reflection, no Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_TrashMemory : IScribedPart
    {
        /// <summary>Namespaced the way vanilla namespaces its own zone properties.</summary>
        private const string RifledKey = "Vixy_TrashDivining_Rifled";

        /// <summary>How many piles a zone gives at each rate before dropping to the next.</summary>
        private const int BandSize = 20;

        /// <summary>Percent chance per band. The last entry is the floor and never runs out.</summary>
        private static readonly int[] BandChance = { 5, 3, 2, 1 };

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == GetSkillEffectChanceEvent.ID;
        }

        public override bool HandleEvent(GetSkillEffectChanceEvent E)
        {
            if (E.Skill is Customs_TrashDivining)
            {
                // The rifled count is a *zone* property, shared by everyone standing in it, so an
                // NPC carrying this part does not just skew its own odds - it spends down the player's
                // own odds in that zone. This part is only ever attached to the player, but
                // `GameObject.DeepCopy` copies every part, so a temporal fugue duplicate or a clone
                // carries it too. #769.
                if (!ParentObject.IsPlayerControlled())
                {
                    return base.HandleEvent(E);
                }

                Zone zone = ParentObject?.CurrentZone;
                if (zone != null)
                {
                    int rifled = RifledIn(zone);
                    zone.SetZoneProperty(RifledKey, (rifled + 1).ToString());

                    if (Raven_Options.TrashDiviningDensity && E.BaseChance > 0)
                    {
                        E.Chance = E.Chance * ChanceAfter(rifled) / E.BaseChance;
                    }
                }
            }

            return base.HandleEvent(E);
        }

        /// <summary>The percent this pile is worth, given how many came before it here.</summary>
        private static int ChanceAfter(int rifled)
        {
            int band = Math.Min(rifled / BandSize, BandChance.Length - 1);
            return BandChance[band];
        }

        /// <summary>How many piles have been rifled in this zone. Zero for a zone never entered.</summary>
        private static int RifledIn(Zone zone)
        {
            return int.TryParse(zone.GetZoneProperty(RifledKey, "0"), out int rifled) ? rifled : 0;
        }
    }
}
