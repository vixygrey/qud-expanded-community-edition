using System;

namespace XRL.World.Parts.Skill
{
    /// <summary>
    /// Finesse, sold by the axe tree. Raises a penetration roll's stat bonus to the attacker's
    /// Agility modifier, for weapons tagged Finesse that roll against Strength.
    /// </summary>
    /// <remarks>
    /// <para>
    /// The axe tree sells this because of the vinereaper, which vanilla describes as "moulded to a
    /// crescent for scything the rough hides of watervine" - a crescent blade named for the crop it
    /// harvests, which is a sickle. Pathfinder's sickle carries agile, finesse and trip. The glaive
    /// is the tree's two-handed finesse weapon. See #342.
    /// </para>
    /// <para>
    /// The Stat == "Strength" guard is load-bearing, not defensive. MeleeWeapon.Stat can be changed
    /// after the blueprint loads - ModPsionic sets it to "Ego" - and comparing Agility against the
    /// running StatBonus alone would quietly convert such a weapon into an Agility weapon, which is
    /// the same override #321 removed from the blueprints. See #366.
    /// </para>
    /// <para>
    /// Reading the field rather than the XML attribute is what makes this safe for merges that state
    /// no Stat at all: MeleeWeapon.Stat is initialised to "Strength", so an omitted attribute matches
    /// and anything Qud adds later does not.
    /// </para>
    /// <para>
    /// One class per tree, never a shared one: SkillFactory.PowersByClass keeps only the first entry
    /// for any given Class, which is how #11 broke Akimbo.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_AxeFinesse : BaseSkill
    {
        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == GetAttackerMeleePenetrationEvent.ID;
        }

        public override bool HandleEvent(GetAttackerMeleePenetrationEvent E)
        {
            if (E.Weapon != null && E.Attacker != null && E.Weapon.HasTag("Finesse"))
            {
                MeleeWeapon weapon = E.Weapon.GetPart<MeleeWeapon>();
                if (weapon != null && weapon.Skill == "Axe" && weapon.Stat == "Strength")
                {
                    int agility = E.Attacker.StatMod("Agility");
                    if (agility > E.StatBonus)
                    {
                        E.StatBonus = agility;
                    }
                }
            }
            return base.HandleEvent(E);
        }
    }
}
