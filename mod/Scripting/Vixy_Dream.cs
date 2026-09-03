using System;
using System.Collections.Generic;
using System.Linq;
using Qud.API;
using XRL;
using XRL.Rules;
using XRL.UI;

namespace XRL.World.Parts
{
    /// <summary>
    /// What a full night's sleep gives back.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The reward is designed before the punishment</b>, which is the design doc's own
    /// instruction. Fatigue on its own is a tax; a dream is the reason to sleep properly, in a safe
    /// place, without being woken — and it is the only thing in this feature that rewards doing so.
    /// </para>
    /// <para>
    /// <b>Dreams quote rather than generate.</b> §4 originally asked for text "Markov-generated from
    /// the player's recent history — creatures killed, zones visited, items carried". Both of Qud's
    /// generators load <c>LibraryCorpus.json</c>, a fixed offline corpus of books and conversations
    /// with nothing about the player in it, so that was never possible. The store it wanted already
    /// ships: <c>JournalAPI.Accomplishments</c> is a serialised list of timestamped deeds, each
    /// carrying pre-authored prose in three registers.
    /// </para>
    /// <para>
    /// <b><c>GospelText</c> is the register a dream wants</b>, and picking it rather than
    /// <c>MuralText</c> is the whole idea. The mural voice reports what happened; the gospel voice
    /// mythologises it, and is frequently <em>counterfactual</em> — vanilla's own Omonporch entry has
    /// "=name= appointed the corrupt administrator Asphodel as earl", which the player did not do.
    /// Deeds returning grander and slightly wrong is what a dream is. `MuralText` and then `Text` are
    /// the fallbacks, because not every accomplishment carries all three.
    /// </para>
    /// <para>
    /// <b>No state.</b> Everything is read at the moment the dream fires.
    /// </para>
    /// </remarks>
    public static class Vixy_Dream
    {
        /// <summary>Where the fatigue a sleep began at is kept, so this can read it on waking.</summary>
        /// <remarks>
        /// An int property on the player rather than a field on <see cref="Vixy_Fatigue"/>: that part
        /// is <c>[Serializable]</c> and shipped, so its layout is frozen and <c>serializable-shape</c>
        /// refuses new instance state. Written on the first turn of a voluntary sleep and cleared on
        /// the first turn awake, so an interrupted sleep leaves nothing behind for the next one.
        /// </remarks>
        public const string SleptFromProperty = "Vixy_DreamSleptFrom";

        /// <summary>How tired I must have been for the night to be worth dreaming about.</summary>
        /// <remarks>
        /// <b>This is the whole of the anti-farm, and a rarer roll could not have done it.</b>
        /// Sleeping is refused only at fatigue zero, so before #818 you could lie down at 1, wake at
        /// 0 and collect a dream: about four turns to accrue the point and twenty to sleep it off.
        /// That is <b>a dream every 24 turns</b> against one per 1,500 in ordinary play — and in a
        /// settlement <c>AmbushChance</c> is 0, so it cost nothing but keystrokes. A chance gate only
        /// makes the loop longer; at one in three it is 72 turns, still twenty times the intended
        /// rate. What closes it is charging real fatigue for the roll.
        /// </remarks>
        public static readonly int Earned = Vixy_Fatigue.Tired;

        /// <summary>Chance in a hundred that a qualifying sleep dreams at all.</summary>
        /// <remarks>
        /// The gate answers the farm; this answers the other half of #818, that something arriving
        /// every single night stops being an event. Roughly one dream per 3,000 turns of unhurried
        /// play.
        /// </remarks>
        public const int DreamChance = 50;

        /// <summary>Chance in a hundred that a dream is a portent rather than a recollection.</summary>
        /// <remarks>
        /// Down from 30. This is the half that hands over something mechanical, and it already
        /// self-limits: every portent spends a location, and there are only so many.
        /// </remarks>
        public const int PortentChance = 25;

        /// <summary>
        /// Roll a dream. Called only on a full, uninterrupted sleep.
        /// </summary>
        /// <remarks>
        /// <para>
        /// Uninterrupted is the whole condition: an ambush ends the sleep before fatigue reaches
        /// zero, so being found costs the dream as well as the rest. That is what makes where you lie
        /// down matter for something other than safety.
        /// </para>
        /// <para>
        /// <b>And a nap is not a night.</b> <paramref name="SleptFrom"/> is the fatigue the sleep
        /// began at, and it must reach <see cref="Earned"/> — the Tired band — before anything is
        /// rolled. See that field for why the gate is fatigue rather than odds.
        /// </para>
        /// <para>
        /// <b>The portent still falls back to a recollection, deliberately.</b> I had meant to drop
        /// that once there was a gate in front, so the two tiers would have independent rates. But
        /// <see cref="Portent"/> fails when every location is already known, and by late game that is
        /// the normal case — so dropping it would turn a quarter of hard-won dreams into silence, to
        /// buy a tidiness nobody can observe.
        /// </para>
        /// </remarks>
        public static void OnFullSleep(GameObject Player, int SleptFrom)
        {
            if (Player == null || !Player.IsPlayer()) return;
            if (SleptFrom < Earned) return;
            if (!DreamChance.in100()) return;

            if (PortentChance.in100() && Portent(Player)) return;
            Recollection(Player);
        }

        /// <summary>
        /// The common tier: the character dreams of something they did, in the gospel voice.
        /// </summary>
        private static void Recollection(GameObject Player)
        {
            string text = PickGospel(Player);
            if (text == null) return;

            BookUI.ShowBook(
                "{{c|You dream.}}\n\n" + text + "\n\n{{K|…and wake with it already going.}}",
                "A Dream");
        }

        /// <summary>
        /// Pick a deed and return its most mythologised surviving register.
        /// </summary>
        /// <remarks>
        /// Revealed entries only — an accomplishment the player has not been shown yet is not
        /// something their character could be dreaming about.
        /// </remarks>
        private static string PickGospel(GameObject Player)
        {
            List<JournalAccomplishment> pool = JournalAPI.Accomplishments?
                .Where(a => a != null && a.Revealed)
                .ToList();
            if (pool == null || pool.Count == 0) return null;

            JournalAccomplishment pick = pool[Stat.Random(0, pool.Count - 1)];
            string text = pick.GospelText;
            if (text.IsNullOrEmpty()) text = pick.MuralText;
            if (text.IsNullOrEmpty()) text = pick.Text;
            if (text.IsNullOrEmpty()) return null;

            // The stored prose carries =name=, pronoun tokens and <spice.…> lookups, so it has to go
            // through the replacer the journal itself uses before anyone reads it.
            return GameText.VariableReplace(text, Player);
        }

        /// <summary>
        /// The uncommon tier: the character wakes knowing where something is.
        /// </summary>
        /// <remarks>
        /// `RevealMapNote` takes a `LearnedFrom` string, so a dream can be recorded as the source the
        /// location was learned from — which is a nicer outcome than a bare reveal, and needs no new
        /// bookkeeping.
        ///
        /// Returns false when there is nothing left unrevealed, so the caller can fall back rather
        /// than spending the roll on nothing.
        /// </remarks>
        private static bool Portent(GameObject Player)
        {
            List<JournalMapNote> hidden = JournalAPI.MapNotes?
                .Where(n => n != null && !n.Revealed)
                .ToList();
            if (hidden == null || hidden.Count == 0) return false;

            JournalMapNote note = hidden[Stat.Random(0, hidden.Count - 1)];
            JournalAPI.RevealMapNote(note, silent: true, LearnedFrom: "a dream");

            BookUI.ShowBook(
                "{{c|You dream of a place you have never been.}}\n\n"
                + GameText.VariableReplace(note.Text ?? "Somewhere out in the salt.", Player)
                + "\n\n{{K|You wake knowing where it is.}}",
                "A Dream");
            return true;
        }
    }
}
