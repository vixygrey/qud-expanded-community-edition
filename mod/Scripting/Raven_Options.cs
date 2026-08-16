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
        public const string MutantHPGainID = "OptionQudExpandedCEMutantHPGain";
        public const string SkillPointGainID = "OptionQudExpandedCESkillPointGain";
        public const string StartingSkillsID = "OptionQudExpandedCEStartingSkills";
        public const string StartingReputationID = "OptionQudExpandedCEStartingReputation";
        public const string ChipDropsID = "OptionQudExpandedCEChipDrops";
        public const string ChipSlotsPlayerID = "OptionQudExpandedCEChipSlotsPlayer";
        public const string ChipSlotsNPCsID = "OptionQudExpandedCEChipSlotsNPCs";

        /// <summary>
        /// Read by Raven_JoppaBuildingSystem rather than here: the building is map data, removed
        /// when a zone activates, not a field on a record this class can write.
        /// </summary>
        public const string JoppaBuildingID = "OptionQudExpandedCEJoppaBuilding";

        private const string ChipSlot = "Chip Interface";

        /// <summary>
        /// Prefix of the tables that put psionic chips into the world: Raven_Chips Tier 1, 2 and 3.
        ///
        /// Six loot tables reference them - Artifact 3 through 8, weight 10 each - and nothing else
        /// does. Matching on the reference rather than on a list of Artifact table names means a
        /// seventh reference added later is governed automatically rather than silently escaping.
        ///
        /// Deliberately does NOT reach the Psionic Adept's starting gear, which names chip
        /// blueprints directly rather than going through these tables. Those chips are the
        /// genotype, not an addition to it - the same line the skills and reputation options draw.
        /// </summary>
        private const string ChipTablePrefix = "Raven_Chips";

        /// <summary>
        /// Chip table references removed from loot tables, kept so they can be put back exactly.
        ///
        /// Holding the original PopulationTable instances, paired with the list each came out of,
        /// keeps this genuinely reversible: weight, number and hint all return as declared, with
        /// nothing rebuilt from assumptions.
        /// </summary>
        private static readonly List<KeyValuePair<PopulationList, PopulationItem>> DetachedChipEntries =
            new List<KeyValuePair<PopulationList, PopulationItem>>();

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
        /// The HP-per-level range this mod has always documented, and the option's default.
        /// Vanilla gives 1-4; 2.2 shipped 2-3 by mistake. Kept in sync with Default= in
        /// mod/Options.xml and with BaseHPGain in mod/Genotypes.xml.
        /// </summary>
        public const string DefaultMutantHPGain = "1-5";

        /// <summary>
        /// Every range the option offers. An unrecognised value falls back to the default rather
        /// than reaching GenotypeEntry.BaseHPGain, because the game parses that string at every
        /// level-up and a malformed one would fail there rather than here.
        /// </summary>
        private static readonly HashSet<string> MutantHPGainChoices = new HashSet<string>
        {
            "1-5",
            "2-3",
            "1-4",
        };

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
        /// One value this mod changes, paired with the vanilla value it replaced.
        ///
        /// Every option here has to restore vanilla's number, not merely stop applying the mod's,
        /// because the mod's XML overwrote it at load and the original is gone from memory by the
        /// time any option is read. Keeping the pair together is what makes each toggle reversible
        /// rather than one-way.
        /// </summary>
        private sealed class Tuning<T>
        {
            public readonly T Mod;
            public readonly T Vanilla;

            public Tuning(T mod, T vanilla)
            {
                Mod = mod;
                Vanilla = vanilla;
            }

            public T For(bool on)
            {
                return on ? Mod : Vanilla;
            }
        }

        /// <summary>
        /// Skill points per level, per genotype: this mod's value against vanilla's.
        ///
        /// The Psionic Adept's 95 is deliberately absent, for the same reason its skills and
        /// reputation are: it is this mod's own genotype rather than a merge onto a vanilla one,
        /// so there is no vanilla value to restore.
        /// </summary>
        private static readonly Dictionary<string, Tuning<string>> SkillPointGain =
            new Dictionary<string, Tuning<string>>
            {
                [Mutant] = new Tuning<string>("65", "50"),
                [TrueKin] = new Tuning<string>("85", "70"),
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
            ApplyMutantHPGain();
            ApplySkillPointGain();
            ApplyStartingSkills();
            ApplyStartingReputation();
            ApplyChipSlots();
            ApplyChipDrops();
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

        /// <summary>
        /// Make the world's psionic chip supply match the option, in either direction.
        ///
        /// Population tables are read from XML at load, but the loaded result stays mutable, so
        /// this is fully live: it changes what future containers and merchants roll, without
        /// needing a new character. Chips already in the world are left alone.
        ///
        /// No chip carries a TinkerItem part, so removing these six references closes the supply
        /// completely rather than leaving tinkering as a way in.
        /// </summary>
        private static void ApplyChipDrops()
        {
            if (Enabled(ChipDropsID, "Yes"))
            {
                foreach (KeyValuePair<PopulationList, PopulationItem> entry in DetachedChipEntries)
                {
                    entry.Key.AddItem(entry.Value);
                }

                DetachedChipEntries.Clear();
                return;
            }

            // Reading the property runs PopulationManager.CheckInit(), which loads the tables if
            // they are not loaded yet - so unlike the genotype and anatomy edits above, this one
            // cannot lose a race with the game's own load order.
            foreach (PopulationInfo info in PopulationManager.Populations.Values)
            {
                DetachChipTables(info);
            }
        }

        /// <summary>
        /// Recursively strip chip table references out of one population and remember where each
        /// came from. Removing when already removed is a no-op, so repeated calls are safe.
        /// </summary>
        private static void DetachChipTables(PopulationList list)
        {
            if (list?.Items == null)
            {
                return;
            }

            for (int i = list.Items.Count - 1; i >= 0; i--)
            {
                PopulationItem item = list.Items[i];

                PopulationTable table = item as PopulationTable;
                if (table != null)
                {
                    if (table.Name != null && table.Name.StartsWith(ChipTablePrefix))
                    {
                        DetachedChipEntries.Add(
                            new KeyValuePair<PopulationList, PopulationItem>(list, table));
                        list.RemoveItem(table);
                    }

                    continue;
                }

                // Groups nest, and a chip reference could sit at any depth. PopulationInfo and
                // PopulationGroup are both PopulationList, so one cast covers every container.
                PopulationList nested = item as PopulationList;
                if (nested != null)
                {
                    DetachChipTables(nested);
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

        /// <summary>
        /// Set the Mutated Human's hit points per level.
        ///
        /// Unlike mutation points and starting skills, this is not a chargen-time value:
        /// XRL.World.Parts.Leveler reads BaseHPGain through RollHP(string) at every level-up, so
        /// the change is live from a character's next level rather than needing a new one.
        /// </summary>
        private static void ApplyMutantHPGain()
        {
            string range = Options.GetOption(MutantHPGainID, DefaultMutantHPGain);
            if (!MutantHPGainChoices.Contains(range))
            {
                range = DefaultMutantHPGain;
            }

            if (GenotypeFactory.TryGetGenotypeEntry(Mutant, out GenotypeEntry entry))
            {
                entry.BaseHPGain = range;
            }
        }

        /// <summary>
        /// Set skill points per level for the two vanilla genotypes.
        ///
        /// Live rather than chargen-scoped, on the same footing as ApplyMutantHPGain: Leveler
        /// reads BaseSPGain through RollSP(string) at every level-up.
        /// </summary>
        private static void ApplySkillPointGain()
        {
            bool on = Enabled(SkillPointGainID, "Yes");
            foreach (KeyValuePair<string, Tuning<string>> pair in SkillPointGain)
            {
                if (GenotypeFactory.TryGetGenotypeEntry(pair.Key, out GenotypeEntry entry))
                {
                    entry.BaseSPGain = pair.Value.For(on);
                }
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
