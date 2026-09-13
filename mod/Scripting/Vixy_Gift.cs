using System.Collections.Generic;
using XRL.UI;
using XRL.World.AI;
using XRL.World.Parts;

namespace XRL.World.Conversations.Parts
{
    /// <summary>
    /// Hand somebody something, and have them remember it. #634.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Both halves of this exist in vanilla and never meet.</b> <c>GiveArtifact</c> and
    /// <c>LibrarianGiveBook</c> pick an item and do not record anything; <c>TakeItem</c> records
    /// nothing either but performs a proper player-to-speaker transfer — except that it matches
    /// inventory against a fixed <c>Blueprints</c>/<c>IDs</c> list declared in XML, so it can only
    /// take <em>named</em> things and cannot offer a choice. Neither touches <c>Opinion</c>, and
    /// nor does the trade screen: <c>CompanionGiveItems</c> calls
    /// <c>TradeUI.ShowTradeScreen(target, 0f)</c>, which is a free transfer with no
    /// trade-completion event of any kind. You can hand a companion your whole inventory and their
    /// regard is unchanged.
    /// </para>
    /// <para>
    /// <b>So this is a picker joined to <c>TakeItem</c>'s transfer, and the opinion is applied at
    /// its own call site.</b> That is the only version that can know what moved. Reusing the trade
    /// screen would get the transfer and not the knowledge — the five trade events
    /// (<c>StartTradeEvent</c>, <c>CanTradeEvent</c>, <c>CanBeTradedEvent</c>,
    /// <c>AllowTradeWithNoInventoryEvent</c>, <c>GetTradePerformanceEvent</c>) all fire before
    /// items move, and the moves themselves are plain <c>ReceiveObject</c> calls.
    /// </para>
    /// <para>
    /// <b>The transfer is <c>TakeItem.Execute</c>'s, copied rather than inherited.</b> Its selection
    /// and its transfer are one method, so there is nothing to call — but the four things it does
    /// after <c>ReceiveObject</c> are all worth having and none of them is obvious: hand the item
    /// back if the receiver refuses it, say so in Qud's own wording, use <c>Does("take")</c> so the
    /// sentence conjugates for the speaker, and set <c>WontSell</c>. That last one matters most —
    /// without it a merchant puts your gift straight back on the shelf at their markup, which reads
    /// as the gift not having landed at all.
    /// </para>
    /// <para>
    /// <b>The important-item rule is <c>Vixy_GiveArtifact</c>'s, because it is this fork's rule
    /// everywhere:</b> a mark I made means do not offer it, a mark the game made means ask. The
    /// failure message is the librarian's shape — it names the exclusion and how to undo it, rather
    /// than presenting an empty menu.
    /// </para>
    /// <para>
    /// <b>A led creature is refused rather than credited.</b> <c>Brain.GetFeeling</c> early-returns
    /// <c>GetFinalLeaderBrain().GetFeeling(Target)</c> before it reads any opinion map, so an
    /// opinion recorded on somebody's bodyguard can never be observed — worse than doing nothing,
    /// because it looks like it worked. <c>AddOpinion</c> itself has no such guard and would happily
    /// write it. Player-led creatures are handled differently again, in
    /// <see cref="IsElementVisibleEvent" /> below.
    /// </para>
    /// <para>
    /// <b>Tradeable and worth something is the floor.</b> Otherwise ten pebbles buy the same regard
    /// as ten carbines: the opinion is flat by design — #634 asks for it to scale against the
    /// grievances rather than against value — and flat with no floor makes the gesture free.
    /// <c>CanBeTradedEvent</c> is re-checked here, which the free-give path skips: it is gated
    /// <c>if (CostMultiple &gt; 0f)</c>, so items that refuse ordinary trade still move through
    /// <c>CompanionGiveItems</c>. A gift is a gift, not a loophole.
    /// </para>
    /// <para>
    /// <b>The reply node is an emote, and that is <c>docs/FEATURES.md</c> §61.2 applied.</b> This
    /// choice is distributed from <c>BaseConversation</c>, so it reaches every mouth in the game,
    /// and no spoken line is true in all of them — a legendary snapjaw carries a proper name
    /// because <c>HeroMaker</c> calls <c>GiveProperName</c>, and its conversation is still
    /// <i>you food?</i>. The cut cannot be made sharper either: 102 of vanilla's 200 conversations
    /// are a single node with no live choice, holding <c>Snapjaw</c> and <c>Goatfolk</c> beside
    /// <c>JoppaFarmer</c> and <c>GenericMerchant</c>. Written replies for a named cast are #919, on
    /// the order #633 shipped in — the mechanism to everyone, the voices afterwards.
    /// </para>
    /// <para>
    /// Charter rule 5: three event handlers, a list filter and a transfer. No I/O, no reflection,
    /// no Harmony.
    /// </para>
    /// </remarks>
    public class Vixy_Gift : IConversationPart
    {
        public override bool WantEvent(int ID, int Propagation)
        {
            return base.WantEvent(ID, Propagation)
                || ID == GetChoiceTagEvent.ID
                || ID == IsElementVisibleEvent.ID
                || ID == EnterElementEvent.ID
                || ID == GetTargetElementEvent.ID;
        }

        /// <summary>The node a familiar giver is sent to instead of <c>Vixy_Gifted</c>.</summary>
        public const string WarmNode = "Vixy_GiftedWarm";

        /// <summary>
        /// Send the reply somewhere warmer once giving has stopped being remarkable.
        /// </summary>
        /// <remarks>
        /// <para>
        /// <b>The ordering is what makes this read correctly, and it is
        /// <c>ConversationUI.SelectChoice</c>'s rather than mine.</b> It runs <c>choice.Enter()</c>
        /// — where <see cref="HandleEvent(EnterElementEvent)" /> hands the item over and records the
        /// opinion — and only then calls <c>GetTargetNode</c>, which sends
        /// <c>GetTargetElementEvent</c>. So the magnitude read here already includes the gift just
        /// given, and the seventh gift is the one that first sees the warmer node rather than the
        /// eighth. A failed or escaped give returns false from <c>Enter()</c> and never reaches this
        /// at all.
        /// </para>
        /// <para>
        /// This is vanilla's own mechanism: <c>ChangeTarget</c> is an <c>IPredicatePart</c> that
        /// does exactly this, assigning <c>E.Target</c> when its predicates match. It cannot be
        /// reused directly only because no conversation predicate reaches <c>Brain.Opinions</c> —
        /// the 58 <c>If*</c> delegates cover quests, state, time, reputation and genotype, and
        /// there is no <c>IfOpinionAtLeast</c> to write.
        /// </para>
        /// <para>
        /// The threshold belongs to <c>Vixy_OpinionGift.Familiar</c> rather than being written
        /// here, so it cannot drift from the band <c>GetText</c> reports on the examine screen.
        /// </para>
        /// </remarks>
        public override bool HandleEvent(GetTargetElementEvent E)
        {
            if (Vixy_OpinionGift.Familiar(The.Speaker, The.Player))
            {
                E.Target = WarmNode;
            }
            return base.HandleEvent(E);
        }

        /// <summary>Vanilla's own tag colour for a choice that hands something over.</summary>
        public override bool HandleEvent(GetChoiceTagEvent E)
        {
            E.Tag = "{{g|[give]}}";
            return false;
        }

        /// <summary>
        /// Whether the choice is worth showing this speaker at all.
        /// </summary>
        /// <remarks>
        /// <para>
        /// <b>Only to somebody I know by name, who knows mine.</b> A gift is a gesture between two
        /// people, and handing one to a stranger you cannot address is a transaction. Both halves
        /// are tested rather than one: <c>HasProperName</c> is whether I know who they are, and
        /// <c>Vixy_Introduce.Done</c> is whether a name has gone the other way — set by
        /// <c>Vixy_Introduce</c>, by <c>Vixy_Introductions</c> noticing one of vanilla's own
        /// introductions, and by <c>Vixy_AskName</c>, which gives my name in the same breath as it
        /// asks for theirs. In practice the marker nearly always implies the name; *nearly* is what
        /// would bite, so both are checked and the intent does not depend on another part's
        /// internals.
        /// </para>
        /// <para>
        /// Hidden rather than shown-and-refused, because the way through is one choice up the same
        /// list — this sits at Ordinal 9600, directly below the two naming exchanges at 9900 and
        /// 10000. <c>Vixy_RitualGate</c> hides the water ritual on the same condition. No fall-open
        /// guard, unlike that one: a creature that can never be introduced to can never be gifted,
        /// and unlike the ritual that strands nothing.
        /// </para>
        /// <para>
        /// <b>Hidden on your own followers, and vanilla is why.</b> Any creature you lead already
        /// carries <c>Give Items</c> from <c>GameObject</c>'s own handler — the trade screen at a
        /// cost multiple of zero, which moves a whole inventory at once rather than one item per
        /// conversation. A second, worse route to the same place would be noise, and the opinion
        /// behind it would be inert anyway for the leader reason above. Somebody <em>else's</em>
        /// follower has no such route, so the choice is shown and refused with a reason on entry.
        /// </para>
        /// <para>
        /// No option gates this. Charter rule 6 asks whether anybody would turn it off, and the
        /// feature is already opt-in at the point of use: nothing happens to a player who does not
        /// introduce themselves and then choose to give, ten times over ten days. #663 settled that
        /// flavour and additions nobody would disable do not earn a line in the menu.
        /// </para>
        /// </remarks>
        public override bool HandleEvent(IsElementVisibleEvent E)
        {
            GameObject speaker = The.Speaker;
            if (speaker == null || !speaker.IsCreature) return false;

            // A dominated creature under my control holds no opinions at all - Brain
            // .TryGetOpinions returns false for IsPlayer() - so the gift would silently vanish.
            if (speaker.IsPlayer()) return false;

            // Somebody I know, who knows me.
            if (!speaker.HasProperName) return false;
            if (!Vixy_Introduce.Done(speaker)) return false;

            Brain brain = speaker.Brain;
            if (brain == null) return false;

            // Vanilla's Give Items already covers everyone I lead, and does it better.
            if (brain.IsPlayerLed()) return false;

            return base.HandleEvent(E);
        }

        public override bool HandleEvent(EnterElementEvent E)
        {
            GameObject player = The.Player;
            GameObject speaker = The.Speaker;
            if (player?.Inventory == null || speaker == null)
            {
                return base.HandleEvent(E);
            }

            // Somebody else's follower. Their captain's regard is the one GetFeeling reads, so
            // recording this here would be a lie that looks like it worked - name them and stop,
            // which is the answer Vixy_CustomsRegard already gives to the same question.
            GameObject leader = speaker.Brain?.GetFinalLeader();
            if (leader != null && leader != speaker)
            {
                return player.ShowFailure(
                    speaker.Does("take", int.MaxValue, null, null, null, AsIfKnown: false)
                        + " their bearing from "
                        + leader.BaseDisplayNameStripped
                        + ", and would not remember it."
                );
            }

            List<GameObject> offerable = new List<GameObject>();
            bool held = false;
            foreach (GameObject item in player.Inventory.GetObjects())
            {
                if (item.IsMarkedImportantByPlayer())
                {
                    held = true;
                    continue;
                }
                if (Giftable(item, speaker))
                {
                    offerable.Add(item);
                }
            }

            if (offerable.Count == 0)
            {
                return player.ShowFailure(
                    held
                        ? "You only have things you've marked important. Unmark any you wish to give."
                        : "You have nothing worth giving."
                );
            }

            GameObject giving = Popup.PickGameObject(
                "Choose something to give.",
                offerable,
                AllowEscape: true
            );

            if (giving == null || !giving.ConfirmUseImportant(player, "give"))
            {
                return false;
            }

            return Hand(player, speaker, giving) ? base.HandleEvent(E) : false;
        }

        /// <summary>
        /// Whether an item is a thing one could actually give somebody.
        /// </summary>
        /// <remarks>
        /// Commercial value is the floor rather than a blueprint list, so it needs no maintenance
        /// and covers this fork's own items for free. It also settles water without a special
        /// case: a waterskin is an object with a value and is offered, while an individual dram is
        /// not an object at all — drams live in a <c>LiquidVolume</c> inside a container, so
        /// nothing in an inventory walk can reach one. That is the intended outcome. The water
        /// ritual is the faction-scale version of this and #753 owns it; a gift is the personal one,
        /// and they should not be two ways to spend the same dram.
        /// </remarks>
        private static bool Giftable(GameObject Item, GameObject Speaker)
        {
            if (Item == null || Item.IsTemporary) return false;
            if (Item.HasPropertyOrTag("QuestItem")) return false;
            if (Item.ValueEach <= 0.0) return false;

            // Re-checked deliberately. The free-give path skips this - TradeUI gates it on
            // CostMultiple > 0f - so items that refuse ordinary trade still move through
            // CompanionGiveItems. A gift should not be the way around that. Checked at the default
            // CostMultiple of 1, which is the question being asked: would this change hands at all.
            return CanBeTradedEvent.Check(Item, The.Player, Speaker);
        }

        /// <summary>
        /// The transfer, and the only place the opinion is recorded.
        /// </summary>
        /// <remarks>
        /// <para>
        /// Follows <c>TakeItem.Execute</c> step for step: split a single item off a stack, offer it,
        /// hand it back if the receiver refuses, announce it in the speaker's own conjugation, and
        /// mark it <c>WontSell</c> so a merchant does not shelve your gift for resale.
        /// </para>
        /// <para>
        /// <b>No <c>CommandRemoveObject</c>, and that is the difference from
        /// <c>Vixy_GiveArtifact</c>.</b> <c>ReceiveObject</c> is <c>TakeObject(…, Silent: true)</c>,
        /// which fires <c>CommandTakeObjectSilent</c> on the receiver and moves the item out of
        /// whatever context it is in — the whole transfer, in one call. That is why <c>TakeItem</c>
        /// never removes anything first, and why its failure branch can hand the item back by
        /// simply having the player receive it again. Removing it first would drop it through
        /// <c>BeginDrop</c>/<c>PerformDrop</c> and leave a failed give lying on the floor. Argyve's
        /// picker removes because the artifact is consumed and nobody receives it; here somebody
        /// does.
        /// </para>
        /// <para>
        /// <b>The <c>Context</c> is passed.</b> <c>TakeObject</c> carries one into
        /// <c>CommandTakeObjectSilent</c> and the vanilla trade path leaves it null, which is
        /// exactly why nothing downstream can tell a gift from a pickup — the gap #634 found. This
        /// part does not need it, since it applies the opinion at its own call site, but naming the
        /// event costs nothing and makes the transfer legible to anything that looks later.
        /// </para>
        /// </remarks>
        private static bool Hand(GameObject Player, GameObject Speaker, GameObject Giving)
        {
            Giving.SplitStack(1, Player);

            if (!Speaker.ReceiveObject(Giving, Context: "Vixy_Gift"))
            {
                Popup.ShowFail("You cannot give " + Giving.t() + "!");
                Player.ReceiveObject(Giving);
                return false;
            }

            Giving.SetIntProperty("WontSell", 1);
            Popup.Show(
                Speaker.Does("take", int.MaxValue, null, null, null, AsIfKnown: false)
                    + " "
                    + Giving.t()
                    + "."
            );

            Speaker.Brain?.AddOpinion<Vixy_OpinionGift>(Player);
            return true;
        }
    }
}
