using System;
using System.Collections.Generic;
using QudExpandedCE;
using XRL;
using XRL.Messages;
using XRL.Rules;
using XRL.UI;
using XRL.World.AI.GoalHandlers;
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
        public enum Where { Settlement, Bed, Sheltered, Open }

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
        /// with no top end gives the player nowhere to aim, and "walk to a town and you can rest" is
        /// a decision worth making.
        ///
        /// <b>Hostility is not a tier here, and used to be.</b> When it was, `Locate` returned
        /// Hostile whenever anything hostile stood in the zone - so Bed, Sheltered and Open could
        /// only apply when nothing hostile was present, which is exactly when no ambush is possible.
        /// Five tiers collapsed to two. Where you are is the tier; whether anything is there to find
        /// you is a precondition, checked in <see cref="RollAmbush"/>.
        /// </remarks>
        public static Where Locate(GameObject Player)
        {
            Cell cell = Player?.CurrentCell;
            if (cell == null) return Where.Open;
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

        /// <summary>
        /// Chance per turn that something already in the zone finds you, in hundredths of a percent.
        /// </summary>
        /// <remarks>
        /// <b>Derived from per-sleep odds, not chosen per turn</b>, and conditional on a hostile
        /// being in the zone at all. A full sleep is 167-250 actions, so a rate that reads harmless
        /// per turn compounds into something else entirely.
        ///
        /// Targets, given something hostile is present:
        ///
        ///   settlement   0 per turn  ->   0%
        ///   bed          6           ->  10%
        ///   sheltered   14           ->  30%
        ///   open        37           ->  60%
        /// </remarks>
        public static int AmbushChance(GameObject Player)
        {
            return Locate(Player) switch
            {
                Where.Settlement => 0,
                Where.Bed => 6,
                // 17 rather than 14, and the change is #777's rather than a retune. The roll fires
                // every action asleep, so shortening a sheltered sleep from 250 actions to its
                // intended 208 also removed 42 rolls - which would have dropped the odds this tier
                // was tuned to from 30% a sleep to 25% as a side effect of fixing arithmetic. 17
                // over 208 actions is 29.8%, which is where #764 put it deliberately.
                Where.Sheltered => 17,
                _ => 37,
            };
        }

        /// <summary>
        /// The nearest thing in the zone that could plausibly come and find you.
        /// </summary>
        /// <remarks>
        /// Sleeping and dormant creatures count - waking them is the point - but the merely
        /// unconscious do not, since a stunned enemy is not a threat that crept up on you.
        /// </remarks>
        private static GameObject FindCulprit(GameObject Player)
        {
            Zone zone = Player?.CurrentZone;
            if (zone == null) return null;

            GameObject nearest = null;
            int best = int.MaxValue;
            foreach (GameObject obj in zone.GetObjectsWithPart("Brain"))
            {
                if (obj == Player || !obj.IsAlive || obj.Brain == null) continue;
                if (!obj.IsHostileTowards(Player)) continue;
                if (obj.HasEffect("Stun") || obj.HasEffect("Paralyzed")) continue;

                int d = obj.DistanceTo(Player);
                if (d < best) { best = d; nearest = obj; }
            }
            return nearest;
        }

        /// <summary>
        /// One ambush roll per turn asleep. On a hit, something real comes for you.
        /// </summary>
        /// <remarks>
        /// <b>The first version woke the player, applied Dazed and printed "something is moving
        /// nearby" without checking that anything was.</b> On open ground in an empty zone - the
        /// common case - that message was simply false, and the mechanic was a randomised penalty
        /// with no danger attached. §3.3 asked for "spawn or wake a nearby hostile"; declining to
        /// spawn was deliberate, and then the waking was never written.
        ///
        /// So an ambush now needs a culprit. No hostile in the zone means no roll and an undisturbed
        /// sleep, which makes the rate mean "chance something finds you" rather than "chance you are
        /// interrupted" - what the tier table always described. Nothing is spawned: waking what is
        /// already there is less arbitrary than conjuring an attacker out of the design's
        /// convenience.
        ///
        /// Aiming it is `Brain.Target` plus a `Kill` goal, which is how `PsychicHunterSystem` sends
        /// a hunter after the player and how the two tutorial creatures work.
        /// </remarks>
        public static void RollAmbush(GameObject Player)
        {
            if (Player == null || !Player.HasEffect<Asleep>()) return;

            int chance = AmbushChance(Player);
            if (chance <= 0) return;

            GameObject culprit = FindCulprit(Player);
            if (culprit == null) return;

            if (Stat.Random(1, 10000) > chance) return;

            // Wake it if it was asleep - that is the half of §3.3 that was missing - and point it
            // at the player rather than hoping its own wandering brings it over.
            Asleep theirs = culprit.GetEffect<Asleep>();
            if (theirs != null) culprit.RemoveEffect(theirs);
            culprit.Brain.Target = Player;
            culprit.Brain.PushGoal(new Kill(Player));

            Asleep mine = Player.GetEffect<Asleep>();
            if (mine != null) Player.RemoveEffect(mine);
            Player.ApplyEffect(new Dazed(Stat.Random(3, 6)));

            MessageQueue.AddPlayerMessage(
                "{{R|You wake with a start. " + culprit.The + culprit.ShortDisplayName + " has found you.}}");
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

            int duration = AskHowLong(Player);
            if (duration <= 0) return;

            int quality = RestQuality(Player);
            string where = quality >= 15
                ? "You settle down to sleep."
                : (quality >= 12 ? "You find a sheltered spot and lie down." : "You lie down on the bare ground.");
            MessageQueue.AddPlayerMessage(where);

            Player.ForceApplyEffect(new Asleep(duration, forced: true, quicksleep: true, Voluntary: true));
        }

        /// <summary>Rounds of sleep the player chose, or 0 if they backed out.</summary>
        /// <remarks>
        /// <para>
        /// <b>This is `Bed`'s own prompt, borrowed rather than invented.</b> `Bed.cs` line 337 asks
        /// "How long would you like to sleep?" with three fixed spans - 150, 375 and 600 rounds -
        /// each labelled with the clock time the sleeper would wake at. Anyone who has used a bedroll
        /// already knows this dialogue, and a `Sleep` command that silently did something else while
        /// offering *less* control than the bedroll in their pack was the actual defect. #776.
        /// </para>
        /// <para>
        /// <b>A timed choice is a ceiling, not a span.</b> `Vixy_Fatigue.Rest` ends the sleep the
        /// moment fatigue reaches zero, so "until 9:00" means "no later than 9:00" - waking earlier
        /// because I am rested is the good outcome rather than a broken promise.
        /// </para>
        /// <para>
        /// <b>"Until rested" is first because it is what most nights want</b>, and it carries a
        /// computed bound rather than the old `Stat.Random(200, 320)`. That range could not keep the
        /// promise the label now makes out loud: a full meter on open ground drains at 4 a turn and
        /// needs about 250, so a low roll woke me unrested roughly half the time. `TurnsToRest`
        /// derives the bound from the drain itself, so the two cannot come apart again.
        /// </para>
        /// </remarks>
        private static int AskHowLong(GameObject Player)
        {
            int[] spans = { 150, 375, 600 };
            List<string> options = new List<string> { "Until rested" };
            foreach (int span in spans)
            {
                options.Add("Until " + Calendar.GetTime(Calendar.TotalTimeTicks + span));
            }

            int pick = Popup.PickOption(
                "How long would you like to sleep?",
                null,
                "",
                "Sounds/UI/ui_notification",
                options.ToArray(),
                null, null, null, null, null, null,
                0, 60, 0, -1,
                AllowEscape: true);

            if (pick < 0) return 0;
            return pick == 0 ? TurnsToRest(Player) : spans[pick - 1];
        }

        /// <summary>
        /// Long enough to reach zero from here, with slack.
        /// </summary>
        /// <remarks>
        /// Derived from <see cref="DrainPerAction"/> rather than guessed, so "until rested" keeps its
        /// word at every rest quality and stays correct if the drain is ever retuned.
        /// </remarks>
        public static int TurnsToRest(GameObject Player)
        {
            int drain = DrainHundredths(Player);
            return Vixy_Fatigue.Get(Player) * 100 / drain + 20;
        }

        /// <summary>
        /// Fatigue removed per action of voluntary sleep, in hundredths of a point.
        /// </summary>
        /// <remarks>
        /// <para>
        /// The one place this arithmetic lives. `Vixy_Fatigue.Rest` spends it and
        /// <see cref="TurnsToRest"/> budgets against it, and a promise made in the sleep menu is only
        /// as good as those two agreeing.
        /// </para>
        /// <para>
        /// <b>It is carried in hundredths because whole points truncated a tier away.</b> This was
        /// <c>4 * RestQuality / 10</c>, and §3.3's rest qualities are tenths — so a sheltered spot's
        /// 12 became <c>4 * 12 / 10 == 4</c>, which is precisely what open ground gets. One of the
        /// four tiers did nothing at all from the day it shipped, and `docs/FEATURES.md` §51.3 spent
        /// that whole time quoting a 4.8 the code never produced. `Accrue` had the same problem on
        /// the other side of the meter and already solved it this way. #777.
        /// </para>
        /// </remarks>
        public static int DrainHundredths(GameObject Player)
        {
            return Math.Max(1, 40 * RestQuality(Player));
        }
    }
}
