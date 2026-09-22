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
    /// Sends bands to eligible places that have fallen empty. #924.
    /// </summary>
    /// <remarks>
    /// <para>
    /// A vacancy is spent when this class evaluates it. The option-off return is the one exception:
    /// that record belongs to a feature which was not running.
    /// </para>
    /// <para>
    /// Selection has three ordered outcomes. A former holder reclaims from its nearest remaining
    /// holding. Otherwise the most hostile nearby holder expands, then a neutral holder. Each origin
    /// is a recorded same-world holding, so travel distance remains real rather than decorative.
    /// </para>
    /// <para>
    /// Charter rule 5: read zone properties and journal notes, then create one token. No I/O,
    /// reflection, or Harmony.
    /// </para>
    /// </remarks>
    public static class Vixy_BandDispatch
    {
        /// <summary>The token blueprint. Named here, which is also its route past #926.</summary>
        public const string Blueprint = "Vixy_Band";

        /// <summary>One in this many answerable vacancies is answered.</summary>
        public const int OneIn = 4;

        private struct Holding
        {
            public string Faction;
            public string ZoneID;
            public int Distance;
        }

        private struct Mission
        {
            public string Name;
            public string Faction;
            public string Origin;

            public bool Valid => !Name.IsNullOrEmpty() && !Faction.IsNullOrEmpty() && !Origin.IsNullOrEmpty();
        }

        private struct Site
        {
            public bool Protected;
            public string Flags;
        }

        /// <summary>
        /// A live zone has fallen empty. Classify it before selecting who may answer.
        /// </summary>
        public static void OnVacancy(Zone Zone, string Lost)
        {
            if (!Raven_Options.TravellingBands || Zone == null) return;

            string target = Zone.ZoneID;
            if (target.IsNullOrEmpty()) return;

            // From here the dispatch has made its one decision. Protected and unanswerable sites
            // stay spent rather than becoming a rerollable encounter source.
            The.ZoneManager.RemoveZoneProperty(target, Vixy_Territory.Vacated);

            if (IsProtectedSite(target, Zone)) return;

            if (!TryCoordinates(target, out string world, out int x, out int y)) return;

            List<Holding> holdings = GetHoldings(target, world, x, y);
            Mission mission = SelectMission(Lost, holdings);
            if (!mission.Valid) return;

            // The rate applies only to journeys that have a legal world-map start and destination.
            if (!TryGetStart(mission.Origin, target, out Cell _)) return;
            if (!Stat.Random(1, OneIn).Equals(1)) return;

            Send(mission.Faction, mission.Name, mission.Origin, target);
        }

        /// <summary>Consider one hostile answer to a recorded holder replacement.</summary>
        public static void OnTakeover(Zone Zone, string Former, string Current)
        {
            if (!Raven_Options.TravellingBands || Zone == null) return;

            string target = Zone.ZoneID;
            if (target.IsNullOrEmpty()
                || !Vixy_Territory.TryConsiderTransition(target, Former, Current)
                || IsProtectedSite(target, Zone)
                || !TryCoordinates(target, out string world, out int x, out int y))
            {
                return;
            }

            Faction attacker = Factions.GetIfExists(Former);
            if (attacker == null || attacker.GetFeelingTowardsFaction(Current) >= 0) return;

            Holding origin = Nearest(
                GetHoldings(target, world, x, y),
                (Holding h) => h.Faction == Former
            );
            if (origin.ZoneID.IsNullOrEmpty()
                || HasInFlightCounterraid(Former, target)
                || !TryGetStart(origin.ZoneID, target, out Cell _)
                || !Stat.Random(1, OneIn).Equals(1))
            {
                return;
            }

            Send(
                Former,
                Vixy_Band.CounterraidMission,
                origin.ZoneID,
                target,
                Former + " -> " + Current
            );
        }

        /// <summary>
        /// Put a fully described band on the world map, bound for <paramref name="ToZone"/>.
        /// </summary>
        public static bool Send(
            string Faction, string Mission, string FromZone, string ToZone, string Trigger = null
        )
        {
            if (!TryGetStart(FromZone, ToZone, out Cell start)) return false;

            GameObject token = GameObject.Create(Blueprint);
            if (token == null) return false;

            token.RequirePart<Vixy_Band>();
            token.SetStringProperty(Vixy_Band.FactionProperty, Faction);
            token.SetStringProperty(Vixy_Band.MissionProperty, Mission);
            token.SetStringProperty(Vixy_Band.OriginProperty, FromZone);
            token.SetStringProperty(Vixy_Band.TargetProperty, ToZone);
            if (!Trigger.IsNullOrEmpty()) token.SetStringProperty(Vixy_Band.TriggerProperty, Trigger);

            AIWorldMapTravel travel = token.RequirePart<AIWorldMapTravel>();
            if (!travel.SetZoneID(ToZone))
            {
                token.Obliterate();
                return false;
            }

            // Pinned keeps the world map cached rather than frozen. It does not make it tick.
            travel.Pinned = true;
            start.AddObject(token, Forced: true, System: true);
            return true;
        }

        /// <summary>
        /// Describe the stable site facts for a destination without loading its zone.
        /// </summary>
        public static string DescribeSite(string ZoneID)
        {
            return Classify(ZoneID, null).Flags;
        }

        /// <summary>
        /// Whether the shared site policy keeps this zone out of emergent world systems.
        /// </summary>
        public static bool IsProtectedSite(string ZoneID, Zone Loaded = null)
        {
            return Classify(ZoneID, Loaded).Protected;
        }

        private static Site Classify(string ZoneID, Zone Loaded)
        {
            List<string> flags = new List<string>();
            if (!TryCoordinates(ZoneID, out string world, out int px, out int py))
            {
                return new Site { Protected = true, Flags = "invalid" };
            }

            int resolvedX = px * 3;
            int resolvedY = py * 3;
            XRL.World.ZoneID.Parse(ZoneID, out string _, out int _, out int _, out int x, out int y, out int _);
            resolvedX += x;
            resolvedY += y;

            bool lair = false;
            bool ruins = false;
            bool protectedNote = false;
            foreach (JournalMapNote note in JournalAPI.GetMapNotesForZone(ZoneID))
            {
                AddSiteFlags(note, flags, ref lair, ref ruins, ref protectedNote);
            }
            foreach (JournalMapNote note in JournalAPI.GetMapNotesForColumn(world, px, py))
            {
                if (note.ResolvedX == resolvedX && note.ResolvedY == resolvedY)
                {
                    AddSiteFlags(note, flags, ref lair, ref ruins, ref protectedNote);
                }
            }

            ZoneBlueprint blueprint = The.ZoneManager.GetZoneBlueprint(new ZoneRequest(ZoneID));
            bool immutable = blueprint?.Cell?.Mutable == false;
            bool proper = Loaded?.HasProperName ?? blueprint?.ProperName == true;
            if (immutable) flags.Add("static");
            if (proper) flags.Add("named");
            if (flags.Count == 0) flags.Add("wilderness");

            return new Site
            {
                Protected = protectedNote || immutable || (proper && !lair && !ruins),
                Flags = string.Join(", ", flags),
            };
        }

        private static void AddSiteFlags(
            JournalMapNote Note,
            List<string> Flags,
            ref bool Lair,
            ref bool Ruins,
            ref bool Protected
        )
        {
            AddFlag(Note, "lair", Flags, ref Lair);
            AddFlag(Note, "ruins", Flags, ref Ruins);
            bool settlement = false;
            bool historic = false;
            bool artifact = false;
            bool merchant = false;
            bool oddity = false;
            AddFlag(Note, "settlement", Flags, ref settlement);
            AddFlag(Note, "historic", Flags, ref historic);
            AddFlag(Note, "artifact", Flags, ref artifact);
            AddFlag(Note, "merchant", Flags, ref merchant);
            AddFlag(Note, "oddity", Flags, ref oddity);
            Protected |= settlement || historic || artifact || merchant || oddity;
        }

        private static void AddFlag(JournalMapNote Note, string Name, List<string> Flags, ref bool Seen)
        {
            if (!Note.Has(Name)) return;
            Seen = true;
            if (!Flags.Contains(Name)) Flags.Add(Name);
        }

        private static List<Holding> GetHoldings(string Target, string World, int X, int Y)
        {
            List<Holding> holdings = new List<Holding>();
            foreach (KeyValuePair<string, Dictionary<string, object>> zone in The.ZoneManager.ZoneProperties)
            {
                if (zone.Key == Target || zone.Value == null) continue;
                if (!zone.Value.TryGetValue(Vixy_Territory.HeldBy, out object holder)) continue;
                if (!TryCoordinates(zone.Key, out string world, out int px, out int py) || world != World) continue;

                string faction = holder as string;
                if (faction.IsNullOrEmpty()) continue;
                holdings.Add(
                    new Holding
                    {
                        Faction = faction,
                        ZoneID = zone.Key,
                        Distance = Math.Abs(px - X) + Math.Abs(py - Y),
                    }
                );
            }
            return holdings;
        }

        private static Mission SelectMission(string Lost, List<Holding> Holdings)
        {
            Holding reclaim = Nearest(Holdings, (Holding h) => h.Faction == Lost);
            if (!reclaim.ZoneID.IsNullOrEmpty())
            {
                return new Mission
                {
                    Name = Vixy_Band.ReclaimMission,
                    Faction = reclaim.Faction,
                    Origin = reclaim.ZoneID,
                };
            }

            int feeling = 0;
            foreach (Holding holding in Holdings)
            {
                Faction faction = Factions.GetIfExists(holding.Faction);
                if (faction == null) continue;
                int value = faction.GetFeelingTowardsFaction(Lost);
                if (value < feeling) feeling = value;
            }
            if (feeling < 0)
            {
                Holding rival = Nearest(
                    Holdings,
                    (Holding h) => Factions.GetIfExists(h.Faction)?.GetFeelingTowardsFaction(Lost) == feeling
                );
                if (!rival.ZoneID.IsNullOrEmpty())
                {
                    return new Mission
                    {
                        Name = Vixy_Band.RivalExpansionMission,
                        Faction = rival.Faction,
                        Origin = rival.ZoneID,
                    };
                }
            }

            Holding neutral = Nearest(
                Holdings,
                (Holding h) => h.Faction != Lost
                    && Factions.GetIfExists(h.Faction)?.GetFeelingTowardsFaction(Lost) == 0
            );
            return neutral.ZoneID.IsNullOrEmpty()
                ? default
                : new Mission
                {
                    Name = Vixy_Band.ExpansionMission,
                    Faction = neutral.Faction,
                    Origin = neutral.ZoneID,
                };
        }

        private static Holding Nearest(List<Holding> Holdings, Predicate<Holding> Include)
        {
            List<Holding> nearest = new List<Holding>();
            int distance = int.MaxValue;
            foreach (Holding holding in Holdings)
            {
                if (!Include(holding)) continue;
                if (holding.Distance < distance)
                {
                    distance = holding.Distance;
                    nearest.Clear();
                }
                if (holding.Distance == distance) nearest.Add(holding);
            }
            return nearest.Count == 0 ? default : nearest.GetRandomElement();
        }

        private static bool HasInFlightCounterraid(string Faction, string Target)
        {
            foreach (GameObject token in The.ZoneManager.FindObjects(
                         (GameObject o) => o.HasPart<Vixy_Band>()))
            {
                if (token.GetStringProperty(Vixy_Band.FactionProperty) == Faction
                    && token.GetStringProperty(Vixy_Band.TargetProperty) == Target)
                {
                    return true;
                }
            }
            return false;
        }

        private static bool TryGetStart(string FromZone, string ToZone, out Cell Start)
        {
            Start = null;
            if (!TryCoordinates(FromZone, out string fromWorld, out int px, out int py)) return false;
            if (!TryCoordinates(ToZone, out string toWorld, out int _, out int _)) return false;
            if (fromWorld != toWorld) return false;

            Zone world = The.ZoneManager.GetZone(fromWorld);
            Start = world?.GetCell(px, py);
            return Start != null;
        }

        private static bool TryCoordinates(string ZoneID, out string World, out int X, out int Y)
        {
            return XRL.World.ZoneID.Parse(ZoneID, out World, out X, out Y);
        }
    }
}
