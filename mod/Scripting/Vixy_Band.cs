using System;
using System.Collections.Generic;
using QudExpandedCE;
using XRL.Rules;
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

        /// <summary>The selected reason for the journey.</summary>
        public const string MissionProperty = "Vixy_BandMission";

        /// <summary>The recorded holding the token left.</summary>
        public const string OriginProperty = "Vixy_BandOrigin";

        /// <summary>The vacancy the token was sent to fill.</summary>
        public const string TargetProperty = "Vixy_BandTarget";

        /// <summary>The ownership replacement that caused a counterraid.</summary>
        public const string TriggerProperty = "Vixy_BandTrigger";

        /// <summary>The scavenger journey phase.</summary>
        public const string LegProperty = "Vixy_BandLeg";

        /// <summary>The saved result of a scavenging trip.</summary>
        public const string ScavengerResultProperty = "Vixy_ScavengerResult";

        /// <summary>How many actual item units the token carries.</summary>
        public const string ScavengerCarriedProperty = "Vixy_ScavengerCarried";

        public const string ReclaimMission = "reclaim";
        public const string RivalExpansionMission = "rival-expansion";
        public const string ExpansionMission = "expansion";
        public const string CounterraidMission = "counterraid";
        public const string ScavengeMission = "scavenge";
        public const string OutboundLeg = "outbound";
        public const string ReturningLeg = "returning";
        public const string ScavengerCacheBlueprint = "Vixy_ScavengerCache";

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
        /// Resolve the mission when a token leaves the world map.
        /// </summary>
        private void Arrive(Zone Where)
        {
            if (ParentObject.GetStringProperty(MissionProperty) == ScavengeMission)
            {
                ArriveScavenger(Where);
                return;
            }

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

        /// <summary>
        /// Take only safe loose items at the target, then carry those same objects home.
        /// </summary>
        private void ArriveScavenger(Zone Where)
        {
            if (ParentObject.GetStringProperty(LegProperty) == ReturningLeg)
            {
                RecoverCargo(Where);
                return;
            }

            if (!Raven_Options.TravellingBands)
            {
                ParentObject.Obliterate();
                return;
            }

            CollectCargo(Where);
            if (!ReturnToOrigin(Where) && ParentObject.GetIntProperty(ScavengerCarriedProperty) == 0)
            {
                ParentObject.Obliterate();
            }
        }

        /// <summary>
        /// Collect one or two uniformly chosen item units from the zone's direct object list.
        /// Containers and every known player, story, or infrastructure marker stay out.
        /// </summary>

        private void CollectCargo(Zone Where)
        {
            ParentObject.RequirePart<Inventory>();

            List<GameObject> candidates = new List<GameObject>();
            List<GameObject> objects = Where.GetObjects();
            for (int i = 0; i < objects.Count; i++)
            {
                if (IsAbandonedLooseItem(objects[i])) candidates.Add(objects[i]);
            }

            int wanted = Math.Min(Stat.Random(1, 2), candidates.Count);
            for (int i = 0; i < wanted; i++)
            {
                int index = Stat.Random(0, candidates.Count - 1);
                GameObject item = candidates[index];
                candidates.RemoveAt(index);
                item.SplitFromStack();
                if (!ParentObject.ReceiveObject(item, NoStack: true, Context: "Vixy_Scavenge"))
                {
                    item.CheckStack();
                }
            }

            int carried = ParentObject.Inventory?.GetObjectStackCount() ?? 0;
            ParentObject.SetIntProperty(ScavengerCarriedProperty, carried);
            ParentObject.SetStringProperty(
                ScavengerResultProperty,
                carried == 0 ? "empty" : carried + (carried == 1 ? " item" : " items")
            );
        }

        /// <summary>
        /// A root object is abandoned only when the game gives no contrary ownership or protection
        /// signal. This deliberately never walks an inventory.
        /// </summary>
        private static bool IsAbandonedLooseItem(GameObject Item)
        {
            return Item != null
                && Item.CurrentCell != null
                && Item.IsReal
                && Item.Takeable
                && !Item.IsTemporary
                && !Item.IsCreature
                && !Item.IsCombatObject()
                && !Item.HasPart<Container>()
                && !Item.HasTag("Corpse")
                && Item.CanClear()
                && !Item.IsSpecialItem()
                && !Item.IsMarkedImportantByPlayer()
                && !Item.IsOwned()
                && !Item.OwnedByPlayer
                && Item.GetIntProperty("DroppedByPlayer") <= 0
                && Item.GetIntProperty("StoredByPlayer") <= 0
                && Item.GetIntProperty("FromStoredByPlayer") <= 0;
        }

        /// <summary>
        /// Lift the token back to its source parasang and give it a fresh travel part.
        /// </summary>
        private bool ReturnToOrigin(Zone Where)
        {
            string origin = ParentObject.GetStringProperty(OriginProperty);
            Cell world = Where.GetWorldCell();
            if (origin.IsNullOrEmpty() || world == null)
            {
                PreserveCargo("return blocked");
                return false;
            }

            ParentObject.RemovePart<AIWorldMapTravel>();
            ParentObject.SetStringProperty(LegProperty, ReturningLeg);
            if (!ParentObject.SystemMoveTo(world))
            {
                PreserveCargo("return blocked");
                return false;
            }

            AIWorldMapTravel travel = ParentObject.RequirePart<AIWorldMapTravel>();
            if (!travel.SetZoneID(origin))
            {
                ParentObject.RemovePart<AIWorldMapTravel>();
                PreserveCargo("return blocked");
                return false;
            }
            travel.Pinned = true;
            return true;
        }

        /// <summary>
        /// Put returned objects in a normal, inspectable container at the origin.
        /// </summary>
        private void RecoverCargo(Zone Where)
        {
            Inventory cargo = ParentObject.Inventory;
            if (cargo == null || cargo.GetObjectCountDirect() == 0)
            {
                ParentObject.Obliterate();
                return;
            }

            GameObject cache = GameObject.Create(ScavengerCacheBlueprint);
            Cell cell = cache == null ? null : Where.GetPullDownLocation(cache);
            if (cache == null || cell == null)
            {
                PreserveCargo("origin cache unavailable");
                return;
            }

            cell.AddObject(cache, Forced: true, System: true);
            while (cargo.GetObjectCountDirect() > 0)
            {
                GameObject item = cargo.GetFirstObjectDirect();
                if (!cache.ReceiveObject(item, NoStack: true, Context: "Vixy_Scavenge"))
                {
                    PreserveCargo("partial return");
                    return;
                }
            }
            ParentObject.Obliterate();
        }

        /// <summary>
        /// A failed recovery remains an openable token rather than losing carried objects.
        /// </summary>
        private void PreserveCargo(string Result)
        {
            ParentObject.RequirePart<Container>();
            ParentObject.DisplayName = "scavenger cache";
            ParentObject.SetStringProperty(ScavengerResultProperty, Result);
        }
    }
}
