using System;
using System.Collections.Generic;
using Qud.API;
using QudExpandedCE;
using XRL.Rules;
using XRL.World;
using XRL.World.Parts;

namespace XRL
{
    /// <summary>
    /// Sends a band toward a place that has fallen empty. #832.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The reason, and only this one.</b> A lair somebody held and no longer does is a vacancy,
    /// and a people who hold ground elsewhere may want it. That is the whole trigger — no site
    /// types, no sacred places, no model of what any faction wants, all of which are #924. It works
    /// only because #923 records who held a place, which is why that shipped first.
    /// </para>
    /// <para>
    /// <b>Who comes is deliberately dumb.</b> The candidate is drawn from factions
    /// <c>Vixy_Territory</c> has recorded holding some <em>other</em> zone — so the world reclaims
    /// using peoples I have actually met, and no new data is invented to decide it. #924 can replace
    /// this with something considered; until then a rule that reads as *your neighbours notice* is
    /// better than a rule nobody can explain.
    /// </para>
    /// <para>
    /// <b>Not the people who just lost it.</b> A faction wiped out of a lair marching back into it
    /// is a respawn wearing a journey, which is the thing #830 decided against.
    /// </para>
    /// <para>
    /// <b>Once per vacancy, and rarely.</b> The vacancy property is removed as the band is sent, so
    /// a place cannot dispatch twice — a re-arming vacancy is a farm, which is #802's lesson paid
    /// for once already. On top of that a low roll, because the point of #832's narrowing is that
    /// the world should be doing this at the edge of my attention rather than around me.
    /// </para>
    /// <para>
    /// <b>The origin is the far end of the journey, not a flourish.</b> A band starts on the
    /// parasang of a zone its faction actually holds, so the distance it walks is the real distance
    /// between two places, paced by <c>TerrainTravel</c>. Sending it from nowhere in particular
    /// would make the travel decorative.
    /// </para>
    /// <para>
    /// Charter rule 5: reads zone properties, creates one object, sets three fields. No I/O, no
    /// reflection, no Harmony.
    /// </para>
    /// </remarks>
    public static class Vixy_BandDispatch
    {
        public const string Blueprint = "Vixy_Band";

        public const int OneIn = 4;

        private const string Reclaim = "reclaim";
        private const string RivalExpansion = "rival-expansion";
        private const string Expansion = "expansion";

        private sealed class Holding
        {
            public string Faction;
            public string ZoneID;
            public int X;
            public int Y;
            public int Distance;
        }

        private sealed class Selection
        {
            public string Faction;
            public string Mission;
            public Holding Origin;
        }

        /// <summary>A zone has fallen empty. Perhaps somebody sets out for it.</summary>
        public static void OnVacancy(string ZoneID, string Lost)
        {
            if (!Raven_Options.TravellingBands) return;
            if (ZoneID.IsNullOrEmpty()) return;

            The.ZoneManager.RemoveZoneProperty(ZoneID, Vixy_Territory.Vacated);

            if (Protected(ZoneID)) return;

            Selection selection = Select(ZoneID, Lost);
            if (selection == null) return;

            if (Stat.Random(1, OneIn) != 1) return;

            Send(
                selection.Faction,
                selection.Origin.ZoneID,
                ZoneID,
                selection.Mission
            );
        }

        /// <summary>
        /// Put a band on the world map at <paramref name="FromZone"/>'s parasang, bound for
        /// <paramref name="ToZone"/>.
        /// </summary>
        public static bool Send(
            string Faction,
            string FromZone,
            string ToZone,
            string Mission = Expansion
        )
        {
            Zone anchor = The.ActiveZone;
            if (anchor == null) return false;

            if (!ZoneID.Parse(FromZone, out string fromWorld, out int px, out int py))
                return false;
            if (!ZoneID.Parse(ToZone, out string toWorld, out int _, out int _))
                return false;
            if (fromWorld != toWorld || fromWorld != anchor.GetZoneWorld()) return false;

            Zone world = The.ZoneManager.GetZone(anchor.GetZoneWorld());
            Cell start = world?.GetCell(px, py);
            if (start == null) return false;

            GameObject token = GameObject.Create(Blueprint);
            if (token == null) return false;

            token.RequirePart<Vixy_Band>();
            token.SetStringProperty(Vixy_Band.FactionProperty, Faction);
            token.SetStringProperty(Vixy_Band.MissionProperty, Mission);
            token.SetStringProperty(Vixy_Band.OriginProperty, FromZone);
            token.SetStringProperty(Vixy_Band.TargetProperty, ToZone);

            AIWorldMapTravel travel = token.RequirePart<AIWorldMapTravel>();
            if (!travel.SetZoneID(ToZone))
            {
                token.Obliterate();
                return false;
            }

            travel.Pinned = true;
            start.AddObject(token, Forced: true, System: true);
            return true;
        }

        public static string SiteFlags(string id)
        {
            List<string> flags = new List<string>();
            if (id.IsNullOrEmpty()) return "unknown";

            if (!ZoneID.Parse(
                    id,
                    out string world,
                    out int px,
                    out int py,
                    out int zx,
                    out int zy,
                    out int _
                ))
                return "unknown";

            foreach (JournalMapNote note in JournalAPI.GetMapNotesForZone(id))
                AddFlags(flags, note);

            foreach (JournalMapNote note in JournalAPI.GetMapNotesForColumn(world, px, py))
            {
                if (note.ResolvedX == px * 3 + zx && note.ResolvedY == py * 3 + zy)
                    AddFlags(flags, note);
            }

            Zone zone = The.ZoneManager.GetZone(id);
            if (zone?.GetBlueprint()?.Cell != null && !zone.GetBlueprint().Cell.Mutable)
                Add(flags, "static");

            if (zone?.GetBlueprint()?.ProperName == true && !HasSafeFlag(flags))
                Add(flags, "proper-named");

            return flags.Count == 0 ? "ordinary" : string.Join(",", flags);
        }

        private static void AddFlags(List<string> flags, JournalMapNote note)
        {
            foreach (string flag in new[] {
                "settlement", "historic", "artifact", "merchant", "oddity"
            })
            {
                if (note.Has(flag)) Add(flags, flag);
            }
            if (note.Has("lair")) Add(flags, "lair");
            if (note.Has("ruins")) Add(flags, "ruins");
        }

        private static void Add(List<string> flags, string flag)
        {
            if (!flags.Contains(flag)) flags.Add(flag);
        }

        private static bool HasSafeFlag(List<string> flags)
        {
            return flags.Contains("lair") || flags.Contains("ruins");
        }

        private static bool Protected(string ZoneID)
        {
            string flags = SiteFlags(ZoneID);
            return flags != "ordinary"
                && (flags.Contains("settlement")
                    || flags.Contains("historic")
                    || flags.Contains("artifact")
                    || flags.Contains("merchant")
                    || flags.Contains("oddity")
                    || flags.Contains("static")
                    || flags.Contains("proper-named"));
        }

        private static Selection Select(string targetID, string lost)
        {
            if (!ZoneID.Parse(
                    targetID,
                    out string world,
                    out int targetPX,
                    out int targetPY,
                    out int targetZX,
                    out int targetZY,
                    out int _
                ))
                return null;

            List<Holding> holdings = Holdings(world, targetPX, targetPY, targetZX, targetZY);
            List<Holding> reclaim = holdings.FindAll(h => h.Faction == lost);
            Holding origin = Nearest(reclaim);
            if (origin != null)
            {
                return new Selection { Faction = lost, Mission = Reclaim, Origin = origin };
            }

            List<Holding> rival = new List<Holding>();
            int lowest = 0;
            foreach (Holding holding in holdings)
            {
                if (holding.Faction == lost) continue;
                Faction faction = Factions.Get(holding.Faction);
                if (faction == null) continue;
                int feeling = faction.GetFeelingTowardsFaction(lost);
                if (feeling >= 0) continue;
                if (feeling < lowest)
                {
                    lowest = feeling;
                    rival.Clear();
                }
                if (feeling == lowest) rival.Add(holding);
            }

            origin = Nearest(rival);
            if (origin != null)
            {
                return new Selection {
                    Faction = origin.Faction,
                    Mission = RivalExpansion,
                    Origin = origin
                };
            }

            List<Holding> neutral = new List<Holding>();
            foreach (Holding holding in holdings)
            {
                if (holding.Faction == lost) continue;
                Faction faction = Factions.Get(holding.Faction);
                if (faction != null && faction.GetFeelingTowardsFaction(lost) == 0)
                    neutral.Add(holding);
            }

            origin = Nearest(neutral);
            return origin == null
                ? null
                : new Selection {
                    Faction = origin.Faction,
                    Mission = Expansion,
                    Origin = origin
                };
        }

        private static List<Holding> Holdings(
            string world,
            int targetPX,
            int targetPY,
            int targetZX,
            int targetZY
        )
        {
            List<Holding> holdings = new List<Holding>();
            int targetX = targetPX * 3 + targetZX;
            int targetY = targetPY * 3 + targetZY;

            foreach (KeyValuePair<string, Dictionary<string, object>> zone
                     in The.ZoneManager.ZoneProperties)
            {
                if (zone.Value == null
                    || !zone.Value.TryGetValue(Vixy_Territory.HeldBy, out object value))
                    continue;

                string faction = value as string;
                if (faction.IsNullOrEmpty()) continue;
                if (!ZoneID.Parse(
                        zone.Key,
                        out string holderWorld,
                        out int px,
                        out int py,
                        out int zx,
                        out int zy,
                        out int _
                    )
                    || holderWorld != world)
                    continue;

                holdings.Add(new Holding {
                    Faction = faction,
                    ZoneID = zone.Key,
                    X = px * 3 + zx,
                    Y = py * 3 + zy,
                    Distance = Math.Abs(px * 3 + zx - targetX)
                        + Math.Abs(py * 3 + zy - targetY)
                });
            }
            return holdings;
        }

        private static Holding Nearest(List<Holding> candidates)
        {
            if (candidates.Count == 0) return null;
            int nearest = int.MaxValue;
            List<Holding> tied = new List<Holding>();
            foreach (Holding candidate in candidates)
            {
                if (candidate.Distance < nearest)
                {
                    nearest = candidate.Distance;
                    tied.Clear();
                }
                if (candidate.Distance == nearest) tied.Add(candidate);
            }
            return tied.GetRandomElement();
        }
    }
}
