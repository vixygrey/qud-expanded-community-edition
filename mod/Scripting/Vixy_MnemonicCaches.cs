using System;
using System.Collections.Generic;
using QudExpandedCE;
using XRL.Rules;
using XRL.World;

namespace XRL
{
    /// <summary>
    /// Gives each newly built procedural ruin or historic-site dungeon floor one finite chance to
    /// contain an ancient mnemonic cache. #1060.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Eligibility is positive generator provenance, not a zone name. Vanilla's RuinsCell and
    /// BaroqueRuinsCell use the exact TerrainRuins and TerrainBaroqueRuins terrain blueprints and
    /// carry the Ruins builder on every surface and subterranean floor. JoppaWorldBuilder instead
    /// stamps each generated historic floor with HistoricSite and adds its SultanDungeon builder;
    /// requiring both excludes neighboring surface zones that merely share its parasang.
    /// </para>
    /// <para>
    /// The ordinary JoppaWorld build path sends AfterZoneBuiltEvent only after all builders,
    /// forced connections, its sanity check, and wall/liquid painting. IZoneFactory.AfterBuildZone
    /// runs later only on factory worlds, which cannot pass either Joppa provenance test here.
    /// </para>
    /// <para>
    /// The attempt is a scalar ZoneManager property, serialized with the save independently of a
    /// loaded zone. It is written as failure before any side effect, so an exception, duplicate
    /// event, revisit, freeze/thaw, or removal of a placed cache cannot create another opportunity.
    /// Existing zones receive no backfill because this system listens only to AfterZoneBuiltEvent.
    /// </para>
    /// <para>
    /// Placement uses bounded reservoirs rather than allocated candidate lists. A surviving room
    /// corner is preferred over another room interior, and any legal reachable ruin floor remains
    /// the fallback. The cache and every independently rolled chip are completed off-map; only the
    /// complete object is published.
    /// </para>
    /// </remarks>
    public class Vixy_MnemonicCaches : IGameSystem
    {
        /// <summary>Persistent per-zone terminal outcome property.</summary>
        public const string AttemptProperty = "Vixy_MnemonicCacheAttempt";

        // Stable save values. Failure is written first and therefore also means an interrupted
        // attempt; every nonzero value is terminal.
        public const int GenerationFailure = 1;
        public const int Disabled = 2;
        public const int NoLegalPlacement = 3;
        public const int Missed = 4;
        public const int Placed = 5;

        private const string CacheBlueprint = "Vixy_MnemonicCache";
        private const string HistoricSiteProperty = "HistoricSite";
        private const string RuinsBuilder = "Ruins";
        private const string SultanDungeonBuilder = "SultanDungeon";
        private const string OrdinaryRuinsTerrain = "TerrainRuins";
        private const string BaroqueRuinsTerrain = "TerrainBaroqueRuins";

        /// <summary>This system persists no instance fields; the zone property owns all state.</summary>
        public override bool WantFieldReflection => false;

        public override void Register(XRLGame Game, IEventRegistrar Registrar)
        {
            Registrar.Register(AfterZoneBuiltEvent.ID);
            base.Register(Game, Registrar);
        }

        public override bool HandleEvent(AfterZoneBuiltEvent E)
        {
            TryGenerate(E.Zone);
            return base.HandleEvent(E);
        }

        private static void TryGenerate(Zone Zone)
        {
            if (!IsEligible(Zone)) return;

            string id = Zone.ZoneID;
            if (The.ZoneManager.HasZoneProperty(id, AttemptProperty)) return;

            // Consumed before the option read, cell selection, chance roll, or object construction.
            The.ZoneManager.SetZoneProperty(id, AttemptProperty, GenerationFailure);
            GameObject cache = null;
            try
            {
                if (!Raven_Options.ChipDrops)
                {
                    SetOutcome(id, Disabled);
                    return;
                }

                Cell placement = FindLegalCell(Zone);
                if (placement == null)
                {
                    SetOutcome(id, NoLegalPlacement);
                    return;
                }

                if (!20.in100())
                {
                    SetOutcome(id, Missed);
                    return;
                }

                cache = BuildCache(Zone.NewTier);
                placement.AddObject(cache);
                if (cache.CurrentCell != placement)
                {
                    throw new InvalidOperationException("The completed mnemonic cache could not enter its selected cell.");
                }

                SetOutcome(id, Placed);
                cache = null;
            }
            catch (Exception exception)
            {
                cache?.Obliterate("mnemonic cache generation failed", Silent: true);
                MetricsManager.LogException("Vixy_MnemonicCaches generation", exception);
            }
        }

        private static void SetOutcome(string ZoneID, int Outcome)
        {
            The.ZoneManager.SetZoneProperty(ZoneID, AttemptProperty, Outcome);
        }

        /// <summary>
        /// True only for tier 3-8 procedural ordinary/baroque ruins or generated historic floors.
        /// </summary>
        public static bool IsEligible(Zone Zone)
        {
            if (Zone == null || Zone.IsWorldMap() || Zone is InteriorZone
                || string.IsNullOrEmpty(Zone.ZoneID) || Zone.ZoneWorld != "JoppaWorld") return false;
            if (Zone.NewTier < 3 || Zone.NewTier > 8) return false;

            GameObject terrain = Zone.GetTerrainObject();
            if (terrain == null || terrain.HasPart("VillageTerrain")) return false;

            ZoneManager manager = The.ZoneManager;
            bool historic = manager.TryGetZoneProperty(
                Zone.ZoneID, HistoricSiteProperty, out string site)
                && !string.IsNullOrEmpty(site)
                && manager.ZoneHasBuilder(Zone.ZoneID, SultanDungeonBuilder);
            bool ruinTerrain = terrain.Blueprint == OrdinaryRuinsTerrain
                || terrain.Blueprint == BaroqueRuinsTerrain;
            if (!historic && (!ruinTerrain || Zone.HasProperName)) return false;

            bool ruins = manager.ZoneHasBuilder(Zone.ZoneID, RuinsBuilder);
            bool includeTerrain = !manager.HasZoneProperty(Zone.ZoneID, "SkipTerrainBuilders");
            List<ZoneBlueprint> blueprints = manager.GetZoneBlueprints(new ZoneRequest(Zone));
            if (blueprints == null) return false;
            for (int i = 0; i < blueprints.Count; i++)
            {
                ZoneBlueprint blueprint = blueprints[i];
                if (blueprint.Cell?.Mutable == false) return false;

                // ZoneHasBuilder sees runtime additions only; terrain builders live in these
                // effective blueprints, including any authored coordinate overlay.
                if (includeTerrain)
                {
                    ZoneBuilderCollection builders = blueprint.Builders;
                    if (builders == null) continue;
                    for (int j = 0; j < builders.Count; j++)
                    {
                        if (builders[j].Class == RuinsBuilder) ruins = true;
                    }
                }
            }

            return historic || ruins;
        }

        /// <summary>Maps effective zone tier to the existing graded chip table.</summary>
        public static string ContentsTableForTier(int Tier)
        {
            if (Tier >= 3 && Tier <= 5) return "Raven_Chips Tier 1";
            if (Tier == 6 || Tier == 7) return "Raven_Chips Tier 2";
            if (Tier == 8) return "Raven_Chips Tier 3";
            return null;
        }

        private static GameObject BuildCache(int Tier)
        {
            string table = ContentsTableForTier(Tier);
            if (table == null)
            {
                throw new InvalidOperationException("No mnemonic cache contents table exists for zone tier " + Tier + ".");
            }

            GameObject cache = GameObject.Create(CacheBlueprint);
            if (cache == null)
            {
                throw new InvalidOperationException("Could not create mnemonic cache blueprint " + CacheBlueprint + ".");
            }

            try
            {
                int count = Stat.Random(1, 2);
                for (int i = 0; i < count; i++)
                {
                    PopulationResult result = PopulationManager.RollOneFrom(table);
                    if (result == null || string.IsNullOrEmpty(result.Blueprint))
                    {
                        throw new InvalidOperationException("Population table " + table + " returned no chip.");
                    }

                    GameObject chip = GameObject.Create(result.Blueprint);
                    if (chip == null)
                    {
                        throw new InvalidOperationException("Could not create chip blueprint " + result.Blueprint + ".");
                    }
                    if (!cache.ReceiveObject(chip, NoStack: true, Context: CacheBlueprint))
                    {
                        chip.Obliterate("mnemonic cache inventory transfer failed", Silent: true);
                        throw new InvalidOperationException(
                            "Could not put chip blueprint " + result.Blueprint + " in a mnemonic cache.");
                    }
                }
                return cache;
            }
            catch
            {
                cache.Obliterate("mnemonic cache construction failed", Silent: true);
                throw;
            }
        }

        private static Cell FindLegalCell(Zone Zone)
        {
            Cell corner = null;
            Cell room = null;
            Cell fallback = null;
            int corners = 0;
            int rooms = 0;
            int all = 0;

            // Fetch once: GetZoneConnections allocates an empty list when this zone has none.
            List<ZoneConnection> connections = The.ZoneManager.GetZoneConnections(Zone.ZoneID);

            for (int y = 0; y < Zone.Height; y++)
            {
                for (int x = 0; x < Zone.Width; x++)
                {
                    Cell cell = Zone.GetCell(x, y);
                    if (!IsLegalCell(Zone, connections, cell)) continue;

                    all++;
                    if (Stat.Random(1, all) == 1) fallback = cell;

                    if (!cell.HasSemanticTag("Inside") || !cell.HasSemanticTag("Room")) continue;
                    rooms++;
                    if (Stat.Random(1, rooms) == 1) room = cell;

                    if (!cell.IsCorner()) continue;
                    corners++;
                    if (Stat.Random(1, corners) == 1) corner = cell;
                }
            }

            return corner ?? room ?? fallback;
        }

        private static bool IsLegalCell(
            Zone Zone,
            List<ZoneConnection> Connections,
            Cell Cell)
        {
            if (Cell == null
                || !Cell.IsReachable()
                || !Cell.IsEmptyForPopulation()
                || !Cell.IsSpawnable()
                || Cell.HasSpawnBlocker()
                || Cell.HasCombatObject()
                || Cell.HasStairs()
                || Cell.HasObjectWithTag("Door")
                || Cell.HasObjectWithPart("Gas")
                || Cell.HasObjectWithPart("Tinkering_Mine")
                || Cell.HasOpenLiquidVolume()
                || Cell.MightBlockPaths()
                || IsConnection(Connections, Cell.X, Cell.Y))
            {
                return false;
            }

            // Looting must have at least one dry, reachable cardinal approach square.
            return IsApproach(Zone.GetCell(Cell.X - 1, Cell.Y))
                || IsApproach(Zone.GetCell(Cell.X + 1, Cell.Y))
                || IsApproach(Zone.GetCell(Cell.X, Cell.Y - 1))
                || IsApproach(Zone.GetCell(Cell.X, Cell.Y + 1));
        }

        private static bool IsApproach(Cell Cell)
        {
            return Cell != null
                && Cell.IsReachable()
                && !Cell.IsSolid()
                && !Cell.HasCombatObject()
                && !Cell.HasOpenLiquidVolume();
        }

        private static bool IsConnection(
            List<ZoneConnection> Connections,
            int X,
            int Y)
        {
            for (int i = 0; i < Connections.Count; i++)
            {
                ZoneConnection connection = Connections[i];
                if (connection.X == X && connection.Y == Y) return true;
            }

            return false;
        }
    }
}
