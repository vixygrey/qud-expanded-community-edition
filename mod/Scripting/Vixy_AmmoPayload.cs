using System;
using System.Collections.Generic;

namespace XRL.World.Parts
{
    /// <summary>
    /// Lets a round carry a payload into a firearm that hardcodes its own projectile.
    ///
    /// Every slug weapon in the game names its projectile on MagazineAmmoLoader, and that field is
    /// where the weapon's ballistics live - 1d6/pen 3 for a revolver through 1d8/pen 7 for a sniper
    /// rifle to the Linear Cannon's 2d12 Vorpal. MagazineAmmoLoader only consults the ROUND's
    /// ProjectileObject when the weapon leaves that field blank, so effect ammunition loaded into a
    /// slug weapon is fired and its payload discarded. That is the defect #14 recorded as "degraded
    /// to plain ammo", and it is structural rather than a bug.
    ///
    /// Blanking the field the way #145 did for the four shotguns is not available here: those two
    /// pellet projectiles are identical to the round's own, while flattening the 19 slug weapons
    /// would demote every one of them to ProjectileLeadSlug's 1d6/pen 3. So instead of replacing the
    /// weapon's projectile, this merges the round's payload INTO it. The gun keeps its ballistics;
    /// the round adds its effect.
    ///
    /// Two events, because one is not available. A part merged onto an abstract base is always
    /// dispatched BEFORE parts declared on the concrete blueprint - ObjectBlueprintLoader.Bake
    /// inherits the parent's children before overlaying the object's own - and AddPartInternals
    /// orders PartsList by IPart.Priority, which can only move a part EARLIER. So this cannot run
    /// after MagazineAmmoLoader at any price, and does not try:
    ///
    ///   LoadAmmoEvent    runs first, which is what makes the read valid: the loader's Ammo field
    ///                    still holds the stack it is about to draw from, before RemoveOne().
    ///   ProjectileSetup  fired by MissileWeapon.SetupProjectile once per projectile, after the
    ///                    projectile object exists. A separate dispatch, so part order is irrelevant.
    ///
    /// Charter rule 5: no file I/O, no network, no Harmony, no reflection of our own. IPart.DeepCopy
    /// uses reflection internally, but that is the game's own public API doing it, not us.
    /// </summary>
    [Serializable]
    public class Vixy_AmmoPayload : IScribedPart
    {
        /// <summary>
        /// Parts that define a projectile's identity rather than its payload. The whole point is to
        /// keep the weapon's own ballistics, so Projectile is the critical one - copying it would
        /// reintroduce exactly the flattening this part exists to avoid.
        /// </summary>
        private static readonly string[] IdentityParts =
        {
            "Projectile",
            "Render",
            "Physics",
            "Description",
            "RulesDescription",
            "MissileStatusColor",
        };

        /// <summary>
        /// Payload parts per blueprint, resolved once. Static, so it is not save shape; blueprints
        /// do not change within a run, and the parts are only ever read as DeepCopy sources.
        /// </summary>
        private static Dictionary<string, List<IPart>> PayloadParts;

        /// <summary>
        /// The payload the round about to fire is carrying, or null. Transient by construction: it
        /// is written during LoadAmmoEvent and read microseconds later during ProjectileSetup, both
        /// inside one FireMissileWeapon call, so it never needs to survive a save.
        ///
        /// [NonSerialized] keeps it out of the save shape that charter rule 5 governs. It is
        /// assigned on EVERY load, including to null, because a stale value here would be plain
        /// slugs quietly behaving like loaded ones.
        /// </summary>
        [NonSerialized]
        private string Pending;

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == PooledEvent<LoadAmmoEvent>.ID;
        }

        public override void Register(GameObject Object, IEventRegistrar Registrar)
        {
            Registrar.Register("ProjectileSetup");
            base.Register(Object, Registrar);
        }

        public override bool HandleEvent(LoadAmmoEvent E)
        {
            Pending = ResolvePayload();
            return base.HandleEvent(E);
        }

        public override bool FireEvent(Event E)
        {
            if (E.ID == "ProjectileSetup" && Pending != null)
            {
                GameObject projectile = E.GetGameObjectParameter("Projectile");
                if (projectile != null)
                {
                    Apply(Pending, projectile);
                }
            }
            return base.FireEvent(E);
        }

        /// <summary>
        /// The blueprint whose parts should ride along, or null when there is nothing to do.
        /// </summary>
        private string ResolvePayload()
        {
            MagazineAmmoLoader loader = ParentObject.GetPart<MagazineAmmoLoader>();
            if (loader == null)
            {
                return null;
            }

            // The weapon defers to its ammunition already - vanilla builds the round's own
            // projectile wholesale, payload included. Doing anything here would apply it twice.
            // This is the branch the four shotguns take since #145.
            if (loader.ProjectileObject.IsNullOrEmpty())
            {
                return null;
            }

            GameObject ammo = loader.Ammo;
            if (ammo == null)
            {
                return null;
            }

            string blueprint = AmmoProjectile(ammo);

            // A round that names the projectile the weapon already fires is ordinary ammunition.
            if (blueprint == null || blueprint == loader.ProjectileObject)
            {
                return null;
            }
            return blueprint;
        }

        /// <summary>
        /// The projectile blueprint a round declares, or null.
        ///
        /// Spelled out per family rather than through IAmmo, because IAmmo does not declare
        /// ProjectileObject - each of the three concrete classes declares its own copy of the
        /// field. GetProjectileBlueprintEvent is no help either: only weapon-side loaders answer
        /// it, never the round. The alternative, GetProjectileObjectEvent, builds a whole GameObject
        /// to ask a question, which is not worth doing once per shot.
        /// </summary>
        private static string AmmoProjectile(GameObject ammo)
        {
            AmmoSlug slug = ammo.GetPart<AmmoSlug>();
            if (slug != null)
            {
                return slug.ProjectileObject.IsNullOrEmpty() ? null : slug.ProjectileObject;
            }
            AmmoShotgunShell shell = ammo.GetPart<AmmoShotgunShell>();
            if (shell != null)
            {
                return shell.ProjectileObject.IsNullOrEmpty() ? null : shell.ProjectileObject;
            }
            AmmoArrow arrow = ammo.GetPart<AmmoArrow>();
            if (arrow != null)
            {
                return arrow.ProjectileObject.IsNullOrEmpty() ? null : arrow.ProjectileObject;
            }
            return null;
        }

        private static void Apply(string blueprint, GameObject projectile)
        {
            List<IPart> parts = Resolve(blueprint);
            for (int i = 0; i < parts.Count; i++)
            {
                IPart source = parts[i];
                // Never displace a part the weapon's own projectile brought with it.
                if (projectile.GetPart(source.Name) == null)
                {
                    projectile.AddPart(source.DeepCopy(projectile));
                }
            }
        }

        private static List<IPart> Resolve(string blueprint)
        {
            if (PayloadParts == null)
            {
                PayloadParts = new Dictionary<string, List<IPart>>();
            }
            List<IPart> cached;
            if (PayloadParts.TryGetValue(blueprint, out cached))
            {
                return cached;
            }

            cached = new List<IPart>();
            GameObject sample = GameObject.CreateSample(blueprint);
            if (sample != null)
            {
                foreach (IPart part in sample.PartsList)
                {
                    if (Array.IndexOf(IdentityParts, part.Name) < 0)
                    {
                        cached.Add(part);
                    }
                }
            }
            PayloadParts[blueprint] = cached;
            return cached;
        }

        /// <summary>
        /// Writes and reads nothing, symmetrically, so this part occupies no bytes in a save.
        /// </summary>
        /// <remarks>
        /// <para>
        /// <c>IScribedPart</c> does exactly one thing in each direction — <c>WriteNamedFields</c> and
        /// <c>ReadNamedFields</c> — and this class has no serialisable state, so what it writes is a
        /// field count of zero and nothing else. Suppressing both halves gives the same on-disk
        /// shape the class had before #497 and the same shape it has now, in every version, which is
        /// the point: there is no boundary between two formats, so nothing has to know where the
        /// boundary is.
        /// </para>
        /// <para>
        /// <b>That knowledge was the bug (#554).</b> This used to read nothing while still writing a
        /// block, gated on a version comparison — and a version cannot separate a save written by
        /// the released 2.7.0, which wrote nothing, from one written by an unreleased build after
        /// #497, which wrote a block. Both record 2.7.0. The reader then left a byte unconsumed, and
        /// an under-read is not contained: <c>IPart.Load</c> repositions to the end of the block only
        /// from inside its <c>catch</c>, so reading too little throws nothing and desynchronises
        /// every object after it in the zone.
        /// </para>
        /// <para>
        /// <b>#497 is not undone.</b> The class stays on the <c>IScribed</c> base, which is the part
        /// that is expensive to do later. When it gains a field, delete both overrides — and by then
        /// the version really will have moved, so nothing has to be inferred from one.
        /// </para>
        /// </remarks>
        public override void Write(GameObject Basis, SerializationWriter Writer)
        {
        }

        /// <summary>The other half of the pair above. Symmetry is the whole mechanism.</summary>
        public override void Read(GameObject Basis, SerializationReader Reader)
        {
        }
    }
}
