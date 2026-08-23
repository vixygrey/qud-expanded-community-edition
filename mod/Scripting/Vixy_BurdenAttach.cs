using XRL;
using XRL.World;
using XRL.World.Parts;

namespace QudExpandedCE
{
    /// <summary>
    /// Puts <c>Vixy_Burden</c> on the player, through both of the two hooks that are needed to
    /// cover both of the ways a player arrives.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <c>[PlayerMutator]</c> runs at character creation and nowhere else, so on its own it would
    /// give the burden bands only to characters rolled after this shipped — every existing save
    /// would silently never get them. <c>ModManager.CallAfterGameLoaded</c> is invoked from
    /// <c>XRLGame.LoadGame</c>, so it covers the other case and only the other case; it does not
    /// fire for a new game. Both are required, and neither is sufficient.
    /// </para>
    /// <para>
    /// Attaching unconditionally rather than checking the option, because the option is read live
    /// every turn: the part is inert while the option is off and starts working the moment it is
    /// switched on, with no restart. Adding the part only when enabled would make the option
    /// restart-scoped for no gain.
    /// </para>
    /// <para>
    /// <c>RequirePart</c> rather than <c>AddPart</c> so a save that already has one does not
    /// collect a second.
    /// </para>
    /// <para>
    /// Charter rule 5: no file I/O, no network, no reflection, no Harmony. This adds one part to
    /// one object.
    /// </para>
    /// </remarks>
    [PlayerMutator]
    [HasCallAfterGameLoaded]
    public class Vixy_BurdenAttach : IPlayerMutator
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
            }
        }
    }
}
