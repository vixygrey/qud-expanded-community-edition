using System.Collections.Generic;
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
        /// <summary>The token blueprint. Named here, which is also its route past #926.</summary>
        public const string Blueprint = "Vixy_Band";

        /// <summary>One in this many vacancies is answered.</summary>
        /// <remarks>
        /// A vacancy is already uncommon — it needs a zone that was held, cleared to the last
        /// member, and left. Rolling on top of that is what keeps a band something I come across
        /// rather than something that follows me around. See #832 on why the trigger is narrowed
        /// instead of optioned into silence.
        /// </remarks>
        public const int OneIn = 4;

        /// <summary>
        /// A zone has fallen empty. Perhaps somebody sets out for it.
        /// </summary>
        public static void OnVacancy(string ZoneID, string Lost)
        {
            if (!Raven_Options.TravellingBands) return;
            if (ZoneID.IsNullOrEmpty()) return;
            if (!Stat.Random(1, OneIn).Equals(1)) return;

            string faction = Neighbour(Lost);
            if (faction.IsNullOrEmpty()) return;

            string from = HeldZone(faction);
            if (from.IsNullOrEmpty()) return;

            if (Send(faction, from, ZoneID))
            {
                // Answered. The vacancy is spent whether or not the band ever arrives - a place
                // that can be answered twice is a faucet.
                The.ZoneManager.RemoveZoneProperty(ZoneID, Vixy_Territory.Vacated);
            }
        }

        /// <summary>
        /// Put a band on the world map at <paramref name="FromZone"/>'s parasang, bound for
        /// <paramref name="ToZone"/>.
        /// </summary>
        /// <remarks>
        /// <c>SetZoneID</c> does the parsing — it is <c>ZoneID.Parse</c> under the name — so the
        /// destination is handed over as a string and the part works out its own parasang. The
        /// world-map zone is reached through any loaded zone's <c>GetZoneWorld()</c>, which returns
        /// the world's name rather than the zone, exactly as <c>Zone</c> does it internally.
        /// </remarks>
        public static bool Send(string Faction, string FromZone, string ToZone)
        {
            Zone anchor = The.ActiveZone;
            if (anchor == null) return false;

            if (!ZoneID.Parse(FromZone, out string _, out int px, out int py)) return false;

            Zone world = The.ZoneManager.GetZone(anchor.GetZoneWorld());
            Cell start = world?.GetCell(px, py);
            if (start == null) return false;

            GameObject token = GameObject.Create(Blueprint);
            if (token == null) return false;

            token.RequirePart<Vixy_Band>();
            token.SetStringProperty(Vixy_Band.FactionProperty, Faction);

            AIWorldMapTravel travel = token.RequirePart<AIWorldMapTravel>();
            if (!travel.SetZoneID(ToZone))
            {
                token.Obliterate();
                return false;
            }

            // Pinned keeps the world map cached rather than frozen, so a journey survives my
            // wandering off. It does not make it tick - only the active zone does that.
            travel.Pinned = true;

            start.AddObject(token, Forced: true, System: true);
            return true;
        }

        /// <summary>
        /// A people who hold ground somewhere and are not the ones who just lost this place.
        /// </summary>
        private static string Neighbour(string Lost)
        {
            List<string> holders = new List<string>();
            foreach (KeyValuePair<string, Dictionary<string, object>> zone
                     in The.ZoneManager.ZoneProperties)
            {
                if (zone.Value == null) continue;
                if (!zone.Value.TryGetValue(Vixy_Territory.HeldBy, out object holder)) continue;

                string name = holder as string;
                if (name.IsNullOrEmpty() || name == Lost) continue;
                if (!holders.Contains(name)) holders.Add(name);
            }
            return holders.Count == 0 ? null : holders.GetRandomElement();
        }

        /// <summary>A zone this faction is recorded as holding, to set out from.</summary>
        private static string HeldZone(string Faction)
        {
            List<string> zones = new List<string>();
            foreach (KeyValuePair<string, Dictionary<string, object>> zone
                     in The.ZoneManager.ZoneProperties)
            {
                if (zone.Value == null) continue;
                if (zone.Value.TryGetValue(Vixy_Territory.HeldBy, out object holder)
                    && (holder as string) == Faction)
                {
                    zones.Add(zone.Key);
                }
            }
            return zones.Count == 0 ? null : zones.GetRandomElement();
        }
    }
}
