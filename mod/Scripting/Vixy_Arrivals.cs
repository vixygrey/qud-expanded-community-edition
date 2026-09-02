using System.Collections.Generic;
using XRL.World;

namespace QudExpandedCE
{
    /// <summary>
    /// Shared by the two features that send somebody to find me — <c>Vixy_Notoriety</c> for what I
    /// have killed and <c>Vixy_Hoard</c> for what I am carrying.
    /// </summary>
    /// <remarks>
    /// <para>
    /// The two are deliberately separate parts, so that one option's code path can be reasoned about
    /// without the other. This holds only what is genuinely identical between them and pure — one
    /// question with one right answer, which is what makes two copies of it a liability rather than
    /// a convenience. The per-zone flag and the resume guard stay in each part, because both carry
    /// instance state and a key of their own.
    /// </para>
    /// <para>
    /// Charter rule 5: no I/O, no network, no reflection, no Harmony.
    /// </para>
    /// </remarks>
    public static class Vixy_Arrivals
    {
        /// <summary>How far from my own level somebody sent to find me may be built.</summary>
        /// <remarks>
        /// Five either way. Qud's own levels are authored in wide steps — the Templar jump from a
        /// Squire at 9 to an Infiltrator at 13 to knights at 24 — so a narrow band would silence
        /// most factions most of the time, and a wide one would put a knight in front of a level-12
        /// character, which is the defect this exists to fix. #806.
        /// </remarks>
        public const int LevelBand = 5;

        /// <summary>Turns between being noticed and somebody hostile turning up.</summary>
        /// <remarks>
        /// <para>
        /// <b>Only hostile arrivals wait.</b> The delay exists to remove the ambush quality — being
        /// killed by something that materialised before I could act — and a trader or a grateful
        /// envoy is not an ambush, so those still arrive on the spot.
        /// </para>
        /// <para>
        /// Ten of my own actions, counted on <c>BeginTakeActionEvent</c>, which is the per-turn hook
        /// <c>Vixy_Fatigue</c> and <c>Vixy_Bearing</c> already use. Long enough to drink something,
        /// take a position, or start for the stairs if I am near them; not so long that crossing a
        /// zone makes me untouchable. Leaving the zone cancels it outright, which is deliberate: the
        /// feature is meant to pose a decision, and walking away is one of the answers.
        /// </para>
        /// </remarks>
        public const int ArrivalDelay = 10;

        /// <summary>
        /// A member of <paramref name="faction"/> whose own blueprint sits within
        /// <see cref="LevelBand"/> of <paramref name="level"/>, or null if none does.
        /// </summary>
        /// <remarks>
        /// <para>
        /// <b>Writing <c>Level</c> on a creature scales nothing, which is why this exists.</b> Both
        /// features used to pick any member and then set its <c>Level</c> stat to mine. That writes
        /// an integer. Hit points, armour, resistances and inventory are all declared on the
        /// blueprint and none of them move: an <c>Issachari Raider</c> has 16 hit points and a
        /// dagger, a <c>Gunner-Knight Templar</c> has 90, fullerite flake armour, a long sword, two
        /// grenades and a rifle, and setting the second one's level to twelve leaves every bit of
        /// that in place. The Templar pool runs from 9 to 39 and is mostly level-24 knights.
        /// </para>
        /// <para>
        /// <b>So the level has to be chosen rather than assigned.</b>
        /// <c>GameObjectBlueprint.Stat</c> reads it without instantiating anything, and the factory
        /// resolves inheritance when it loads the blueprints — which is how <c>Faction.IsMember</c>
        /// already reads <c>Brain</c>/<c>Factions</c> off a <c>Knight Templar</c> that never
        /// declares one.
        /// </para>
        /// <para>
        /// <b><c>Dynamic: true</c> is load-bearing and is not a default</b>, which #802 is the
        /// lesson for: it applies <c>IsExcludedFromDynamicEncounters</c>, the flag Qud marks its
        /// unique named characters with, and without it a Barathrumite could be Argyve.
        /// <c>IsBaseBlueprint</c> is filtered either way.
        /// </para>
        /// <para>
        /// Returning null rather than falling back to any member at all is the point. A faction with
        /// nobody near my level should stay silent — the Issachari have only level-8 blueprints, so
        /// they have nothing to send a late character, and that is a better answer than sending
        /// somebody who cannot fight or somebody who cannot be fought.
        /// </para>
        /// </remarks>
        public static GameObjectBlueprint NearLevel(string faction, int level)
        {
            List<GameObjectBlueprint> members = Faction.GetMembers(
                faction,
                b =>
                {
                    int own = LevelOf(b);
                    return own > 0 && own >= level - LevelBand && own <= level + LevelBand;
                },
                Dynamic: true,
                ReadOnly: false);

            return members.IsNullOrEmpty() ? null : members.GetRandomElement();
        }

        /// <summary>Any member of <paramref name="faction"/>, without regard to level.</summary>
        /// <remarks>
        /// For somebody who has not come to fight. Level matching exists so that a fight is fair,
        /// and applying it to a visitor does real harm rather than none: the Barathrumites have
        /// nobody within five levels of a character past about eighteen, so filtering the grateful
        /// envoy in <c>Vixy_Notoriety</c> would have silenced that feature's only reward path for
        /// exactly the characters most likely to have earned it.
        /// </remarks>
        public static GameObjectBlueprint AnyMember(string faction)
        {
            List<GameObjectBlueprint> members =
                Faction.GetMembers(faction, null, Dynamic: true, ReadOnly: false);
            return members.IsNullOrEmpty() ? null : members.GetRandomElement();
        }

        /// <summary>A blueprint's own level, reading a range as its lower bound.</summary>
        /// <remarks>
        /// <c>Statistic.sValue</c> is a separate string field from <c>BaseValue</c>, so a blueprint
        /// declaring <c>sValue="18-29"</c> reports a level of <b>zero</b> through
        /// <c>GameObjectBlueprint.Stat</c>. Two of the fifteen factions' members are written that
        /// way — <c>Barathrumite Tinker</c> and <c>Barathrumite Arconaut</c> — and a bare
        /// <c>Stat("Level")</c> would drop both without saying so, leaving the Barathrumites able to
        /// send nothing but chromelings. Taking the lower bound is the conservative reading: it
        /// makes them eligible slightly early rather than never.
        /// </remarks>
        private static int LevelOf(GameObjectBlueprint b)
        {
            Statistic stat = b.GetStat("Level");
            if (stat == null) return 0;
            if (stat.BaseValue > 0) return stat.BaseValue;

            string s = stat.sValue;
            if (s.IsNullOrEmpty()) return 0;

            int end = 0;
            while (end < s.Length && char.IsDigit(s[end])) end++;
            return end == 0 ? 0 : int.Parse(s.Substring(0, end));
        }
    }
}
