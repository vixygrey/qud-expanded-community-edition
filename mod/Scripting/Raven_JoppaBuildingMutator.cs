using XRL;
using XRL.World;

namespace QudExpandedCE
{
    /// <summary>
    /// Registers the Joppa building system on a new character.
    ///
    /// [PlayerMutator] runs at character creation, so the system is scribed into the save from
    /// the start and is in place before the player first sets foot in Joppa.
    /// </summary>
    [PlayerMutator]
    public class Raven_JoppaBuildingMutator : IPlayerMutator
    {
        public void mutate(GameObject player)
        {
            The.Game.AddSystem(new Raven_JoppaBuildingSystem());
        }
    }
}
