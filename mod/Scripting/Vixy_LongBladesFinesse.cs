using System;

namespace XRL.World.Parts.Skill
{
    /// <summary>
    /// Finesse, sold by the long blade tree. Raises a penetration roll's stat bonus to the
    /// attacker's Agility modifier when that beats the Strength modifier the roll would
    /// otherwise use, and only for weapons tagged Finesse.
    /// </summary>
    /// <remarks>
    /// One class per tree, never a shared one: SkillFactory.PowersByClass keeps only the first
    /// entry for any given Class, which is how #11 broke Akimbo.
    /// </remarks>
    [Serializable]
    public class Vixy_LongBladesFinesse : BaseSkill
    {
        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == GetAttackerMeleePenetrationEvent.ID;
        }

        public override bool HandleEvent(GetAttackerMeleePenetrationEvent E)
        {
            if (E.Weapon != null
                && E.Attacker != null
                && E.Weapon.HasTag("Finesse")
                && E.Weapon.GetWeaponSkill() == "LongBlades")
            {
                int agility = E.Attacker.StatMod("Agility");
                if (agility > E.StatBonus)
                {
                    E.StatBonus = agility;
                }
            }
            return base.HandleEvent(E);
        }
    }
}
