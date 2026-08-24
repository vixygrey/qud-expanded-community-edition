using System;

namespace XRL.World.Parts.Skill
{
    /// <summary>
    /// Finesse, sold by the cudgel tree. Raises a penetration roll's stat bonus to the attacker's
    /// Agility modifier, for weapons tagged Finesse that roll against Strength.
    /// </summary>
    /// <remarks>
    /// <para>
    /// The cudgel tree sells this because of the mace line. Pathfinder's finesse bludgeon is a
    /// mace-family weapon - the light mace carries agile, finesse and shove, while the warhammer
    /// never does - so the mace ladder is the tree's finesse pick and the war hammers stay Strength.
    /// The quarterstaff is the tree's two-handed finesse weapon, on the strength of the monk trait
    /// both Pathfinder staves carry. See #342.
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
    /// and anything Qud adds later does not. It matters more here than in the other trees, because
    /// Cudgel is what MeleeWeapon.Skill defaults to - 118 vanilla weapons declare no Skill at all.
    /// </para>
    /// <para>
    /// One class per tree, never a shared one: SkillFactory.PowersByClass keeps only the first entry
    /// for any given Class, which is how #11 broke Akimbo.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_CudgelFinesse : BaseSkill
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
                if (weapon != null && weapon.Skill == "Cudgel" && weapon.Stat == "Strength")
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
