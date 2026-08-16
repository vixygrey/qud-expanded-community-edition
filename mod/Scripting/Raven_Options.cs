using System.Collections.Generic;
using XRL;
using XRL.UI;

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

        /// <summary>
        /// Read by Raven_JoppaBuildingSystem rather than here: the building is map data, removed
        /// when a zone activates, not a field on a record this class can write.
        /// </summary>
        public const string JoppaBuildingID = "OptionQudExpandedCEJoppaBuilding";

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
        }

        private static bool Enabled(string id, string fallback)
        {
            return Options.GetOption(id, fallback) == "Yes";
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
