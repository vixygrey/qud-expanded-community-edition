using System;

namespace XRL.World.Parts
{
    /// <summary>
    /// A gate does not stay open. It swings shut once nothing is standing in it.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Qud closes nothing behind you. There is no auto-close anywhere in the game — no field for it,
    /// and nothing sets a door closed except a deliberate action — so a gate you walk through stays
    /// swinging for the rest of the run. See #631.
    /// </para>
    /// <para>
    /// <b>The fiction is vanilla's own, in the descriptions.</b> A brinestalk gate is <i>"shaved into
    /// pickets and set across an iron-latched rail"</i> and an iron gate is <i>"set across a latched
    /// rail"</i>. A latched gate swings shut and catches; that is what a latch is for. Nothing here
    /// needed inventing — charter rule 2 is satisfied by reading the two blueprints this part goes
    /// on.
    /// </para>
    /// <para>
    /// <b>Gates only, and that is the whole scope line.</b> <c>Gate</c> is already a clean subtype of
    /// <c>Door</c> that vanilla overrides into something recognisably different — you can see through
    /// it (<c>OccludingWhileClosed="false"</c>), shoot through it (<c>AllowMissiles</c>) and fly over
    /// it (<c>Flyover</c>). Auto-closing interior doors would fight tactical play, where leaving a
    /// door open to shoot through is a real decision. A gate closed behind you costs nothing, because
    /// a closed gate is still a firing line.
    /// </para>
    /// <para>
    /// <b>It shuts every open gate, not only the one I walked through.</b> That is broader than the
    /// issue's title and it is deliberate. Closing precisely <em>behind me</em> means remembering
    /// which gate a creature passed through, which is an instance field on a
    /// <c>[Serializable]</c> part and so a permanent addition to every save's layout — what
    /// <c>docs/STYLEGUIDE.md</c> §1 and <c>validate_mod.py</c>'s <c>serializable-shape</c> ask be a
    /// considered decision. The two behaviours almost never differ: gates generate closed, so an open
    /// one is nearly always one somebody just walked through. Paying a save field forever to
    /// distinguish them was the worse trade.
    /// </para>
    /// <para>
    /// <b>Closing does not contain anything, and the feature is not pretending to.</b>
    /// <c>Door.HandleEvent(EnteredCellEvent)</c> has <em>any combat object</em> open a closed door by
    /// walking into its cell, so a shut gate stops nothing that can walk. Livestock still wander out.
    /// What this buys is that the village looks like somebody lives in it, and followers are never
    /// stranded, because they open it themselves.
    /// </para>
    /// <para>
    /// <b>Deferred to end of turn because it has to be.</b> <c>AttemptClose</c> refuses while
    /// anything in the cell <c>BlocksClosing</c>, and the leaving-cell events all fire before the
    /// move completes — so closing there would always be closing on top of somebody.
    /// <c>Silent: true</c> matters for the same reason: the refusal messages fire on
    /// <c>gameObject.IsPlayer()</c> regardless of who asked, so a player standing in a gateway would
    /// otherwise be told it cannot be closed, once per turn, forever.
    /// </para>
    /// <para>
    /// <para>
    /// Reads <c>Door.Open</c> rather than <c>bOpen</c>: the latter compiles and is marked
    /// <c>[Obsolete("mod compat, will be removed after Q2 2024")]</c>, so it is a warning today
    /// and a broken build later. <c>compile_scripting.py</c> reports warnings, which is how this
    /// was caught.
    /// </para>
    /// <para>
    /// <b>No option, under charter rule 6.</b> An option earns its place where a reasonable
    /// player could want the mod without that part. A gate that shuts itself changes no number,
    /// no mechanic and no interaction - it cannot even keep anything in - so nobody would turn
    /// it off, and a switch nobody uses costs a line in the menu, a helptext to keep true and a
    /// branch to carry forever. It shipped with one in #631 and it was removed in #663.
    /// </para>
    /// <para>
    /// Charter rule 5: one end-of-turn check calling a public method on a vanilla part. No I/O, no
    /// reflection, no Harmony, no state.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_SelfClosingGate : IScribedPart
    {
        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == SingletonEvent<EndTurnEvent>.ID;
        }

        public override bool HandleEvent(EndTurnEvent E)
        {
            Door door = ParentObject.GetPart<Door>();

            if (door != null && door.Open)
            {
                door.AttemptClose(
                    null,
                    UsePopups: false,
                    UsePopupsForFailures: false,
                    IgnoreMobility: false,
                    IgnoreSpecialConditions: false,
                    FromMove: false,
                    Silent: true
                );
            }

            return base.HandleEvent(E);
        }
    }
}
