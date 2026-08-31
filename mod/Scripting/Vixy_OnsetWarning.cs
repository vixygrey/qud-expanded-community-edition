using System;
using QudExpandedCE;
using XRL.World.Effects;

namespace XRL.World.Parts
{
    /// <summary>
    /// Says that a disease onset has begun, that its deadline is close, and that it has been fought
    /// off — three moments vanilla either never announces or announces only conditionally.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Sometimes the game never tells you there was anything to win.</b> All three onsets run the
    /// same twelve lines: every 1200 turns, <c>MakeSave("Toughness", 13)</c>; a pass is
    /// <c>Stage--</c>, a fail is <c>Stage++</c>; cured at <c>Stage &lt;= -2</c>, contracted at
    /// <c>Stage &gt;= 3 || Days &gt;= 5</c>. Both of the *good news* messages are gated on
    /// <c>SawSore</c>, and <c>SawSore</c> is only set when a save is **failed**:
    /// </para>
    /// <code>
    /// if (Object.MakeSave("Toughness", 13, …)) {
    ///     Stage--;
    ///     if (SawSore &amp;&amp; Stage &gt; -2 &amp;&amp; Object.IsPlayer())
    ///         AddPlayerMessage("You feel a bit better.");
    /// } else {
    ///     Stage++;
    ///     if (Stage &lt; 3) { …AddPlayerMessage("Your throat feels sore."); SawSore = true; }
    /// }
    /// </code>
    /// <para>
    /// So two consecutive opening passes reach <c>Stage -2</c>, the cure branch runs, and its message
    /// is gated on <c>SawSore</c> too — 2,400 turns of contest, resolved, in complete silence. The
    /// silence is *caused* by having done well on the first roll. See #581.
    /// </para>
    /// <para>
    /// <b>And the last thing it tells you can be that you are improving.</b> <c>Days &gt;= 5</c> is
    /// tested after the improvement message and does not care what <c>Stage</c> is. Three saves won
    /// in a row can end with *"You feel a bit better."* and the disease landing in the same tick,
    /// because the clock ran out one step short of the cure. That is not a missing message but an
    /// actively misleading one, produced by correct code.
    /// </para>
    /// <para>
    /// <b>The deadline is the thing worth saying, because it is the thing you can act on.</b> All
    /// three onsets accept Yuckwheat and honey for a save bonus — +3 for glotrot, +2 for the others —
    /// and glotrot has an outright cure in flaming ick. <c>Bonus</c> is consumed when a save actually
    /// uses it, so it is a one-shot a player can deliberately stack before a roll. The game ships
    /// three counters to this and never says the clock is running.
    /// </para>
    /// <para>
    /// <b>Only messages, because <c>GetDetails()</c> is closed.</b> The issue asked for the status
    /// screen line to carry the trend. Both call sites invoke <c>GetDetails()</c> directly on the
    /// effect — <c>CharacterStatusScreen.HandleHighlightEffect</c> and <c>GameObject</c> — and
    /// <c>Campfire.ProcessEffectDescription</c> is pure string substitution, so there is no hook.
    /// Reaching it would mean Harmony, or substituting a subclass and thereby writing a mod type into
    /// save data that an uninstall could not read back. Neither is worth a line of flavour text, and
    /// a deadline belongs in a message at the moment it matters rather than on a screen you would
    /// have to think to open.
    /// </para>
    /// <para>
    /// <b>Stage magnitude is deliberately absent.</b> It is the part that would need
    /// <c>GetDetails()</c>, and day 2 versus day 5 matters more than stage 1 versus stage 2, because
    /// only one of them is a deadline.
    /// </para>
    /// <para>
    /// <b>Three diseases, and that is all of them.</b> <c>ApplyEffectEvent.Check</c> is called with
    /// <c>"Disease"</c> six times and <c>"DiseaseOnset"</c> three, with named checks for Glotrot,
    /// Ironshank and Monochrome twice each. <c>Ill</c> does not gate on <c>Disease</c> and is not one.
    /// </para>
    /// <para>
    /// <b>No polling and no per-effect knowledge.</b> <c>ApplyEffectEvent</c> reaches the object an
    /// onset is being applied to, so the start is heard rather than discovered; and
    /// <c>GetDiseaseOnsetEvent.GetFor</c> is vanilla's own central lookup, which all three onsets
    /// answer and which <c>BoostedImmunity</c> and <c>Campfire</c> already use. Nothing here
    /// enumerates effects.
    /// </para>
    /// <para>
    /// Charter rule 5: no instance state — the counters are int properties, as
    /// <c>validate_mod.py</c>'s <c>serializable-shape</c> check requires — no Harmony, no reflection,
    /// and no vanilla record touched.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_OnsetWarning : IPart
    {
        /// <summary>1 while an onset this part has announced is still running.</summary>
        public const string ActiveProperty = "Vixy_OnsetActive";

        /// <summary>The highest <c>Days</c> already reported on.</summary>
        public const string DayProperty = "Vixy_OnsetDay";

        /// <summary>
        /// The day the deadline warning fires, of the five an onset lasts.
        /// </summary>
        /// <remarks>
        /// One day of grace. `Days` is incremented before the `Days >= 5` test, so warning as it
        /// reaches 4 leaves a full 1200-turn tick to eat Yuckwheat or find honey — long enough to
        /// act on and short enough to feel like a deadline.
        /// </remarks>
        public const int WarnOnDay = 4;

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == ApplyEffectEvent.ID;
        }

        public override void Register(GameObject Object, IEventRegistrar Registrar)
        {
            Registrar.Register("EndTurn");
            base.Register(Object, Registrar);
        }

        /// <summary>
        /// Announces an onset as it takes hold — the moment vanilla is silent about.
        /// </summary>
        /// <remarks>
        /// Returning <c>base.HandleEvent(E)</c> and never <c>false</c>: this event is a veto for the
        /// effect being applied, and this part only listens.
        /// </remarks>
        public override bool HandleEvent(ApplyEffectEvent E)
        {
            if (E.Name == "DiseaseOnset" && ParentObject.IsPlayer() && Raven_Options.OnsetWarning)
            {
                ParentObject.SetIntProperty(ActiveProperty, 1);
                ParentObject.SetIntProperty(DayProperty, 0);
                Say(E.Effect, Line.Begins);
            }

            return base.HandleEvent(E);
        }

        public override bool FireEvent(Event E)
        {
            if (E.ID == "EndTurn" && ParentObject.GetIntProperty(ActiveProperty) > 0)
            {
                Tick();
            }

            return base.FireEvent(E);
        }

        /// <summary>
        /// Reports a new day, or the end of the onset.
        /// </summary>
        /// <remarks>
        /// Polling `Days` rather than trying to run inside the effect's own tick, so nothing here
        /// depends on whether this part's `EndTurn` handler is registered before or after the
        /// effect's. Worst case a line lands one turn late, which against a 1200-turn cadence is
        /// invisible — and #717 shipped inert because I reasoned about dispatch order instead of
        /// arranging not to care about it.
        /// </remarks>
        private void Tick()
        {
            Effect onset = GetDiseaseOnsetEvent.GetFor(ParentObject);

            if (onset == null)
            {
                Finish();
                return;
            }

            if (!Raven_Options.OnsetWarning)
            {
                return;
            }

            int days = DaysOf(onset);
            if (days <= ParentObject.GetIntProperty(DayProperty))
            {
                return;
            }

            ParentObject.SetIntProperty(DayProperty, days);
            if (days == WarnOnDay)
            {
                Say(onset, Line.Deadline);
            }
        }

        /// <summary>
        /// The onset is over. Says so only when it was beaten.
        /// </summary>
        /// <remarks>
        /// When it was lost instead, the player is now carrying the disease itself and vanilla has
        /// already shown its own popup and journal entry — that moment was never the quiet one.
        /// </remarks>
        private void Finish()
        {
            ParentObject.SetIntProperty(ActiveProperty, 0);
            ParentObject.SetIntProperty(DayProperty, 0);

            if (!Raven_Options.OnsetWarning)
            {
                return;
            }

            if (ParentObject.HasEffect<Glotrot>())
            {
                return;
            }

            if (ParentObject.HasEffect<Ironshank>() || ParentObject.HasEffect<Monochrome>())
            {
                return;
            }

            Say(null, Line.Cleared);
        }

        /// <summary>
        /// `Days` off whichever onset this is. The three share no base class, so this is three
        /// casts rather than one field read.
        /// </summary>
        private static int DaysOf(Effect Onset)
        {
            return Onset switch
            {
                GlotrotOnset g => g.Days,
                IronshankOnset i => i.Days,
                MonochromeOnset m => m.Days,
                _ => 0,
            };
        }

        /// <summary>Which of the three lines to say.</summary>
        private enum Line
        {
            Begins,
            Deadline,
            Cleared,
        }

        /// <summary>
        /// Says the line for this onset and moment, in the body part that onset belongs to.
        /// </summary>
        /// <remarks>
        /// Terse and physical, and never a number: the test #581 sets is *would the character know
        /// this*. Someone five days into a rotting tongue knows they are running out of time; nobody
        /// knows their own save DC. The `Cleared` line is deliberately generic — by the time it
        /// fires the effect is gone and there is nothing left to read the body part off.
        /// </remarks>
        private static void Say(Effect Onset, Line Moment)
        {
            string text = Moment switch
            {
                Line.Cleared => "Whatever had hold of you loosens its grip.",
                Line.Begins => Onset switch
                {
                    GlotrotOnset => "Something is wrong with your throat.",
                    IronshankOnset => "Something is wrong with your legs.",
                    MonochromeOnset => "Something is wrong with your eyes.",
                    _ => null,
                },
                _ => Onset switch
                {
                    GlotrotOnset => "Your tongue is blackening at the root.",
                    IronshankOnset => "Your knees are setting like cooling iron.",
                    MonochromeOnset => "The colour is draining out of the world.",
                    _ => null,
                },
            };

            if (!text.IsNullOrEmpty())
            {
                IComponent<GameObject>.AddPlayerMessage("{{r|" + text + "}}");
            }
        }
    }
}
