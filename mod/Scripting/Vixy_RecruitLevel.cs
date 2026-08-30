using System;

namespace XRL.World.Conversations.Parts
{
    /// <summary>
    /// Appends the recruit's level to the water ritual's join choice, so the tag reads
    /// <c>[250 reputation] [level 14]</c>.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The price is built from their level and stops saying so exactly where it matters.</b>
    /// <c>WaterRitualJoinParty.Awake</c> sets
    /// <c>Math.Max(50, 200 + (Speaker.Level - Player.Level) * 12)</c> — <c>REPUTATION_BASE_UNIT</c>
    /// is 50 and the factor is a quarter of it — so the number I am charged is an encoding of the
    /// level difference <em>only above the floor</em>. At thirteen levels below me the price is a
    /// flat 50 and encodes nothing at all, which is most late-game recruiting. #592 argued this half
    /// reveals nothing the transaction does not already imply; that is true for a strong recruit and
    /// false for every weak one.
    /// </para>
    /// <para>
    /// <b>Appending to a tag that vanilla assigns and then refuses.</b>
    /// <c>WaterRitualJoinParty.HandleEvent(GetChoiceTagEvent)</c> writes <c>E.Tag = …</c> outright
    /// and returns <c>false</c>, which reads as final and is not:
    /// <c>IConversationElement.HandleEvent</c> discards each part's return value and stops only when
    /// <c>E.HandlePartDispatch</c> says so. Parts after it still run. So this reads whatever is
    /// there and appends, and the ordering it depends on is the one thing here worth a test.
    /// </para>
    /// <para>
    /// <b>Deliberately not an <c>IWaterRitualPart</c>.</b> That base would supply matching
    /// <c>Lowlight</c> and <c>Numeric</c> colours — and its
    /// <c>HandleEvent(IsElementVisibleEvent)</c> returns its own <c>Visible</c> field, which
    /// defaults to <c>false</c>. Inheriting it to borrow two colour properties would have hidden
    /// vanilla's join choice outright. A plain <c>IConversationPart</c> wanting one event cannot
    /// reach the visibility vote at all.
    /// </para>
    /// <para>
    /// Hence the fixed <c>{{K|…}}</c>: vanilla's tag recolours with affordability and this does not
    /// track it, so a colour that never matches reads as a separate annotation rather than as a
    /// price that failed to dim. It is the register <c>Description</c> already uses for
    /// <c>Weight:</c>.
    /// </para>
    /// <para>
    /// Charter rule 5: no instance state, one event handler, no Harmony and no reflection. The part
    /// merges onto vanilla's <c>JoinPartyChoice</c>; nothing is replaced.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_RecruitLevel : IConversationPart
    {
        public override bool WantEvent(int ID, int Propagation)
        {
            return base.WantEvent(ID, Propagation) || ID == GetChoiceTagEvent.ID;
        }

        public override bool HandleEvent(GetChoiceTagEvent E)
        {
            GameObject speaker = The.Speaker;
            if (speaker == null)
            {
                return base.HandleEvent(E);
            }

            if (!E.Tag.IsNullOrEmpty())
            {
                E.Tag += " ";
            }

            E.Tag += "{{K|[level " + speaker.Stat("Level") + "]}}";

            return base.HandleEvent(E);
        }
    }
}
