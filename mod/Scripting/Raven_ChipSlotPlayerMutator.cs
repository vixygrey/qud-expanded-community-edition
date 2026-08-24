using System.Collections.Generic;
using XRL;
using XRL.World;
using XRL.World.Anatomy;
using XRL.World.Parts;

namespace QudExpandedCE
{
    /// <summary>
    /// Takes the shared Chip Interface slot off a Mutated Human at character creation.
    ///
    /// The player's body comes from their genotype's anatomy, and only one of those is
    /// player-exclusive:
    ///
    ///   Mutated Human  -> "Humanoid"     shared with every humanoid NPC in the game
    ///   True Kin       -> "TrueKin"      this mod's own; no vanilla creature uses it
    ///   Psionic Adept  -> "PsionicAdept" this mod's own; deliberately never touched
    ///
    /// The merge that gives every humanoid *NPC* a slot therefore gives the Mutated Human player
    /// one as a side-effect. Nobody chose that, and #352 found it made the mutant the strongest
    /// chip user in the game: a chip's level is a tracker that sums with a mutation's inherent
    /// BaseLevel before the rank cap, so one slot on a genotype that already mutates outperforms
    /// four on the genotype the chips were built for. docs/FEATURES.md 3 states the system's
    /// purpose as granting mutations "to genotypes that cannot mutate", which excludes this one
    /// by its own wording. So the slot goes, and #353 records the decision.
    ///
    /// The anatomy cannot express it - "Humanoid" is one record and NPCs still need their slot -
    /// which is why this class exists at all.
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
            Body body = player?.GetPart<Body>();
            BodyPart root = body?.GetBody();
            if (root == null)
            {
                return;
            }

            List<BodyPart> existing = FindChipSlots(root);

            // Exactly one slot means the shared Humanoid one, which is the only case here.
            // The counts a player can reach are fixed by the anatomies and the two options:
            //
            //   Mutated Human  1 (NPC option on) or 0 (off)
            //   True Kin       2 (player option on) or 0 (off)
            //   Psionic Adept  4, always - its anatomy is governed by neither option
            //
            // So one is unambiguous. Counting rather than reading the genotype name keeps this
            // working if the genotype is ever renamed again, which it has been once already.
            if (existing.Count != 1)
            {
                return;
            }

            root.RemovePart(existing[0], true);
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
