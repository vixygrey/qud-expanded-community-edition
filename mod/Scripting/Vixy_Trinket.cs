using System;
using XRL.Messages;

namespace XRL.World.Parts
{
    /// <summary>
    /// Gives a trinket one small, ordinary action that does nothing but say what happened — the
    /// affordance that makes a trinket a trinket rather than a description with a weight.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Why any C# at all, given charter rule 5.</b> Rule 5 says to use the data where the game
    /// already does a thing in data, and I checked before writing this: all 1,371 part classes in
    /// <c>tools/qud-api.json</c> were searched for a generic, XML-configurable "perform a flavour
    /// action" part, and there is none. Vanilla gives each of its six trinkets a bespoke class —
    /// <c>Chair</c>, <c>Crayons</c>, <c>BubbleLevel</c>, <c>SpiralIron</c> — so there was no data
    /// route to prefer. See #603.
    /// </para>
    /// <para>
    /// <b>Why subclasses rather than XML attributes, which is not the shape I reached for first.</b>
    /// The obvious design was one part with <c>Verb</c> and <c>Message</c> set per blueprint. That
    /// costs three instance fields, and rule 5 is explicit that <c>[Serializable]</c> field layout
    /// is an identifier written into every save — renaming or removing one can break saves that
    /// already exist. <c>tools/validate_mod.py</c> flagged it, correctly. An expression-bodied
    /// member compiles to a get-only property with no backing storage, so the strings below reach
    /// no save at all, and the whole family holds zero instance state. #411 set that precedent with
    /// <c>VariantBlueprint => "Icy Vapor"</c>.
    /// </para>
    /// <para>
    /// The trade is real and worth naming: the flavour text lives in C# rather than in XML, which
    /// is the wrong direction for a data-first fork. It buys save stability, six classes of four
    /// lines each, and a shape closer to vanilla's — which gives every trinket its own class too.
    /// </para>
    /// <para>
    /// <b>These are deliberately incapable of doing anything.</b> The register the category runs on
    /// is *one small human thing with no mechanical payoff*, and its stated failure mode is
    /// trinkets that turn out to be secretly useful. So the base prints a message and spends a
    /// turn. There is no hook by which a subclass can affect a stat, move an object, or touch
    /// anything outside the message queue, and that limitation is the feature — a future trinket
    /// wanting a real mechanic needs its own part rather than an extra override here.
    /// </para>
    /// <para>
    /// <b>A log line, not a popup.</b> <c>MessageQueue.AddPlayerMessage</c> rather than
    /// <c>Popup.Show</c>: #603's neighbour #581 is the issue about Qud interrupting the player for
    /// things that do not warrant it, and shaking a snow globe is the clearest possible case of
    /// something that does not. Nothing here stops play.
    /// </para>
    /// <para>
    /// <b>On the object, not the actor.</b> <c>GetInventoryActionsEvent</c> is sent to the item
    /// itself, which is what is wanted: the action belongs to the trinket and travels with it, so
    /// one handed to a companion or left in a chest keeps it. The save-baked concern that sent
    /// <c>Vixy_LiquidGather</c> to <c>Vixy_PlayerParts</c> instead does not apply, because these
    /// are new blueprints — no existing save holds one that could miss out.
    /// </para>
    /// <para>
    /// <b>The turn is the price.</b> Vanilla charges a turn for sitting in a chair and nothing for
    /// pouring a drink, so there is precedent either way. A turn is the cheapest real cost the game
    /// has, and paying it is what separates a small deliberate moment from a free button.
    /// </para>
    /// <para>
    /// Charter rule 5 otherwise: no Harmony, no reflection, no I/O, and no instance state, so the
    /// save shape of every class here is empty and stays that way.
    /// </para>
    /// </remarks>
    [Serializable]
    public abstract class Vixy_Trinket : IScribedPart
    {
        /// <summary>
        /// The command these parts fire. Mod-prefixed because <c>InventoryActionEvent</c>
        /// dispatches by name and a collision with a vanilla command would silently run something
        /// else. Shared across the family, which is safe: the event is delivered to one object, and
        /// that object answers for itself.
        /// </summary>
        public const string CommandID = "Vixy_UseTrinket";

        /// <summary>The menu entry, lowercase and imperative — "shake", "ring", "turn over".</summary>
        protected abstract string Verb { get; }

        /// <summary>
        /// The line printed when the action is taken. Written the way Qud writes: second person,
        /// terse, physical, and finished — it reports what happened rather than inviting anything.
        /// </summary>
        protected abstract string Message { get; }

        /// <summary>
        /// Energy spent, in the usual thousand-per-turn units. One turn at base Quickness. A
        /// trinket that should be free can override this to <c>0</c>.
        /// </summary>
        protected virtual int Energy => 1000;

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade)
                || ID == GetInventoryActionsEvent.ID
                || ID == InventoryActionEvent.ID;
        }

        public override bool HandleEvent(GetInventoryActionsEvent E)
        {
            E.AddAction("Vixy_UseTrinket", Verb, CommandID, null, 'u', FireOnActor: false);
            return base.HandleEvent(E);
        }

        public override bool HandleEvent(InventoryActionEvent E)
        {
            if (E.Command == CommandID)
            {
                // Only the player has a message queue to read. A companion told to shake a snow
                // globe should still spend the turn, so the energy is charged either way.
                if (E.Actor != null && E.Actor.IsPlayer() && !string.IsNullOrEmpty(Message))
                {
                    MessageQueue.AddPlayerMessage(Message);
                }

                if (Energy > 0)
                {
                    E.Actor?.UseEnergy(Energy, "Item Trinket");
                }
            }

            return base.HandleEvent(E);
        }
    }

    /// <summary>Turn it over and watch it run out.</summary>
    [Serializable]
    public class Vixy_TrinketHourglass : Vixy_Trinket
    {
        protected override string Verb => "turn over";
        protected override string Message =>
            "You turn the hourglass over. The sand starts again.";
    }

    /// <summary>Look at your own face.</summary>
    [Serializable]
    public class Vixy_TrinketHandMirror : Vixy_Trinket
    {
        protected override string Verb => "look in";
        protected override string Message =>
            "You look at your own face a moment, and put the mirror away.";
    }

    /// <summary>Shake it and watch it settle.</summary>
    [Serializable]
    public class Vixy_TrinketSnowGlobe : Vixy_Trinket
    {
        protected override string Verb => "shake";
        protected override string Message =>
            "You shake the globe. The flecks lift, drift, and settle.";
    }

    /// <summary>Look through it at nothing in particular.</summary>
    [Serializable]
    public class Vixy_TrinketKaleidoscope : Vixy_Trinket
    {
        protected override string Verb => "look through";
        protected override string Message =>
            "You look through the kaleidoscope. The chips fall into an arrangement no one has seen.";
    }

    /// <summary>Spin it on a flat surface. It falls over.</summary>
    [Serializable]
    public class Vixy_TrinketSpinningTop : Vixy_Trinket
    {
        protected override string Verb => "spin";
        protected override string Message =>
            "You set the top going. It walks a slow circle and topples.";
    }

    /// <summary>Ring it. Nobody comes.</summary>
    [Serializable]
    public class Vixy_TrinketHandBell : Vixy_Trinket
    {
        protected override string Verb => "ring";
        protected override string Message => "You ring the bell. Nobody comes.";
    }
}
