using System;
using XRL.World.Effects;
using QudExpandedCE;

namespace XRL.World.Parts
{
    /// <summary>
    /// Drives the graded burden bands. Recomputes the player's load each turn and keeps the
    /// matching <c>Vixy_Burdened</c> effect on them.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Shaped after vanilla's own arrangement: <c>Inventory</c> is a part that checks load on
    /// <c>TurnTick</c> and applies the <c>Overburdened</c> effect. Doing the same means the band
    /// shows in the effects list, which matters for a system whose whole point is making weight
    /// legible.
    /// </para>
    /// <para>
    /// Player-only, matching vanilla: <c>GameObject.IsOverburdened()</c> opens with
    /// <c>if (!IsPlayerControlled()) return false;</c>, so no NPC is ever burdened at any load.
    /// Extending bands to every creature would be a large behavioural change and a per-turn cost
    /// on every actor.
    /// </para>
    /// <para>
    /// Charter rule 5: no instance state, so nothing is added to the save. The band is derived
    /// from carried weight every tick and read back off the effect.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Burden : IPart
    {
        public override bool WantTurnTick() => true;

        public override void TurnTick(long TimeTick, int Amount)
        {
            Refresh();
            base.TurnTick(TimeTick, Amount);
        }

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == CarryingCapacityChangedEvent.ID;
        }

        public override bool HandleEvent(CarryingCapacityChangedEvent E)
        {
            Refresh();
            return base.HandleEvent(E);
        }

        private void Refresh()
        {
            GameObject who = ParentObject;
            if (who == null || !who.IsPlayerControlled())
            {
                return;
            }

            if (!Raven_Options.BurdenGradient
                || Vixy_Burdened.BandFor(Vixy_Burdened.LoadPercent(who)) == Vixy_Burdened.None)
            {
                who.RemoveEffect<Vixy_Burdened>();
                return;
            }

            Vixy_Burdened current = who.GetEffect<Vixy_Burdened>();
            if (current == null)
            {
                who.ApplyEffect(new Vixy_Burdened());
                return;
            }

            // The effect stores nothing, so this is how a band change reaches the stat shifts and
            // the display name. Cheap: two integer reads and at most two stat writes.
            current.Refresh();
        }
    }
}
