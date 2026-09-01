using System;

namespace XRL.World.Parts
{
    /// <summary>
    /// Spends a use of the melee weapon that just landed a hit. Sits on the player, because that is
    /// the only place a single listener can hear every melee weapon.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Why the player and not the weapon.</b> `Combat` fires <c>WeaponHit</c> at the weapon and
    /// <c>WieldedWeaponHit</c> at the attacker, and only the second is any use here: a part on the
    /// weapon would mean merging into the ~718 carried melee blueprints that sit at 25 hitpoints,
    /// while <c>WieldedWeaponHit</c> carries the weapon as a parameter and reaches one part on the
    /// player. Zero vanilla records for the whole melee half. See #195.
    /// </para>
    /// <para>
    /// Missile weapons get no such gift. There is no central per-shot hook — <c>ShotComplete</c>
    /// knows the weapon but only reaches the weapon, and <c>BeginMissileAttack</c> reaches the
    /// attacker carrying no parameters at all — so that half is <c>Vixy_Worn</c> merged onto the 64
    /// blueprints that declare <c>MissileWeapon</c>. The feature is deliberately half player-part
    /// and half merge, and the reason is that asymmetry in vanilla rather than a preference.
    /// </para>
    /// <para>
    /// <b>Per hit, not per swing.</b> <c>WieldedWeaponHit</c> is fired inside the hit branch, after
    /// penetration is resolved, so a miss costs nothing. That is deliberate: wear should follow use
    /// that accomplished something, and it is the closest melee analogue to a shot leaving a barrel.
    /// </para>
    /// <para>
    /// The arithmetic, the tier interval and both exemptions all live in <c>Vixy_Worn.Use</c>, so
    /// the two halves cannot drift apart.
    /// </para>
    /// <para>
    /// Charter rule 5: no instance state, one string-event handler, no Harmony and no reflection.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_WeaponWear : IPart
    {
        public override void Register(GameObject Object, IEventRegistrar Registrar)
        {
            Registrar.Register("WieldedWeaponHit");
            base.Register(Object, Registrar);
        }

        public override bool FireEvent(Event E)
        {
            if (E.ID == "WieldedWeaponHit")
            {
                // Wear is a player-facing system, and this part is only ever attached to the player -
                // but `GameObject.DeepCopy` copies every part, so a temporal fugue duplicate or a
                // clone of the player carries it too, with no save or load involved. Without this the
                // copy wears its own weapons for as long as it exists. #769.
                if (!ParentObject.IsPlayerControlled())
                {
                    return base.FireEvent(E);
                }

                GameObject weapon = E.GetGameObjectParameter("Weapon");

                // A missile weapon used as a club would otherwise wear twice - once here and once
                // through its own ShotComplete handler. Melee wear is for melee use.
                if (weapon != null && weapon.GetPart<MissileWeapon>() == null)
                {
                    Vixy_Worn.Use(weapon);
                }
            }

            return base.FireEvent(E);
        }
    }
}
