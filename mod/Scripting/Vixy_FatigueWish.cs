using System;
using System.Text;
using QudExpandedCE;
using XRL.Messages;
using XRL.UI;
using XRL.Wish;
using XRL.World.Effects;
using XRL.World.Parts;

namespace XRL.World
{
    /// <summary>
    /// <c>wish vixyfatigue</c> — read the meter, and <c>wish vixyfatigue:600</c> — set it.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>This exists because the test plan for the fatigue work could not be carried out.</b> Three
    /// of its regression checks are claims about a number — that a world-map crossing charges once
    /// rather than twice, that a domination bills once on return, that turning the option off and on
    /// costs nothing. `Vixy_Fatigued` shows four words, and 126 against 252 reads as the same word,
    /// so none of those was performable. I wrote a plan and never counted whether anything could
    /// execute it. #782.
    /// </para>
    /// <para>
    /// <b>The stamps are the point of the readout.</b> Single-charging is not a claim about the
    /// meter, it is a claim about `Vixy_FatigueChargedTurn` and `Vixy_FatigueOnWorldMapSince` — so
    /// printing those against the current turn is the only honest way to check it. Taking a snapshot
    /// before and after a crossing answers in one line what watching the bands cannot answer at all.
    /// </para>
    /// <para>
    /// <b>And the setter is what makes the rest of the plan affordable.</b> Several checks begin
    /// "reach Exhausted", which is about 2,900 actions of unhurried play. That is not a test, it is
    /// an afternoon.
    /// </para>
    /// <para>
    /// <b>Wishes are the game's own dev channel and reach mods by design.</b>
    /// `WishManager.UpdateCommandCollection` calls
    /// <c>ModManager.GetMethodsWithAttribute(typeof(WishCommand), typeof(HasWishCommand))</c> —
    /// `ModManager`, so mod assemblies are scanned deliberately, the same way `[PlayerMutator]` is
    /// found. Nothing here is player-facing unless it is typed, and charter rule 5 is untouched: no
    /// file I/O, no network, no reflection of my own, no Harmony.
    /// </para>
    /// <para>
    /// <b>Namespaced deliberately.</b> Wish names are one global namespace shared with every other
    /// installed mod, and `fatigue` is a word more than one of them might want.
    /// </para>
    /// </remarks>
    [HasWishCommand]
    public class Vixy_FatigueWish
    {
        [WishCommand("vixyfatigue", null)]
        public static void Report()
        {
            GameObject player = The.Player;
            if (player == null) return;

            int fatigue = Vixy_Fatigue.Get(player);
            int now = (int)XRL.Core.XRLCore.CurrentTurn;
            int charged = player.GetIntProperty(Vixy_Fatigue.ChargedTurnProperty);
            int onMap = player.GetIntProperty(Vixy_Fatigue.OnMapSinceProperty);
            int drain = Vixy_Sleep.DrainHundredths(player);

            StringBuilder sb = new StringBuilder();
            sb.Append("{{Y|Fatigue}}  ").Append(fatigue).Append(" / ").Append(Vixy_Fatigue.Max)
              .Append("   band ").Append(BandName(fatigue))
              .Append("   option ").Append(Raven_Options.Fatigue ? "{{G|on}}" : "{{R|off}}").Append('\n');

            sb.Append("carried  accrue ").Append(player.GetIntProperty("Vixy_FatigueRemainder"))
              .Append("/100   rest ").Append(player.GetIntProperty("Vixy_FatigueRestRemainder"))
              .Append("/100\n");

            sb.Append("{{Y|Here}}  ").Append(Vixy_Sleep.Locate(player))
              .Append("   quality ").Append(Vixy_Sleep.RestQuality(player)).Append("/10")
              .Append("   burden ").Append(Vixy_Sleep.BurdenFactor(player)).Append('%')
              .Append("   load ").Append(Vixy_Burdened.LoadPercent(player)).Append("%\n");

            sb.Append("sleep  drain ").Append(drain / 100).Append('.').Append((drain % 100).ToString("00"))
              .Append("/action   to rest ").Append(Vixy_Sleep.TurnsToRest(player)).Append(" actions")
              .Append("   ambush ").Append(Vixy_Sleep.AmbushChance(player)).Append("/10000 per action\n");

            // The two stamps are why this command exists: single-charging is a claim about these,
            // not about the meter.
            sb.Append("{{Y|Turn}}  now ").Append(now)
              .Append("   charged ").Append(charged == 0 ? "unset" : charged.ToString())
              .Append(" ({{C|gap ").Append(charged == 0 ? 0 : now - charged).Append("}})")
              .Append("   on map since ").Append(onMap == 0 ? "not on map" : onMap.ToString());

            Popup.Show(sb.ToString());
        }

        [WishCommand("vixyfatigue", null)]
        public static void Set(string rest)
        {
            GameObject player = The.Player;
            if (player == null) return;

            if (!int.TryParse(rest?.Trim(), out int value))
            {
                MessageQueue.AddPlayerMessage("{{R|vixyfatigue: expected a number 0-" + Vixy_Fatigue.Max + ".}}");
                return;
            }

            // Set clamps to 0..Max, so a silly number is corrected rather than refused.
            Vixy_Fatigue.Set(player, value);
            MessageQueue.AddPlayerMessage(
                "{{Y|Fatigue set to " + Vixy_Fatigue.Get(player) + " (" + BandName(Vixy_Fatigue.Get(player)) + ").}}");
        }

        private static string BandName(int Fatigue)
        {
            return Vixy_Fatigue.BandFor(Fatigue) switch
            {
                Vixy_Fatigue.Collapsing => "{{R|collapsing}}",
                Vixy_Fatigue.Exhausted => "{{r|exhausted}}",
                Vixy_Fatigue.Weary => "{{W|weary}}",
                Vixy_Fatigue.Tired => "{{y|tired}}",
                _ => "{{g|rested}}",
            };
        }
    }
}
