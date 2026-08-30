using System;

namespace XRL.World.Parts.Skill
{
    /// <summary>
    /// Wary, sold by the Tactics tree. Supplies the `Bonus` term of the hidden-object search roll,
    /// which vanilla reads on every search and nothing has ever written.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The defect this exists for.</b> `Physics.Search()` runs every player turn over the current
    /// cell and its eight neighbours, and `Hidden` resolves it as
    /// `Bonus + Stat.Random(1, Searcher.Intelligence) >= Difficulty`. `Stat.Random(Low, High)` is
    /// `Rnd.Next(Low, High + 1)`, so the roll's ceiling is exactly the searcher's Intelligence — and
    /// `Hidden.Difficulty` defaults to <b>15</b>. A character at Intelligence 14 or below therefore
    /// **cannot ever** find a default-difficulty hidden object. Not unlikely: impossible. Filed
    /// upstream as #621 and closed NOT_PLANNED, so this is the only answer the fork will get. See
    /// #221.
    /// </para>
    /// <para>
    /// <b>It covers everything hidden, not only traps.</b> Three parts read the same `Bonus` off the
    /// same event: `Hidden` (8 authored blueprints at difficulty 15–23, Young Ivory among them),
    /// `HiddenRender` (`PondDown`, difficulty 2) and `EelSpawn`. Mines are not a separate path —
    /// `Miner.SetMineOrBomb` attaches `Hidden` at runtime with `12 + Mark * 3`, so a Mark III mine is
    /// difficulty 21. One bonus improves all of it, `PondDown` included, and no filter is possible
    /// from the searcher's side. That breadth is intended rather than tolerated.
    /// </para>
    /// <para>
    /// <b>Why the Tactics tree, which is not where the issue looked.</b> #221 proposed Tinkering or
    /// Customs and Folklore. Both are `Attribute="Intelligence"` — so either would have filed the fix
    /// for low-Intelligence characters under Intelligence, where the builds it exists for never look,
    /// and Customs and Folklore is joint-most-expensive at 150. Tactics is Agility, costs 50 to
    /// enter, and its existing powers are all about not being caught out: `Hurdle`, `Juke`,
    /// `Kickback`. Noticing an ambush is the same sentence as the rest of that tree.
    /// </para>
    /// <para>
    /// The roll is against Intelligence while the skill is filed under Agility, which reads oddly for
    /// a moment. Vanilla files a skill by the attribute the *skill* belongs to rather than the stat
    /// its rolls use, so nothing forces the pairing — and the fiction is not "you got cleverer", it
    /// is that you have learned what a tripwire looks like.
    /// </para>
    /// <para>
    /// <b>A flat bonus rather than the floor the issue wanted, and the arithmetic is why.</b> A floor
    /// — "roll as though your Intelligence were at least F" — can only be expressed here as
    /// `Bonus = F - Intelligence`, because the roll itself cannot be reached. That raises the
    /// *minimum* roll as well as the maximum, compressing the range to `[1 + F - INT, F]`, and it
    /// inverts the ordering: at F = 18 an Intelligence 10 character with this power finds a
    /// difficulty-15 object 40% of the time while an Intelligence 20 character without it manages
    /// 30%. Being *worse* at noticing traps for having bought Intelligence is not a thing to ship.
    /// A flat term moves everyone by the same amount and keeps the ordering intact.
    /// </para>
    /// <para>
    /// <b>+6 is chosen against the difficulty ladder, not picked.</b> It is the smallest value that
    /// takes the whole default tier off zero: at Intelligence 10 a difficulty-15 object needs a roll
    /// of 9 on 1d10, which is 20% per search rather than never. It deliberately does <i>not</i> make
    /// a Mark III mine at 21 reachable from Intelligence 10 — that one stays hard, which is the
    /// correct answer for the hardest thing on the ladder.
    /// </para>
    /// <para>
    /// <b>How the bonus reaches the event at all, which is the fragile part.</b> `DoSearching` builds
    /// the event and fires it at the cell in the same breath, so nothing can hand it a bonus from
    /// outside. What makes this reachable is that `Search()` passes `eSearched` **by reference**
    /// through all nine calls, so one Event object serves the current cell and its eight neighbours —
    /// and `Cell.FireEvent` iterates the cell's objects, of which the searcher is one. So this fires
    /// on the searcher's own cell, sets the term, and the value rides the reused event into every
    /// neighbour.
    /// </para>
    /// <para>
    /// The consequence, stated because it is a real limitation rather than a rounding error: for a
    /// hidden object in the searcher's <em>own</em> cell the ordering depends on where the searcher
    /// sits in `Cell.Objects`, so the bonus may or may not have been set when that object resolves.
    /// The eight neighbours are reliable, and they are the ones that matter — a hidden thing in your
    /// own cell has usually already gone off.
    /// </para>
    /// <para>
    /// Charter rule 5: no instance state, no Harmony, no reflection. The bonus is a `const`, so
    /// nothing is added to any save.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_TacticsWary : BaseSkill
    {
        /// <summary>
        /// The search bonus. `const` rather than a field so no save carries it — see rule 5, and
        /// `validate_mod.py`'s `serializable-shape` check, which is right to refuse the alternative.
        /// </summary>
        public const int SearchBonus = 6;

        public override void Register(GameObject Object, IEventRegistrar Registrar)
        {
            Registrar.Register("Searched");
            base.Register(Object, Registrar);
        }

        public override bool FireEvent(Event E)
        {
            if (E.ID == "Searched" && E.GetGameObjectParameter("Searcher") == ParentObject)
            {
                // Never lower a bonus somebody else set. Nothing in vanilla writes this term today,
                // but the event is shared across all nine cells of one search and a second writer
                // would be invisible here otherwise.
                if (E.GetIntParameter("Bonus") < SearchBonus)
                {
                    E.SetParameter("Bonus", SearchBonus);
                }
            }

            return base.FireEvent(E);
        }
    }
}
