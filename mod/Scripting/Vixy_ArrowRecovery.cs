using System;
using System.Collections.Generic;
using QudExpandedCE;
using XRL.Rules;

namespace XRL.World.Parts
{
    /// <summary>
    /// Lets a fired arrow survive its own impact, sometimes, and land where it hit.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Arrows vanish because of one line of data, not because the game cannot leave them.</b>
    /// `MissileWeapon` already knows how to put a projectile on the floor — it calls
    /// <c>ImpactCell.AddObject(Projectile, …)</c> on both impact paths. What decides an arrow's fate is
    /// <c>TemporaryProjectile</c> carrying <c>&lt;part Name="Physics" IsReal="false" /&gt;</c>, which
    /// `BaseArrowProjectile` inherits, so <c>CleanupProjectile</c> always takes
    /// <c>Projectile.Obliterate()</c>. See #643.
    /// </para>
    /// <para>
    /// <b>This does not touch <c>IsReal</c>, and that is the point.</b> Making projectiles real would
    /// give every arrow in flight weight, a cell, a save footprint and a stack — which is presumably
    /// why Freehold made them unreal. Instead this listens for the projectile's own impact and creates
    /// a <em>new, real</em> arrow at the cell, leaving the projectile to be obliterated as usual. The
    /// issue guessed at this shape; the assembly confirms it is the available one.
    /// </para>
    /// <para>
    /// <b>The seam is <c>ProjectileHit</c>, which is fired on the projectile.</b> `MissileWeapon`
    /// raises it at <c>:1806</c> (the failed-to-penetrate path, <c>Penetrations: 0</c>) and
    /// <c>:2303</c> (the hit path), both carrying <c>ImpactCell</c>, and both <em>before</em>
    /// <c>CleanupProjectile</c> runs. So a part on the projectile hears its own landing, knows where,
    /// and still has time to leave something behind.
    /// </para>
    /// <para>
    /// <b>One merge reaches every arrow.</b> All nine vanilla arrow projectiles and all six of this
    /// fork's effect arrows inherit <c>BaseArrowProjectile</c>, so the part goes on that one blueprint.
    /// Unlike a merge onto a container it also reaches existing saves for free, because a projectile is
    /// created fresh on every shot.
    /// </para>
    /// <para>
    /// <b>Recovery is derived from the arrow, not chosen for it.</b> The chance is the projectile's own
    /// <c>StrengthPenetration</c> × <see cref="RecoveryPerPenetration"/> — a ladder Freehold already
    /// wrote, running 2 for wooden to 9 for zetachrome. A wooden arrow usually breaks and a zetachrome
    /// one usually does not, which is both the fiction and the existing scale, so charter rule 2 gets
    /// an answer that is not a number I picked out of the air. The one figure that <em>is</em> mine is
    /// the multiplier, and it is one constant in one place.
    /// </para>
    /// <para>
    /// <b>An arrow that carries anything comes back as nothing.</b> Rather than listing the effect
    /// arrows, this compares the projectile's parts against <c>BaseArrowProjectile</c>'s own: a plain
    /// arrow adds none, and every effect arrow in the game adds exactly one — vanilla's
    /// <c>ProjectileExplosiveArrow</c> adds <c>HEGrenade</c>, and this fork's six add
    /// <c>TemperatureOnHit</c>, <c>GasGrenade</c>, <c>StickyOnHit</c> or <c>FlashbangGrenade</c>. So
    /// the rule is *an arrow that is only an arrow comes back*, and a future effect arrow is covered
    /// without anybody remembering to add it to a list.
    /// </para>
    /// <para>
    /// Charter rule 5: no instance state, so nothing is added to the save. One string event, one
    /// cached lookup built from public blueprint data, no I/O, no reflection, no Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_ArrowRecovery : IScribedPart
    {
        /// <summary>
        /// Percentage points of recovery chance per point of the arrow's <c>StrengthPenetration</c>.
        /// </summary>
        /// <remarks>
        /// Ten, so the ladder runs wooden 20% to zetachrome 90%. This is the only invented number in
        /// the feature: the *shape* comes from Freehold's own material ladder, and this decides how
        /// steep it is. Raising it makes archery cheaper; lowering it makes the bow dead weight again,
        /// which is the thing #643 exists to prevent.
        /// </remarks>
        private const int RecoveryPerPenetration = 10;

        /// <summary>
        /// Projectile blueprint to the arrow blueprint that fires it, built once from the blueprint
        /// table.
        /// </summary>
        /// <remarks>
        /// <c>AmmoArrow.HandleEvent(GetProjectileObjectEvent)</c> does
        /// <c>GameObject.Create(ProjectileObject)</c> and stamps no back-reference, so a projectile
        /// does not know which arrow it came from. Rather than tagging sixteen blueprints, this
        /// inverts the relationship the blueprints already state — every <c>AmmoArrow</c> names its
        /// projectile, so the reverse map is derivable and needs no data of its own.
        /// </remarks>
        private static Dictionary<string, string> AmmoByProjectile;

        /// <summary>The parts <c>BaseArrowProjectile</c> resolves to, cached for the plainness test.</summary>
        private static HashSet<string> PlainArrowParts;

        public override void Register(GameObject Object, IEventRegistrar Registrar)
        {
            Registrar.Register("ProjectileHit");
            base.Register(Object, Registrar);
        }

        public override bool FireEvent(Event E)
        {
            if (E.ID == "ProjectileHit" && Raven_Options.ArrowRecovery)
            {
                TryRecover(E.GetParameter("ImpactCell") as Cell);
            }

            return base.FireEvent(E);
        }

        private void TryRecover(Cell ImpactCell)
        {
            if (ImpactCell == null || ParentObject == null || !IsPlainArrow())
            {
                return;
            }

            string ammo = GetAmmoBlueprint(ParentObject.Blueprint);
            if (ammo == null)
            {
                return;
            }

            Projectile projectile = ParentObject.GetPart<Projectile>();
            if (projectile == null || projectile.StrengthPenetration <= 0)
            {
                return;
            }

            if (!(projectile.StrengthPenetration * RecoveryPerPenetration).in100())
            {
                return;
            }

            GameObject recovered = GameObject.Create(ammo);
            if (recovered != null)
            {
                ImpactCell.AddObject(recovered);
            }
        }

        /// <summary>
        /// True when this projectile is an arrow and nothing more — no payload, no on-hit effect.
        /// </summary>
        /// <remarks>
        /// Compared against <c>BaseArrowProjectile</c> rather than a fixed allow-list, so the test
        /// stays correct as Freehold or this fork adds parts to the shared base. This part itself is
        /// excluded, since it is the thing doing the asking.
        /// </remarks>
        private bool IsPlainArrow()
        {
            if (PlainArrowParts == null)
            {
                PlainArrowParts = new HashSet<string>();
                if (
                    GameObjectFactory.Factory.Blueprints.TryGetValue(
                        "BaseArrowProjectile",
                        out var baseBlueprint
                    )
                )
                {
                    foreach (string name in baseBlueprint.Parts.Keys)
                    {
                        PlainArrowParts.Add(name);
                    }
                }
            }

            if (PlainArrowParts.Count == 0)
            {
                return false;
            }

            for (int i = 0; i < ParentObject.PartsList.Count; i++)
            {
                string name = ParentObject.PartsList[i].Name;
                if (name != Name && !PlainArrowParts.Contains(name))
                {
                    return false;
                }
            }

            return true;
        }

        /// <summary>Which arrow fires this projectile, or null if nothing does.</summary>
        private static string GetAmmoBlueprint(string projectileBlueprint)
        {
            if (AmmoByProjectile == null)
            {
                AmmoByProjectile = new Dictionary<string, string>();
                foreach (var entry in GameObjectFactory.Factory.Blueprints)
                {
                    string fired = entry.Value.GetPartParameter<string>(
                        "AmmoArrow",
                        "ProjectileObject"
                    );
                    if (!string.IsNullOrEmpty(fired) && !AmmoByProjectile.ContainsKey(fired))
                    {
                        AmmoByProjectile[fired] = entry.Key;
                    }
                }
            }

            AmmoByProjectile.TryGetValue(projectileBlueprint, out var ammo);
            return ammo;
        }

        /// <summary>
        /// Writes and reads nothing, symmetrically, so this part occupies no bytes in a save. Same
        /// reasoning as <c>Vixy_Burden</c>; delete both overrides when it gains a field.
        /// </summary>
        public override void Write(GameObject Basis, SerializationWriter Writer)
        {
        }

        /// <summary>The other half of the pair above. Symmetry is the whole mechanism.</summary>
        public override void Read(GameObject Basis, SerializationReader Reader)
        {
        }
    }
}
