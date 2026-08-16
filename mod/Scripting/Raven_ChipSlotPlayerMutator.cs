using System.Collections.Generic;
using XRL;
using XRL.World;
using XRL.World.Anatomy;
using XRL.World.Parts;

namespace QudExpandedCE
{
    /// <summary>
    /// Corrects the player's Chip Interface slots at character creation, in the one case the
    /// anatomy edits in Raven_Options cannot cover on their own.
    ///
    /// The player's body comes from their genotype's anatomy, and only one of those is
    /// player-exclusive:
    ///
    ///   Mutated Human  -> "Humanoid"     shared with every humanoid NPC in the game
    ///   True Kin       -> "TrueKin"      this mod's own; no vanilla creature uses it
    ///   Psionic Adept  -> "PsionicAdept" this mod's own; deliberately never touched
    ///
    /// So the True Kin and Psionic Adept cases are already right by the time a body is built.
    /// A Mutated Human, though, gets whatever the *NPC* option left on "Humanoid" - which is
    /// wrong whenever the two options disagree. Without this, turning off chip slots for NPCs
    /// would silently take a Mutated Human player's slot as well, which is not what the option
    /// says it does.
    ///
    /// Charter rule 5: no file I/O, no network, no reflection, no Harmony. This reads two
    /// options and adds or removes one body part on a single object.
    /// </summary>
    /// <remarks>
    /// [PlayerMutator] is what the game scans for. Implementing IPlayerMutator without it is the
    /// quiet failure mode - the class compiles, ships, and is simply never called. 11 of the
    /// installed mods that implement this interface carry the attribute; that is the pattern with
    /// evidence behind it.
    /// </remarks>
    [PlayerMutator]
    public class Raven_ChipSlotPlayerMutator : IPlayerMutator
    {
        private const string ChipSlot = "Chip Interface";

        public void mutate(GameObject player)
        {
            bool wanted = Raven_Options.PlayerChipSlots;

            // When both options agree, the anatomy the body was just built from already matches
            // what the player asked for, and there is nothing to correct. This is the common
            // case - both options default on - so it is checked first and costs nothing.
            if (wanted == Raven_Options.NPCChipSlots)
            {
                return;
            }

            Body body = player?.GetPart<Body>();
            BodyPart root = body?.GetBody();
            if (root == null)
            {
                return;
            }

            List<BodyPart> existing = FindChipSlots(root);

            // A Psionic Adept is never adjusted. Its anatomy is its own and is not governed by
            // either option, so any slots found here are the genotype's four, not the shared
            // Humanoid one. Detecting that by slot count rather than by genotype name keeps this
            // working if the genotype is ever renamed again.
            if (existing.Count > 1)
            {
                return;
            }

            if (wanted && existing.Count == 0)
            {
                root.AddPart(ChipSlot);
            }
            else if (!wanted && existing.Count > 0)
            {
                foreach (BodyPart slot in existing)
                {
                    root.RemovePart(slot, true);
                }
            }
        }

        private static List<BodyPart> FindChipSlots(BodyPart root)
        {
            List<BodyPart> found = new List<BodyPart>();
            List<BodyPart> parts = root.GetParts();
            if (parts == null)
            {
                return found;
            }

            foreach (BodyPart part in parts)
            {
                if (part != null && part.Type == ChipSlot)
                {
                    found.Add(part);
                }
            }

            return found;
        }
    }
}
