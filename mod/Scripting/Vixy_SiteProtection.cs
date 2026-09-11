using System.Collections.Generic;
using Qud.API;
using XRL.World;

namespace XRL
{
    /// <summary>Classifies sites that must not receive automatic world changes.</summary>
    public static class Vixy_SiteProtection
    {
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
            ZoneBlueprint blueprint = zone?.GetBlueprint();
            if (blueprint?.Cell != null && !blueprint.Cell.Mutable)
                Add(flags, "static");

            if (blueprint?.ProperName == true && !HasSafeFlag(flags))
                Add(flags, "proper-named");

            return flags.Count == 0 ? "ordinary" : string.Join(",", flags);
        }

        public static bool IsProtected(string zoneID)
        {
            string flags = SiteFlags(zoneID);
            return flags != "ordinary"
                && (flags.Contains("settlement")
                    || flags.Contains("historic")
                    || flags.Contains("artifact")
                    || flags.Contains("merchant")
                    || flags.Contains("oddity")
                    || flags.Contains("static")
                    || flags.Contains("proper-named"));
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
    }
}
