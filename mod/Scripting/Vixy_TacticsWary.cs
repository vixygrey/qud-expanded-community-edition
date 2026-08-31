using System;
using System.Collections.Generic;
using XRL.Messages;
using XRL.UI;

namespace XRL.World.Parts.Skill
{
    /// <summary>
    /// Wary: a second look at the cell you just stepped into, and the ones around it, carrying a
    /// bonus vanilla's own search never supplies.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>This is the second attempt, and the first one shipped inert.</b> #717 put a part on the
    /// player registering <c>"Searched"</c>, on the reading that the searcher would receive the
    /// event it was firing. It never did: <c>Cell.AddObject</c> calls <c>physics.EnterCell(this)</c>
    /// — inside which <c>Search()</c> runs — <em>before</em> <c>Objects.Add(Object)</c>, so at the
    /// moment of the search the mover has left one cell's list and not yet joined the next. It was
    /// in the dispatch set of no cell at all. Withdrawn in #720 and recorded in
    /// <c>docs/LESSONS.md</c> as <i>"a dispatch list is a snapshot"</i>. See #722.
    /// </para>
    /// <para>
    /// <b>The door is four lines further down the same method.</b>
    /// </para>
    /// <code>
    /// physics.EnterCell(this)          // Search() runs here. Mover in NEITHER cell.
    /// Objects.Add(Object)              // mover joins the cell
    /// Object.ProcessEnterCell(...)
    /// Object.ProcessEnteredCell(...)   // EnteredCellEvent - mover present
    /// </code>
    /// <para>
    /// So a part handling <c>EnteredCellEvent</c> is standing in the cell and can do what
    /// <c>Physics.Search()</c> does — with the <c>Bonus</c> set.
    /// </para>
    /// <para>
    /// <b>The bonus belongs to whoever fires the event, which is what #717 had backwards.</b>
    /// <c>Physics.DoSearching</c> builds <c>Event.New("Searched", "Searcher", ParentObject)</c> and
    /// sets no bonus at all; <c>Hidden</c> then reads
    /// <c>E.GetIntParameter("Bonus") + Stat.Random(1, Intelligence) &gt;= Difficulty</c>. Nothing
    /// consults the searcher. Firing a second <c>Searched</c> with the term set puts the number
    /// where <c>Hidden</c> actually looks.
    /// </para>
    /// <para>
    /// <b>It is a second roll, not an improved one — accepted deliberately.</b> Vanilla's bonus-0
    /// search has already run inside <c>EnterCell</c> and cannot be suppressed from here, so the
    /// real chance is <c>1 − P(both fail)</c>, which <c>Hidden</c>'s <c>!Found</c> guard makes a
    /// clean union. Below the difficulty a hidden thing carries, <c>Stat.Random(1, Intelligence)</c>
    /// <em>cannot</em> succeed — which is the defect #221 was filed about — so for exactly the
    /// characters this exists for, the double roll and the intended single roll are the same number.
    /// The overshoot lands only on characters who could already find things, and it errs toward
    /// noticing a mine rather than missing one. #722 weighed lowering the bonus or gating the second
    /// roll on the first being hopeless; both trade a real cost for exactness against a difficulty
    /// the searcher has no way to know.
    /// </para>
    /// <para>
    /// <b>Mines are the population that matters, and none of them declares this in a blueprint.</b>
    /// Eight vanilla blueprints carry <c>Hidden</c> — lagroots, beths, young ivory, yonderbrush. But
    /// <c>Miner.SetMineOrBomb</c> does <c>RequirePart&lt;Hidden&gt;().Difficulty = 12 + Mark * 3</c>
    /// when a mine is laid, and vanilla ships Marks 1 to 3, so a laid field sits at difficulty 15,
    /// 18 or 21. <c>LayMineGoal</c> and <c>Submerged</c> add it at runtime too. A part added when an
    /// object is created is declared by no blueprint, so counting declarations understates this
    /// badly.
    /// </para>
    /// <para>
    /// <b>Three parts read the bonus</b> — <c>Hidden</c>, <c>HiddenRender</c> and <c>EelSpawn</c> —
    /// so all three get the second roll. That is wanted: an eel lurking in water is exactly the
    /// hidden threat this is named for.
    /// </para>
    /// <para>
    /// Charter rule 5: no instance state, one event handler, no Harmony and no reflection. Every
    /// member used is public with vanilla callers.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_TacticsWary : BaseSkill
    {
        /// <summary>
        /// Added to the searching roll. A `const`, because instance state on a `[Serializable]` type
        /// is written into every save and `validate_mod.py`'s `serializable-shape` check is right to
        /// refuse the alternative.
        /// </summary>
        public const int SearchBonus = 6;

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == EnteredCellEvent.ID;
        }

        public override bool HandleEvent(EnteredCellEvent E)
        {
            // System moves are bookkeeping - zone rebuilds and the like - rather than the player
            // walking somewhere and looking around. Everything else searches, including teleports
            // and being dragged: arriving somewhere unexpectedly is when you would most want to
            // notice what is already there.
            if (!E.System && E.Object == ParentObject && ParentObject.IsPlayer())
            {
                Look(E.Cell);
            }

            return base.HandleEvent(E);
        }

        /// <summary>
        /// Fires a bonused <c>Searched</c> at <paramref name="Here"/> and its neighbours.
        /// </summary>
        /// <remarks>
        /// The shape is <c>Physics.Search</c>'s: the cell plus <c>GetLocalAdjacentCells()</c>, one
        /// event object reused across all of them. The <c>HasObjectWithRegisteredEvent</c> guard is
        /// <c>DoSearching</c>'s own and is what keeps this from dispatching nine times a step
        /// through cells where nothing is listening.
        /// </remarks>
        private void Look(Cell Here)
        {
            if (Here == null)
            {
                return;
            }

            Event searched = Event.New("Searched", "Searcher", ParentObject);
            searched.SetParameter("Bonus", SearchBonus);

            int listening = Sweep(Here, searched);

            List<Cell> adjacent = Here.GetLocalAdjacentCells();
            for (int i = 0; i < adjacent.Count; i++)
            {
                listening += Sweep(adjacent[i], searched);
            }

            Report(listening);
        }

        /// <summary>Fires at one cell, and reports whether anything there was listening.</summary>
        private static int Sweep(Cell C, Event Searched)
        {
            if (C == null || !C.HasObjectWithRegisteredEvent("Searched"))
            {
                return 0;
            }

            C.FireEvent(Searched);
            return 1;
        }

        /// <summary>
        /// Says what the search did, behind Debug Internals.
        /// </summary>
        /// <remarks>
        /// <b>This exists because the previous attempt could not be tested.</b> `Hidden` sets
        /// `Found = true` and prints nothing, so a successful search is indistinguishable from a
        /// search that never ran — which is exactly how #717 reached a merge while doing nothing.
        /// #722's last checkbox asks for a printed confirmation that the handler fired, and a
        /// permanent one costs a player nothing: `Options.DebugInternals` is off by default and is
        /// vanilla's own convention for this, used by `Physics`, `Brain` and `Look`.
        ///
        /// It reports cells that had a listener rather than things revealed, because that is the
        /// honest measure of whether this ran: zero listeners means nothing was hidden nearby, and a
        /// nonzero count with nothing appearing means the rolls failed, which is a different fact
        /// from the handler being dead.
        /// </remarks>
        private static void Report(int Listening)
        {
            if (Options.DebugInternals)
            {
                MessageQueue.AddPlayerMessage(
                    "{{K|[Wary] searched, " + Listening + " cell(s) with something listening}}");
            }
        }
    }
}
