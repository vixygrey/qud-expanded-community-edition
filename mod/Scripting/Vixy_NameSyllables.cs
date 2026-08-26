namespace QudExpandedCE
{
    /// <summary>
    /// Every syllable mod/Naming.xml adds to the vanilla Qudish namestyle.
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
    }
}
