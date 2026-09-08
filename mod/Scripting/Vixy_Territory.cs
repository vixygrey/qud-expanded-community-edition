using System.Collections.Generic;
using XRL.World;
using XRL.World.Parts;

namespace XRL
{
    /// <summary>
    /// Records which people hold a place, and notices when they stop. #923.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Nothing in Caves of Qud knows who lives anywhere.</b> Across all 284 zone declarations in
    /// <c>Worlds.xml</c> the complete attribute set is <c>Level</c>, <c>x</c>, <c>y</c>,
    /// <c>Name</c>, <c>NameContext</c>, <c>Tier</c>, weather and audio — no owner, no site type. And
    /// the one builder that would know says nothing:
    /// <c>FactionEncounters.BuildFactionEncounter</c> takes a faction, draws its leader from
    /// <c>BaseFactionHeroTemplate_&lt;Faction&gt;</c> and its members from
    /// <c>GetFactionMembers(Faction)</c>, places the lot, and sets no zone property at all. The
    /// faction that populated a zone is known for the length of one method call.
    /// </para>
    /// <para>
    /// <b>An <c>IGameSystem</c>, and this fork's first.</b> <c>AfterZoneBuiltEvent</c> and
    /// <c>ZoneDeactivatedEvent</c> both do <c>The.Game.HandleEvent(E)</c> <em>before</em>
    /// <c>Zone.HandleEvent(E)</c>, so one registered listener hears every zone in the game. That is
    /// the cheap tier of <c>docs/LESSONS.md</c>'s <i>ask what dispatches per-object and what
    /// dispatches centrally</i>; the alternative was a part on every zone.
    /// <c>XRL.PsychicHunterSystem</c> is vanilla's precedent and registers the same way.
    /// <c>Vixy_Notoriety</c> considered a system and chose a part, for reasons that do not apply
    /// here — it needed the player placed first, and this does not care where the player is.
    /// </para>
    /// <para>
    /// <b>Occupancy is computed from the creatures present, not from the builder.</b> That is
    /// deliberately broader: a creature carries <c>Brain.GetPrimaryFaction()</c> however it arrived,
    /// so an ordinary population-table lair is covered exactly as well as a faction encounter, and
    /// no vanilla builder has to be touched.
    /// </para>
    /// <para>
    /// <b>Only people hold ground.</b> <c>Vixy_Regard.CanHold</c> decides, and it is the same test
    /// #921 uses to decide who can think better of you — because both questions are *is this a
    /// person*. Measured over the game: <b>445 of 957</b> creature blueprints pass. Snapjaws 36/36,
    /// Merchants 50/50, Mopango 18/18, Templar 14/15. Excluded entirely: Robots 0/53, Unshelled
    /// Reptiles 0/32, Arachnids 0/22, Insects 0/21, Fish 0/16, Winged Mammals 0/15. A bat does not
    /// hold a cave.
    /// </para>
    /// <para>
    /// <b>Awakened machines hold; ordinary ones do not, and that falls out for free.</b> The Slynth,
    /// Thah and the newly sentient pass on their own conversations — <c>Slynth</c>,
    /// <c>SlynthWanderer</c>, <c>Thah</c>, <c>NewlySentientBeings</c> — while base <c>Robots</c>
    /// fails the emote-only test. The distinction the game already draws between a machine and an
    /// awakened one is the distinction this makes, with no special case to drift.
    /// </para>
    /// <para>
    /// <b>Held and vacated are deliberately asymmetric.</b> Holding wants a real presence —
    /// <see cref="Threshold"/> living members and the plurality — while vacancy wants none at all.
    /// That sidesteps having to pick a middle number for the one wounded snapjaw left in a lair: it
    /// is not a holding, and it is not yet a vacancy either.
    /// </para>
    /// <para>
    /// <b>Zone properties, because they are keyed by <c>ZoneID</c> rather than held on the zone.</b>
    /// <c>ZoneManager.ZoneProperties</c> is a <c>Dictionary&lt;string, Dictionary&lt;string,
    /// object&gt;&gt;</c> serialised with the main save, so a record survives its zone being frozen
    /// to disk and — the point of the whole exercise — can be read for a zone that is not loaded.
    /// #832's bands need to find a vacancy without thawing half the map.
    /// </para>
    /// <para>
    /// <b>The cost was measured rather than guessed.</b> A real save at turn 3,285 holds 18 frozen
    /// zones and 486,586 bytes of zone data — about <b>27 KB per zone</b>, one zone per ~180 turns.
    /// A record is a tokenised property name and faction against a <c>ZoneID</c>: at worst ~41
    /// bytes, realistically under 10, since <c>WriteOptimized</c> puts repeated strings in the token
    /// table once. **Roughly 0.1% of what the zone it describes already costs.** A 250,000-turn run
    /// would carry ~1,400 records for ~57 KB uncompressed, against ~38 MB of zone data.
    /// </para>
    /// <para>
    /// <b>Known limit: a zone that has never been built has no record.</b> Occupancy cannot be known
    /// before a zone exists, so anything reading this can only ever see places the player has
    /// visited — whether or not they emptied them. #832 inherits that and it cannot be fixed here.
    /// </para>
    /// <para>
    /// No option. This records a fact and changes no behaviour; whatever acts on it carries the
    /// switch. Charter rule 5: two event handlers and a dictionary. No I/O, no reflection, no
    /// Harmony.
    /// </para>
    /// </remarks>
    public class Vixy_Territory : IGameSystem
    {
        /// <summary>The faction holding a zone, if any.</summary>
        public const string HeldBy = "Vixy_HeldBy";

        /// <summary>Set once a zone that was held has been emptied of its holders.</summary>
        public const string Vacated = "Vixy_Vacated";

        /// <summary>
        /// Living members a faction needs present before it counts as holding the place.
        /// </summary>
        /// <remarks>
        /// Three is a party rather than a stray. Vacancy is not the mirror of this — see the
        /// asymmetry note on the class — so this number only ever decides whether a *new* holding is
        /// recorded, never whether an existing one has ended.
        /// </remarks>
        public const int Threshold = 3;

        public override void Register(XRLGame Game, IEventRegistrar Registrar)
        {
            Registrar.Register(AfterZoneBuiltEvent.ID);
            Registrar.Register(ZoneDeactivatedEvent.ID);
            base.Register(Game, Registrar);
        }

        /// <summary>A zone has just been populated. Write down whose it is.</summary>
        public override bool HandleEvent(AfterZoneBuiltEvent E)
        {
            Record(E.Zone);
            return base.HandleEvent(E);
        }

        /// <summary>
        /// I am leaving. Whatever is true now is what gets remembered.
        /// </summary>
        /// <remarks>
        /// On leaving rather than on entering, because leaving is when the answer has changed. Qud
        /// has no <i>cleared</i> signal at all — #830 traced that a built zone keeps exactly what it
        /// was left with, corpses included — so emptiness has to be computed, and the moment after I
        /// have finished with a place is the cheapest moment that is not a visit late.
        /// <c>Zone.Deactivated</c> only sends the event, so the cells and their occupants are still
        /// walkable here.
        /// </remarks>
        public override bool HandleEvent(ZoneDeactivatedEvent E)
        {
            Record(E.Zone);
            return base.HandleEvent(E);
        }

        private static void Record(Zone Zone)
        {
            if (Zone == null || Zone.IsWorldMap()) return;

            string id = Zone.ZoneID;
            if (id.IsNullOrEmpty()) return;

            string holder = Dominant(Zone, out int living);
            string was = The.ZoneManager.TryGetZoneProperty(id, HeldBy, out string Value) ? Value : null;

            if (holder != null)
            {
                The.ZoneManager.SetZoneProperty(id, HeldBy, holder);
                The.ZoneManager.RemoveZoneProperty(id, Vacated);
                return;
            }

            // Nobody holds it now. That is only news if somebody did, and only a vacancy if none of
            // them are left - one survivor is neither a holding nor an opening.
            if (!was.IsNullOrEmpty() && living <= 0)
            {
                The.ZoneManager.SetZoneProperty(id, Vacated, was);
                The.ZoneManager.RemoveZoneProperty(id, HeldBy);
            }
        }

        /// <summary>
        /// The faction with the most living people here, if it clears <see cref="Threshold"/>.
        /// </summary>
        /// <param name="Living">
        /// How many members of the previously recorded holder are still alive, which is what decides
        /// a vacancy rather than a holding.
        /// </param>
        private static string Dominant(Zone Zone, out int Living)
        {
            Living = 0;
            string id = Zone.ZoneID;
            string was = The.ZoneManager.TryGetZoneProperty(id, HeldBy, out string Value) ? Value : null;

            Dictionary<string, int> census = new Dictionary<string, int>();
            List<GameObject> objects = Zone.GetObjects();
            for (int i = 0; i < objects.Count; i++)
            {
                GameObject o = objects[i];
                if (o == null || o.IsPlayer() || !o.IsCreature) continue;

                // A corpse is not a garrison. Zones keep their dead, so this has to be asked.
                if (!o.IsAlive) continue;

                // Somebody I am leading is not the local population.
                if (o.Brain != null && o.Brain.IsPlayerLed()) continue;

                if (!Vixy_Regard.CanHold(o)) continue;

                string faction = o.Brain?.GetPrimaryFaction();
                if (faction.IsNullOrEmpty()) continue;

                census.TryGetValue(faction, out int n);
                census[faction] = n + 1;
                if (faction == was) Living++;
            }

            string best = null;
            int most = 0;
            foreach (KeyValuePair<string, int> entry in census)
            {
                if (entry.Value > most)
                {
                    most = entry.Value;
                    best = entry.Key;
                }
            }

            return most >= Threshold ? best : null;
        }
    }
}
