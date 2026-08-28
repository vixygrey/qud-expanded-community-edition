using XRL;
using XRL.World;
using XRL.World.Parts;

namespace QudExpandedCE
{
    /// <summary>
    /// Puts this mod's own parts on the player, through both of the two hooks that are needed to
    /// cover both of the ways a player arrives.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <c>[PlayerMutator]</c> runs at character creation and nowhere else, so on its own it would
    /// give these parts only to characters rolled after each one shipped — every existing save
    /// would silently never get them. <c>ModManager.CallAfterGameLoaded</c> is invoked from
    /// <c>XRLGame.LoadGame</c>, so it covers the other case and only the other case; it does not
    /// fire for a new game. Both are required, and neither is sufficient.
    /// </para>
    /// <para>
    /// Attaching unconditionally rather than checking each option, because the options are read
    /// live: a part is inert while its option is off and starts working the moment it is switched
    /// on, with no restart. Adding a part only when its option was enabled would make that option
    /// restart-scoped for no gain.
    /// </para>
    /// <para>
    /// <c>RequirePart</c> rather than <c>AddPart</c> so a save that already has one does not
    /// collect a second.
    /// </para>
    /// <para>
    /// <b>One class for all of them, rather than one per feature.</b> This was
    /// <c>Vixy_BurdenAttach</c> until the bearings part needed the same two hooks. Renaming it was
    /// free — it is not <c>[Serializable]</c>, so no save carries its shape, and the game finds it
    /// by the <c>[PlayerMutator]</c> attribute rather than by name from XML, so there was no
    /// identifier to orphan in the sense of <c>docs/STYLEGUIDE.md</c> §1. <c>Raven_</c>-prefixed
    /// mutators stay where they are regardless: that prefix is Mura's credit line under charter
    /// rule 3, and folding one in here would erase it.
    /// </para>
    /// <para>
    /// Charter rule 5: no file I/O, no network, no reflection, no Harmony. This adds parts to one
    /// object.
    /// </para>
    /// </remarks>
    [PlayerMutator]
    [HasCallAfterGameLoaded]
    public class Vixy_PlayerParts : IPlayerMutator
    {
        /// <summary>New characters, at creation.</summary>
        public void mutate(GameObject player)
        {
            Attach(player);
        }

        /// <summary>Existing saves, on load.</summary>
        [CallAfterGameLoaded]
        public static void OnGameLoaded()
        {
            Attach(The.Player);
        }

        private static void Attach(GameObject player)
        {
            if (player != null)
            {
                player.RequirePart<Vixy_Burden>();
                player.RequirePart<Vixy_Bearing>();
            }
        }
    }
}
