using System;
using System.Collections.Generic;
using System.Text;
using Genkit;
using QudExpandedCE;
using XRL.Rules;
using XRL.World;

namespace XRL
{
    /// <summary>
    /// Lets a cleared wilderness zone regain a little of the wildlife vanilla originally put there.
    /// </summary>
    /// <remarks>
    /// <para>
    /// This records blueprints from the completed zone rather than replaying its population tables.
    /// A template contains far more than fauna: decoration, loot, encounters, and bosses can all be
    /// conditional nodes. The objects that survived vanilla's build are the one authoritative local
    /// wildlife pool.
    /// </para>
    /// <para>
    /// Zones do not tick while frozen, so this does no background work. It writes a departure turn
    /// when a built eligible zone deactivates and evaluates once when that zone activates again.
    /// The finite cohort count matters more than a live-population cap: killing a recovered creature
    /// cannot turn the same zone into an endless experience or corpse source.
    /// </para>
    /// <para>
    /// Charter rule 5: public events and public zone properties only. No I/O, reflection, Harmony,
    /// or replayed vanilla builders.
    /// </para>
    /// </remarks>
    public class Vixy_WildlifeRecovery : IGameSystem
    {
        public const string Pool = "Vixy_WildlifePool";
        public const string LastLeft = "Vixy_WildlifeLastLeft";
        public const string LastAttempt = "Vixy_WildlifeLastAttempt";
        public const string CohortsRemaining = "Vixy_WildlifeCohortsRemaining";

        /// <summary>Full absences a zone may answer over its whole save.</summary>
        public const int CohortBudget = 3;

        /// <summary>One Qud month.</summary>
        public const long RecoveryInterval = 30L * Calendar.TurnsPerDay;

        /// <summary>Keep an arrival from receiving fauna underfoot.</summary>
        public const int PlayerClearance = 6;

        public override void Register(XRLGame Game, IEventRegistrar Registrar)
        {
            Registrar.Register(AfterZoneBuiltEvent.ID);
            Registrar.Register(ZoneDeactivatedEvent.ID);
            Registrar.Register(ZoneActivatedEvent.ID);
            base.Register(Game, Registrar);
        }

        /// <summary>Capture what this particular completed zone actually received from vanilla.</summary>
        public override bool HandleEvent(AfterZoneBuiltEvent E)
        {
            RecordPool(E.Zone);
            return base.HandleEvent(E);
        }

        /// <summary>Remember the start of an absence even when the option is currently off.</summary>
        public override bool HandleEvent(ZoneDeactivatedEvent E)
        {
            RecordDeparture(E.Zone);
            return base.HandleEvent(E);
        }

        /// <summary>Resolve one bounded recovery attempt after a sufficiently long absence.</summary>
        public override bool HandleEvent(ZoneActivatedEvent E)
        {
            Recover(E.Zone);
            return base.HandleEvent(E);
        }

        /// <summary>
        /// The ecology predicate is deliberately narrower than "not a person". Animal is the
        /// engine's own lineage for animals, fish, insects, arachnids, worms, shellfish, and ooze;
        /// robots, people, and plants are separate lineages.
        /// </summary>
        public static bool IsWildlife(GameObject Object)
        {
            if (Object == null
                || !Object.IsCreature
                || !Object.IsAlive
                || Object.IsPlayer()
                || Object.IsPlayerLed()
                || Object.IsTemporary
                || Object.HasProperName)
            {
                return false;
            }

            GameObjectBlueprint blueprint = Object.GetBlueprint(UseDefault: false);
            return blueprint != null
                && (blueprint.Name == "Animal" || blueprint.InheritsFrom("Animal"));
        }

        /// <summary>Diagnostic state for the active zone, used only by <c>vixywildlife</c>.</summary>
        public static string Describe(Zone Zone)
        {
            StringBuilder sb = new StringBuilder();
            if (Zone == null)
            {
                return "{{R|No active zone.}}";
            }

            string id = Zone.ZoneID;
            List<string> pool = ReadPool(id);
            long now = Calendar.TotalTimeTicks;
            long left = ReadLong(id, LastLeft);
            long attempted = ReadLong(id, LastAttempt);
            int remaining = ReadInt(id, CohortsRemaining);

            sb.Append("zone  ").Append(id)
              .Append("\noption  ").Append(Raven_Options.WildlifeRecovery ? "{{G|on}}" : "{{R|off}}")
              .Append("\neligible  ").Append(IsEligible(Zone) ? "{{G|yes}}" : "{{R|no}}")
              .Append("\npool  ").Append(pool.Count)
              .Append("   wildlife now  ").Append(CountWildlife(Zone))
              .Append("\ncohorts remaining  ").Append(remaining)
              .Append("\nlast left  ").Append(DescribeTurn(left, now))
              .Append("\nlast attempt  ").Append(DescribeTurn(attempted, now));
            return sb.ToString();
        }

        private static void RecordPool(Zone Zone)
        {
            if (!IsEligible(Zone)) return;

            string id = Zone.ZoneID;
            if (The.ZoneManager.HasZoneProperty(id, Pool)) return;

            HashSet<string> blueprints = new HashSet<string>();
            List<GameObject> objects = Zone.GetObjects();
            for (int i = 0; i < objects.Count; i++)
            {
                GameObject Object = objects[i];
                if (IsWildlife(Object) && !Object.Blueprint.IsNullOrEmpty())
                {
                    blueprints.Add(Object.Blueprint);
                }
            }

            if (blueprints.Count == 0) return;

            The.ZoneManager.SetZoneProperty(id, Pool, string.Join("\n", blueprints));
            The.ZoneManager.SetZoneProperty(id, CohortsRemaining, CohortBudget);
        }

        private static void RecordDeparture(Zone Zone)
        {
            if (!IsEligible(Zone)) return;

            string id = Zone.ZoneID;
            if (!The.ZoneManager.HasZoneProperty(id, Pool)) return;

            The.ZoneManager.SetZoneProperty(id, LastLeft, Calendar.TotalTimeTicks);
        }

        private static void Recover(Zone Zone)
        {
            if (!Raven_Options.WildlifeRecovery || !IsEligible(Zone)) return;

            string id = Zone.ZoneID;
            List<string> pool = ReadPool(id);
            if (pool.Count == 0 || CountWildlife(Zone) > 0) return;

            long left = ReadLong(id, LastLeft);
            long attempted = ReadLong(id, LastAttempt);
            long now = Calendar.TotalTimeTicks;
            int remaining = ReadInt(id, CohortsRemaining);
            if (left <= 0 || now - left < RecoveryInterval || attempted >= left || remaining <= 0) return;

            // A qualifying absence is spent even if a later object or cell check cannot place
            // anything. Re-entering a constrained zone must not become a reroll loop.
            The.ZoneManager.SetZoneProperty(id, LastAttempt, now);
            The.ZoneManager.SetZoneProperty(id, CohortsRemaining, remaining - 1);

            int count = Stat.Random(1, 2);
            for (int i = 0; i < count; i++)
            {
                GameObject candidate = GameObject.Create(pool[Stat.Random(0, pool.Count - 1)]);
                if (candidate == null) continue;

                Cell landing = FindLegalCell(Zone, candidate);
                if (landing == null)
                {
                    candidate.Obliterate();
                    continue;
                }

                landing.AddObject(candidate);
            }
        }

        private static Cell FindLegalCell(Zone Zone, GameObject Candidate)
        {
            HashSet<Location2D> connections = new HashSet<Location2D>();
            foreach (ZoneConnection connection in Zone.EnumerateConnections())
            {
                connections.Add(connection.Loc2D);
            }

            Cell player = The.PlayerCell;
            List<Cell> legal = new List<Cell>();
            bool livesOnWalls = Candidate.Brain != null && Candidate.Brain.LivesOnWalls;
            bool aquatic = Candidate.Brain != null && Candidate.Brain.Aquatic;

            foreach (Cell cell in Zone.GetCells())
            {
                if (connections.Contains(cell.Location)
                    || cell.HasSpawnBlocker()
                    || cell.HasCombatObject()
                    || (player != null && player.ParentZone == Zone && cell.DistanceTo(player) < PlayerClearance))
                {
                    continue;
                }

                if (livesOnWalls)
                {
                    if (!cell.HasWall()) continue;
                }
                else if (!cell.IsReachable() || !cell.IsEmptyForPopulation() || !cell.IsSpawnable())
                {
                    continue;
                }

                if (aquatic && !cell.HasAquaticSupportFor(Candidate)) continue;
                legal.Add(cell);
            }

            return legal.Count == 0 ? null : legal[Stat.Random(0, legal.Count - 1)];
        }

        private static bool IsEligible(Zone Zone)
        {
            if (Zone == null || Zone.IsWorldMap() || Zone.ZoneID.IsNullOrEmpty()) return false;
            if (The.ZoneManager.GetZoneNamedByPlayer(Zone.ZoneID)) return false;
            return !Vixy_BandDispatch.IsProtectedSite(Zone.ZoneID, Zone);
        }

        private static int CountWildlife(Zone Zone)
        {
            int count = 0;
            List<GameObject> objects = Zone.GetObjects();
            for (int i = 0; i < objects.Count; i++)
            {
                if (IsWildlife(objects[i])) count++;
            }
            return count;
        }

        private static List<string> ReadPool(string ZoneID)
        {
            if (!The.ZoneManager.TryGetZoneProperty(ZoneID, Pool, out string saved)
                || saved.IsNullOrEmpty())
            {
                return new List<string>();
            }
            return new List<string>(saved.Split(new[] { '\n' }, StringSplitOptions.RemoveEmptyEntries));
        }

        private static int ReadInt(string ZoneID, string Name)
        {
            return The.ZoneManager.TryGetZoneProperty(ZoneID, Name, out int value) ? value : 0;
        }

        private static long ReadLong(string ZoneID, string Name)
        {
            return The.ZoneManager.TryGetZoneProperty(ZoneID, Name, out long value) ? value : 0;
        }

        private static string DescribeTurn(long Turn, long Now)
        {
            if (Turn <= 0) return "never";
            return Turn + "  (" + ((Now - Turn) / Calendar.TurnsPerDay) + " days ago)";
        }
    }
}
