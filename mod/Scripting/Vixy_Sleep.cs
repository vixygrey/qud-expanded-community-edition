using System;
using QudExpandedCE;
using XRL;
using XRL.Messages;
using XRL.Rules;
using XRL.World.Effects;

namespace XRL.World.Parts
{
    /// <summary>
    /// Voluntary sleep: where you lie down, and what finds you while you are under.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>This is the half that makes fatigue a decision rather than a chore.</b> Rest quality and
    /// ambush chance both key on where the player sleeps, which is what gives a bedroll a reason to
    /// exist and what §1 asks for: *"where you sleep, and what finds you while you're under, is the
    /// interesting part."*
    /// </para>
    /// <para>
    /// <b>Vanilla's <c>Asleep</c> is reused wholesale rather than reimplemented.</b> Its
    /// vulnerability maths is already tuned — −12 DV and +4 penetration for attackers — and other
    /// mods and creatures interact with it. It is applied with <c>Voluntary: true</c>, which is what
    /// <c>Vixy_Fatigue.Rest</c> reads to decide whether sleep is restful: gas, narcolepsy and the
    /// gaze effects all leave that flag false, so no involuntary sleep can clear fatigue and the
    /// gas-grenade exploit never opens.
    /// </para>
    /// <para>
    /// <b><c>forced: true</c> does not mean involuntary.</b> It bypasses the <c>CanApplySleep</c>
    /// refusals, and <c>Bed</c> passes it alongside <c>Voluntary: true</c> for exactly this case — a
    /// deliberate sleep that should not be blocked. The two flags are orthogonal and easy to read
    /// backwards.
    /// </para>
    /// <para>
    /// <b>No new state.</b> Everything here is computed from the player's surroundings at the moment
    /// they lie down.
    /// </para>
    /// </remarks>
    public static class Vixy_Sleep
    {
        /// <summary>
        /// Where the player is sleeping, as one tier. Both tables key on this so they cannot
        /// disagree about how many tiers exist.
        /// </summary>
        /// <remarks>
        /// The first version had `RestQuality` distinguishing a sheltered spot from open ground while
        /// `AmbushChance` did not, so the two disagreed silently. One function deciding the tier and
        /// two reading it removes the failure rather than fixing an instance of it.
        /// </remarks>
        public enum Where { Settlement, Bed, Sheltered, Open, Hostile }

        /// <summary>
        /// A named settlement is the one genuinely safe place to sleep.
        /// </summary>
        /// <remarks>
        /// `Zone.IsCheckpoint()` is the game's own notion of a safe hub - it tests for a
        /// `CheckpointWidget` in cell (0,0) - and the ten zones carrying it are Joppa, the Stilt,
        /// Grit Gate, Kyakukya, Yd Freehold, Ezra and the Arrivarium. Using it means the safe list is
        /// Freehold's rather than one this fork invented and would have to maintain.
        ///
        /// The design doc put a settlement at 0.1% per turn. It is 0 here, deliberately: a tier list
        /// with no top end gives the player nowhere to aim, and "walk to a town and you can rest"
        /// is a decision worth making. Hostiles in the zone still override it - a settlement under
        /// attack is not a safe place to lie down.
        /// </remarks>
        public static Where Locate(GameObject Player)
        {
            Cell cell = Player?.CurrentCell;
            if (cell == null) return Where.Open;
            if (HostilesPresent(Player)) return Where.Hostile;
            if (Player.CurrentZone?.IsCheckpoint() ?? false) return Where.Settlement;
            if (cell.HasObjectWithPart("Bed")) return Where.Bed;
            if (Player.CurrentZone?.IsInside() ?? false) return Where.Sheltered;
            return Where.Open;
        }

        /// <summary>Rest quality in tenths, so the arithmetic stays integer.</summary>
        public static int RestQuality(GameObject Player)
        {
            int tenths = Locate(Player) switch
            {
                Where.Settlement => 15,
                Where.Bed => 15,
                Where.Sheltered => 12,
                _ => 10,
            };

            // Sleeping in your armour rests you less. Heavily burdened is the burden mod's band 3;
            // it is off by default, so this is a bonus interaction rather than load-bearing. #176.
            if (Player != null && Player.GetIntProperty("Vixy_BurdenBand") >= 3) tenths = tenths * 3 / 4;

            return Math.Max(1, tenths);
        }

        /// <summary>Ambush chance per turn asleep, in hundredths of a percent.</summary>
        /// <remarks>
        /// <b>These are derived from per-sleep odds, not chosen per turn.</b> That is the correction
        /// this table needed: a full sleep is 167-250 actions, so a rate that reads harmless per turn
        /// compounds into something else entirely. The design doc's 0.5% for open ground is a
        /// <b>71%</b> chance of being ambushed over one sleep, which is not "location is a decision",
        /// it is "beds or nothing".
        ///
        /// Targets, and what they compound to over a full 1000-fatigue sleep:
        ///
        ///   settlement   0 per turn  ->   0%
        ///   bed          3           ->   5%
        ///   sheltered    6           ->  14%
        ///   open        14           ->  30%
        ///   hostile     64           ->  80%
        /// </remarks>
        public static int AmbushChance(GameObject Player)
        {
            return Locate(Player) switch
            {
                Where.Settlement => 0,
                Where.Bed => 3,
                Where.Sheltered => 6,
                Where.Hostile => 64,
                _ => 14,
            };
        }

        private static bool HostilesPresent(GameObject Player)
        {
            Zone zone = Player?.CurrentZone;
            if (zone == null) return false;
            foreach (GameObject obj in zone.GetObjectsWithPart("Combat"))
            {
                if (obj != Player && obj.IsHostileTowards(Player) && obj.IsAlive)
                {
                    return true;
                }
            }
            return false;
        }

        /// <summary>
        /// One ambush roll per turn asleep. On a hit, wake hard.
        /// </summary>
        /// <remarks>
        /// This is what makes location a decision rather than a formality, and why a bedroll earns
        /// its weight: a bed is sixty times safer than lying down among hostiles. Nothing is spawned
        /// - waking to something already in the zone is both cheaper and less arbitrary than
        /// conjuring an attacker out of the design's convenience.
        /// </remarks>
        public static void RollAmbush(GameObject Player)
        {
            if (Player == null || !Player.HasEffect<Asleep>()) return;
            if (Stat.Random(1, 10000) > AmbushChance(Player)) return;

            Asleep asleep = Player.GetEffect<Asleep>();
            if (asleep != null) Player.RemoveEffect(asleep);

            Player.ApplyEffect(new Dazed(Stat.Random(3, 6)));
            MessageQueue.AddPlayerMessage("{{R|You wake with a start. Something is moving nearby.}}");
            The.Core?.RenderBase();
        }

        /// <summary>
        /// Lie down, if there is any reason to.
        /// </summary>
        /// <remarks>
        /// Refusing when already rested is deliberate: the alternative is a command that always
        /// succeeds and does nothing, which trains the player to stop reading its messages.
        /// </remarks>
        public static void Attempt(GameObject Player)
        {
            if (Player == null || !Player.IsPlayer()) return;

            if (Player.HasEffect<Asleep>())
            {
                Player.ShowFailure("You are already asleep.");
                return;
            }

            if (Vixy_Fatigue.Get(Player) <= 0)
            {
                Player.ShowFailure("You are not tired.");
                return;
            }

            if (Player.OnWorldMap())
            {
                Player.ShowFailure("You cannot sleep out here.");
                return;
            }

            int quality = RestQuality(Player);
            string where = quality >= 15
                ? "You settle down to sleep."
                : (quality >= 12 ? "You find a sheltered spot and lie down." : "You lie down on the bare ground.");
            MessageQueue.AddPlayerMessage(where);

            // Duration is generous - fatigue drain, not the clock, is what ends the sleep in
            // practice, and Asleep already wakes on damage.
            Player.ForceApplyEffect(new Asleep(Stat.Random(200, 320), forced: true, quicksleep: true, Voluntary: true));
        }
    }
}
