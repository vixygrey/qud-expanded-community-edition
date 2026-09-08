using System.Collections.Generic;
using System.Text;
using QudExpandedCE;
using XRL.UI;
using XRL.Wish;
using XRL.World;
using XRL.World.Parts;

namespace XRL
{
    /// <summary>
    /// <c>vixyband</c> — send one now, and see what is already walking.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>A band is rare on purpose, which makes it hard to look at.</b> It needs a zone that was
    /// held, cleared to its last member and left, then a one-in-four roll, and it then advances only
    /// while I am crossing the world map. Waiting for one to happen is not a test.
    /// </para>
    /// <para>
    /// <b>The listing half is the more useful one.</b> A band that never arrives has several
    /// possible reasons — no path, a destination that will not build, or simply that I have been
    /// underground — and they look identical from the outside. Showing what is in flight and where
    /// it is heading tells them apart.
    /// </para>
    /// <para>
    /// Namespaced deliberately: wish names are one global namespace shared with every installed mod.
    /// </para>
    /// </remarks>
    [HasWishCommand]
    public class Vixy_BandWish
    {
        [WishCommand("vixyband", null)]
        public static void Report()
        {
            StringBuilder sb = new StringBuilder();
            sb.Append("{{Y|Bands}}  option ")
              .Append(Raven_Options.TravellingBands ? "{{G|on}}" : "{{R|off}}")
              .Append("   one vacancy in ").Append(Vixy_BandDispatch.OneIn).Append(" is answered\n");

            List<string> flight = new List<string>();
            foreach (GameObject o in The.ZoneManager.FindObjects(
                         (GameObject x) => x.HasPart<Vixy_Band>()))
            {
                AIWorldMapTravel travel = o.GetPart<AIWorldMapTravel>();
                Cell at = o.CurrentCell;
                flight.Add(
                    "{{G|" + o.GetStringProperty(Vixy_Band.FactionProperty, "?") + "}}"
                    + "  at " + (at == null ? "nowhere" : at.X + "," + at.Y)
                    + "  bound for " + (travel == null
                        ? "{{R|no route}}"
                        : travel.ParasangX + "," + travel.ParasangY)
                );
            }

            sb.Append("\n{{Y|in flight}}  ").Append(flight.Count).Append('\n');
            foreach (string line in flight)
            {
                sb.Append("  ").Append(line).Append('\n');
            }

            List<string> vacancies = new List<string>();
            foreach (KeyValuePair<string, Dictionary<string, object>> zone
                     in The.ZoneManager.ZoneProperties)
            {
                if (zone.Value != null
                    && zone.Value.TryGetValue(Vixy_Territory.Vacated, out object was))
                {
                    vacancies.Add(zone.Key + "  {{K|" + was + "}} gone");
                }
            }
            sb.Append("\n{{Y|unanswered vacancies}}  ").Append(vacancies.Count).Append('\n');
            int shown = vacancies.Count < 8 ? vacancies.Count : 8;
            for (int i = 0; i < shown; i++)
            {
                sb.Append("  ").Append(vacancies[i]).Append('\n');
            }
            if (vacancies.Count > shown)
            {
                sb.Append("  … and ").Append(vacancies.Count - shown).Append(" more\n");
            }

            if (flight.Count == 0 && vacancies.Count == 0)
            {
                sb.Append("\nNothing to answer and nothing walking. A vacancy needs a zone that was\n")
                  .Append("held, cleared to the last of them, and left - see {{Y|vixyterritory}}.");
            }

            Popup.Show(sb.ToString());
        }

        /// <summary>
        /// <c>vixyband &lt;faction&gt;</c> — send one from anywhere that faction holds, to the
        /// vacancy nearest to hand.
        /// </summary>
        /// <remarks>
        /// Deliberately uses the ordinary dispatch path rather than a shortcut, so what this
        /// produces is what play produces. If there is no recorded vacancy it says so rather than
        /// inventing a destination, because a band sent somewhere arbitrary would not be testing the
        /// thing that matters.
        /// </remarks>
        [WishCommand("vixyband", null)]
        public static void Send(string Faction)
        {
            string destination = null;
            foreach (KeyValuePair<string, Dictionary<string, object>> zone
                     in The.ZoneManager.ZoneProperties)
            {
                if (zone.Value != null && zone.Value.ContainsKey(Vixy_Territory.Vacated))
                {
                    destination = zone.Key;
                    break;
                }
            }

            if (destination == null)
            {
                Popup.Show("No recorded vacancy to send anybody to. Empty a lair and leave it first.");
                return;
            }

            string from = null;
            foreach (KeyValuePair<string, Dictionary<string, object>> zone
                     in The.ZoneManager.ZoneProperties)
            {
                if (zone.Value != null
                    && zone.Value.TryGetValue(Vixy_Territory.HeldBy, out object holder)
                    && (holder as string) == Faction)
                {
                    from = zone.Key;
                    break;
                }
            }

            if (from == null)
            {
                Popup.Show("Nowhere recorded that {{G|" + Faction + "}} holds, so nowhere to set out from.");
                return;
            }

            bool sent = Vixy_BandDispatch.Send(Faction, from, destination);
            Popup.Show(sent
                ? "{{G|" + Faction + "}} set out from " + from + "\nfor " + destination + "."
                : "{{R|Could not send.}} No world-map cell for " + from + ", or no route.");
        }
    }
}
