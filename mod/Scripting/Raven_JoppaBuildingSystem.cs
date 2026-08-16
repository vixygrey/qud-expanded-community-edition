using System;
using System.Collections.Generic;
using XRL;
using XRL.UI;
using XRL.World;

namespace QudExpandedCE
{
    /// <summary>
    /// Removes this mod's Joppa building when the player has turned it off.
    ///
    /// The building is a Load="Merge" map patch applied when the Joppa zone is generated. A map
    /// merge cannot be gated on an option - it happens as data loads, long before any option is
    /// read - so the building is removed after the fact instead.
    ///
    /// Removal matches blueprint AND cell against the patch's own contents, because the patch
    /// places ordinary vanilla objects (DirtPath, RustedMetalWall) that exist elsewhere in Joppa.
    /// The ten cells where the patch covered a vanilla DirtPath have it put back.
    ///
    /// 89 objects across 76 cells, generated from mod/Joppa.rpm and kept in step
    /// with it by tools/validate_mod.py.
    ///
    /// Charter rule 5: no file I/O, no network, no reflection, no Harmony.
    /// </summary>
    [Serializable]
    public class Raven_JoppaBuildingSystem : IGameSystem
    {
        /// <summary>One object at one cell. Nested to avoid colliding with XRL.World.Point.</summary>
        private readonly struct Cel
        {
            public readonly int X;
            public readonly int Y;
            public readonly string Blueprint;

            public Cel(int x, int y, string blueprint)
            {
                X = x;
                Y = y;
                Blueprint = blueprint;
            }
        }

        private static readonly Cel[] PlacedObjects =
        {
            new Cel(16, 17, "DirtPath"),
            new Cel(17, 18, "DirtPath"),
            new Cel(17, 19, "DirtPath"),
            new Cel(18, 18, "DirtPath"),
            new Cel(18, 19, "DirtPath"),
            new Cel(19, 14, "RustedMetalWall"),
            new Cel(19, 15, "RustedMetalWall"),
            new Cel(19, 16, "RustedMetalWall"),
            new Cel(19, 17, "RustedMetalWall"),
            new Cel(19, 18, "RustedMetalWall"),
            new Cel(19, 19, "DirtPath"),
            new Cel(19, 20, "DirtPath"),
            new Cel(20, 14, "RustedMetalWall"),
            new Cel(20, 15, "Bookshelf"),
            new Cel(20, 15, "DirtPath"),
            new Cel(20, 16, "DirtPath"),
            new Cel(20, 17, "Low Table"),
            new Cel(20, 18, "RustedMetalWall"),
            new Cel(20, 19, "DirtPath"),
            new Cel(20, 20, "DirtPath"),
            new Cel(21, 14, "RustedMetalWall"),
            new Cel(21, 15, "Bed"),
            new Cel(21, 15, "DirtPath"),
            new Cel(21, 16, "DirtPath"),
            new Cel(21, 17, "Floor Cushion"),
            new Cel(21, 18, "RustedMetalWall"),
            new Cel(21, 19, "RustedMetalWall"),
            new Cel(21, 20, "DirtPath"),
            new Cel(21, 21, "DirtPath"),
            new Cel(22, 14, "RustedMetalWall"),
            new Cel(22, 15, "DirtPath"),
            new Cel(22, 15, "Dresser"),
            new Cel(22, 16, "DirtPath"),
            new Cel(22, 17, "DirtPath"),
            new Cel(22, 18, "DirtPath"),
            new Cel(22, 18, "Oven"),
            new Cel(22, 19, "RustedMetalWall"),
            new Cel(22, 20, "DirtPath"),
            new Cel(22, 21, "DirtPath"),
            new Cel(23, 13, "RustedMetalWall"),
            new Cel(23, 14, "RustedMetalWall"),
            new Cel(23, 15, "DirtPath"),
            new Cel(23, 15, "Torchpost"),
            new Cel(23, 16, "DirtPath"),
            new Cel(23, 17, "DirtPath"),
            new Cel(23, 18, "DirtPath"),
            new Cel(23, 18, "Woven Basket"),
            new Cel(23, 19, "RustedMetalWall"),
            new Cel(23, 20, "DirtPath"),
            new Cel(23, 21, "DirtPath"),
            new Cel(24, 13, "RustedMetalWall"),
            new Cel(24, 14, "CyberneticsStationRack"),
            new Cel(24, 14, "DirtPath"),
            new Cel(24, 15, "DirtPath"),
            new Cel(24, 16, "DirtPath"),
            new Cel(24, 17, "DirtPath"),
            new Cel(24, 18, "DirtPath"),
            new Cel(24, 19, "RustedMetalWall"),
            new Cel(24, 20, "DirtPath"),
            new Cel(24, 21, "DirtPath"),
            new Cel(25, 13, "RustedMetalWall"),
            new Cel(25, 14, "CyberneticsTerminal2"),
            new Cel(25, 14, "DirtPath"),
            new Cel(25, 15, "DirtPath"),
            new Cel(25, 16, "DirtPath"),
            new Cel(25, 17, "DirtPath"),
            new Cel(25, 18, "DirtPath"),
            new Cel(25, 19, "Raven_Rusted Door"),
            new Cel(25, 21, "DirtPath"),
            new Cel(26, 13, "RustedMetalWall"),
            new Cel(26, 14, "DirtPath"),
            new Cel(26, 14, "Raven_Empty Gun Rack"),
            new Cel(26, 15, "DirtPath"),
            new Cel(26, 15, "Raven_Empty Weapon Rack"),
            new Cel(26, 16, "DirtPath"),
            new Cel(26, 16, "Raven_Empty Armor Rack"),
            new Cel(26, 17, "DirtPath"),
            new Cel(26, 17, "Vase"),
            new Cel(26, 18, "Chest"),
            new Cel(26, 18, "DirtPath"),
            new Cel(26, 19, "RustedMetalWall"),
            new Cel(26, 20, "Torchpost"),
            new Cel(27, 13, "RustedMetalWall"),
            new Cel(27, 14, "RustedMetalWall"),
            new Cel(27, 15, "RustedMetalWall"),
            new Cel(27, 16, "RustedMetalWall"),
            new Cel(27, 17, "RustedMetalWall"),
            new Cel(27, 18, "RustedMetalWall"),
            new Cel(27, 19, "RustedMetalWall"),
        };

        /// <summary>Cells where the patch covered a vanilla DirtPath, restored on removal.</summary>
        private static readonly Cel[] RestoreDirtPath =
        {
            new Cel(19, 17, "DirtPath"),
            new Cel(20, 17, "DirtPath"),
            new Cel(20, 18, "DirtPath"),
            new Cel(21, 18, "DirtPath"),
            new Cel(21, 19, "DirtPath"),
            new Cel(22, 19, "DirtPath"),
            new Cel(23, 19, "DirtPath"),
            new Cel(24, 19, "DirtPath"),
            new Cel(25, 19, "DirtPath"),
            new Cel(26, 20, "DirtPath"),
        };

        /// <summary>
        /// Objects only this mod defines. Their presence identifies the modded Joppa without
        /// hardcoding a zone ID, which would break if Qud ever renumbered its world.
        /// </summary>
        private static readonly string[] Signature =
        {
            "Raven_Empty Gun Rack",
            "Raven_Empty Weapon Rack",
            "Raven_Empty Armor Rack",
            "Raven_Rusted Door",
        };

        public override void Register(XRLGame game, IEventRegistrar registrar)
        {
            registrar.Register(ZoneActivatedEvent.ID);
        }

        public override bool HandleEvent(ZoneActivatedEvent E)
        {
            // Default "Yes": the building is part of what this mod has always been (charter
            // rule 6), so it stays unless the player asks for it to go.
            if (Options.GetOption(Raven_Options.JoppaBuildingID, "Yes") == "Yes")
            {
                return true;
            }

            Zone zone = E.Zone;
            if (zone != null && LooksLikeOurJoppa(zone))
            {
                RemoveBuilding(zone);
            }

            return true;
        }

        private static bool LooksLikeOurJoppa(Zone zone)
        {
            foreach (Cel p in PlacedObjects)
            {
                if (Array.IndexOf(Signature, p.Blueprint) < 0)
                {
                    continue;
                }

                Cell cell = zone.GetCell(p.X, p.Y);
                if (cell != null && FindIn(cell, p.Blueprint) != null)
                {
                    return true;
                }
            }

            return false;
        }

        private static void RemoveBuilding(Zone zone)
        {
            foreach (Cel p in PlacedObjects)
            {
                Cell cell = zone.GetCell(p.X, p.Y);
                if (cell == null)
                {
                    continue;
                }

                // Runs on every zone activation, so an already-removed building is a no-op.
                GameObject found = FindIn(cell, p.Blueprint);
                if (found != null)
                {
                    found.Obliterate(Silent: true);
                }
            }

            foreach (Cel p in RestoreDirtPath)
            {
                Cell cell = zone.GetCell(p.X, p.Y);
                if (cell != null && FindIn(cell, p.Blueprint) == null)
                {
                    cell.AddObject(p.Blueprint);
                }
            }
        }

        private static GameObject FindIn(Cell cell, string blueprint)
        {
            List<GameObject> objects = cell.GetObjects();
            if (objects == null)
            {
                return null;
            }

            foreach (GameObject o in objects)
            {
                if (o != null && o.Blueprint == blueprint)
                {
                    return o;
                }
            }

            return null;
        }
    }
}
