using System;
using System.Collections.Generic;
using QudExpandedCE;
using XRL.Rules;
using XRL.World.Conversations.Parts;

namespace XRL.World.Parts
{
    /// <summary>
    /// Notices when I am carrying a fortune, and occasionally sends somebody about it — raiders who
    /// want it, or a trader who heard I had it.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Item A2 of <c>docs/DESIGN_difficulty_systems.md</c></b>, split out as #189. That document's
    /// §0 governs it: it scales with <em>player power</em> rather than depth or elapsed time, it has
    /// to pass the two-question test — does the world explain it, does it create a decision — it
    /// ships behind an option defaulted off, and notoriety has to <em>sometimes</em> pay rather than
    /// only cost, which is the fourth constraint #644 added.
    /// </para>
    /// <para>
    /// <b>The decision it creates is carry or cache, and caching is genuinely safe.</b>
    /// <c>ZoneManager.FreezeZone</c> serialises a zone to disk rather than discarding it, and the
    /// only path that discards one — <c>DeleteZone</c> — is reachable solely from the
    /// <c>rebuild</c>/<c>flushandrebuild</c> wish commands. A homestead cache persists, so this asks
    /// a real question rather than setting a trap.
    /// </para>
    /// <para>
    /// <b>The axis is carried value, and nothing needed building to measure it.</b>
    /// <c>GameObject.ValueEach</c> runs <c>GetIntrinsicValueEvent</c>, then <c>AdjustValueEvent</c>,
    /// then <c>GetExtrinsicValueEvent</c> — and both <c>Inventory</c> and <c>Body</c> answer that
    /// last one by adding each contained or worn object's own <c>Value</c>, which recurses. So
    /// asking myself for <c>.Value</c> already totals everything I carry and wear. It is a property
    /// read, not a sum.
    /// </para>
    /// <para>
    /// <b>Value rather than artifacts, and the margin is not close.</b> The obvious alternative is
    /// <c>GiveArtifact.IsArtifact</c>, which this fork already uses in <c>Vixy_GiveArtifact</c>. Of
    /// the top fifty items by value, <b>69% is invisible to it</b> — the Otherpearl at 33,333,
    /// Gimeleth, the Kesil and Shemesh Faces, all seven Light Circles. <c>IsArtifact</c> measures
    /// ancient tech; this issue says fortune, and the treasure end is exactly the half it cannot
    /// see. Water counts too, at one per dram through <c>LiquidVolume</c>, which is correct for a
    /// setting where water is the currency.
    /// </para>
    /// <para>
    /// <b>They do not fail it on the <c>TinkerItem</c> clause, which is worth knowing before anyone
    /// tries to widen the predicate.</b> The Otherpearl inherits <c>TinkerItem</c> from <c>Armor</c>
    /// and Gimeleth inherits it from <c>MeleeWeapon</c>; both pass the first test. They fail the
    /// second by two different routes — the Otherpearl carries an <c>Examiner</c> from
    /// <c>BaseBracelet</c> that sets only <c>Alternate</c>, so its <c>Complexity</c> is the field's
    /// default of 0 and <c>0 &gt; 0</c> is false, while Gimeleth has no <c>Examiner</c> at all and
    /// falls through to the bare <c>return false</c>. Relaxing the <c>TinkerItem</c> requirement
    /// would therefore change nothing about what this can see.
    /// </para>
    /// <para>
    /// <b>So <c>IsArtifact</c> still decides <em>who</em> turns up, just not <em>whether</em>.</b>
    /// Mechanimists venerate ancient tech and the Putus Templar want it destroyed, so a hoard that
    /// is mostly artifacts draws different attention from one that is mostly treasure. That splits
    /// the two nouns cleanly instead of making one axis do both jobs.
    /// </para>
    /// <para>
    /// Charter rule 5: no I/O, no network, no reflection, no Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Hoard : IPart
    {
        /// <summary>Carried value before anybody takes an interest. See the remarks.</summary>
        /// <remarks>
        /// Deliberately high, and deliberately a round number rather than a tuned one: about twelve
        /// Nullray Pistols, or two and a half Zetachrome Lunes, or the Otherpearl by itself. I set
        /// it from blueprint data rather than from a real character, which is the same gap that made
        /// my #190 test plan wrong, so it is a starting position to be corrected against a save.
        /// </remarks>
        public const int Threshold = 15000;

        /// <summary>Chance in a hundred that a first arrival brings somebody who wants it.</summary>
        public const int RaiderChance = 3;

        /// <summary>
        /// The same, for the trader. Near-even with <see cref="RaiderChance"/> on purpose.
        /// </summary>
        /// <remarks>
        /// Rolled only when the raider roll misses, so the two can never arrive together and the
        /// effective rate is 2% of the 97% that miss — 1.94%, against 3%. Near enough to even that
        /// the system is not a difficulty tax with a story attached, which is what §0's fourth
        /// constraint is for. #190 is the deliberately lopsided one; this is not.
        /// </remarks>
        public const int TraderChance = 2;

        /// <summary>How far off somebody arrives, in cells.</summary>
        public const int ArrivalDistance = 8;

        /// <summary>The per-zone flag marking a zone as already rolled.</summary>
        /// <remarks>
        /// Its own key on the same store <c>Vixy_Notoriety</c> uses, so the two features share the
        /// mechanism without either knowing about the other — which is the sharing #189's own
        /// comments ask for, without the coupling. #802 has the reasoning.
        /// </remarks>
        public const string RolledProperty = "Vixy_HoardRolled";

        /// <summary>Whether this part has seen a zone yet since the game was loaded.</summary>
        /// <remarks>
        /// <c>[NonSerialized]</c> is the whole mechanism: it is false again after every load by
        /// definition, which is exactly the condition being detected. It also covers the option
        /// being switched on mid-session, where the zone I am standing in would otherwise roll the
        /// moment I took a step. #806.
        /// </remarks>
        [NonSerialized]
        private bool Resumed;

        /// <summary>Who comes for a hoard of ancient tech.</summary>
        /// <remarks>
        /// Both named in the issue: the Templar want artifacts destroyed, the Mechanimists want them
        /// venerated, and either is a reason to come and take them off me. Neither is sent unless
        /// they already want me dead — see <see cref="Willing"/>, which is why the Mechanimists are
        /// on this list at all rather than being a bug waiting for a friendly player.
        /// </remarks>
        public static readonly string[] TechRaiders = { "Templar", "Mechanimists" };

        /// <summary>Who comes for a hoard of ordinary treasure.</summary>
        public static readonly string[] WealthRaiders = { "Issachari" };

        /// <summary>Traders who deal in ancient tech.</summary>
        public static readonly string[] TechTraders =
        {
            "Gunsmith", "Armorer", "Grenadier", "DiskMerchant",
        };

        /// <summary>Traders who deal in everything else worth carrying.</summary>
        public static readonly string[] WealthTraders = { "Jeweler", "Gemcutter", "Apothecary" };

        public override bool SameAs(IPart p) => true;

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == EnteredCellEvent.ID;
        }

        public override bool HandleEvent(EnteredCellEvent E)
        {
            if (!Raven_Options.CarriedHoard || E.Object != ParentObject)
            {
                return base.HandleEvent(E);
            }
            if (!Arrived()) return base.HandleEvent(E);

            // The threshold is checked after the zone is retired, not before, so a zone I walked
            // through while poor is spent all the same. Otherwise every zone visited before the
            // first fortune would stay armed, and coming into money would set off everywhere I had
            // already been the next time I walked back through it.
            if (ParentObject.Value < Threshold) return base.HandleEvent(E);

            bool tech = MostlyArtifacts();
            if (Stat.Random(1, 100) <= RaiderChance)
            {
                SendRaiders(tech);
            }
            else if (Stat.Random(1, 100) <= TraderChance)
            {
                SendTrader(tech);
            }
            return base.HandleEvent(E);
        }

        /// <summary>
        /// True once per zone, on the first arrival in it — and never again in that zone.
        /// </summary>
        /// <remarks>
        /// The zone is retired before anything is rolled, so a failed roll spends it too and walking
        /// back through is inert. Vanilla's <c>CheckPsychicHunters</c> does it in this order and
        /// #802 has the reasoning; the flag lives on <c>ZoneManager.ZoneProperties</c>, which the
        /// manager serialises itself, so this part's layout stays free to change.
        /// </remarks>
        private bool Arrived()
        {
            Zone zone = ParentObject.CurrentZone;
            if (zone == null || zone.IsWorldMap() || zone.ZoneID.IsNullOrEmpty()) return false;

            // Resuming a save is not arriving somewhere. The first zone seen after a load is still
            // retired, so it cannot fire later either, but nothing is rolled in it. #806.
            bool resuming = !Resumed;
            Resumed = true;

            if (The.ZoneManager.HasZoneProperty(zone.ZoneID, RolledProperty)) return false;
            The.ZoneManager.SetZoneProperty(zone.ZoneID, RolledProperty, true);
            return !resuming;
        }

        /// <summary>
        /// Whether most of what I am carrying, by value, is ancient tech rather than treasure.
        /// </summary>
        /// <remarks>
        /// Measured as a share rather than a count, because a count cannot tell one Otherpearl from
        /// forty grenades. <c>GiveArtifact.IsArtifact</c> is <c>public static</c> and is the
        /// predicate <c>Vixy_GiveArtifact</c> already uses, so the definition of <em>artifact</em>
        /// comes from vanilla and cannot drift between this fork's two answers to that question —
        /// it would be a real defect for the hoard index to count something the give-artifact picker
        /// then declined to offer.
        /// </remarks>
        private bool MostlyArtifacts()
        {
            Inventory inventory = ParentObject.Inventory;
            if (inventory == null) return false;

            double artifacts = 0.0;
            foreach (GameObject item in inventory.GetObjects(GiveArtifact.IsArtifact))
            {
                artifacts += item.Value;
            }
            return artifacts * 2.0 >= ParentObject.Value;
        }

        /// <summary>Puts a band of them in the zone, come to take it.</summary>
        /// <remarks>
        /// <para>
        /// Ordinary members rather than <c>HeroMaker</c> heroes, and that is the difference between
        /// a band and a boss. #190 sends one named champion because one is the whole event there;
        /// here the fiction is a raiding party, and two or three near my level is a fight I can lose
        /// without it being a wall.
        /// </para>
        /// <para>
        /// <b>"Near my level" is chosen, not assigned, and that distinction killed a character.</b>
        /// This used to take any member of the faction and write my level onto its <c>Level</c>
        /// stat, which changes an integer and nothing else — the Templar pool runs from 9 to 39 and
        /// is mostly level-24 knights, so a party of three arrived with ninety hit points, fullerite
        /// armour and rifles apiece however small the number said they were.
        /// <see cref="Vixy_Arrivals.NearLevel"/> picks by the blueprint's own authored level and
        /// returns nothing when the faction has nobody suitable, which is why this can now decline
        /// to send anyone at all. #806.
        /// </para>
        /// </remarks>
        private void SendRaiders(bool tech)
        {
            string faction = Willing(tech ? TechRaiders : WealthRaiders);
            if (faction.IsNullOrEmpty()) return;

            int placed = 0;
            int wanted = Stat.Random(2, 3);
            for (int i = 0; i < wanted; i++)
            {
                // Drawn per raider rather than once for the band, so a party is not three copies of
                // one blueprint when the faction has more than one to offer.
                GameObjectBlueprint pick =
                    Vixy_Arrivals.NearLevel(faction, ParentObject.Stat("Level"));
                if (pick == null) return;

                Cell landing = Landing();
                if (landing == null) break;

                GameObject who = GameObject.Create(pick.Name);
                if (who == null) continue;

                landing.AddObject(who);
                placed++;
            }
            if (placed == 0) return;

            // Hostile creatures attack rather than talk, so the arrival line is the whole of the
            // explanation - the same constraint #632 established and #190 records.
            IComponent<GameObject>.AddPlayerMessage(
                "{{R|" + Faction.GetFormattedName(faction) + "}} have come for what you are carrying.");
        }

        /// <summary>
        /// One of <paramref name="factions"/> that already wants me dead, or null if none does.
        /// </summary>
        /// <remarks>
        /// <b>Somebody has to be willing to rob me, and most of Qud is not.</b> The Templar open at
        /// -700 and the Issachari at -475, so both are past <c>Brain.GetFeelingLevel</c>'s -10 line
        /// from the start — but the <b>Mechanimists open at 0</b>. Sent unfiltered they would arrive
        /// perfectly friendly and stand there while the message announced they had come for my
        /// hoard, which is #190's envoy bug wearing the other face. Filtering here rather than
        /// forcing hostility afterwards keeps the world's own answer: a faction I am on good terms
        /// with does not raid me, and if I mend things with the Templar they stop coming.
        /// </remarks>
        private static string Willing(string[] factions)
        {
            List<string> hostile = new List<string>();
            foreach (string faction in factions)
            {
                if (The.Game.PlayerReputation.GetFeeling(faction) <= -10) hostile.Add(faction);
            }
            return hostile.Count == 0 ? null : hostile.GetRandomElement();
        }

        /// <summary>Puts one trader in the zone, come to deal.</summary>
        /// <remarks>
        /// <para>
        /// <b>This is §0's fourth constraint, and it is the piece most at risk.</b> Vanilla wrote
        /// its own version of this valve — <c>PsychicHunterSystem.CreateExtradimensionalSoloDeviant</c>,
        /// which clears allegiance, joins a faction, attaches a conversation and never sets
        /// <c>Hostile</c> — and then never called it. It appears once in the whole assembly, its own
        /// definition, against fifteen mentions of the three hostile creators beside it. So across
        /// the entirety of Qud's only notoriety system, the number of shipping encounters where
        /// notoriety pays rather than costs is <b>zero</b>. I built this first for that reason.
        /// </para>
        /// <para>
        /// <b>A merchant blueprint rather than a conversation of my own.</b> <c>BaseMerchant</c>
        /// already carries a <c>GenericMerchant</c> conversation, the neutral <c>Merchants</c>
        /// faction and a <c>GenericInventoryRestocker</c>, so these arrive able to trade with stock
        /// in hand. Writing dialogue would have produced something worse and taken longer.
        /// </para>
        /// </remarks>
        private void SendTrader(bool tech)
        {
            // A trader who would not talk to me is not an opportunity. Merchants are neutral by
            // default, so this only bites if I have made an enemy of them.
            if (The.Game.PlayerReputation.GetFeeling("Merchants") <= -10) return;

            Cell landing = Landing();
            if (landing == null) return;

            GameObject who = GameObject.Create((tech ? TechTraders : WealthTraders).GetRandomElement());
            if (who == null) return;

            landing.AddObject(who);
            IComponent<GameObject>.AddPlayerMessage(
                "{{G|" + who.DisplayNameOnly
                + "}} has sought you out, having heard what you are carrying.");
        }

        /// <summary>A passable cell a walk away, or null if there is not one.</summary>
        /// <remarks>
        /// The bare <c>getClosestPassableCell()</c> sorts every passable cell in the zone by distance
        /// from its own and returns the nearest — called on my cell, that is my cell. The predicate
        /// overload keeps the nearest-first ordering, so a floor lands them at the edge of the room.
        /// Both overloads return the cell they were called on when nothing matches, which is the case
        /// that has to be caught rather than used.
        /// </remarks>
        private Cell Landing()
        {
            Cell cell = ParentObject.CurrentCell;
            if (cell == null) return null;

            Cell landing = cell.getClosestPassableCell(c => c.DistanceTo(cell) >= ArrivalDistance);
            return (landing == null || landing == cell) ? null : landing;
        }
    }
}
