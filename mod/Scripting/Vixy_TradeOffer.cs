using System;
using XRL.UI;

namespace XRL.World.Parts
{
    /// <summary>
    /// Stops <c>[begin trade]</c> being offered by someone who has nothing to trade.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Asking a giant dragonfly to trade is a valid choice right up until you make it, at which
    /// point the game says it has nothing to trade. The information existed before the question was
    /// asked. See #571.
    /// </para>
    /// <para>
    /// <b>No conversation merge, unlike the other three.</b> <c>CanTradeEvent.Check</c> fires a
    /// legacy <c>"CanTrade"</c> string event on the actor and the speaker <em>before</em> its pooled
    /// dispatch, and a handler that clears the <c>CanTrade</c> flag turns the choice off:
    /// <c>Trade.CheckVisible</c> derives <c>Visible</c> from <c>Enabled</c>, which is what
    /// <c>CanTradeEvent</c> returns. So this is one part on the player and no XML.
    /// </para>
    /// <para>
    /// <b>The obvious predicate is useless.</b> <c>HasPart&lt;Inventory&gt;()</c> catches nothing —
    /// the root <c>Creature</c> blueprint carries <c>&lt;part Name="Inventory" /&gt;</c>, so every
    /// creature in the game has one, dragonflies included. That branch of vanilla's own refusal is
    /// for non-creature objects. What actually empties a dragonfly's side of the screen is that its
    /// bite is <em>equipped natural equipment</em>, which <c>ValidForTrade</c> rejects, so nothing
    /// is listed.
    /// </para>
    /// <para>
    /// <b>So the test is vanilla's own, composed the way vanilla composes it.</b>
    /// <c>TradeUI.GetObjects</c> lists what passes <c>ValidForTrade</c>, and
    /// <c>ShowTradeScreen</c> refuses when that list is empty, <c>costMultiple &gt; 0</c>, and
    /// <c>AllowTradeWithNoInventoryEvent</c> does not override it. All three are reproduced here,
    /// and two of them are called rather than reimplemented.
    /// </para>
    /// <para>
    /// <b>Companions are exempt, deliberately.</b> <c>ShowTradeScreen</c> zeroes
    /// <c>costMultiple</c> for anything <c>IsPlayerLed</c>, and the refusal is gated on
    /// <c>costMultiple &gt; 0</c> — so an empty companion still opens, which is how you give them
    /// things. Hiding that would break a working interaction to fix a cosmetic one.
    /// </para>
    /// <para>
    /// <b>The maintenance liability, stated plainly.</b> This mirrors a composition that lives
    /// inside <c>TradeUI</c>. If Freehold changes when the refusal fires, this drifts out of step —
    /// hiding a choice that would have worked, or offering one that will not. The item test itself
    /// is not duplicated (<c>ValidForTrade</c> is called), so what can rot is the three-way
    /// combination rather than the definition of a tradeable object, and a wrong answer costs a menu
    /// entry rather than an item. That was a considered trade, not an oversight.
    /// </para>
    /// <para>
    /// Charter rule 5: one event handler and one pass over an inventory. No I/O, no reflection, no
    /// Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_TradeOffer : IScribedPart
    {
        public override void Register(GameObject Object, IEventRegistrar Registrar)
        {
            Registrar.Register("CanTrade");
            base.Register(Object, Registrar);
        }

        public override bool FireEvent(Event E)
        {
            if (E.ID == "CanTrade" && E.HasFlag("CanTrade"))
            {
                GameObject speaker = E.GetGameObjectParameter("SpeakingWith");
                if (HasNothingToTrade(speaker))
                {
                    E.SetFlag("CanTrade", State: false);
                }
            }

            return base.FireEvent(E);
        }

        /// <summary>
        /// True when opening the trade screen with this creature would only report that it has
        /// nothing to trade.
        /// </summary>
        private static bool HasNothingToTrade(GameObject trader)
        {
            if (trader == null || trader.IsPlayerLed())
            {
                return false;
            }

            if (trader.Inventory == null)
            {
                return true;
            }

            GameObject player = The.Player;
            bool relevant = CanAcceptObjectEvent.Relevant(player);

            foreach (GameObject item in trader.Inventory.GetObjects())
            {
                if (TradeUI.ValidForTrade(item, trader, player, 1f, relevant))
                {
                    return false;
                }
            }

            return !AllowTradeWithNoInventoryEvent.Check(player, trader);
        }
    }
}
