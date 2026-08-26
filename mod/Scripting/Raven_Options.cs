using System;
using System.Collections.Generic;
using XRL;
using XRL.UI;
using XRL.Names;
using XRL.World;
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
        public const string MutantHPGainID = "OptionQudExpandedCEMutantHPGain";
        public const string SkillPointGainID = "OptionQudExpandedCESkillPointGain";
        public const string StartingSkillsID = "OptionQudExpandedCEStartingSkills";
        public const string StartingReputationID = "OptionQudExpandedCEStartingReputation";
        public const string SkillRequirementsID = "OptionQudExpandedCESkillRequirements";
        public const string SkillCostsID = "OptionQudExpandedCESkillCosts";
        public const string ChipDropsID = "OptionQudExpandedCEChipDrops";
        public const string ChipSlotsPlayerID = "OptionQudExpandedCEChipSlotsPlayer";
        public const string ChipSlotsNPCsID = "OptionQudExpandedCEChipSlotsNPCs";
        public const string BurdenGradientID = "OptionQudExpandedCEBurdenGradient";
        public const string WiderNamesID = "OptionQudExpandedCEWiderNames";
        public const string GenderedNamesID = "OptionQudExpandedCEGenderedNames";
        public const string GenderSelectionID = "OptionQudExpandedCEGenderSelection";
        public const string PronounSelectionID = "OptionQudExpandedCEPronounSelection";

        public const string NameFlavourID = "OptionQudExpandedCENameFlavour";

        /// <summary>
        /// Read by Raven_JoppaBuildingSystem rather than here: the building is map data, removed
        /// when a zone activates, not a field on a record this class can write.
        /// </summary>
        public const string JoppaBuildingID = "OptionQudExpandedCEJoppaBuilding";


        /// <summary>The vanilla namestyle mod/Naming.xml merges its new syllables into.</summary>
        private const string QudishStyle = "Qudish";

        /// <summary>
        /// The namestyles that carry the gendered ending pools. Switching the option off sets
        /// every scope on them to Chance 0, which ApplyTo evaluates last - so the scope stops
        /// matching, the style stops competing, and naming falls back to Qudish exactly as
        /// vanilla does it.
        /// </summary>
        private static readonly string[] GenderedStyles =
        {
            "Vixy_Qudish Feminine", "Vixy_Qudish Neutral"
        };

        /// <summary>
        /// The syllables mod/Naming.xml adds to Qudish, in their own file so the spell
        /// checker can skip them. Vixy_NameSyllables says why the list is restated at all.
        /// </summary>
        private static readonly string[] AddedPrefixes = Vixy_NameSyllables.AddedPrefixes;
        private static readonly string[] AddedInfixes = Vixy_NameSyllables.AddedInfixes;
        private static readonly string[] AddedPostfixes = Vixy_NameSyllables.AddedPostfixes;

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
        private const string Ego = "Ego";

        /// <summary>
        /// The chargen panel lines this mod owns, paired with the option that delivers each.
        ///
        /// Every one is an <extrainfo> element in mod/Genotypes.xml and must match its text
        /// exactly: the list holds strings and there is nothing else to match on. A line the
        /// options do not govern is deliberately absent - the Psionic Adept's four chip slots and
        /// its Mechanimist standing are the genotype rather than an addition to one, and the HP
        /// and stat-point lines describe vanilla.
        /// </summary>
        private const string MenacingStareInfo = "May use {{r|Menacing Stare}}";
        private const string JoppaReputationInfo = "+300 reputation with {{C|Joppa}}";
        private const string TrueKinChipSlotInfo =
            "{{C|2}} Chip Interface slots; {{W|Ego}} raises the mental mutations chips grant";

        /// <summary>
        /// Where each managed line sat when first seen, so restoring one puts it back rather than
        /// at the bottom. List.Add appends, so without this a player toggling an option twice
        /// would watch the panel reorder itself.
        /// </summary>
        private static readonly Dictionary<string, int> ChargenInfoIndex =
            new Dictionary<string, int>();

        /// <summary>
        /// Vanilla's own True Kin Ego description, captured the first time it is seen.
        ///
        /// Captured rather than written out here so that turning chip slots off restores whatever
        /// Qud actually ships, not whatever it shipped the day this was written.
        /// </summary>
        private static string VanillaTrueKinEgo;

        /// <summary>
        /// The True Kin Ego description while the player has chip slots.
        ///
        /// Word for word the Psionic Adept's, so the two genotypes read alike on the attribute
        /// screen. "Should you acquire any" is the honest qualifier: chargen hands out no chips,
        /// and a character may never find one.
        /// </summary>
        private const string TrueKinEgoWithChips =
            "Your {{W|Ego}} score determines the potency of your mental mutations, should you "
            + "acquire any, your ability to haggle with merchants, and your ability to dominate "
            + "the wills of other living creatures.";

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

        /// <summary>One power's attribute requirement, as this mod sets it and as vanilla had it.</summary>
        private sealed class PowerRequirement
        {
            public readonly string Skill;
            public readonly string Power;
            public readonly Tuning<string> Attribute;
            public readonly Tuning<string> Minimum;

            public PowerRequirement(
                string skill, string power, Tuning<string> attribute, Tuning<string> minimum)
            {
                Skill = skill;
                Power = power;
                Attribute = attribute;
                Minimum = minimum;
            }
        }

        /// <summary>One power's skill point cost, as this mod sets it and as vanilla had it.</summary>
        private sealed class PowerCost
        {
            public readonly string Skill;
            public readonly string Power;
            public readonly Tuning<int> Cost;

            public PowerCost(string skill, string power, Tuning<int> cost)
            {
                Skill = skill;
                Power = power;
                Cost = cost;
            }
        }

        private static Tuning<string> Range(string mod, string vanilla)
        {
            return new Tuning<string>(mod, vanilla);
        }

        // The Axe and Cudgel rewrite is one idea applied twelve times: accept either the tree's
        // own attribute or Agility, so an Agility build can buy powers it already has the stats
        // for. Vanilla gates both trees on Strength alone.
        private static readonly Tuning<string> StrengthOrAgility =
            Range("Strength|Agility", "Strength");

        // Unchanged by the mod, but stated rather than skipped so every row of the table below
        // says what it restores. A row that silently left a field alone would be the one place a
        // future edit could go wrong unnoticed.
        private static readonly Tuning<string> Intelligence = Range("Intelligence", "Intelligence");
        private static readonly Tuning<string> AgilityOrStrength =
            Range("Agility|Strength", "Agility|Strength");

        /// <summary>
        /// Every attribute requirement this mod retunes, against vanilla's own Base/Skills.xml.
        ///
        /// Read out of the game's data rather than reconstructed from the mod's changelog, because
        /// the two have disagreed before - see the Mutated Human HP gain in #90.
        /// </summary>
        private static readonly PowerRequirement[] Requirements =
        {
            new PowerRequirement("Axe", "Cleave", StrengthOrAgility, Range("19|19", "19")),
            new PowerRequirement("Axe", "Charging Strike", StrengthOrAgility, Range("19|19", "19")),
            new PowerRequirement("Axe", "Dismember", StrengthOrAgility, Range("21|21", "21")),
            new PowerRequirement("Axe", "Hook and Drag", StrengthOrAgility, Range("23|23", "23")),
            new PowerRequirement("Axe", "Decapitate", StrengthOrAgility, Range("25|25", "25")),
            new PowerRequirement("Axe", "Berserk!", StrengthOrAgility, Range("29|29", "29")),

            new PowerRequirement("Cudgel", "Bludgeon", StrengthOrAgility, Range("17|17", "17")),
            new PowerRequirement("Cudgel", "Charging Strike", StrengthOrAgility, Range("19|19", "19")),
            new PowerRequirement("Cudgel", "Conk", StrengthOrAgility, Range("21|21", "21")),
            new PowerRequirement("Cudgel", "Backswing", StrengthOrAgility, Range("23|23", "23")),
            new PowerRequirement("Cudgel", "Slam", StrengthOrAgility, Range("25|25", "25")),
            new PowerRequirement("Cudgel", "Demolish", StrengthOrAgility, Range("29|29", "29")),

            // Vanilla asks for 29 in one of Strength or Agility AND 23 in the other, whichever way
            // round; the mod asks only for 29 in either. Restoring it means putting back both the
            // paired attribute list and its paired minimums.
            new PowerRequirement(
                "Long Blade",
                "En Garde!",
                Range("Strength|Agility", "Strength,Agility|Agility,Strength"),
                Range("29|29", "29,23|29,23")),

            // The mod leaves Attribute alone here - vanilla already accepts either - and cuts only
            // the thresholds. Vanilla adopted Strength-or-Agility for this tree itself, so the
            // requirement cut is all that is still the mod's own.
            new PowerRequirement(
                "Multiweapon Fighting", "Multiweapon Expertise", AgilityOrStrength,
                Range("21|21", "23|23")),
            new PowerRequirement(
                "Multiweapon Fighting", "Multiweapon Mastery", AgilityOrStrength,
                Range("25|25", "27|27")),

            // Tinkering is deliberately absent, and so is Long Blade's Dueling Stance. Both were
            // cut by this fork - Tinker I/II/III from 19/23/29 to 17/21/25, Dueling Stance from
            // Int 17 to 15 - and nothing anywhere records why. #331 settled that an undocumented
            // cut is not an option's business: an option offers a choice between two things
            // somebody meant, and these were drift.
            //
            // #331 removed them from here and stopped, which is the opposite of what it decided:
            // mod/Skills.xml kept declaring the cut values, so they went on shipping and could no
            // longer be switched off. #421 put those values back to vanilla's, which is what makes
            // their absence here correct rather than a hole. `skill-option-coverage` in
            // tools/validate_mod.py now fails if the two halves disagree again, in either
            // direction.
        };

        /// <summary>
        /// Every skill point cost this mod retunes, against vanilla's own Base/Skills.xml.
        ///
        /// Tinker I, II and III are deliberately absent: mod/Skills.xml restates their 100/200/300
        /// but those are vanilla's numbers already, so they belong to neither toggle. Their
        /// attribute minimums are vanilla's too since #421, so they are in no table at all.
        /// </summary>
        private static readonly PowerCost[] Costs =
        {
            // Raised to offset the free Cooking and Gathering + Meal Preparation the starting
            // skills option grants. Turning that option off while leaving this one on means
            // paying the offset without the thing it offsets.
            new PowerCost("Cooking and Gathering", "Butchery", new Tuning<int>(100, 50)),
            new PowerCost("Cooking and Gathering", "Spicer", new Tuning<int>(100, 50)),

            // Disassemble was free in this fork against vanilla's 100, and like the Tinkering
            // requirements above nothing records why, so it is gone from here and mod/Skills.xml
            // no longer sets its cost either (#331, then #421 for the half that was missed).
            // Reverse Engineer's rise is the other half of the Cooking offset and stays.
            new PowerCost("Tinkering", "Reverse Engineer", new Tuning<int>(200, 100)),
        };

        /// <summary>Runs whenever any option changes, and once as options are first read.</summary>

        /// <summary>
        /// Weight 0 excludes a syllable from the draw without removing it: GetRandomNameElement
        /// sums only weights above 0 and skips the rest. So this is a switch that can be flipped
        /// back, rather than an edit to undo.
        ///
        /// If another mod adds a syllable this one also adds, the loader merges them into a
        /// single element and switching this off silences it for both. That is unavoidable -
        /// there is one element and one weight - and it is the additive direction, so nothing
        /// vanilla is ever affected.
        /// </summary>
        private static void ApplyWiderNames()
        {
            int weight = Enabled(WiderNamesID, "Yes") ? 1 : 0;
            if (!NameStyles.NameStyleTable.TryGetValue(QudishStyle, out NameStyle style))
            {
                return;
            }
            SetWeights(style.Prefixes, AddedPrefixes, weight);
            SetWeights(style.Infixes, AddedInfixes, weight);
            SetWeights(style.Postfixes, AddedPostfixes, weight);
        }

        private static void SetWeights<T>(List<T> pool, string[] added, int weight)
            where T : NameElement
        {
            foreach (T element in pool)
            {
                if (Array.IndexOf(added, element.Name) >= 0)
                {
                    element.Weight = weight;
                }
            }
        }

        /// <summary>
        /// Chance is the last thing NameScope.ApplyTo evaluates - `return Chance.in100()` - so 0
        /// stops the scope matching at all and the namestyle drops out of the running. Naming
        /// becomes gender-blind again, which is what vanilla does.
        /// </summary>
        private static void ApplyGenderedNames()
        {
            int chance = Enabled(GenderedNamesID, "Yes") ? 100 : 0;
            foreach (string name in GenderedStyles)
            {
                if (NameStyles.NameStyleTable.TryGetValue(name, out NameStyle style))
                {
                    foreach (NameScope scope in style.Scopes)
                    {
                        scope.Chance = chance;
                    }
                }
            }
        }

        /// <summary>
        /// Qud ships a complete gender and pronoun system switched off. Thirteen genders with full
        /// grammar tables, a separate pronoun-set system, replication between the two, and a
        /// selection UI written down to its screen coordinates - all of it unreachable, because
        /// QudCustomizeCharacterModuleWindow.GetSelections yields the Gender and Pronoun Set rows
        /// only `if (Gender.EnableSelection)` and `if (PronounSet.EnableSelection)`.
        ///
        /// Both are public static fields with no setter to work around. Vanilla sets them from the
        /// root attribute of Genders.xml and PronounSets.xml, and a mod could do the same - but an
        /// XML attribute loads unconditionally, and charter rule 6 wants this to be a choice. So it
        /// is set here instead, which is the one thing that makes it optional.
        ///
        /// This does not touch the genders themselves. Turning the option off hides the rows; a
        /// character who already picked a gender keeps it, because the gender is stored on the
        /// object rather than re-read from this flag.
        ///
        /// Setting them here is necessary and NOT sufficient. QudCustomizeCharacterModule.Init
        /// calls PronounSet.Reinit(), which clears the pronoun sets and re-reads PronounSets.xml -
        /// whose root carries EnableSelection="false" - so character creation undoes the pronoun
        /// half of this as it opens. Gender has no equivalent Reinit and survives, which is why
        /// the bug showed as one row appearing and the other not. Vixy_NameFlavourModule.Init
        /// calls this again afterwards.
        /// </summary>
        /// <summary>
        /// Public because Vixy_NameFlavourModule.Init has to call it again. Character creation
        /// resets one of these two flags as it opens; see that method for why.
        /// </summary>
        public static void ApplyChargenSelection()
        {
            Gender.EnableSelection = Enabled(GenderSelectionID, "Yes");
            PronounSet.EnableSelection = Enabled(PronounSelectionID, "Yes");
        }

        /// <summary>
        /// The NamingTag each name-flavour choice asks for, or null for a value this does not know.
        ///
        /// These are identifiers: mod/Naming.xml scopes on them by name, and STYLEGUIDE.md section
        /// 1 applies - renaming one here without renaming it there fails silently, because a tag
        /// nothing scopes on selects nothing.
        ///
        /// "Random" is a real tag rather than the absence of one. All three namestyles carry a
        /// Vixy_Random scope at equal priority, so the weighted draw splits evenly between them -
        /// which is what makes an explicit even split different from simply not asking.
        /// </summary>
        public static string NameFlavourTag()
        {
            switch (Options.GetOption(NameFlavourID, "Random"))
            {
                case "Masc":
                    return "Vixy_Masc";
                case "Femme":
                    return "Vixy_Femme";
                case "Random":
                    return "Vixy_Random";
                default:
                    return null;
            }
        }

        /// <summary>
        /// Keep the player's NamingTag matching the option.
        ///
        /// The tag has to live on the object because renaming yourself in game goes through
        /// GameObject.GiveProperName, which calls NameMaker.MakeName(this, ...) - a valid `For`,
        /// so Generate reads Gender, Species and Tag off the object and ignores anything an option
        /// knows. Without this, character creation followed the option and every rename afterwards
        /// followed your gender instead.
        ///
        /// Written here as well as at boot so the option stays reversible, which is what charter
        /// rule 5 asks of anything mutating loaded data: this makes the property match the option's
        /// current value rather than performing a one-way edit, so changing your mind mid-run takes
        /// effect on the next rename.
        /// </summary>
        public static void ApplyPlayerNameFlavour()
        {
            GameObject player = The.Player;
            if (player == null)
            {
                return;
            }
            string tag = NameFlavourTag();
            if (tag == null)
            {
                player.RemoveStringProperty("NamingTag");
            }
            else
            {
                player.SetStringProperty("NamingTag", tag);
            }
        }

        [OptionFlagUpdate]
        public static void OnOptionFlagUpdate()
        {
            ApplyMutationPoints();
            ApplyMutantHPGain();
            ApplySkillPointGain();
            ApplyStartingSkills();
            ApplyStartingReputation();
            ApplyChipSlots();
            ApplyTrueKinEgoDescription();
            ApplyChargenInfo();
            ApplyChipDrops();
            ApplySkillRequirements();
            ApplySkillCosts();
            ApplyWiderNames();
            ApplyGenderedNames();
            ApplyChargenSelection();
            ApplyPlayerNameFlavour();
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
        /// True when graded burden bands are switched on.
        ///
        /// Read live by Vixy_Burden every turn rather than applied here, because there is no
        /// loaded record to write - the band is derived from carried weight, so the off-switch is
        /// a runtime decision. Charter rule 6 prefers exactly that shape, and it means flipping
        /// this mid-run takes effect on the next tick with no restart.
        ///
        /// Defaults off: rule 6 reserves "off by default" for genuinely new opinions this fork
        /// introduces, and a burden gradient is one. Vanilla's cliff is what the mod has always
        /// shipped.
        /// </summary>
        public static bool BurdenGradient => Enabled(BurdenGradientID, "No");
        private static void ApplyChipSlots()
        {
            SetChipSlots(TrueKinAnatomy, PlayerChipSlots);
            SetChipSlots(HumanoidAnatomy, NPCChipSlots);
        }

        /// <summary>
        /// Make the chargen genotype panel match the options.
        ///
        /// Every line this mod adds is static XML, so without this the panel promises things the
        /// player has switched off - "May use Menacing Stare" with starting skills disabled, and so
        /// on. Charter rule 6 makes these options a promise, and the panel is where a player reads
        /// it while choosing.
        ///
        /// Only this mod's own three lines are touched. Rebuilding the list from a captured copy
        /// would be simpler and would discard <extrainfo> another mod had added since, which
        /// charter rule 1 does not allow.
        ///
        /// There is no Mutated Human chip line any more. #353 took that genotype's slot away, so
        /// a line describing one would promise something chargen will not deliver - which is the
        /// defect #275 was about, arriving from the other direction. The remaining chip line is
        /// the True Kin's, and it follows the player option, which after #353 governs nothing else.
        /// </summary>
        private static void ApplyChargenInfo()
        {
            SetChargenInfo(Mutant, MenacingStareInfo, Enabled(StartingSkillsID, "Yes"));
            SetChargenInfo(Mutant, JoppaReputationInfo, Enabled(StartingReputationID, "Yes"));
            SetChargenInfo(TrueKin, TrueKinChipSlotInfo, PlayerChipSlots);
        }

        /// <summary>
        /// Make one panel line present or absent to match its option, in either direction.
        ///
        /// Sets state rather than toggling it, like SetChipSlots: option handlers run repeatedly
        /// and in any order, so removing when already removed and restoring when already present
        /// are both no-ops.
        /// </summary>
        private static void SetChargenInfo(string genotype, string line, bool wanted)
        {
            // Try rather than Get: options are read before XRL.GenotypeFactory.Init() on some
            // paths, and this becomes a no-op instead of throwing.
            if (!GenotypeFactory.TryGetGenotypeEntry(genotype, out GenotypeEntry entry))
            {
                return;
            }

            List<string> info = entry.ExtraInfo;
            if (info == null)
            {
                return;
            }

            int at = info.IndexOf(line);
            if (wanted)
            {
                if (at >= 0)
                {
                    return;
                }

                // Back where it started, or at the end if the list has since grown shorter.
                int want = ChargenInfoIndex.TryGetValue(line, out int remembered)
                    ? Math.Min(remembered, info.Count)
                    : info.Count;
                info.Insert(want, line);
                return;
            }

            if (at < 0)
            {
                return;
            }

            ChargenInfoIndex[line] = at;
            info.RemoveAt(at);
        }

        /// <summary>
        /// Make the True Kin's Ego description match whether the player has chip slots.
        ///
        /// Vanilla tells a True Kin that Ego governs haggling and domination and says nothing of
        /// mental mutations. That is right for a genotype that cannot mutate and wrong for one
        /// wearing a psionic chip: 23 of the 36 mutations the chips grant are Mental, and Qud
        /// scales that category with Ego. Ego is spent at chargen and cannot be reallocated, so
        /// the sentence is read at the one moment it can still change a decision.
        ///
        /// This cannot be done in XML. GenotypeStat.MergeWith carries Minimum, Maximum and Bonus
        /// and never touches ChargenDescription, so a merge setting one is a silent no-op - see
        /// docs/LESSONS.md. Writing the public field is the same operation ApplyMutationPoints
        /// performs on the same type, and charter rule 5 names it.
        ///
        /// Sets state rather than toggling it, like SetChipSlots: option handlers run repeatedly
        /// and in any order, so this assigns a value derived from the option instead of editing
        /// what is there.
        /// </summary>
        private static void ApplyTrueKinEgoDescription()
        {
            // Try rather than Get: options are read before XRL.GenotypeFactory.Init() on some
            // paths, and this becomes a no-op instead of throwing.
            if (!GenotypeFactory.TryGetGenotypeEntry(TrueKin, out GenotypeEntry entry))
            {
                return;
            }

            if (entry.Stats == null || !entry.Stats.TryGetValue(Ego, out GenotypeStat ego))
            {
                return;
            }

            // The first run that can capture is the first run that can write, so there is no
            // window where this restores null.
            if (VanillaTrueKinEgo == null)
            {
                VanillaTrueKinEgo = ego.ChargenDescription;
            }

            ego.ChargenDescription = PlayerChipSlots ? TrueKinEgoWithChips : VanillaTrueKinEgo;
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

        /// <summary>
        /// Find one power by its skill's name and its own, or null if either is absent.
        ///
        /// Matches on Name through PowerList rather than indexing SkillEntry.Powers, because what
        /// that dictionary is keyed by is not something this mod should depend on - and every
        /// power mod/Skills.xml declares omits Class=, so a class-keyed lookup would find nothing.
        /// </summary>
        private static PowerEntry FindPower(string skillName, string powerName)
        {
            SkillEntry skill = SkillFactory.Factory?.GetSkillIfExists(skillName);
            if (skill?.PowerList == null)
            {
                return null;
            }

            foreach (PowerEntry power in skill.PowerList)
            {
                if (power != null && power.Name == powerName)
                {
                    return power;
                }
            }

            return null;
        }

        /// <summary>
        /// Make the twenty retuned attribute requirements match the option, in either direction.
        /// </summary>
        /// <remarks>
        /// This one takes effect on restart, and its option says so with Restart="true" - the
        /// attribute vanilla itself uses for OptionEnableMods.
        ///
        /// The reason is in the game rather than in this mod. PowerEntry.MeetsAttributeMinimum
        /// gates on a cached _requirements list built from Attribute and Minimum, and
        /// InitRequirements() opens by returning early when that list already exists, so it will
        /// not rebuild. The cache is private, and clearing it would need reflection, which charter
        /// rule 5 forbids outright.
        ///
        /// What saves this is that HandleXMLNode never primes the cache: it is null after load and
        /// built lazily on first use. Options are read at boot, before any skills screen exists, so
        /// the value written here is the one the cache is eventually built from. InitRequirements
        /// is deliberately NOT called - warming the cache early would freeze whichever value
        /// happened to be current at that moment for the rest of the session.
        /// </remarks>
        private static void ApplySkillRequirements()
        {
            bool on = Enabled(SkillRequirementsID, "Yes");
            foreach (PowerRequirement tuning in Requirements)
            {
                PowerEntry power = FindPower(tuning.Skill, tuning.Power);
                if (power == null)
                {
                    continue;
                }

                power.Attribute = tuning.Attribute.For(on);
                power.Minimum = tuning.Minimum.For(on);
            }
        }

        /// <summary>
        /// Make the four retuned skill point costs match the option, in either direction.
        ///
        /// Fully live, unlike the requirements above: Cost is a plain public int with nothing
        /// derived from it, read directly wherever a power is priced or purchased.
        /// </summary>
        private static void ApplySkillCosts()
        {
            bool on = Enabled(SkillCostsID, "Yes");
            foreach (PowerCost tuning in Costs)
            {
                PowerEntry power = FindPower(tuning.Skill, tuning.Power);
                if (power != null)
                {
                    power.Cost = tuning.Cost.For(on);
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
