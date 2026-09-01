using System;
using System.Collections.Generic;
using QudExpandedCE;
using XRL.Rules;

namespace XRL.World.Parts
{
    /// <summary>
    /// Counts who I have killed, by faction, and occasionally sends somebody about it — a champion
    /// with a grudge, or far more rarely somebody grateful that I thinned their enemy.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Item A3 of <c>docs/DESIGN_difficulty_systems.md</c></b>, split out as #190. That document's
    /// §0 governs it: it scales with <em>player power</em> rather than depth or elapsed time, it has
    /// to pass the two-question test — does the world explain it, does it create a decision — it
    /// ships behind an option defaulted off, and notoriety has to <em>sometimes</em> pay rather than
    /// only cost, which is the fourth constraint #644 added and the reason the second roll exists.
    /// </para>
    /// <para>
    /// <b>The threshold is five hundred, and that is not a large number by accident.</b> Fifty
    /// snapjaws in one cave expedition is ordinary play and a tenth of one threshold. The intent is a
    /// handful of these across a whole run — a hunter that arrives twice is a story, one that arrives
    /// twenty times is a tax.
    /// </para>
    /// <para>
    /// <b>Only broadly sentient factions send anybody, and the list is curated rather than derived.</b>
    /// Qud has no faction flag for sentience. The obvious proxy — factions <c>Naming.xml</c> scopes
    /// on — fails outright, because Qud authors names for bears, crabs, fish, worms and oozes; and
    /// <c>Culture</c> tags are the mechanism <c>docs/LESSONS.md</c> records as nearly dead. So this is
    /// a judgement written down where it can be argued with, which is better than a derivation that
    /// would be wrong. A baboon troop does not send an avenger because a baboon troop cannot hear
    /// about it.
    /// </para>
    /// <para>
    /// <b>Why a part and not an <c>IGameSystem</c>.</b> <c>ZoneActivatedEvent</c> dispatches to
    /// <c>The.Game</c> and to <c>Zone</c>, never to the player, which is why
    /// <c>XRL.PsychicHunterSystem</c> must be a system — it acts <em>before</em> the player is placed.
    /// A hunter needs the player placed first, so <c>EnteredCellEvent</c> on a part is both cheaper
    /// and more correct. Charter rule 5's ceiling does not move; <c>Vixy_TacticsWary</c> is this
    /// fork's precedent for the hook.
    /// </para>
    /// <para>
    /// <b>The tallies live in game state, not in this part.</b> A <c>Dictionary</c> field on a
    /// <c>[Serializable]</c> part puts its shape into every save, and charter rule 5 treats a shipped
    /// part's layout as frozen. Game state is keyed by string and costs nothing to extend, so a
    /// sixteenth faction later is not a save migration.
    /// </para>
    /// <para>
    /// Charter rule 5: no I/O, no network, no reflection, no Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Notoriety : IPart
    {
        /// <summary>Kills of one faction before its champion may come. See the remarks.</summary>
        public const int Threshold = 500;

        /// <summary>Chance in a hundred that an eligible grudge pays out on any one arrival.</summary>
        public const int HunterChance = 4;

        /// <summary>The same, for the grateful visit. Deliberately rarer than the hunter.</summary>
        public const int AllyChance = 1;

        /// <summary>How far off somebody arrives. See the remarks on <see cref="Send"/>.</summary>
        public const int ArrivalDistance = 8;

        /// <summary>
        /// Factions with enough of a social network to hear that I have been killing them.
        /// </summary>
        /// <remarks>
        /// Curated on purpose — see the remarks on the class. Every name here is checked against
        /// vanilla's <c>Factions.xml</c>; a typo would fail silently, the same way a scope naming a
        /// culture nothing carries never fires.
        /// </remarks>
        public static readonly string[] Sentient =
        {
            "Barathrumites", "Consortium", "Dromad", "Goatfolk", "Hindren",
            "Issachari", "Mechanimists", "Mopango", "Naphtaali", "Pariahs",
            "Seekers", "Snapjaws", "Templar", "Trolls", "Urchins",
        };

        /// <summary>The zone I was last seen in, so an arrival can be told from a step.</summary>
        [NonSerialized]
        private string LastZone;

        public override bool SameAs(IPart p) => true;

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == EnteredCellEvent.ID;
        }

        public override void Register(GameObject Object, IEventRegistrar Registrar)
        {
            // The legacy string event, not a MinEvent: KilledEvent.Send fires Event.New("Killed")
            // on the killer and gates it on HasRegisteredEvent, so registering is what makes the
            // count possible at all.
            Registrar.Register("Killed");
            base.Register(Object, Registrar);
        }

        public override bool FireEvent(Event E)
        {
            if (E.ID == "Killed" && Raven_Options.FactionChampions)
            {
                Count(E.GetGameObjectParameter("Object"));
            }
            return base.FireEvent(E);
        }

        private static string Key(string faction) => "Vixy_Kills_" + faction;

        /// <summary>Adds one to the tally for whoever the dead thing belonged to.</summary>
        private void Count(GameObject dead)
        {
            if (dead == null || dead == ParentObject) return;

            string faction = dead.GetPrimaryFaction();
            if (faction.IsNullOrEmpty() || Array.IndexOf(Sentient, faction) < 0) return;

            The.Game.SetIntGameState(Key(faction), The.Game.GetIntGameState(Key(faction)) + 1);
        }

        public override bool HandleEvent(EnteredCellEvent E)
        {
            if (!Raven_Options.FactionChampions || E.Object != ParentObject)
            {
                return base.HandleEvent(E);
            }

            string zone = ParentObject.CurrentZone?.ZoneID;
            if (zone.IsNullOrEmpty() || zone == LastZone)
            {
                return base.HandleEvent(E);
            }
            LastZone = zone;

            // Both rolls are made per arrival rather than per kill: a threshold crossed mid-fight
            // should not put somebody into that fight, and an arrival is the moment the world gets
            // to have already heard. The hunter is rolled first and returns if it fires, so the two
            // can never arrive together and the grateful visit stays the rarer of the two.
            List<string> owed = Owed();
            if (owed.Count == 0) return base.HandleEvent(E);

            string faction = owed.GetRandomElement();
            if (Stat.Random(1, 100) <= HunterChance)
            {
                Send(faction, faction, Hunter: true);
            }
            else if (Stat.Random(1, 100) <= AllyChance)
            {
                // The grateful visit comes from somebody who dislikes the faction I have been
                // thinning, not from that faction - snapjaws do not thank me for killing snapjaws.
                // Whoever hates them most is the one with a reason to be pleased.
                string glad = MostOpposedTo(faction);
                if (!glad.IsNullOrEmpty()) Send(glad, faction, Hunter: false);
            }
            return base.HandleEvent(E);
        }

        /// <summary>
        /// A sentient faction that dislikes <paramref name="enemy"/> most, or null if none does.
        /// </summary>
        /// <remarks>
        /// <para>
        /// Read from vanilla's own feelings rather than a table of my own, so who is pleased follows
        /// Qud's canon rather than my opinion. Restricted to <see cref="Sentient"/> for the same
        /// reason the grudge is: somebody has to be able to hear about it and act on it.
        /// </para>
        /// <para>
        /// <b>Through <c>GetFeelingTowardsFaction</c>, not <c>FactionFeeling</c> directly</b>, and
        /// the difference is most of the feature. Only three of the fifteen name a specific enemy
        /// among the other fourteen — Templar about Barathrumites at -100, and Barathrumites and
        /// Mechanimists about each other at -50. The remaining twelve say it through
        /// <c>&lt;feeling About="*"&gt;</c> instead, which nine of the fifteen carry. A raw
        /// dictionary lookup misses every one of those, so this would have fired for three factions
        /// out of fifteen and never for the snapjaws and goatfolk anybody actually kills five
        /// hundred of. The accessor resolves specific, then wildcard, then zero, so an authored
        /// rivalry still outranks a blanket one.
        /// </para>
        /// <para>
        /// <b>Candidates who would not talk to me are dropped before the comparison, not after.</b>
        /// Only three of the fifteen carry that -50 wildcard — Seekers, Snapjaws and Templar — and
        /// those are the three whose starting reputation with me is -500, -475 and -700. The
        /// blanket dislike that makes them the "gladdest" about everything is the same misanthropy
        /// that makes them hostile to me, so ranking first and filtering after would pick one of
        /// them almost every time and then throw the visit away. <c>PlayerReputation.GetFeeling</c>
        /// bands my standing at -100/-50/0/50/100 and is the whole test: a stranger just built has
        /// no personal opinion of me yet, so reputation is all <c>Brain.GetFeeling</c> would have
        /// summed anyway.
        /// </para>
        /// <para>
        /// <b>What survives is the schism, and I think that is the right answer rather than a thin
        /// one.</b> Every other faction's wildcard is zero or absent, so once the misanthropes are
        /// out the only remaining dislike among the fifteen is authored: Templar and Consortium
        /// about the Barathrumites, Barathrumites and Mechanimists about each other. So this pays
        /// out around Barathrum's quarrel with the Templar and the Mechanimists and almost nowhere
        /// else — which is Qud's central mid-game conflict, and legible on sight in a way a
        /// snapjaw thanking me for goatfolk never would have been.
        /// </para>
        /// <para>
        /// <b>Ties break randomly.</b> Where two do qualify jointly there is no reason to prefer
        /// whichever I happened to list first, and a fixed order would read as a rule.
        /// </para>
        /// </remarks>
        private static string MostOpposedTo(string enemy)
        {
            List<string> worst = new List<string>();
            int lowest = 0;
            foreach (string candidate in Sentient)
            {
                if (candidate == enemy) continue;
                Faction f = Factions.Get(candidate);
                if (f == null) continue;

                // Somebody arriving to thank me has to be willing to approach me at all.
                if (The.Game.PlayerReputation.GetFeeling(candidate) <= -10) continue;

                int feeling = f.GetFeelingTowardsFaction(enemy);
                if (feeling >= 0 || feeling > lowest) continue;
                if (feeling < lowest)
                {
                    lowest = feeling;
                    worst.Clear();
                }
                worst.Add(candidate);
            }
            return worst.Count == 0 ? null : worst.GetRandomElement();
        }

        /// <summary>
        /// Builds somebody from <paramref name="faction"/> and puts them in the zone.
        /// </summary>
        /// <remarks>
        /// <para>
        /// <b>The arrival message is how they explain themselves, and it has to be, because a
        /// hunter cannot talk.</b> <c>Brain.GetFeelingLevel</c> calls any feeling below -10
        /// hostile, and hostile creatures attack rather than converse — #632 established that the
        /// expensive way, so a <c>ConversationScript</c> on somebody sent to kill me is worth
        /// nothing. The line printed on arrival is the whole of the explanation, which is why it
        /// names the faction rather than being atmosphere.
        /// </para>
        /// <para>
        /// <b>I do not force the hunter hostile, because the arithmetic already does.</b>
        /// <c>Brain.GetFeeling</c> sums a personal opinion and <c>GetBaseFactionFeeling</c>, and
        /// the latter reads my reputation with them — five hundred of their dead is far past the
        /// -10 line on its own. Forcing it would mean <c>Allegiance.Hostile</c>, which is hostile
        /// to <em>everything</em> and would set the champion against his own kin.
        /// </para>
        /// <para>
        /// <b>That same arithmetic is why the envoy's faction is filtered before it is chosen.</b>
        /// Their feeling toward me is my reputation with <em>them</em>, which the grudge I am being
        /// thanked for says nothing about: an envoy from somebody I am already at war with would
        /// walk up and attack, which reads as a broken feature rather than a rare one.
        /// <see cref="MostOpposedTo"/> drops those candidates rather than this method discarding a
        /// built one, for the reason recorded there.
        /// </para>
        /// <para>
        /// <b><c>SpecialType</c> stays at its <c>"Hero"</c> default deliberately.</b> A custom
        /// value would need a <c>Special="Champion"</c> scope per faction — every scope in
        /// vanilla's <c>Naming.xml</c> is faction-bound — and until those exist the five
        /// <c>NameMaker</c> calls all carry <c>SpecialFaildown: true</c>, so an unknown value does
        /// not merely do nothing: it misses each faction's own hero namestyle
        /// (<c>Snapjaw Hero Title</c> and its kin) and falls down to generic naming. Passing
        /// nothing names them better than passing a word with no scope behind it.
        /// </para>
        /// <para>
        /// <b>They arrive across the room, not in my square.</b> The bare
        /// <c>getClosestPassableCell()</c> sorts every passable cell in the zone by distance from
        /// its own and returns the nearest, so called on my cell it returns my cell. The predicate
        /// overload keeps that nearest-first ordering, so a distance floor lands them at the edge
        /// of the room — seen, then met. Both overloads return <c>this</c> when nothing matches,
        /// which is the one case that has to be caught rather than placed.
        /// </para>
        /// <para>
        /// <b><c>TierOverride</c> is not a difficulty lever.</b> It reaches
        /// <c>MutateFromPopulationTable</c> and <c>inventoryTier</c> only, so it scales gear and
        /// mutations. Matching my level is a separate write to the creature's own <c>Level</c>, a
        /// little either side so it is neither a pushover nor a wall.
        /// </para>
        /// </remarks>
        private void Send(string faction, string about, bool Hunter)
        {
            Cell cell = ParentObject.CurrentCell;
            if (cell == null) return;

            // Nearest-first, so this is the closest cell that is still a walk away rather than the
            // far corner. The equality check is the no-match case: both overloads return the cell
            // they were called on, which is mine.
            Cell landing = cell.getClosestPassableCell(c => c.DistanceTo(cell) >= ArrivalDistance);
            if (landing == null || landing == cell) return;

            List<GameObjectBlueprint> members = Faction.GetMembers(faction, null, Dynamic: false);
            if (members.IsNullOrEmpty()) return;

            GameObject who = GameObject.Create(members.GetRandomElement().Name);
            if (who == null) return;

            int level = Math.Max(1, ParentObject.Stat("Level") + Stat.Random(-2, 2));
            who.GetStat("Level").BaseValue = level;
            HeroMaker.MakeHero(who, "BaseFactionHeroTemplate_" + faction, null,
                Math.Max(1, level / 5));

            landing.AddObject(who);

            // Spent, not cleared, and only once somebody is actually standing there: the count
            // keeps running, so a player who goes on killing them earns the next one rather than
            // starting from nothing.
            The.Game.SetIntGameState(Key(about),
                The.Game.GetIntGameState(Key(about)) - Threshold);

            if (Hunter)
            {
                who.SetIntProperty("Vixy_Champion", 1);
                IComponent<GameObject>.AddPlayerMessage(
                    "{{R|" + who.DisplayNameOnly + "}} has come for you on behalf of "
                    + Faction.GetFormattedName(faction) + ".");
            }
            else
            {
                who.SetIntProperty("Vixy_Envoy", 1);
                IComponent<GameObject>.AddPlayerMessage(
                    "{{G|" + who.DisplayNameOnly + "}} of " + Faction.GetFormattedName(faction)
                    + " has sought you out, on the strength of what you have done to "
                    + Faction.GetFormattedName(about) + ".");
            }
        }

        /// <summary>Every faction currently owed a reckoning, cheapest test first.</summary>
        public List<string> Owed()
        {
            List<string> owed = new List<string>();
            foreach (string faction in Sentient)
            {
                if (The.Game.GetIntGameState(Key(faction)) >= Threshold)
                {
                    owed.Add(faction);
                }
            }
            return owed;
        }
    }
}
