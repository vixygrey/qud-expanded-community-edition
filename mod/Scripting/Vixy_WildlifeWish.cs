using System.Text;
using QudExpandedCE;
using XRL.UI;
using XRL.Wish;
using XRL.World;

namespace XRL
{
    /// <summary>Reports the current wildlife recovery decision without changing the zone.</summary>
    [HasWishCommand]
    public static class Vixy_WildlifeWish
    {
        [WishCommand("vixywildlife", null)]
        public static void Report()
        {
            StringBuilder sb = new StringBuilder();
            Vixy_WildlifeRecovery.RecoveryReport report = Vixy_WildlifeRecovery.CurrentReport();
            Zone zone = The.ActiveZone;
            bool installed = The.Game?.GetSystem<Vixy_WildlifeRecovery>() != null;

            sb.Append("{{Y|Wildlife recovery}}  system ")
              .Append(installed ? "{{G|installed}}" : "{{R|MISSING}}")
              .Append("   option ")
              .Append(Raven_Options.WildlifeRecovery ? "{{G|on}}" : "{{K|off}}")
              .Append('\n');

            if (zone == null)
            {
                sb.Append("\nNo active zone.");
                Popup.Show(sb.ToString());
                return;
            }

            sb.Append("zone  ").Append(zone.ZoneID).Append('\n')
              .Append("site  ").Append(Vixy_SiteProtection.SiteFlags(zone.ZoneID)).Append('\n');

            if (report == null || report.ZoneID != zone.ZoneID)
            {
                sb.Append("\nNo recovery decision is recorded for this activation.");
                Popup.Show(sb.ToString());
                return;
            }

            sb.Append("elapsed ticks  ").Append(report.Elapsed)
              .Append("   elapsed days  ").Append(report.Elapsed / Calendar.TurnsPerDay).Append('\n')
              .Append("cooldown ticks  ").Append(report.Cooldown).Append('\n')
              .Append("wildlife  ").Append(report.ExistingWildlife)
              .Append("   capacity  ").Append(report.Capacity).Append('\n')
              .Append("decision  ").Append(report.Decision).Append('\n');

            Append(sb, "sources", report.Sources);
            Append(sb, "candidates", report.Candidates);
            Append(sb, "placed", report.Placed);
            Popup.Show(sb.ToString());
        }

        private static void Append(StringBuilder sb, string title, System.Collections.Generic.List<string> lines)
        {
            sb.Append('\n').Append("{{Y|").Append(title).Append("}}  ").Append(lines.Count).Append('\n');
            int shown = lines.Count < 12 ? lines.Count : 12;
            for (int i = 0; i < shown; i++)
                sb.Append("  ").Append(lines[i]).Append('\n');
            if (lines.Count > shown)
                sb.Append("  ").Append(lines.Count - shown).Append(" more\n");
        }
    }
}
