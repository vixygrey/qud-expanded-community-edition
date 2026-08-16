using System.Collections.Generic;
using XRL;
using XRL.UI;
using XRL.World.Anatomy;

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
        }

        private static bool Enabled(string id, string fallback)
        {
            return Options.GetOption(id, fallback) == "Yes";
        }

        /// <summary>True when the player asked to keep their own chip slots.</summary>
        public static bool PlayerChipSlots => Enabled(ChipSlotsPlayerID, "Yes");

        /// <summary>True when the player asked to leave other humanoids their chip slots.</summary>
        public static bool NPCChipSlots => Enabled(ChipSlotsNPCsID, "Yes");
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
