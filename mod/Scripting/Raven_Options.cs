using XRL;

namespace QudExpandedCE
{
    /// <summary>
    /// Reads this mod's options and applies them to already-loaded game data.
    ///
    /// Declaring an option is pure XML (mod/Options.xml); reading one requires C#. A field
    /// carrying [OptionFlag] is populated from the named option, and a method carrying
    /// [OptionFlagUpdate] runs whenever any option changes.
    ///
    /// Charter rule 5: no file I/O, no network, no reflection, no Harmony. This reads an option
    /// and writes a public field on a record the game has already loaded.
    /// </summary>
    [HasOptionFlagUpdate]
    public static class Raven_Options
    {
        public const string MutationPointsID = "Option_QudExpandedCE_MutationPoints";

        /// <summary>The genotype whose mutation points the slider controls.</summary>
        private const string MutantGenotype = "Mutated Human";

        /// <summary>
        /// Mutation points a Mutated Human starts with. Vanilla is 12; this mod's long-standing
        /// value, and this option's default, is 16.
        /// </summary>
        [OptionFlag(MutationPointsID)]
        public static int MutationPoints = 16;

        /// <summary>
        /// Applies every option. Runs on any option change.
        ///
        /// GenotypeFactory.GetGenotypeEntry would throw if genotypes are not loaded yet, so the
        /// Try form is used: if this runs before XRL.GenotypeFactory.Init(), it does nothing
        /// rather than crashing, and the next option change applies it.
        /// </summary>
        [OptionFlagUpdate]
        public static void Apply()
        {
            ApplyMutationPoints();
        }

        private static void ApplyMutationPoints()
        {
            if (GenotypeFactory.TryGetGenotypeEntry(MutantGenotype, out GenotypeEntry entry))
            {
                entry.MutationPoints = MutationPoints;
            }
        }
    }
}
