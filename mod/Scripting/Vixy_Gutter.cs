using System;
using System.Collections.Generic;
using XRL.Messages;
using XRL.Rules;

namespace XRL.World.Parts
{
    /// <summary>
    /// Exhaustion makes the mind unreliable: a mental mutation gutters out mid-thought.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>This is §3.2.1's rule as a mechanism.</b> Fatigue should make the character *unreliable*
    /// rather than *weaker* — a stat penalty is the lazy reading. Losing a capability you were
    /// counting on, at a moment you did not choose, is the sharper one.
    /// </para>
    /// <para>
    /// <b>It does not intercept the use, and that is deliberate.</b> The obvious build is a true
    /// misfire — cancel the activation, keep the cooldown. It cannot be done evenly. Mutation
    /// commands dispatch two different ways: 28 go through <c>CommandEvent</c>, which a part on the
    /// player can cancel, and 35 go through the legacy <c>Event.New(Command)</c> path that
    /// <c>CommandEvent.Send</c> fires *first* and aborts on. A handler never sees those in time. So
    /// an interception-based misfire would fire on some of the player's mutations and silently never
    /// fire on the rest, decided by which ones they happened to roll — the #588 defect again.
    /// </para>
    /// <para>
    /// <b>Writing the cooldown is vanilla's own idiom.</b> <c>SphynxSalt_Tonic</c> finds mental
    /// abilities with <c>Class.Contains("Mental")</c> and assigns <c>entry.Cooldown</c> directly; the
    /// setter registers the countdown with <c>ActivatedAbilities</c>, so a plain write is the
    /// supported path rather than a shortcut around one. It reaches all 26 activated mental
    /// abilities identically, and <c>NotUsableDescription</c> — the single gate consulted before any
    /// command is sent — already refuses the press with the right message for free.
    /// </para>
    /// <para>
    /// <b>The half of §3.2.1 that is missing is missing on purpose.</b> The companion mechanic was
    /// false sounds, and there is nothing in Qud for a false sound to hide among: eight distinct
    /// "You hear" strings in the whole assembly, every one tied to an identifiable cause, and no
    /// hallucination effect (<c>WakingDream</c> and <c>DeepDream</c> are metempsychosis). A phantom
    /// noise with no true counterpart is identified as this mod on its second occurrence. See
    /// docs/LESSONS.md.
    /// </para>
    /// </remarks>
    public static class Vixy_Gutter
    {
        /// <summary>Rounds of cooldown a slip costs, in segments — Precognition's own 500 is 50.</summary>
        public const int Cost = 200;

        /// <summary>One action in this many slips, at Exhausted.</summary>
        public const int ExhaustedOdds = 200;

        /// <summary>One action in this many slips, at Collapsing.</summary>
        public const int CollapsingOdds = 80;

        /// <summary>
        /// Rolled once per action from <see cref="Vixy_Fatigue"/>, on the event fatigue already
        /// accrues on. Costs roughly five slips across the whole exhausted stretch.
        /// </summary>
        public static void Slip(GameObject Player)
        {
            if (Player == null || !Player.IsPlayer()) return;

            int fatigue = Vixy_Fatigue.Get(Player);
            if (fatigue < Vixy_Fatigue.Exhausted) return;

            int odds = (fatigue >= Vixy_Fatigue.Collapsing) ? CollapsingOdds : ExhaustedOdds;
            if (Stat.Random(1, odds) != 1) return;

            ActivatedAbilityEntry entry = PickReadyMental(Player);
            if (entry == null) return;

            entry.Cooldown = Cost;
            MessageQueue.AddPlayerMessage(
                "{{r|Your concentration slips, and " + entry.DisplayName + " gutters out.}}");
        }

        /// <summary>
        /// A mental ability the player could have used this turn, chosen at random.
        /// </summary>
        /// <remarks>
        /// <c>IsUsable</c> already means enabled and off cooldown. Toggles that are currently *on*
        /// are skipped: writing a cooldown would not turn one off, so the message would name a
        /// capability the player can still see running.
        /// </remarks>
        private static ActivatedAbilityEntry PickReadyMental(GameObject Player)
        {
            ActivatedAbilities abilities = Player.GetPart<ActivatedAbilities>();
            if (abilities?.AbilityByGuid == null) return null;

            List<ActivatedAbilityEntry> ready = new List<ActivatedAbilityEntry>();
            foreach (ActivatedAbilityEntry entry in abilities.AbilityByGuid.Values)
            {
                if (entry == null || entry.Class == null) continue;
                if (!entry.Class.Contains("Mental")) continue;
                if (!entry.IsUsable) continue;
                if (entry.ToggleState) continue;
                ready.Add(entry);
            }

            if (ready.Count == 0) return null;
            return ready[Stat.Random(0, ready.Count - 1)];
        }
    }
}
