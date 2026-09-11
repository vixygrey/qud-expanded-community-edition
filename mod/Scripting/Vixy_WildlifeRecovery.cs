using System;
using System.Collections.Generic;
using QudExpandedCE;
using XRL.Rules;
using XRL.World;
using XRL.World.Parts;
using XRL.World.ZoneBuilders;

namespace XRL
{
    /// <summary>Restores a small amount of non-sentient wildlife when wilderness recovers.</summary>
    public class Vixy_WildlifeRecovery : IGameSystem
    {
        public const string LastLeft = "Vixy_WildlifeLastLeft";
        public const string LastRecovery = "Vixy_WildlifeLastRecovery";
        public const int DaysAway = 30;
        public const int WildlifeCap = 6;
        public const int CohortCap = 2;

        private static readonly List<PopulationSource> Sources = new List<PopulationSource>();
        private static RecoveryReport LastReport;

        private sealed class PopulationSource
        {
            public string Table;
            public string Hint;
            public bool ReachableOnly;
        }

        public sealed class RecoveryReport
        {
            public string ZoneID;
            public string Decision;
            public string SiteFlags;
            public long Elapsed;
            public long Cooldown;
            public int ExistingWildlife;
            public int Capacity;
            public List<string> Sources = new List<string>();
            public List<string> Candidates = new List<string>();
            public List<string> Placed = new List<string>();
        }

        public override void Register(XRLGame Game, IEventRegistrar Registrar)
        {
            Registrar.Register(ZoneDeactivatedEvent.ID);
            Registrar.Register(ZoneActivatedEvent.ID);
            base.Register(Game, Registrar);
        }

        public override bool HandleEvent(ZoneDeactivatedEvent E)
        {
            if (E.Zone != null && !E.Zone.IsWorldMap() && E.Zone.Built)
                The.ZoneManager.SetZoneProperty(E.Zone.ZoneID, LastLeft, Calendar.TotalTimeTicks);
            return base.HandleEvent(E);
        }

        public override bool HandleEvent(ZoneActivatedEvent E)
        {
            Recover(E.Zone);
            return base.HandleEvent(E);
        }

        private static void Recover(Zone zone)
        {
            if (zone == null) return;

            RecoveryReport report = new RecoveryReport
            {
                ZoneID = zone.ZoneID,
                SiteFlags = Vixy_SiteProtection.SiteFlags(zone.ZoneID),
                Decision = "not considered"
            };
            LastReport = report;

            if (!Raven_Options.WildlifeRecovery)
            {
                report.Decision = "disabled";
                return;
            }

            if (!Eligible(zone, out string reason))
            {
                report.Decision = reason;
                return;
            }

            if (!The.ZoneManager.TryGetZoneProperty(zone.ZoneID, LastLeft, out long lastLeft))
            {
                report.Decision = "first observation";
                return;
            }

            long now = Calendar.TotalTimeTicks;
            report.Elapsed = Math.Max(0L, now - lastLeft);
            if (report.Elapsed < Interval)
            {
                report.Decision = "cooldown: zone was away less than one month";
                return;
            }

            if (The.ZoneManager.TryGetZoneProperty(zone.ZoneID, LastRecovery, out long lastRecovery))
            {
                report.Cooldown = Math.Max(0L, Interval - (now - lastRecovery));
                if (report.Cooldown > 0)
                {
                    report.Decision = "cooldown: previous recovery was less than one month ago";
                    return;
                }
            }

            report.ExistingWildlife = CountWildlife(zone);
            report.Capacity = Math.Max(0, WildlifeCap - report.ExistingWildlife);
            if (report.Capacity == 0)
            {
                report.Decision = "cap reached";
                The.ZoneManager.SetZoneProperty(zone.ZoneID, LastRecovery, now);
                return;
            }

            ResolveSources(zone, Sources);
            for (int i = 0; i < Sources.Count; i++)
                report.Sources.Add(Describe(Sources[i]));

            int target = Math.Min(CohortCap, report.Capacity);
            List<PopulationResult> candidates = GenerateCandidates(zone, Sources);
            for (int i = 0; i < candidates.Count && report.Placed.Count < target; i++)
            {
                PopulationResult result = candidates[i];
                GameObject creature = GameObject.Create(result.Blueprint);
                if (creature == null) continue;

                if (!creature.IsCreature || !Vixy_Regard.IsAnimal(creature))
                {
                    creature.Obliterate();
                    continue;
                }

                report.Candidates.Add(result.Blueprint);
                if (!HasPlacementCell(zone))
                {
                    creature.Obliterate();
                    continue;
                }

                ZoneBuilderSandbox.PlaceObjectInArea(
                    zone,
                    zone.area,
                    creature,
                    report.Placed.Count,
                    0,
                    result.Hint,
                    result.Builder,
                    bAllowCaching: true
                );
                report.Placed.Add(result.Blueprint);
            }

            The.ZoneManager.SetZoneProperty(zone.ZoneID, LastRecovery, now);
            report.Decision = report.Placed.Count == 0 ? "attempted: no cohort placed" : "recovered";
        }

        private static bool Eligible(Zone zone, out string reason)
        {
            if (zone.IsWorldMap())
            {
                reason = "world map";
                return false;
            }
            if (!zone.Built || zone.GetBlueprint() == null)
            {
                reason = "zone is not built";
                return false;
            }
            if (Vixy_SiteProtection.IsProtected(zone.ZoneID))
            {
                reason = "protected site: " + Vixy_SiteProtection.SiteFlags(zone.ZoneID);
                return false;
            }
            if (The.ZoneManager.GetZoneNamedByPlayer(zone.ZoneID))
            {
                reason = "named by player";
                return false;
            }
            foreach (GameObject obj in zone.GetObjects())
            {
                if (obj == null) continue;
                if (obj.IsPlayerLed())
                {
                    reason = "player-led creature present";
                    return false;
                }
                if (The.Player != null && !The.Player.ID.IsNullOrEmpty() && obj.Owner == The.Player.ID)
                {
                    reason = "player-owned object present";
                    return false;
                }
                if (obj.HasPart<Container>() || obj.HasPart<Bed>() || obj.HasPart<Campfire>() || obj.HasPart<CampfireRemains>())
                {
                    reason = "player footprint marker present";
                    return false;
                }
            }
            reason = null;
            return true;
        }

        private static int CountWildlife(Zone zone)
        {
            int count = 0;
            foreach (GameObject obj in zone.GetObjects())
            {
                if (obj != null && obj.IsCreature && obj.IsAlive && Vixy_Regard.IsAnimal(obj))
                    count++;
            }
            return count;
        }

        private static bool HasPlacementCell(Zone zone)
        {
            foreach (Cell cell in zone.GetCells())
            {
                if (cell.IsEmpty() && !cell.HasSpawnBlocker())
                    return true;
            }
            return false;
        }

        private static List<PopulationResult> GenerateCandidates(Zone zone, List<PopulationSource> sources)
        {
            List<PopulationResult> candidates = new List<PopulationResult>();
            for (int i = 0; i < sources.Count; i++)
            {
                PopulationSource source = sources[i];
                List<PopulationResult> generated = PopulationManager.Generate(
                    source.Table,
                    "zonetier",
                    zone.NewTier.ToString()
                );
                foreach (PopulationResult result in generated)
                {
                    if (result.Blueprint.IsNullOrEmpty()) continue;
                    if (result.Hint.IsNullOrEmpty()) result.Hint = source.Hint;
                    candidates.Add(result);
                }
            }

            for (int i = candidates.Count - 1; i > 0; i--)
            {
                int index = Stat.Random(0, i);
                PopulationResult result = candidates[index];
                candidates[index] = candidates[i];
                candidates[i] = result;
            }
            return candidates;
        }

        private static void ResolveSources(Zone zone, List<PopulationSource> result)
        {
            result.Clear();
            ZoneBlueprint blueprint = zone.GetBlueprint();
            if (blueprint == null) return;

            foreach (ZoneBuilderBlueprint builder in blueprint.Builders)
            {
                if (builder == null) continue;
                if ((builder.Class == "Population" || builder.Class == "PopTableZoneBuilder")
                    && builder.Parameters != null
                    && builder.Parameters.TryGetValue("Table", out object table))
                {
                    AddSource(result, table as string, null, false);
                }
                else if (builder.Class != null && builder.Class.StartsWith("ZoneTemplate:", StringComparison.Ordinal))
                {
                    string name = builder.Class.Substring("ZoneTemplate:".Length);
                    if (ZoneTemplateManager.Templates.TryGetValue(name, out ZoneTemplate template))
                    {
                        Walk(template.GlobalRoot, null, false, result);
                        Walk(template.SingleRoot, null, false, result);
                        Walk(template.Root, null, false, result);
                    }
                }
            }
            for (int i = result.Count - 1; i >= 0; i--)
            {
                PopulationSource source = result[i];
                source.Table = source.Table.Replace("{zonetier}", zone.NewTier.ToString());
                if (!PopulationManager.HasPopulation(source.Table))
                    result.RemoveAt(i);
            }
        }

        private static void Walk(ZoneTemplateNode node, string inheritedHint, bool reachableOnly, List<PopulationSource> result)
        {
            if (node == null) return;
            string hint = node.Hint ?? inheritedHint;
            bool reachable = reachableOnly;
            if (node is ZTCellFilterOutNode filter && filter.Filter != null
                && filter.Filter.ToLowerInvariant().Contains("!reachable"))
                reachable = true;

            if (node is ZTPopulatonNode population)
                AddSource(result, population.Table, hint, reachable);

            foreach (ZoneTemplateNode child in node.Children)
                Walk(child, hint, reachable, result);
        }

        private static void AddSource(List<PopulationSource> result, string table, string hint, bool reachableOnly)
        {
            if (table.IsNullOrEmpty()) return;
            foreach (PopulationSource source in result)
            {
                if (source.Table == table && source.Hint == hint && source.ReachableOnly == reachableOnly)
                    return;
            }
            result.Add(new PopulationSource { Table = table, Hint = hint, ReachableOnly = reachableOnly });
        }

        private static string Describe(PopulationSource source)
        {
            return source.Table + (source.Hint.IsNullOrEmpty() ? "" : " [" + source.Hint + "]")
                + (source.ReachableOnly ? " [reachable]" : "");
        }

        public static long Interval => (long)Calendar.TurnsPerDay * DaysAway;

        public static RecoveryReport CurrentReport()
        {
            return LastReport;
        }
    }
}
