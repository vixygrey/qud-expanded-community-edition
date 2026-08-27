using XRL.World;

namespace QudExpandedCE
{
    /// <summary>
    /// Tells a component whether the save it is reading predates this mod's move to named fields.
    ///
    /// The `IScribed*` base classes serialise a component's public instance fields by NAME, which
    /// is what lets a field be added or removed later without breaking saves that already exist.
    /// Freehold's serialization page recommends them strongly, and adds that converting a
    /// non-scribed class afterwards is "possible, but nontrivial" - so the cheap moment to convert
    /// is while a class still has no fields to migrate, which is where this fork's three were.
    ///
    /// Converting is not free even then. `IComponent.Write` writes each public instance field
    /// unnamed and in reflection order, so a component with no fields writes NOTHING;
    /// `WriteNamedFields` writes a count first, so the same component writes a zero. One byte, but
    /// a real format change: a reader expecting that count in a save that never wrote one reads
    /// into whatever follows.
    ///
    /// `IPart.Load` wraps every component in a length-delimited block and calls `SkipBlock` on any
    /// read error, so the worst case is contained rather than corrupting - but the component is
    /// dropped from that object. This exists so the worst case does not happen at all.
    ///
    /// Charter rule 5: reads only what the save already holds, no file I/O of its own.
    /// </summary>
    public static class Vixy_SaveFormat
    {
        /// <summary>`manifest.json`'s `id`, which is the key the game writes into every save.</summary>
        private const string ModID = "QudExpandedCommunityEdition";

        /// <summary>
        /// The last release that wrote unnamed fields. Expressed as the last OLD version rather
        /// than the first new one on purpose: the first new one is not known until the release is
        /// cut, and guessing it wrong would point the guard at the wrong side of the boundary.
        /// </summary>
        private static readonly XRL.Version LastUnscribed = new XRL.Version(2, 7, 0);

        /// <summary>
        /// True when the component should read nothing, because the save was written before the
        /// named-field format.
        ///
        /// A save that does not record this mod at all is treated the same way. It cannot have
        /// written a named-field block, so reading one would consume bytes belonging to whatever
        /// comes next - and the components this guards hold no state, so reading nothing costs
        /// nothing.
        /// </summary>
        public static bool PredatesNamedFields(SerializationReader Reader)
        {
            if (Reader?.ModVersions == null)
            {
                return true;
            }

            if (!Reader.ModVersions.TryGetValue(ModID, out XRL.Version wrote))
            {
                return true;
            }

            return wrote <= LastUnscribed;
        }
    }
}
