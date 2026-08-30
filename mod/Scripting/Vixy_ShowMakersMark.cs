using System;
using XRL.UI;

namespace XRL.World.Conversations.Parts
{
    /// <summary>
    /// Shows a conversation choice only when I am carrying something the person I am talking to
    /// made — matched on the maker's mark the item already carries.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>This reads data vanilla already writes; it adds no ledger of its own.</b> Two parts carry
    /// a mark and the issue conflated them. <c>HasMakersMark</c> sits on the <em>creature</em> and
    /// holds only <c>Mark</c> and <c>Color</c>. <c>XRL.World.Parts.MakersMark</c> sits on the
    /// <em>item</em> and holds <c>Mark</c>, <c>Color</c> <b>and <c>CrafterName</c></b>, which is
    /// what <c>MakersMark.AddCrafter</c> stamps from <c>NameForMark(Crafter)</c>. So the link from
    /// an object back to the person who made it is already on the object, already serialised, and
    /// already printed — a marked blade's description reads <i>"this dagger bears the mark of
    /// Argyve."</i> See #595.
    /// </para>
    /// <para>
    /// <b>What was missing was the reaction, and only that.</b> You could buy a dagger stamped with
    /// Argyve's name, carry it back to Argyve, and he had nothing to say about it. Recognition and
    /// price both already ship: <c>GenericInventoryRestocker.GetCraftmarkApplication</c> stamps
    /// every eligible item in a hero merchant's stock and raises its <c>Commerce.Value</c> in the
    /// same breath. Nobody responding to their own work is the whole of the gap.
    /// </para>
    /// <para>
    /// <b>Matching is on the name, not the glyph.</b> <c>Mark</c> is one or more glyph characters
    /// and <c>MakersMark.AddCrafter</c> concatenates them when several crafters touch an object, so
    /// a substring test on it would false-positive the moment two makers share a glyph — and
    /// <c>MakersMark.Generate</c> draws from a finite pool, so they will. <c>CrafterName</c> is
    /// <c>;;</c>-joined instead, which splits cleanly and compares against the speaker's own
    /// reference name computed the same way.
    /// </para>
    /// <para>
    /// <b>Rate-limited by Freehold rather than by me.</b> <c>TriggersMakersMarkCreationEvent</c> has
    /// exactly two handlers, <c>ModMasterwork</c> and <c>ModLegendary</c>, so the game's own answer
    /// to "when is an object worth marking" is *when it is notable*. Inheriting that filter is why
    /// this needs no frequency tuning of its own, and why a player will meet it rarely enough for it
    /// to stay a small moment.
    /// </para>
    /// <para>
    /// <b>A replica is deliberately not its original.</b> <c>HasMakersMark.HandleEvent</c> on
    /// <c>ReplicaCreatedEvent</c> generates a <em>new</em> mark and colour, so a clone of a smith is
    /// not that smith. Nothing here has to special-case it; the names simply do not match.
    /// </para>
    /// <para>
    /// <b>No off-switch.</b> Charter rule 6 asks whether anybody would actually turn a thing off
    /// before it gets a switch. This changes no number, no loot table and no character creation; it
    /// adds one conversation line that appears only when I am already carrying the speaker's own
    /// work, which the mark filter above makes rare on its own. There is nothing here to refuse but
    /// a sentence, so an option would have spent a line in the menu, a <c>helptext</c> to keep true
    /// and a branch to carry forever, and bought nothing — the same reasoning
    /// <c>Vixy_LiquidGather</c> records, and #692 had just cut five options to fit the menu.
    /// </para>
    /// <para>
    /// Charter rule 5: no instance state, one visibility handler, no Harmony and no reflection. The
    /// choice merges into <c>BaseConversation</c>, so no vanilla record is modified.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_ShowMakersMark : IConversationPart
    {
        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == IsElementVisibleEvent.ID;
        }

        public override bool HandleEvent(IsElementVisibleEvent E)
        {
            GameObject speaker = The.Speaker;
            GameObject player = The.Player;

            if (speaker == null || player == null || !speaker.IsCreature)
            {
                return false;
            }

            // A speaker who never had a mark cannot have made anything. Cheapest test first: this
            // fires for every conversation in the game, and almost nobody carries one.
            if (speaker.GetPart<XRL.World.Parts.HasMakersMark>() == null)
            {
                return false;
            }

            if (!CarryingWorkOf(player, speaker))
            {
                return false;
            }

            return base.HandleEvent(E);
        }

        /// <summary>
        /// True when <paramref name="player"/> is carrying an object stamped with
        /// <paramref name="speaker"/>'s name.
        /// </summary>
        /// <remarks>
        /// <c>GetInventoryAndEquipment</c> rather than <c>GetInventory</c>, so a blade I am holding
        /// counts as much as one in the pack — showing someone their own work should not require
        /// putting it away first. Followers are not searched: the enumeration is the actor's own.
        /// </remarks>
        private static bool CarryingWorkOf(GameObject player, GameObject speaker)
        {
            string speakerName = XRL.World.Parts.MakersMark.NameForMark(speaker);
            if (speakerName.IsNullOrEmpty())
            {
                return false;
            }

            foreach (GameObject item in player.GetInventoryAndEquipment())
            {
                var mark = item.GetPart<XRL.World.Parts.MakersMark>();
                if (mark == null || mark.CrafterName.IsNullOrEmpty())
                {
                    continue;
                }

                // CrafterName is ";;"-joined when several crafters touched the object, and
                // MakersMark renders it as an and-list. Compare the parts, never the whole string.
                foreach (string crafter in mark.CrafterName.CachedDoubleSemicolonExpansion())
                {
                    if (crafter == speakerName)
                    {
                        return true;
                    }
                }
            }

            return false;
        }
    }
}
