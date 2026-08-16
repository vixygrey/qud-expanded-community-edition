using System.Collections.Generic;
using XRL;
using XRL.UI;
using XRL.World.Anatomy;
using XRL.World.Skills;

namespace QudExpandedCE
{
    /// <summary>
    /// Reads this mod's options and applies them to already-loaded game data.
    ///
    /// Declaring an option is pure XML (mod/Options.xml); reading one requires C#. A class marked
    /// [HasOptionFlagUpdate] gets its [OptionFlagUpdate] method called whenever options change,
    /// and values are read with Options.GetOption, which always returns a string.
    ///
    /// Every apply method is written to be idempotent and reversible: it makes the game data
    /// match the option's current value, rather than performing a one-way edit. Option handlers
    /// run repeatedly and in any order, so "add when on" without "remove when off" would leave
    /// the game in whichever state the player visited last.
    ///
    /// Charter rule 5: no file I/O, no network, no reflection, no Harmony. This reads options and
    /// writes public fields on records the game has already loaded.
    /// </summary>
    [HasOptionFlagUpdate]
    public static class Raven_Options
    {
        public const string MutationPointsID = "OptionQudExpandedCEMutationPoints";
        public const string StartingSkillsID = "OptionQudExpandedCEStartingSkills";
        public const string StartingReputationID = "OptionQudExpandedCEStartingReputation";
        public const string ChipSlotsPlayerID = "OptionQudExpandedCEChipSlotsPlayer";
        public const string ChipSlotsNPCsID = "OptionQudExpandedCEChipSlotsNPCs";
        public const string MultiweaponPistolsID = "OptionQudExpandedCEMultiweaponPistols";

        /// <summary>
        /// Read by Raven_JoppaBuildingSystem rather than here: the building is map data, removed
        /// when a zone activates, not a field on a record this class can write.
        /// </summary>
        public const string JoppaBuildingID = "OptionQudExpandedCEJoppaBuilding";

        private const string ChipSlot = "Chip Interface";

        /// <summary>
        /// Anatomies whose Chip Interface slots are optional, and which option governs each.
        ///
        /// "Humanoid" is vanilla's, merged into by mod/Bodies.xml, and is shared by every humanoid
        /// NPC *and* by a Mutated Human player - vanilla's Mutated Human genotype is
        /// BodyObject="Humanoid". That sharing is why the player needs a separate correction at
        /// chargen; see Raven_ChipSlotPlayerMutator.
        ///
        /// "TrueKin" is this mod's own anatomy and no vanilla creature uses it, so it is
        /// player-only and the player's option can govern it directly.
        ///
        /// "PsionicAdept" is deliberately absent. Its four slots are the genotype rather than an
        /// addition to one - the same reasoning that keeps it out of AddedSkills.
        /// </summary>
        private const string HumanoidAnatomy = "Humanoid";
        private const string TrueKinAnatomy = "TrueKin";

        /// <summary>
        /// Slots removed from each anatomy, kept so they can be put back verbatim.
        ///
        /// Restoring the original AnatomyPart instances rather than constructing new ones keeps
        /// this genuinely reversible: whatever the XML declared - flags, laterality, everything -
        /// is what comes back, with nothing reconstructed from assumptions.
        /// </summary>
        private static readonly Dictionary<string, List<AnatomyPart>> DetachedChipSlots =
            new Dictionary<string, List<AnatomyPart>>();

        /// <summary>
        /// The mod's one addition to the Multiweapon Fighting tree, and the skill it lives in.
        ///
        /// It has its own class, Raven_TwoGunStance, rather than reusing Pistol_Akimbo. Sharing
        /// the class displaced vanilla's entry in SkillFactory.PowersByClass, which holds one
        /// PowerEntry per class - see Raven_TwoGunStance for what that broke.
        /// </summary>
        private const string MultiweaponSkill = "Multiweapon Fighting";
        private const string TwoGunStance = "Two-Gun Stance";

        /// <summary>The power while it is removed, so it can be put back verbatim.</summary>
        private static PowerEntry DetachedTwoGunStance;

        /// <summary>The key it was filed under, so it goes back exactly where it came from.</summary>
        private static string DetachedKey;

        private const string TwoGunStanceClass = "Raven_TwoGunStance";

        /// <summary>Kept in sync with the Description in mod/Skills.xml.</summary>
        private const string TwoGunStanceDescriptionStart =
            "Whenever you make a ranged attack while wielding multiple pistols";

        private const string Mutant = "Mutated Human";
        private const string TrueKin = "True Kin";

        /// <summary>
        /// This mod's long-standing value, and the option's default. Vanilla Qud gives 12.
        /// Kept in sync with Default= in mod/Options.xml.
        /// </summary>
        public const int DefaultMutationPoints = 16;

        /// <summary>
        /// Skills this mod grants on top of vanilla's, per genotype.
        ///
        /// Vanilla gives Mutated Human {Run, Camp} and True Kin {Rebuke Robot, Run, Camp}; none of
        /// those appear here, so turning the option off restores exactly vanilla's starting kit
        /// rather than stripping a genotype bare.
        ///
        /// The Psionic Adept is deliberately absent. It is this mod's own genotype rather than a
        /// merge onto a vanilla one, so its skills are not an addition to something — they are all
        /// it has, and removing them would leave a genotype starting with nothing.
        /// </summary>
        private static readonly Dictionary<string, string[]> AddedSkills = new Dictionary<string, string[]>
        {
            [Mutant] = new[]
            {
                "Physic_StaunchWounds",
                "CookingAndGathering",
                "CookingAndGathering_MealPreparation",
                "Persuasion_MenacingStare",
            },
            [TrueKin] = new[]
            {
                "Physic_StaunchWounds",
                "CookingAndGathering",
                "CookingAndGathering_MealPreparation",
            },
        };

        /// <summary>
        /// Reputation this mod grants, per genotype.
        ///
        /// Only Mutated Human. True Kin's Templar +600 is vanilla's and must not be touched, and
        /// the Psionic Adept's Mechanimist standing is part of its own design for the same reason
        /// its skills are.
        /// </summary>
        private static readonly Dictionary<string, KeyValuePair<string, int>> AddedReputation =
            new Dictionary<string, KeyValuePair<string, int>>
            {
                [Mutant] = new KeyValuePair<string, int>("Joppa", 300),
            };

        /// <summary>Runs whenever any option changes, and once as options are first read.</summary>
        [OptionFlagUpdate]
        public static void OnOptionFlagUpdate()
        {
            ApplyMutationPoints();
            ApplyStartingSkills();
            ApplyStartingReputation();
            ApplyChipSlots();
            ApplyMultiweaponPistols();
        }

        private static bool Enabled(string id, string fallback)
        {
            return Options.GetOption(id, fallback) == "Yes";
        }

        /// <summary>True when the player asked to keep their own chip slots.</summary>
        public static bool PlayerChipSlots => Enabled(ChipSlotsPlayerID, "Yes");

        /// <summary>True when the player asked to leave other humanoids their chip slots.</summary>
        public static bool NPCChipSlots => Enabled(ChipSlotsNPCsID, "Yes");

        /// <summary>
        /// Add or remove Two-Gun Stance from Multiweapon Fighting to match the option.
        ///
        /// Skill trees are read every time the player opens the skills screen rather than baked
        /// into a character, so unlike the chip slots this takes effect immediately and needs no
        /// restart. Powers the player has already bought are parts on them and are not touched.
        ///
        /// SkillEntry exposes no name on a PowerEntry - IBaseSkillEntry has Tile, Foreground,
        /// Detail and Description and nothing else - so the key in SkillEntry.Powers is the only
        /// identifier available, and both that dictionary and PowerList have to be kept in step.
        /// </summary>
        private static void ApplyMultiweaponPistols()
        {
            // GetSkillIfExists rather than GetSkill: options are read before skills are loaded on
            // the first pass, and the throwing variant would take the whole handler down with it.
            SkillEntry skill = SkillFactory.Factory?.GetSkillIfExists(MultiweaponSkill);
            if (skill?.Powers == null || skill.PowerList == null)
            {
                return;
            }

            bool wanted = Enabled(MultiweaponPistolsID, "Yes");
            string key = FindKey(skill);

            if (wanted)
            {
                if (key == null && DetachedTwoGunStance != null)
                {
                    skill.Powers[DetachedKey ?? TwoGunStance] = DetachedTwoGunStance;
                    if (!skill.PowerList.Contains(DetachedTwoGunStance))
                    {
                        skill.PowerList.Add(DetachedTwoGunStance);
                    }

                    DetachedTwoGunStance = null;
                    DetachedKey = null;
                }

                return;
            }

            if (key != null)
            {
                DetachedTwoGunStance = skill.Powers[key];
                DetachedKey = key;
                skill.PowerList.Remove(DetachedTwoGunStance);
                skill.Powers.Remove(key);
            }
        }

        /// <summary>
        /// Locate this mod's power in a skill, without assuming what SkillEntry.Powers is keyed by.
        ///
        /// The dictionary could reasonably be keyed by display name or by implementation class, and
        /// PowerEntry exposes neither - IBaseSkillEntry carries only Tile, Foreground, Detail and
        /// Description. Guessing wrong would not throw: the lookup would simply miss, the removal
        /// would never run, and the option would sit in the menu doing nothing at all.
        ///
        /// So match on the key OR on Description, which this mod sets in mod/Skills.xml and is
        /// therefore the one identifier it can be certain of.
        /// </summary>
        private static string FindKey(SkillEntry skill)
        {
            foreach (KeyValuePair<string, PowerEntry> pair in skill.Powers)
            {
                if (pair.Key == TwoGunStance || pair.Key == TwoGunStanceClass)
                {
                    return pair.Key;
                }

                if (pair.Value?.Description != null
                    && pair.Value.Description.StartsWith(TwoGunStanceDescriptionStart))
                {
                    return pair.Key;
                }
            }

            return null;
        }

        private static void ApplyChipSlots()
        {
            SetChipSlots(TrueKinAnatomy, PlayerChipSlots);
            SetChipSlots(HumanoidAnatomy, NPCChipSlots);
        }

        /// <summary>
        /// Make an anatomy's Chip Interface slots match the option, in either direction.
        ///
        /// Option handlers run repeatedly and in any order, so this sets state rather than
        /// toggling it: removing when already removed, or restoring when already present, are
        /// both no-ops.
        /// </summary>
        private static void SetChipSlots(string anatomyName, bool wanted)
        {
            // GetAnatomy returns null rather than throwing if bodies have not loaded yet, which
            // happens when options are read before Anatomies.Init().
            Anatomy anatomy = Anatomies.GetAnatomy(anatomyName);
            if (anatomy?.Parts == null)
            {
                return;
            }

            if (!DetachedChipSlots.TryGetValue(anatomyName, out List<AnatomyPart> detached))
            {
                detached = new List<AnatomyPart>();
                DetachedChipSlots[anatomyName] = detached;
            }

            if (wanted)
            {
                foreach (AnatomyPart part in detached)
                {
                    if (!anatomy.Parts.Contains(part))
                    {
                        anatomy.Parts.Add(part);
                    }
                }

                detached.Clear();
                return;
            }

            for (int i = anatomy.Parts.Count - 1; i >= 0; i--)
            {
                AnatomyPart part = anatomy.Parts[i];
                if (part?.Type?.Type == ChipSlot)
                {
                    detached.Add(part);
                    anatomy.Parts.RemoveAt(i);
                }
            }
        }

        private static void ApplyMutationPoints()
        {
            string raw = Options.GetOption(MutationPointsID, DefaultMutationPoints.ToString());
            if (!int.TryParse(raw, out int points))
            {
                points = DefaultMutationPoints;
            }

            // Try rather than Get: if this runs before XRL.GenotypeFactory.Init(), the genotype is
            // not loaded yet and this becomes a no-op instead of throwing.
            if (GenotypeFactory.TryGetGenotypeEntry(Mutant, out GenotypeEntry entry))
            {
                entry.MutationPoints = points;
            }
        }

        private static void ApplyStartingSkills()
        {
            bool on = Enabled(StartingSkillsID, "Yes");
            foreach (KeyValuePair<string, string[]> pair in AddedSkills)
            {
                if (!GenotypeFactory.TryGetGenotypeEntry(pair.Key, out GenotypeEntry entry)
                    || entry.Skills == null)
                {
                    continue;
                }

                foreach (string skill in pair.Value)
                {
                    bool present = entry.Skills.Contains(skill);
                    if (on && !present)
                    {
                        entry.Skills.Add(skill);
                    }
                    else if (!on && present)
                    {
                        entry.Skills.Remove(skill);
                    }
                }
            }
        }

        private static void ApplyStartingReputation()
        {
            bool on = Enabled(StartingReputationID, "No");
            foreach (KeyValuePair<string, KeyValuePair<string, int>> pair in AddedReputation)
            {
                if (!GenotypeFactory.TryGetGenotypeEntry(pair.Key, out GenotypeEntry entry)
                    || entry.Reputations == null)
                {
                    continue;
                }

                string with = pair.Value.Key;
                GenotypeReputation existing = entry.Reputations.Find(r => r != null && r.With == with);

                if (on && existing == null)
                {
                    entry.Reputations.Add(new GenotypeReputation { With = with, Value = pair.Value.Value });
                }
                else if (on)
                {
                    existing.Value = pair.Value.Value;
                }
                else if (existing != null)
                {
                    entry.Reputations.Remove(existing);
                }
            }
        }
    }
}
