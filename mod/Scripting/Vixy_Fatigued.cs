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
    }
}
