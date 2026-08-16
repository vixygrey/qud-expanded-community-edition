using System;

namespace XRL.World.Parts.Skill
{
    /// <summary>
    /// Two-Gun Stance, the Multiweapon Fighting version of the Pistol tree's Akimbo.
    ///
    /// Behaviour is inherited and deliberately identical - this exists to own a distinct class
    /// name, not to do anything different.
    ///
    /// Sharing Pistol_Akimbo, as this power did until #11, silently displaced a vanilla record.
    /// SkillFactory.PowersByClass is a Dictionary&lt;string, PowerEntry&gt; holding ONE entry per
    /// class, and vanilla grants powers by class name - the Gunslinger calling is literally
    /// &lt;skill Name="Pistol_Akimbo" /&gt;. A second power declaring the same class takes that slot
    /// when the mod loads, so the Gunslinger showed this mod's name for vanilla's power, and
    /// vanilla's Akimbo reported Multiweapon Fighting as its ParentSkill.
    ///
    /// The collision was invisible while both powers were called "Akimbo". Renaming one is what
    /// surfaced it; the defect had been there since the power was first added.
    ///
    /// Charter rule 5: no file I/O, no network, no reflection, no Harmony. It adds no state.
    /// </summary>
    /// <remarks>
    /// Namespace and [Serializable] follow the installed-mod precedent for custom skill powers -
    /// GrvShortBlades_Jab and HearthpyreGoverning_Locate both sit in XRL.World.Parts.Skill and are
    /// marked [Serializable], which a part attached to the player needs to survive a save.
    /// </remarks>
    [Serializable]
    public class Raven_TwoGunStance : Pistol_Akimbo
    {
        /// <summary>
        /// Do not register a second identical ability when the character already has Akimbo.
        ///
        /// Buying this and the Pistol tree's Akimbo attaches two parts, and each inherited
        /// AddAbility registers an activated ability under the same command. HandleEvent below
        /// silences the matching duplicate on the *toggle*; this handles the ability entry. In play that showed
        /// as "Akimbo" twice on the bar and left the skills screen reopening itself on Escape.
        /// It did not survive a save - the ability list is rebuilt from parts on load and the
        /// duplicate collapsed - so the saved character was always fine; the damage was confined
        /// to the running session.
        ///
        /// AddAbility is not virtual, so the duplicate cannot be suppressed at the point it is
        /// created. AddSkill is, so it is suppressed one level up instead.
        ///
        /// Returning true without calling base reports the power as successfully learnt while
        /// skipping only the ability registration. That matters: returning false would leave the
        /// purchase in whatever state Qud reserves for a skill that refused to attach, which is
        /// not documented anywhere and would be guesswork. The power still functions - this part
        /// continues to answer CanFireAllMissileWeaponsEvent, and vanilla's already-registered
        /// ability drives the toggle.
        /// </summary>
        public override bool AddSkill(GameObject GO)
        {
            if (HasSeparateAkimbo(GO))
            {
                return true;
            }

            return base.AddSkill(GO);
        }

        /// <summary>
        /// Let vanilla's Akimbo handle the toggle when the character has both.
        ///
        /// Suppressing the duplicate ability in AddSkill leaves one entry on the bar and one
        /// command, but both parts still *listen* for that command, and each one announces the
        /// toggle - so the log read "Akimbo Toggled Off" twice.
        ///
        /// Returning true without calling base is "I did nothing, carry on": the event keeps
        /// propagating and vanilla's part does the work and the announcing. When this is the only
        /// Akimbo on the character, base runs as normal and this part drives the toggle itself.
        /// </summary>
        public override bool HandleEvent(CommandEvent E)
        {
            if (HasSeparateAkimbo(ParentObject))
            {
                return true;
            }

            return base.HandleEvent(E);
        }

        /// <summary>
        /// True when some OTHER Akimbo part is attached - vanilla's, not this one.
        ///
        /// GetPartsDescendedFrom&lt;Pistol_Akimbo&gt; returns this part too, since it derives from
        /// it, so identity has to be compared rather than type.
        /// </summary>
        private bool HasSeparateAkimbo(GameObject GO)
        {
            if (GO == null)
            {
                return false;
            }

            foreach (Pistol_Akimbo other in GO.GetPartsDescendedFrom<Pistol_Akimbo>())
            {
                if (!ReferenceEquals(other, this))
                {
                    return true;
                }
            }

            return false;
        }
    }
}
