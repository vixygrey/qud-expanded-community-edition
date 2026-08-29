namespace QudExpandedCE
{
    /// <summary>
    /// Every syllable and word mod/Naming.xml adds to a vanilla namestyle.
    ///
    /// This is data, not logic, and it lives in its own file for two reasons. Nothing at runtime
    /// can tell a merged-in syllable from a vanilla one - the loader appends both into the same
    /// List and neither carries a marker - and reading mod/Naming.xml back would be file I/O,
    /// which charter rule 5 forbids. So the list has to be restated here, and
    /// validate_mod.py's naming-option-coverage check holds the two halves together in both
    /// directions.
    ///
    /// Separate from Raven_Options.cs so that .typos.toml can skip it. These are invented name
    /// fragments rather than words - `thi`, `sya`, `nye` - and there is no typo to fix in any of
    /// them, but Raven_Options.cs is 700 lines of real prose that should stay spell-checked.
    /// Same reasoning the file already applies to mod/Naming.xml and tools/qud-api.json.
    /// </summary>
    public static class Vixy_NameSyllables
    {
        public static readonly string[] AddedPrefixes =
        {
            "ae", "be", "ce", "dho", "el", "en", "esh", "hy", "ia", "ish", "je", "kae", "le", "li",
            "lu", "mya", "ne", "oa", "pe", "phi", "re", "rhy", "sa", "se", "she", "shy", "sse", "te",
            "the", "va", "ve", "vi", "wa", "we", "xa", "ye", "za", "ze", "zi"
        };

        public static readonly string[] AddedInfixes =
        {
            "ala", "eli", "ien", "isa", "nye", "sya", "thi", "vae"
        };

        public static readonly string[] AddedPostfixes =
        {
            "ek", "eth", "ik", "ith", "oq", "orr", "oth", "uk", "urn", "yr", "yth", "zar"
        };

        /// <summary>
        /// The Issachari additions, which are whole words rather than syllables.
        ///
        /// An Issachari name is one hyphenated phrase - verb, preposition, noun - so the pools hold
        /// words and the register is the constraint. A bodily or violent act, sited against the
        /// desert's materials, its elements, or its myth. Brine and the-Red-and-White are lifted
        /// from the Issachari's own barks rather than invented, and Mirage from their banner.
        /// </summary>
        public static readonly string[] AddedIssachariPrefixes = { "Bleeds", "Burns", "Spits" };

        public static readonly string[] AddedIssachariInfixes =
        {
            "beneath", "across", "against", "beyond", "through"
        };

        public static readonly string[] AddedIssachariPostfixes =
        {
            "Brine", "the-Red-and-White", "Mirage", "Rust"
        };
    }
}
