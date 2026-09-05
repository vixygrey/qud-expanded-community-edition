using System;
using XRL.World.Parts;

namespace XRL.World.Effects
{
    /// <summary>
    /// The readout for <see cref="Vixy_Fatigue"/>: one word on the active-effects line.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The meter had no readout at all.</b> `Vixy_Fatigue` is an `IPart`, and
    /// `AbilityBar.InternalUpdateActiveEffects` walks `Object.Effects` — parts never reach that line.
    /// So the only thing that had ever told me my fatigue was a one-off message at each band
    /// crossing, and those scroll away. #782.
    /// </para>
    /// <para>
    /// <b>The status bar is where this belongs and it is shut.</b> Hunger and thirst are not effects:
    /// `Stomach.FoodStatus()` is rendered directly by `Qud.UI/PlayerStatusBar.cs` line 333 and
    /// `XRL.UI/Sidebar.cs` line 1268. `StringDataType` is a *private* enum of exactly eight members,
    /// each with its own `UITextSkin` field; `Stomach` is fetched by `GetPart&lt;Stomach&gt;()` and its
    /// methods called by name; and no event is fired anywhere in `PlayerStatusBar`. There is nothing
    /// to register for and nothing to append to, so reaching it would need Harmony and charter rule 5
    /// closes it.
    /// </para>
    /// <para>
    /// <b>Vanilla does both, and the second half is open.</b> `Famished` is an ordinary `Effect` with
    /// a `Duration` and a coloured `GetDescription()`, so hunger appears twice — a continuous readout
    /// in the status bar and a chip on the effects line once it turns bad. Fatigue can have the chip.
    /// </para>
    /// <para>
    /// <b>One effect that renames itself, rather than four that swap.</b> `Vixy_Burdened` already
    /// does exactly this, and copying its shape means one serialisable class and no per-band churn.
    /// It carries no state of its own: the band is derived from the property bag on every refresh, so
    /// nothing here can disagree with the meter.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Fatigued : IScribedEffect
    {
        public Vixy_Fatigued()
        {
            DisplayName = "tired";
            // No countdown, as Vixy_Burdened: Effect does not decrement unless
            // UseStandardDurationCountdown is overridden to true, and Vixy_Fatigue owns removal.
            Duration = 9999;
        }

        /// <summary>
        /// Take the current band's word and colour.
        /// </summary>
        /// <remarks>
        /// Colours climb the way the band messages already do, and borrow vanilla's hunger vocabulary
        /// at the top: `Stomach.FoodStatus` reads `{{W|Hungry}}` then `{{R|Famished!}}`, so a player
        /// reading this line beside their food status sees the same escalation mean the same thing.
        /// </remarks>
        public void Refresh(GameObject Who)
        {
            int fatigue = Vixy_Fatigue.Get(Who);

            DisplayName = Vixy_Fatigue.BandFor(fatigue) switch
            {
                Vixy_Fatigue.Collapsing => "{{R|collapsing}}",
                Vixy_Fatigue.Exhausted => "{{r|exhausted}}",
                Vixy_Fatigue.Weary => "{{W|weary}}",
                _ => "{{y|tired}}",
            };
        }

        /// <summary>
        /// What this band actually costs, for the Show Effects screen.
        /// </summary>
        /// <remarks>
        /// <para>
        /// <b>Without this the screen printed <c>[effect details]</c></b>, which is
        /// <c>Effect.GetDetails</c>'s own placeholder. <c>GameObject.ShowActiveEffects</c> lists any
        /// effect whose <c>GetDescription()</c> is non-null and then prints its details; the base
        /// description returns <c>DisplayName</c>, so this effect was correctly listed and then
        /// correctly asked for details it did not have. <c>Vixy_Burdened</c> and <c>Vixy_Wound</c>
        /// both override it and this one never did.
        /// </para>
        /// <para>
        /// <b>Derived from the band rather than stored</b>, the same way <see cref="Refresh"/> is, so
        /// nothing here can disagree with the meter.
        /// </para>
        /// <para>
        /// <b>The consequences are read off the code, not summarised from the design.</b> Guttering
        /// is <c>Vixy_Gutter</c>, which reaches Mental Mutations, Physical Mutations, Skills and
        /// Maneuvers — so <em>abilities</em>, not <em>concentration</em> — from Weary upward. Travel
        /// refusal is <c>Vixy_Fatigue.HandleEvent(CanTravelEvent)</c> at Exhausted and above, and it
        /// is named plainly because it is a hard capability loss rather than a chance of one.
        /// Collapse is <c>Vixy_Fatigue.Collapse</c>, above Collapsing only.
        /// </para>
        /// <para>
        /// <b>Tired says what it does rather than reading as an oversight.</b> It carries no penalty
        /// at all — its one mechanical effect is that it is the gate <c>Vixy_Dream.Earned</c> checks,
        /// so a full uninterrupted sleep from here can dream. Leaving the line empty would look like
        /// the defect this fixes.
        /// </para>
        /// <para>
        /// <c>Campfire.ProcessEffectDescription</c> runs <c>InitCap</c> and <c>CapAfterNewlines</c>
        /// over the result, so each line is sentence-cased by the caller.
        /// </para>
        /// </remarks>
        public override string GetDetails()
        {
            int fatigue = Vixy_Fatigue.Get(Object);
            string cost = Vixy_Fatigue.BandFor(fatigue) switch
            {
                Vixy_Fatigue.Collapsing =>
                    "Abilities gutter out often.\n"
                    + "You may collapse where you stand.\n"
                    + "You cannot travel long distances.",
                Vixy_Fatigue.Exhausted =>
                    "Abilities gutter out more often.\n"
                    + "You cannot travel long distances.",
                Vixy_Fatigue.Weary =>
                    "Abilities occasionally gutter out.",
                _ =>
                    "No penalty yet.\n"
                    + "Sleeping through from here may bring a dream.",
            };
            return cost + "\n" + Position(fatigue);
        }

        /// <summary>
        /// Where in the current band the meter is sitting, in words.
        /// </summary>
        /// <remarks>
        /// <para>
        /// <b>The band alone is a very slow readout.</b> `Accrue` takes hundredths and `BaseAccrual`
        /// is 22, so unhurried play is 0.22 fatigue an action — which makes `tired` and `weary`
        /// **909 actions** each, `exhausted` 682 and `collapsing` 227. Nine hundred actions reading
        /// one unchanging word is most of a game day, and the band-crossing message that would have
        /// placed me scrolled away long before. #853.
        /// </para>
        /// <para>
        /// <b>Words rather than a number or a percentage.</b> The meter's imprecision is deliberate
        /// — §51.5d puts a word on the effects line rather than a figure precisely so fatigue is
        /// read rather than counted — and a percentage here would promise a resolution the rest of
        /// the design declines to offer.
        /// </para>
        /// <para>
        /// <b>Thirds, computed rather than tabulated</b>, because the bands are not the same width:
        /// 200, 200, 150 and 50. A fixed table of cut points would have to be corrected every time
        /// one moved, and #821 moved them all once already.
        /// </para>
        /// <para>
        /// <b>The multiply comes before the divide, and that is load-bearing.</b>
        /// `(fatigue - floor) * 3 / span` in that order keeps the thirds honest; dividing first
        /// truncates to zero for the whole band and the reading would never move — the integer trap
        /// `docs/LESSONS.md` records from `4 * RestQuality / 10`, which cost a design tier. The
        /// `Math.Min` catches the one value that lands exactly on the ceiling, `Max` itself.
        /// </para>
        /// </remarks>
        private static string Position(int Fatigue)
        {
            int band = Vixy_Fatigue.BandFor(Fatigue);
            int ceiling;
            string next;
            switch (band)
            {
                case Vixy_Fatigue.Collapsing:
                    ceiling = Vixy_Fatigue.Max;
                    next = null;
                    break;
                case Vixy_Fatigue.Exhausted:
                    ceiling = Vixy_Fatigue.Collapsing;
                    next = "collapse";
                    break;
                case Vixy_Fatigue.Weary:
                    ceiling = Vixy_Fatigue.Exhausted;
                    next = "exhaustion";
                    break;
                default:
                    band = Vixy_Fatigue.Tired;
                    ceiling = Vixy_Fatigue.Weary;
                    next = "weariness";
                    break;
            }

            int third = Math.Min(2, (Fatigue - band) * 3 / (ceiling - band));
            if (third == 0) return "You are not far into this.";
            if (third == 1) return "You are well into this.";
            return next == null
                ? "You are about to drop."
                : "You are on the edge of " + next + ".";
        }
    }
}
