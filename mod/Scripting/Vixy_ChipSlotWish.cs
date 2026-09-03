using System.Collections.Generic;
using System.Text;
using XRL;
using XRL.Messages;
using XRL.Wish;
using XRL.World;
using XRL.World.Anatomy;
using XRL.World.Parts;

namespace QudExpandedCE
{
    /// <summary>
    /// <c>vixychipslot</c> — adds Chip Interface slots to the body I already have.
    /// </summary>
    /// <remarks>
    /// <para>
    /// From a player question on #820: is there a wish that gives chip slots to a character who is
    /// not humanoid? There was not, and the closest thing cost them their body plan.
    /// </para>
    /// <para>
    /// <b>Chip slots come from the anatomy, so there was never a runtime route to one.</b> The
    /// genotype picks the anatomy at character creation — <c>PsionicAdept</c> has four,
    /// <c>TrueKin</c> two, <c>Humanoid</c> one which
    /// <see cref="Raven_ChipSlotPlayerMutator"/> then takes back off the player. Nothing after
    /// chargen could change that number.
    /// </para>
    /// <para>
    /// <b>Vanilla's nearest answer is <c>rebuildbody:</c>, and it is the wrong tool.</b>
    /// <c>rebuildbody:PsionicAdept</c> does yield four slots, but <c>Body.Rebuild</c> replaces the
    /// whole anatomy — which is exactly what somebody asking this question is trying to keep. And
    /// there is no vanilla wish that adds a single body part: the only <c>AddPart</c> call in the
    /// entire wish surface is hardcoded inside <c>postgolem</c>.
    /// </para>
    /// <para>
    /// <b>It is a value change, not a balance one, because nothing reaches it without being typed.</b>
    /// Charter rule 6 is satisfied trivially. Worth saying out loud, though: this hands a Mutated
    /// Human chip slots, which is what #352 and #353 deliberately removed — a chip's level sums with
    /// a mutation's own <c>BaseLevel</c> before the rank cap, so the genotype that already mutates
    /// is the strongest chip user in the game. That reasoning was about what the *game* hands out.
    /// A dev command is a different question, and #820 answered it deliberately rather than by
    /// oversight.
    /// </para>
    /// <para>
    /// <b>Wishes reach mods by design.</b> <c>WishManager.UpdateCommandCollection</c> scans
    /// <c>ModManager.GetMethodsWithAttribute(typeof(WishCommand), typeof(HasWishCommand))</c>, and
    /// <c>ModManager.ActiveAssemblies</c> is documented as "the current executing assembly followed
    /// by any enabled script mod assemblies" — so this is an extension point rather than a way in.
    /// Charter rule 5: no I/O, no network, no reflection of my own, no Harmony.
    /// </para>
    /// <para>
    /// <b>Namespaced, like <c>vixyfatigue</c>.</b> Wish names are one global namespace shared with
    /// every installed mod, and <c>chipslot</c> is a phrase more than one of them might want.
    /// </para>
    /// </remarks>
    [HasWishCommand]
    public class Vixy_ChipSlotWish
    {
        /// <summary>The body part type a psionic chip is worn on.</summary>
        private const string ChipSlot = "Chip Interface";

        /// <summary>
        /// Stamped on every slot this wish creates, so <c>:0</c> can find exactly those.
        /// </summary>
        /// <remarks>
        /// <c>BodyPart.FindByManager(Manager, Type, Store)</c> is vanilla's own retrieval by manager,
        /// so removing what this added never touches a slot the anatomy provided. Without it the
        /// only way to tell them apart would be counting, and counting is what
        /// <see cref="Raven_ChipSlotPlayerMutator"/> has to do precisely because it has no manager to
        /// go on.
        /// </remarks>
        private const string Manager = "Vixy_ChipSlotWish";

        /// <summary>Most slots one invocation will add.</summary>
        /// <remarks>
        /// Not balance — a bound. <c>vixychipslot:9999</c> would build a nonsense body and make the
        /// equipment screen crawl, and a message explaining that is friendlier than either obeying
        /// it or refusing without saying why.
        /// </remarks>
        private const int MostAtOnce = 8;

        [WishCommand("vixychipslot", null)]
        public static void AddOne() => Apply(1);

        [WishCommand("vixychipslot", null)]
        public static void AddMany(string rest)
        {
            if (!int.TryParse(rest?.Trim(), out int count) || count < 0)
            {
                MessageQueue.AddPlayerMessage(
                    "{{R|vixychipslot: expected a number, 0 to " + MostAtOnce
                    + ". 0 removes the slots this wish added.}}");
                return;
            }

            Apply(count);
        }

        private static void Apply(int Count)
        {
            GameObject player = The.Player;
            BodyPart root = player?.GetPart<Body>()?.GetBody();
            if (root == null)
            {
                MessageQueue.AddPlayerMessage("{{R|vixychipslot: no body to work with.}}");
                return;
            }

            if (Count == 0)
            {
                Remove(player, root);
                return;
            }

            if (Count > MostAtOnce)
            {
                MessageQueue.AddPlayerMessage(
                    "{{R|vixychipslot: " + MostAtOnce + " at a time. Run it again for more.}}");
                return;
            }

            for (int i = 0; i < Count; i++)
            {
                // Dynamic so the slot survives a later rebuildbody: - Body.Rebuild re-places
                // top-level dynamic parts by position hint and discards the rest, and a wished slot
                // quietly vanishing on an unrelated wish would read as a bug rather than a rule.
                // Named rather than positional: Manager is the seventh parameter of twenty-one, and
                // counting nulls to reach it is how the wrong field gets set silently.
                root.AddPart(ChipSlot, Manager: Manager, Dynamic: true);
            }

            Report(player, root, Count + " slot" + (Count == 1 ? "" : "s") + " added");
        }

        private static void Remove(GameObject Player, BodyPart Root)
        {
            List<BodyPart> mine = new List<BodyPart>();
            Root.FindByManager(Manager, ChipSlot, mine);

            if (mine.Count == 0)
            {
                MessageQueue.AddPlayerMessage(
                    "{{y|vixychipslot: this wish has not added any slots to remove.}}");
                return;
            }

            // RemovePart unequips first, and UnequipPartAndChildren prefers the inventory over the
            // drop inventory - so a chip in a slot being removed goes into my pack rather than onto
            // the floor or out of existence.
            foreach (BodyPart part in mine)
            {
                Root.RemovePart(part, true);
            }

            Report(Player, Root, mine.Count + " slot" + (mine.Count == 1 ? "" : "s") + " removed");
        }

        /// <summary>
        /// Say what happened and, more usefully, what the total is now.
        /// </summary>
        private static void Report(GameObject Player, BodyPart Root, string What)
        {
            int all = CountSlots(Root);

            List<BodyPart> mine = new List<BodyPart>();
            Root.FindByManager(Manager, ChipSlot, mine);

            StringBuilder sb = Event.NewStringBuilder();
            sb.Append("{{G|vixychipslot: ").Append(What).Append(". }}")
              .Append("{{W|").Append(all).Append("}} Chip Interface slot")
              .Append(all == 1 ? "" : "s").Append(" now, ")
              .Append(mine.Count).Append(" of them from this wish.");

            MessageQueue.AddPlayerMessage(sb.ToString());
        }

        /// <summary>
        /// Every Chip Interface slot on this body, however it got there.
        /// </summary>
        /// <remarks>
        /// <c>BodyPart</c> has <c>FindByManager</c> but no find-by-type, so this walks
        /// <c>GetParts()</c> the same way <see cref="Raven_ChipSlotPlayerMutator"/> already does.
        /// </remarks>
        private static int CountSlots(BodyPart Root)
        {
            int found = 0;
            List<BodyPart> parts = Root.GetParts();
            if (parts == null) return 0;

            foreach (BodyPart part in parts)
            {
                if (part != null && part.Type == ChipSlot) found++;
            }
            return found;
        }
    }
}
