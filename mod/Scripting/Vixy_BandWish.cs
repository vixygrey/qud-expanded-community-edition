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
                    + "  " + o.GetStringProperty(Vixy_Band.MissionProperty, "legacy")
                    + "  from " + o.GetStringProperty(Vixy_Band.OriginProperty, "?")
                    + "  at " + (at == null ? "nowhere" : at.X + "," + at.Y)
                    + "  bound for " + (travel == null
                        ? "{{R|no route}}"
                        : travel.ParasangX + "," + travel.ParasangY)
                    + "  target " + o.GetStringProperty(Vixy_Band.TargetProperty, "?")
                    + "  [" + Vixy_BandDispatch.SiteFlags(
                        o.GetStringProperty(Vixy_Band.TargetProperty)
                    ) + "]"
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
            // "Recorded", not "unanswered". Every vacancy a dispatch considered is spent by it,
            // so with the option on this list is empty and a name in it is a defect worth chasing.
            // With the option off nothing considers them, and #929 is why they will stay here.
            sb.Append("\n{{Y|recorded vacancies}}  ").Append(vacancies.Count).Append('\n');
            if (vacancies.Count > 0 && !Raven_Options.TravellingBands)
            {
                sb.Append("  {{K|recorded with bands off, and inert - see FEATURES 65.8}}\n");
            }
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
                sb.Append("\nNothing walking, and nothing recorded. An empty list is the resting\n")
                  .Append("state rather than a queue that ran dry: every vacancy is spent by the\n")
                  .Append("dispatch that considered it, answered or not. A new one needs a zone\n")
                  .Append("that was held, cleared to the last of them, and left - see\n")
                  .Append("{{Y|vixyterritory}}.");
            }

            Popup.Show(sb.ToString());
        }

        /// <summary>
        /// <c>vixyband &lt;faction&gt;</c> — send one from anywhere that faction holds, to the
        /// vacancy nearest to hand.
        /// </summary>
        /// <remarks>
        /// Deliberately uses the ordinary dispatch path rather than a shortcut, so what this
        /// produces is what play produces.
        /// <para>
        /// <b>It falls back to wherever I am standing, and says so.</b> Recorded vacancies used to
        /// accumulate, so there was nearly always one lying about to aim at; since #929 spends every
        /// vacancy on the dispatch that considered it, there is usually none. Refusing on that
        /// ground would leave the only instrument for #832's two unverified questions unable to
        /// fire. Sending a band to my own zone is also the better test of the pair — arrival is the
        /// half that builds a party, and this is the one way to be standing in it when that happens.
        /// </para>
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

            bool here = false;
            if (destination == null)
            {
                // No recorded opening, so aim at my own zone instead. Not from the world map: the
                // destination is parsed as a parasang and a zone, and the map itself is neither.
                Zone mine = The.ActiveZone;
                if (mine == null || mine.IsWorldMap())
                {
                    Popup.Show(
                        "No recorded vacancy, and no zone to fall back on - step off the world map\n"
                            + "and try again, or empty a lair and leave it first."
                    );
                    return;
                }
                destination = mine.ZoneID;
                here = true;
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
                    + (here ? "\n\n{{K|No recorded vacancy, so they are bound for where I stand.}}" : "")
                : "{{R|Could not send.}} No world-map cell for " + from + ", or no route.");
        }
    }
}
