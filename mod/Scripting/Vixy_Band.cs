using System;
using QudExpandedCE;
using XRL.World.ZoneBuilders;

namespace XRL.World.Parts
{
    /// <summary>
    /// A band crossing the world map, and the party it becomes when it arrives. #832.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The token is not the party, because it cannot be.</b> <c>Brain.GoToPartyLeader</c> refuses
    /// world-map targets outright — <c>if (TargetCell.ParentZone.IsWorldMap()) return false;</c> —
    /// and <c>JoinPartyLeaderCommand</c> applies that rule generically across every cached zone, so
    /// a leader lifted onto the map strands its whole retinue. <c>SystemMoveTo</c> moves one object
    /// and there is no party-move. So one object travels and the party is *built* at the
    /// destination.
    /// </para>
    /// <para>
    /// <b>Built by vanilla's own builder, which is public.</b>
    /// <c>FactionEncounters.BuildFactionEncounter(Faction, Zone, ZoneLevel, ZoneTier)</c> is
    /// <c>public static</c>, and it is what places every faction camp in the game — a
    /// <c>HeroMaker</c> leader from <c>BaseFactionHeroTemplate_&lt;Faction&gt;</c>, members bound by
    /// <c>SetAlliedLeader&lt;AllyRetinue&gt;</c>, and the right inventories and props. So an arriving
    /// band is indistinguishable from a placed one, because it is one.
    /// </para>
    /// <para>
    /// <b>Only while I am on the world map.</b> <c>ZoneManager.Tick</c> marks and weathers the
    /// active zone and nothing else, so <c>AIWorldMapTravel.TurnTick</c> reaches this only when the
    /// world map is the active zone. A band advances while I travel overland and stands still while
    /// I am underground. That is a fiction compromise stated rather than hidden: the world moves
    /// when I move through it.
    /// </para>
    /// <para>
    /// <b>Arrival is detected by leaving the world map, not by reaching a cell.</b>
    /// <c>AIWorldMapTravel.TakeAction</c> ends its journey with
    /// <c>SystemMoveTo(GetPullDownLocation(...))</c>, which drops the token into the destination
    /// zone — and <c>CheckZone</c> then removes the travel part on the next <c>EnteredCellEvent</c>.
    /// Both parts see that event and part order is not something to depend on, so this asks the only
    /// question that is true either way: <em>am I somewhere that is not the world map?</em>
    /// </para>
    /// <para>
    /// Charter rule 5: one event handler and a call into a vanilla builder. No I/O, no reflection,
    /// no Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Band : IPart
    {
        /// <summary>
        /// Where the band's faction is kept — a property on the token, not a field on this part.
        /// </summary>
        /// <remarks>
        /// Charter rule 5: a <c>[Serializable]</c> type's field layout is written into every save
        /// and becomes an identifier, so every scripted type in this fork holds zero instance state
        /// and <c>serializable-shape</c> fires the moment one does not. A string property on the
        /// object is serialised with the object and carries no such obligation — the same choice
        /// <c>Vixy_Notoriety</c> made when it put its tallies in game state rather than in the part.
        /// </remarks>
        public const string FactionProperty = "Vixy_BandFaction";

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == EnteredCellEvent.ID;
        }

        public override bool HandleEvent(EnteredCellEvent E)
        {
            Zone zone = E.Cell?.ParentZone;
            if (zone != null && !zone.IsWorldMap())
            {
                Arrive(zone);
            }
            return base.HandleEvent(E);
        }

        /// <summary>
        /// Become a real party here, and stop being a token.
        /// </summary>
        /// <remarks>
        /// <para>
        /// <b>The token removes itself either way.</b> If the encounter cannot be built — an unknown
        /// faction, a zone with nowhere to put anybody — leaving a banner lying in a ruin would be
        /// worse than the band never having come. <c>Obliterate</c> rather than <c>Destroy</c>
        /// because there is no corpse to leave and nothing should drop.
        /// </para>
        /// <para>
        /// Level and tier come from the destination rather than from the band, so a war party that
        /// walks into the deep jungle arrives as the jungle's problem. That is
        /// <c>HandleFactionEncounterWish</c>'s own default and it wants no cleverness.
        /// </para>
        /// </remarks>
        private void Arrive(Zone Where)
        {
            string Faction = ParentObject.GetStringProperty(FactionProperty);
            if (!Faction.IsNullOrEmpty() && Raven_Options.TravellingBands)
            {
                try
                {
                    FactionEncounters.BuildFactionEncounter(
                        Faction, Where, Where.Level, Where.NewTier
                    );
                }
                catch (Exception x)
                {
                    MetricsManager.LogException("Vixy_Band arrival", x);
                }
            }

            ParentObject.Obliterate();
        }
    }
}
