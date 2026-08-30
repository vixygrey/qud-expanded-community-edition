using System;
using QudExpandedCE;
using XRL.UI;
using XRL.World.Effects;

namespace XRL.World.Parts
{
    /// <summary>
    /// Stops a charmed merchant handing over their shop for nothing. Beguile, proselytize or mask a
    /// shopkeep and they still show you everything and still like you — they just expect paying.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The exploit is one line of vanilla, and it is not a mistake in itself.</b>
    /// <c>TradeUI.ShowTradeScreen</c> opens with
    /// <c>bool flag = Trader.IsPlayerLed(); if (flag) { _costMultiple = 0f; }</c> — a follower's
    /// possessions are communal, which is right for a companion recruited over a long game and wrong
    /// for a shopkeep enchanted forty seconds ago. Five effects reach that line — <c>Beguiled</c>,
    /// <c>Proselytized</c>, <c>Lovesick</c>, <c>Rebuked</c>, <c>SlaveMask</c> — and none of them
    /// contains a single check for a merchant. See #563 — whose list of five is four effects plus
    /// one part, since <c>SlaveMask</c> is the mask's own part and <c>DomesticatedSlave</c> is the
    /// creature's state.
    /// </para>
    /// <para>
    /// <b>The seam, which I expected not to exist.</b> <c>TradeUI</c> is named in no <c>Base/</c> XML
    /// file, which is the shape <c>docs/LESSONS.md</c> records as "a mod's reach ends where nothing in
    /// XML names the object" — the wall #585 and #570 both died on. That lesson is about
    /// <i>substituting a class</i>, and this needs a <i>field</i>:
    /// </para>
    /// <code>
    /// public static float costMultiple = 1f;                      // :64  public, static, writable
    /// if (flag) { _costMultiple = 0f; }                           // :349 the exploit
    /// costMultiple = _costMultiple;                               // :351 assigned
    /// StartTradeEvent.Send(player, Trader, ...);                  // :420 fires here
    /// GetObjects(Trader, Objects[0], The.Player, costMultiple);   // :433 first use
    /// </code>
    /// <para>
    /// The event fires between the assignment and the first use, and <c>Send</c> dispatches to the
    /// actor before the trader — so a part on the player can write the field and the screen prices
    /// from the new value. Public member, no reflection, no Harmony, no vanilla code copied, and no
    /// blueprint merges at all. Attached through <c>Vixy_PlayerParts</c>, so it reaches saves that
    /// already exist.
    /// </para>
    /// <para>
    /// <b>What this deliberately does not do.</b> <c>costMultiple</c> multiplies every row
    /// (<c>Totals[i] *= costMultiple</c>), so it cannot express #563's designed rule — the guild's
    /// stock costs, the merchant's own boots do not. That distinction is marked per item as
    /// <c>_stock</c> by <c>GenericInventoryRestocker</c>, and nothing in reach reads it before
    /// <c>TradeUI:1415</c> clears it on transfer. So this restores the price and says nothing about
    /// ownership. It also leaves the three <c>WontSell</c> gates alone: those test
    /// <c>IsPlayerLed()</c> directly, so a charmed merchant's never-for-sale items stay purchasable —
    /// at cost, which is close to what charm ought to buy.
    /// </para>
    /// <para>
    /// <b>Containers are untouched, structurally rather than by a guard.</b> Every vanilla caller that
    /// passes <c>0f</c> is a container — <c>Container</c>, <c>InteriorContainer</c>, <c>PickItem</c>,
    /// and the one in <c>GameObject</c>. None of them is <c>IsPlayerLed</c>, so <c>flag</c> is false,
    /// so nothing was zeroed and <c>E.Companion</c> is false here. The merchant path is
    /// <c>Trade.cs:100</c>, which passes the default <c>1f</c> — which is why restoring <b>1f</b> is
    /// exactly undoing the companion rule rather than inventing a rate.
    /// </para>
    /// <para>
    /// <b>A genuinely recruited merchant keeps communal pricing</b>, which is the fourth checkbox on
    /// the issue. The discriminator is the five charm effects rather than <c>IsPlayerLed</c>, so a
    /// shopkeep who joined you the long way round is unaffected.
    /// </para>
    /// <para>
    /// Charter rule 5: no instance state, so nothing is added to the save. One event handler, no I/O,
    /// no reflection, no Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_MerchantOwnership : IScribedPart
    {
        /// <summary>
        /// What a charmed merchant's goods cost: vanilla's own default, undoing the zeroing rather
        /// than inventing a discount.
        /// </summary>
        /// <remarks>
        /// The conversation trade path (<c>Trade.cs:100</c>) calls <c>ShowTradeScreen(Trader)</c> and
        /// takes the <c>_costMultiple = 1f</c> default, so this is the rate an uncharmed merchant
        /// would have offered. A charm discount would be new content needing its own justification
        /// under charter rule 2, and vanilla gives charm no price benefit by design — the free shop
        /// is the companion rule leaking, not a discount somebody wrote.
        /// </remarks>
        private const float NormalRate = 1f;

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == StartTradeEvent.ID;
        }

        public override bool HandleEvent(StartTradeEvent E)
        {
            // E.Companion is TradeUI's own `flag` — Trader.IsPlayerLed() — so a false value means
            // nothing was zeroed and there is nothing to put back.
            if (
                E.Companion
                && Raven_Options.CharmedMerchantPrices
                && E.Trader != null
                && E.Trader.IsMerchant()
                && IsCharmed(E.Trader)
            )
            {
                TradeUI.costMultiple = NormalRate;
            }

            return base.HandleEvent(E);
        }

        /// <summary>
        /// True when this creature is following the player because of a charm rather than a choice.
        /// </summary>
        /// <remarks>
        /// Four effects and one part. #563 lists five effects and one of them is not an effect:
        /// <c>SlaveMask</c> is a part <c>DomesticatedSlave.cs:48</c> puts on the mask itself, and its
        /// job is to <i>clear</i> <c>PartyLeader</c> when the mask comes off. It appears in no XML at
        /// all. The creature-side state is <c>DomesticatedSlave</c>, which is what belongs here.
        ///
        /// Tested individually rather than through a shared base because they have none —
        /// <c>Beguiled</c> and <c>Proselytized</c> descend from different roots, and
        /// <c>DomesticatedSlave</c> is an <c>IBondedCompanion</c> part rather than an effect. A sixth
        /// door would have to be added by name, which is worth preferring to a looser test that might
        /// catch a genuine companion.
        /// </remarks>
        private static bool IsCharmed(GameObject who)
        {
            return who.HasEffect<Beguiled>()
                || who.HasEffect<Proselytized>()
                || who.HasEffect<Lovesick>()
                || who.HasEffect<Rebuked>()
                || who.HasPart<DomesticatedSlave>();
        }

        /// <summary>
        /// Writes and reads nothing, symmetrically, so this part occupies no bytes in a save. Same
        /// reasoning as <c>Vixy_Burden</c>; delete both overrides when it gains a field.
        /// </summary>
        public override void Write(GameObject Basis, SerializationWriter Writer)
        {
        }

        /// <summary>The other half of the pair above. Symmetry is the whole mechanism.</summary>
        public override void Read(GameObject Basis, SerializationReader Reader)
        {
        }
    }
}
