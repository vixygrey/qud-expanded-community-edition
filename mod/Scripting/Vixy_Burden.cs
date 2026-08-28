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
    public class Vixy_Burden : IScribedPart
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

        /// <summary>
        /// Writes and reads nothing, symmetrically, so this part occupies no bytes in a save.
        /// </summary>
        /// <remarks>
        /// <para>
        /// <c>IScribedPart</c> does exactly one thing in each direction — <c>WriteNamedFields</c> and
        /// <c>ReadNamedFields</c> — and this class has no serialisable state, so what it writes is a
        /// field count of zero and nothing else. Suppressing both halves gives the same on-disk
        /// shape the class had before #497 and the same shape it has now, in every version, which is
        /// the point: there is no boundary between two formats, so nothing has to know where the
        /// boundary is.
        /// </para>
        /// <para>
        /// <b>That knowledge was the bug (#554).</b> This used to read nothing while still writing a
        /// block, gated on a version comparison — and a version cannot separate a save written by
        /// the released 2.7.0, which wrote nothing, from one written by an unreleased build after
        /// #497, which wrote a block. Both record 2.7.0. The reader then left a byte unconsumed, and
        /// an under-read is not contained: <c>IPart.Load</c> repositions to the end of the block only
        /// from inside its <c>catch</c>, so reading too little throws nothing and desynchronises
        /// every object after it in the zone.
        /// </para>
        /// <para>
        /// <b>#497 is not undone.</b> The class stays on the <c>IScribed</c> base, which is the part
        /// that is expensive to do later. When it gains a field, delete both overrides — and by then
        /// the version really will have moved, so nothing has to be inferred from one.
        /// </para>
        /// </remarks>
        public override void Write(GameObject Basis, SerializationWriter Writer)
        {
        }

        /// <summary>The other half of the pair above. Symmetry is the whole mechanism.</summary>
        public override void Read(GameObject Basis, SerializationReader Reader)
        {
        }
    }
}
