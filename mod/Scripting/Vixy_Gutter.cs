using System;
using System.Collections.Generic;
using XRL.Messages;
using XRL.Rules;

namespace XRL.World.Parts
{
    /// <summary>
    /// Tiredness makes a character unreliable: something they were counting on gutters out.
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

        /// <summary>One action in this many slips, at Weary.</summary>
        /// <remarks>
        /// <b>Weary had no mechanical effect at all until #822</b>, though `docs/DESIGN_sleep.md`
        /// §3.2.1 always said it should — it was written and never built, so crossing 600 cost a
        /// message and a word in the status bar. Sized against the band rather than by feel: at the
        /// post-#821 rate the Weary stretch is about 909 actions, so 1 in 500 is roughly
        /// <b>two slips across the whole of it</b>. Present, not punishing, and consistent with the
        /// ladder above.
        /// </remarks>
        public const int WearyOdds = 500;

        /// <summary>One action in this many slips, at Exhausted.</summary>
        public const int ExhaustedOdds = 200;

        /// <summary>One action in this many slips, at Collapsing.</summary>
        public const int CollapsingOdds = 80;

        /// <summary>
        /// The ability classes tiredness can take away.
        /// </summary>
        /// <remarks>
        /// <para>
        /// <b>This was <c>Class.Contains("Mental")</c>, and that reached one class out of six.</b>
        /// Vanilla's activated abilities carry <c>Mental Mutations</c> (40 of them),
        /// <c>Physical Mutations</c> (36), <c>Skills</c> (34), <c>Cybernetics</c>, <c>Items</c> and
        /// <c>Maneuvers</c>. So this only ever fired for a character with mental mutations — and a
        /// True Kin, a genotype this fork ships its own content for, has no mutations at all and got
        /// nothing from Exhausted but the world-map refusal (#822).
        /// </para>
        /// <para>
        /// <b>Including <c>Skills</c> is what reaches everybody</b>, because every character has
        /// some. Reaching for Charge and finding it gone is unreliability, which is §1's rule; a stat
        /// penalty would be the "merely punishing" thing that rule forbids.
        /// </para>
        /// <para>
        /// <b><c>Cybernetics</c>, <c>Items</c> and <c>Tonics</c> are left out deliberately.</b> A
        /// grenade does not care how tired I am, and an implant guttering because I am sleepy reads
        /// as a malfunction rather than as fatigue. The line is my own body and my own training.
        /// </para>
        /// </remarks>
        public static readonly string[] Classes =
        {
            "Mental Mutations",
            "Physical Mutations",
            "Skills",
            "Maneuvers",
        };

        /// <summary>
        /// Rolled once per action from <see cref="Vixy_Fatigue"/>, on the event fatigue already
        /// accrues on. Roughly two slips across the Weary stretch, three across Exhausted and three
        /// more across Collapsing — so the meter's last three bands each cost about the same number
        /// of failures, arriving faster as it fills.
        /// </summary>
        public static void Slip(GameObject Player)
        {
            if (Player == null || !Player.IsPlayer()) return;

            int fatigue = Vixy_Fatigue.Get(Player);
            if (fatigue < Vixy_Fatigue.Weary) return;

            int odds = OddsFor(fatigue);
            if (Stat.Random(1, odds) != 1) return;

            ActivatedAbilityEntry entry = PickReady(Player);
            if (entry == null) return;

            entry.Cooldown = Cost;
            MessageQueue.AddPlayerMessage(Slipped(entry));
        }

        /// <summary>
        /// A mental ability the player could have used this turn, chosen at random.
        /// </summary>
        /// <remarks>
        /// <c>IsUsable</c> already means enabled and off cooldown. Toggles that are currently *on*
        /// are skipped: writing a cooldown would not turn one off, so the message would name a
        /// capability the player can still see running.
        /// </remarks>
        /// <summary>How often a slip comes due at this much fatigue.</summary>
        private static int OddsFor(int Fatigue)
        {
            if (Fatigue >= Vixy_Fatigue.Collapsing) return CollapsingOdds;
            if (Fatigue >= Vixy_Fatigue.Exhausted) return ExhaustedOdds;
            return WearyOdds;
        }

        /// <summary>
        /// What losing this reads like.
        /// </summary>
        /// <remarks>
        /// <b>Concentration is the wrong word for a manoeuvre.</b> The original line was written when
        /// only mental mutations could gutter, and "your concentration slips" is exactly right for
        /// one of those. Applied to Charge it says the wrong thing about why the character failed —
        /// so the body gets its own phrasing, and the mind keeps the one it had.
        /// </remarks>
        private static string Slipped(ActivatedAbilityEntry Entry)
        {
            bool mental = Entry.Class != null && Entry.Class.Contains("Mental");

            return mental
                ? "{{r|Your concentration slips, and " + Entry.DisplayName + " gutters out.}}"
                : "{{r|Your body will not answer, and " + Entry.DisplayName + " comes to nothing.}}";
        }

        private static ActivatedAbilityEntry PickReady(GameObject Player)
        {
            ActivatedAbilities abilities = Player.GetPart<ActivatedAbilities>();
            if (abilities?.AbilityByGuid == null) return null;

            List<ActivatedAbilityEntry> ready = new List<ActivatedAbilityEntry>();
            foreach (ActivatedAbilityEntry entry in abilities.AbilityByGuid.Values)
            {
                if (entry == null || entry.Class == null) continue;
                if (Array.IndexOf(Classes, entry.Class) < 0) continue;
                if (!entry.IsUsable) continue;
                if (entry.ToggleState) continue;
                ready.Add(entry);
            }

            if (ready.Count == 0) return null;
            return ready[Stat.Random(0, ready.Count - 1)];
        }
    }
}
