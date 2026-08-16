using System;

namespace XRL.World.Parts.Skill
{
    /// <summary>
    /// Two-Gun Stance, the Multiweapon Fighting version of the Pistol tree's Akimbo.
    ///
    /// Behaviour is entirely inherited and deliberately identical - this exists to own a distinct
    /// class name, not to do anything different.
    ///
    /// Sharing Pistol_Akimbo, as this power did until #11, silently displaced a vanilla record.
    /// SkillFactory.PowersByClass is a Dictionary&lt;string, PowerEntry&gt; holding ONE entry per
    /// class, and vanilla grants powers by class name - the Gunslinger calling is literally
    /// &lt;skill Name="Pistol_Akimbo" /&gt;. A second power declaring the same class takes that slot
    /// when the mod loads, so the Gunslinger began showing this mod's name for vanilla's power,
    /// and vanilla's Akimbo started reporting Multiweapon Fighting as its ParentSkill.
    ///
    /// The collision was invisible while both powers were called "Akimbo". Renaming one of them
    /// is what surfaced it; the defect had been there since the power was first added.
    ///
    /// Charter rule 5: no file I/O, no network, no reflection, no Harmony. It adds no state, so
    /// nothing here changes what a save contains beyond the class name itself.
    /// </summary>
    /// <remarks>
    /// Namespace and [Serializable] follow the installed-mod precedent for custom skill powers -
    /// GrvShortBlades_Jab and HearthpyreGoverning_Locate both sit in XRL.World.Parts.Skill and are
    /// marked [Serializable], which is what a part attached to the player needs to survive a save.
    /// </remarks>
    [Serializable]
    public class Raven_TwoGunStance : Pistol_Akimbo
    {
    }
}
