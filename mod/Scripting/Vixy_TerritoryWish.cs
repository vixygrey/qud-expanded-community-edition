using System.Collections.Generic;
using System.Text;
using XRL.UI;
using XRL.Wish;
using XRL.World;

namespace XRL
{
    /// <summary>
    /// <c>vixyterritory</c> — what <see cref="Vixy_Territory"/> has recorded, and whether it is
    /// running at all.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The system it reports on is invisible by construction</b>, which is fine for a record and
    /// awkward for a test. #923 writes zone properties and produces no output at any point, so
    /// without this the only way to know it works is to read a save. This is the same gap that made
    /// #921's defences unjudgeable until they announced themselves, answered the cheaper way because
    /// nothing here belongs in a player's message log.
    /// </para>
    /// <para>
    /// <b>The first line is the one that matters.</b> This fork had never installed an
    /// <c>IGameSystem</c> before #923, and <c>RequireSystem</c> on an <em>existing save</em> is the
    /// step with no in-repo precedent — <c>RequirePart</c> is well-trodden, this is not. If the
    /// system is missing, everything below is empty for a reason that has nothing to do with zones.
    /// So it is reported separately rather than inferred from a silent result, which is
    /// <c>docs/LESSONS.md</c>'s <i>a search that finds nothing has two explanations</i> built into
    /// the tool.
    /// </para>
    /// <para>
    /// <b>Reads <c>ZoneProperties</c> directly rather than per zone</b>, because the point of the
    /// record is that it is queryable for zones that are not loaded. Walking the dictionary is also
    /// the only way to see the whole picture; asking zone by zone would need a list of zones, which
    /// is the thing being tested.
    /// </para>
    /// <para>
    /// <b>Namespaced deliberately.</b> Wish names are one global namespace shared with every
    /// installed mod, and <c>territory</c> is a word more than one of them might want.
    /// </para>
    /// <para>
    /// Charter rule 5: reads two dictionaries and prints. No I/O, no reflection of my own, no
    /// Harmony.
    /// </para>
    /// </remarks>
    [HasWishCommand]
    public class Vixy_TerritoryWish
    {
        [WishCommand("vixyterritory", null)]
        public static void Report()
        {
            StringBuilder sb = new StringBuilder();

            bool installed = The.Game?.GetSystem<Vixy_Territory>() != null;
            sb.Append("{{Y|Territory}}  system ")
              .Append(installed ? "{{G|installed}}" : "{{R|MISSING}}")
              .Append("   holding needs ").Append(Vixy_Territory.Threshold).Append(" or more\n");

            if (!installed)
            {
                sb.Append("\n{{R|Nothing below can be trusted.}} RequireSystem did not take on this\n")
                  .Append("save, so no zone has been recorded whatever the map looks like.");
                Popup.Show(sb.ToString());
                return;
            }

            List<string> held = new List<string>();
            List<string> vacated = new List<string>();

            foreach (KeyValuePair<string, Dictionary<string, object>> zone
                     in The.ZoneManager.ZoneProperties)
            {
                if (zone.Value == null) continue;
                if (zone.Value.TryGetValue(Vixy_Territory.HeldBy, out object holder))
                {
                    held.Add(zone.Key + "  {{G|" + holder + "}}");
                }
                if (zone.Value.TryGetValue(Vixy_Territory.Vacated, out object was))
                {
                    vacated.Add(zone.Key + "  {{K|" + was + "}} gone");
                }
            }

            sb.Append("zones recorded  ").Append(held.Count + vacated.Count)
              .Append("   of ").Append(The.ZoneManager.ZoneProperties.Count)
              .Append(" carrying any property\n");

            Append(sb, "held", held);
            Append(sb, "vacated", vacated);

            if (held.Count == 0 && vacated.Count == 0)
            {
                sb.Append("\nNothing recorded yet. Expected on a save where no zone has been built\n")
                  .Append("or left since the system arrived - it writes on build and on leaving.");
            }

            Popup.Show(sb.ToString());
        }

        /// <summary>
        /// One section, capped, and saying so when it caps.
        /// </summary>
        /// <remarks>
        /// A long game records hundreds of zones and <c>Popup.Show</c> is not a scrollable log, so
        /// this truncates — and prints the count it dropped, because a silently short list is the
        /// failure `docs/LESSONS.md` files under no silent caps.
        /// </remarks>
        private static void Append(StringBuilder sb, string Title, List<string> Lines)
        {
            sb.Append('\n').Append("{{Y|").Append(Title).Append("}}  ").Append(Lines.Count).Append('\n');
            int shown = Lines.Count < 12 ? Lines.Count : 12;
            for (int i = 0; i < shown; i++)
            {
                sb.Append("  ").Append(Lines[i]).Append('\n');
            }
            if (Lines.Count > shown)
            {
                sb.Append("  … and ").Append(Lines.Count - shown).Append(" more\n");
            }
        }
    }
}
