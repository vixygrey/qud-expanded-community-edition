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
    /// Charter rule 5: no file I/O, no network, no reflection, no Harmony. This reads an option
    /// and writes a public field on a record the game has already loaded.
    /// </summary>
    [HasOptionFlagUpdate]
    public static class Raven_Options
    {
        public const string MutationPointsID = "OptionQudExpandedCEMutationPoints";

        /// <summary>The genotype whose mutation points the slider controls.</summary>
        private const string MutantGenotype = "Mutated Human";

        /// <summary>
        /// This mod's long-standing value, and the option's default. Vanilla Qud gives 12.
        /// Kept in sync with Default= in mod/Options.xml.
        /// </summary>
        public const int DefaultMutationPoints = 16;

        /// <summary>Runs whenever any option changes, and once as options are first read.</summary>
        [OptionFlagUpdate]
        public static void OnOptionFlagUpdate()
        {
            ApplyMutationPoints();
        }

        private static void ApplyMutationPoints()
        {
            // Every option value is a string, including sliders.
            string raw = Options.GetOption(MutationPointsID, DefaultMutationPoints.ToString());
            if (!int.TryParse(raw, out int points))
            {
                points = DefaultMutationPoints;
            }

            // Try rather than Get: if this runs before XRL.GenotypeFactory.Init(), the genotype
            // is not loaded yet and this becomes a no-op instead of throwing.
            if (GenotypeFactory.TryGetGenotypeEntry(MutantGenotype, out GenotypeEntry entry))
            {
                entry.MutationPoints = points;
            }
        }
    }
}
