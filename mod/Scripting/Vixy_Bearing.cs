using System;
using XRL.World.Effects;
using QudExpandedCE;

namespace XRL.World.Parts
{
    /// <summary>
    /// Tells a wayfarer which of a parasang's nine zones they have just walked into.
    /// </summary>
    /// <remarks>
    /// <para>
    /// A parasang is a 3×3 block of zones and the game never says which one you are standing in.
    /// The numbers were always there — <c>Zone.X</c> and <c>Zone.Y</c> each run 0–2 within the
    /// parasang, parsed out of the zone ID the moment the zone is built — and nothing surfaced
    /// them. Vanilla itself does the same lookup in <c>GameObject.GetDirectionFromCellXY</c>, to
    /// label the destinations in the descend-from-the-world-map menu, but that method is private
    /// and the menu only appears when there is more than one place to land.
    /// </para>
    /// <para>
    /// <b>Gated on Mind's Compass, not on Wayfaring.</b> The power costs 0, so it arrives with the
    /// skill; <c>Survival_Trailblazer</c> is its class and the thing to test for. Knowing where you
    /// are inside the block you are standing in is the same idea as regaining your bearings when
    /// lost, one scale down.
    /// </para>
    /// <para>
    /// <b>Silent while lost.</b> Being lost is exactly the state in which you should not know where
    /// you are, and vanilla drops you at a uniformly random one of the nine when it happens
    /// (<c>TerrainTravel</c> rolls <c>Stat.Random(0, 2)</c> for both axes). Taken from modo_lv's
    /// ParasangRegion, which had the idea first.
    /// </para>
    /// <para>
    /// <b>Carries no instance state, so nothing is added to the save.</b> "Only when it changes"
    /// is answered from the event rather than from a remembered field: <c>EnteringZoneEvent</c>
    /// carries <c>Origin</c>, the cell being left, so both bearings are in hand at once. Stairs
    /// therefore stay silent — descending keeps X and Y and changes only Z.
    /// </para>
    /// <para>
    /// Charter rule 5: two public ints off a zone the game has already built, one string, one
    /// message. No I/O, no reflection, no Harmony, no state.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Bearing : IScribedPart
    {
        /// <summary>The nine, indexed [Y][X], each 0-2. Matches vanilla's own private table.</summary>
        private static readonly string[][] Bearings =
        {
            new[] { "northwest", "north", "northeast" },
            new[] { "west", "centre", "east" },
            new[] { "southwest", "south", "southeast" },
        };

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == EnteringZoneEvent.ID;
        }

        public override bool HandleEvent(EnteringZoneEvent E)
        {
            Announce(E.Origin?.ParentZone, E.Cell?.ParentZone);
            return base.HandleEvent(E);
        }

        /// <summary>
        /// Reports the arrival zone's bearing, unless the departure zone had the same one.
        /// </summary>
        private void Announce(Zone from, Zone to)
        {
            GameObject who = ParentObject;
            if (who == null || !who.IsPlayerControlled())
            {
                return;
            }

            if (!Raven_Options.Bearings
                || !who.HasSkill("Survival_Trailblazer")
                || who.HasEffect<Lost>())
            {
                return;
            }

            string arriving = BearingFor(to);
            if (arriving == null || arriving == BearingFor(from))
            {
                return;
            }

            AddPlayerMessage("You get your bearings: the " + arriving + " of this parasang.");
        }

        /// <summary>
        /// The zone's position within its parasang, or null where the idea does not apply.
        /// </summary>
        /// <remarks>
        /// Three ways it does not apply, and each has to be excluded separately.
        ///
        /// <list type="bullet">
        /// <item>The world map, where a zone ID carries no coordinates at all and
        /// <c>ZoneID.Parse</c> leaves every one of them at -1.</item>
        /// <item>A world with no world map. <c>Worlds.xml</c> ships five and only two declare a
        /// <c>Map</c>; the other three are Tzimtzlum, the Thin World and <c>Interior</c>, where
        /// there is no overland grid for a bearing to be a bearing on. Read off the blueprint
        /// rather than matched against a list of world names, so a world a later patch adds is
        /// covered without this needing to be edited.</item>
        /// <item>An interior zone specifically, which is the reason the check above cannot be
        /// skipped: an interior inherits its parent object's parasang coordinates, so a vehicle
        /// cabin would otherwise report where the vehicle happens to be parked.</item>
        /// </list>
        /// </remarks>
        private static string BearingFor(Zone zone)
        {
            if (zone == null || zone.IsWorldMap())
            {
                return null;
            }

            if (zone.Y < 0 || zone.Y >= Bearings.Length
                || zone.X < 0 || zone.X >= Bearings[zone.Y].Length)
            {
                return null;
            }

            // ZoneWorld, deliberately, and not ResolveZoneWorld(): InteriorZone overrides the
            // resolver to return the world its parent object is standing in, which would let every
            // interior through the check this line exists to make. The field stays "Interior".
            string map = WorldFactory.Factory?.getWorld(zone.ZoneWorld)?.Map;
            if (map.IsNullOrEmpty())
            {
                return null;
            }

            return Bearings[zone.Y][zone.X];
        }
    }
}
