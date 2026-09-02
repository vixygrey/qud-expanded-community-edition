using System;
using System.Collections.Generic;
using HistoryKit;
using XRL.Language;

namespace XRL.Annals
{
    /// <summary>
    /// A sultan recovers something they lost years earlier — the first event in this fork that
    /// answers another one.
    /// </summary>
    /// <remarks>
    /// <para>
    /// #731's first slice. That issue's complaint is that a sultan's biography reads as a shuffled
    /// list: the seventeen vanilla events are self-contained set-pieces, so nothing requires a prior
    /// cause or demands a consequence, and order conveys no meaning. This is one link, built to prove
    /// the shape before any of it is authored at scale.
    /// </para>
    /// <para>
    /// <b>The debt is structural, not a prose gesture.</b> <c>LoseItemAtTavern</c> does
    /// <c>RemoveEntityListItem("items", …)</c>, so the loss is recorded in the event's
    /// <c>removedListProperties</c> — a real, machine-readable fact about that sultan. This reads
    /// that item back and returns it with <c>AddEntityListItem</c>. The link can therefore be
    /// *verified* rather than asserted: the recovered name matches the lost one, which is what makes
    /// #731's causal-chain metric measurable instead of a matter of impression.
    /// </para>
    /// <para>
    /// <b>Subclassing <c>HistoricEvent</c> is extension, not replacement.</b> It is a public,
    /// non-abstract, <c>[Serializable]</c> class with a <c>virtual Generate()</c>, and vanilla's own
    /// seventeen are subclasses of it. Nothing about this touches
    /// <c>QudHistoryFactory.GenerateNewSultan</c>, which is the static method #731's body worried
    /// about having to replace.
    /// </para>
    /// <para>
    /// <b>And it cannot orphan a save, which is the question worth answering first for anything
    /// touching worldgen.</b> <c>HistoricEvent.Load</c> always constructs a plain
    /// <c>new HistoricEvent()</c> and reads the property dictionaries back into it — the subclass is
    /// never restored. So this type exists only during generation; the moment a game is saved, this
    /// is an ordinary event carrying its own baked text. Remove the mod and the history still loads,
    /// with these events intact and inert.
    /// </para>
    /// <para>
    /// Charter rule 5: no I/O, no network, no reflection, no Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_RecoverLostItem : HistoricEvent
    {
        /// <summary>Event-property key holding the thing that went missing.</summary>
        public const string ItemKey = "Vixy_recoveredItem";

        /// <summary>Event-property key holding the year it went missing.</summary>
        public const string LostYearKey = "Vixy_lostYear";

        /// <summary>
        /// The two inputs travel as event properties rather than as fields on this class.
        /// </summary>
        /// <remarks>
        /// <para>
        /// <b>Because the fields would be a lie about where the data lives.</b> Only <c>id</c>,
        /// <c>year</c>, <c>duration</c> and the property dictionaries are written by
        /// <c>HistoricEvent.Save</c>, so a field on a subclass reaches no save at all — while
        /// <c>validate_mod.py</c>'s <c>serializable-shape</c> check, reading only the
        /// <c>[Serializable]</c> attribute, quite reasonably says it does. Putting them in
        /// <c>eventProperties</c> makes the storage match what actually persists.
        /// </para>
        /// <para>
        /// <b>And they are written into the dictionary directly rather than through
        /// <c>SetEventProperty</c>, which is not a shortcut.</b> That method calls
        /// <c>ExpandString</c>, which needs the history context this event does not have until
        /// <c>ApplyEvent</c> runs — and an item's name is data, not a template. Expanding it would
        /// mangle any name containing angle brackets.
        /// </para>
        /// </remarks>
        public static Vixy_RecoverLostItem For(string item, long lostYear)
        {
            return new Vixy_RecoverLostItem
            {
                eventProperties = new Dictionary<string, string>
                {
                    { ItemKey, item },
                    { LostYearKey, lostYear.ToString() },
                },
            };
        }

        public override void Generate()
        {
            duration = 0L;

            string Item = GetEventProperty(ItemKey);
            if (Item.IsNullOrEmpty()) return;
            if (!long.TryParse(GetEventProperty(LostYearKey, "0"), out long LostYear)) return;

            AddEntityListItem("items", Item);

            long gone = Math.Max(1L, year - LostYear);
            string years = Grammar.Cardinal((int)Math.Min(gone, int.MaxValue));

            // <entity.name> and <entity.subjectPronoun> are vanilla's own tokens, left unexpanded
            // here exactly as CapturedByBandits leaves them - the gospel is expanded when it is read,
            // not when it is written.
            SetEventProperty(
                "gospel",
                "After " + years + " years, <entity.name> recovered " + Item
                    + ", which <entity.subjectPronoun> had lost. "
                    + "<entity.subjectPronoun.capitalize> did not say how.");

            SetEventProperty(
                "tombInscription",
                "What " + Grammar.MakePossessive("<entity.name>") + " hand let fall, "
                    + Grammar.MakePossessive("<entity.name>") + " hand took up again: " + Item + ".");

            // One of the two categories vanilla actually uses. Inventing a third would risk a value
            // nothing knows how to render.
            SetEventProperty("tombInscriptionCategory", "EnduresHardship");
        }
    }
}
