using System;

namespace XRL.World.Parts.Skill
{
    /// <summary>
    /// Finesse, sold by the short blade tree. Raises a penetration roll's stat bonus to the
    /// attacker's Agility modifier, for weapons tagged Finesse that roll against Strength.
    /// </summary>
    /// <remarks>
    /// <para>
    /// The Stat == "Strength" guard is load-bearing, not defensive. Three vanilla melee weapons
    /// roll against something else, and one of them - TauDagger, at Stat="Ego" - inherits
    /// BaseDagger and so carries the Finesse tag. Comparing Agility against the running StatBonus
    /// alone would convert a psionic artefact into an Agility weapon, which is the same override
    /// #321 removed from the blueprints. See #366.
    /// </para>
    /// <para>
    /// Reading the field rather than the XML attribute is what makes this safe for the 20 vanilla
    /// merges that state no Stat at all: MeleeWeapon.Stat is initialised to "Strength", so an
    /// omitted attribute matches and anything Qud adds later does not.
    /// </para>
    /// <para>
    /// One class per tree, never a shared one: SkillFactory.PowersByClass keeps only the first
    /// entry for any given Class, which is how #11 broke Akimbo.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_ShortBladesFinesse : BaseSkill
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
                if (weapon != null && weapon.Skill == "ShortBlades" && weapon.Stat == "Strength")
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
