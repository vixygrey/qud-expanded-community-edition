using System;
using System.Collections.Generic;
using HistoryKit;
using XRL;
using XRL.Annals;
using XRL.CharacterBuilds;
using XRL.CharacterBuilds.Qud;

namespace QudExpandedCE
{
    /// <summary>
    /// Reads the sultan history the game has just generated and answers one of its loose ends.
    /// </summary>
    /// <remarks>
    /// <para>
    /// #731's first slice. The route is <c>BOOTEVENT_AFTERINITIALIZESULTANHISTORY</c>, which
    /// <c>QudSpecificBootHandlersModule</c> fires immediately after generation and whose return value
    /// it assigns straight back to <c>game.sultanHistory</c>:
    /// </para>
    /// <para>
    /// <code>
    /// game.sultanHistory = QudHistoryFactory.GenerateNewSultanHistory();
    /// game.sultanHistory = QudHistoryFactory.GenerateVillageEraHistory(game.sultanHistory);
    /// game.sultanHistory = info.fireBootEvent(BOOTEVENT_INITIALIZESULTANHISTORY, game, game.sultanHistory);
    /// game.sultanHistory = info.fireBootEvent(BOOTEVENT_AFTERINITIALIZESULTANHISTORY, game, game.sultanHistory);
    /// </code>
    /// </para>
    /// <para>
    /// <b>Nothing in vanilla handles either hook</b>, checked across all fifteen modules declared in
    /// vanilla's <c>EmbarkModules.xml</c>: the only references to those constants are the definition
    /// and the firing site. This is a purpose-built extension point going spare, so #731's worry
    /// about replacing a static generator does not arise — and this is the same raise of charter rule
    /// 5 as <c>Vixy_NameFlavourModule</c>, already argued and already accepted, rather than a new one.
    /// </para>
    /// <para>
    /// <b>A separate module from the name one, deliberately, and guarded as well.</b>
    /// <c>Vixy_NameFlavourModule</c> adds itself to <c>info.modules</c> early so the name re-roll
    /// reaches it, and <c>EmbarkBuilder</c> later does
    /// <c>embarkInfo.modules.AddRange(modules.Where(m =&gt; m.enabled))</c> with no duplicate check —
    /// so that module is in the list twice and its handler fires twice per boot event. Its two
    /// handlers survive it because one sets a property and the other returns a name, which are
    /// idempotent by luck rather than by design. <b>Appending history events is not idempotent</b>:
    /// run twice, it doubles everything. So this lives in its own module, which never joins the list
    /// early, <em>and</em> carries a game-state guard, because a separate module only protects until
    /// somebody adds a second handler to it.
    /// </para>
    /// <para>
    /// <b>Game state is available by then</b>, which is why the guard can live there:
    /// <c>INITIALIZEGAMESTATESINGLETONS</c> is step 9 of the boot sequence and
    /// <c>INITIALIZEHISTORY</c> is step 12.
    /// </para>
    /// <para>
    /// <b>Fail toward vanilla.</b> #731's P8: a mod that breaks worldgen breaks it at the least
    /// recoverable moment in the game. Everything here is wrapped, and any failure returns the
    /// history exactly as generated. There is nothing to roll back, because the only mutation is
    /// appending events to a list that vanilla has already finished with.
    /// </para>
    /// <para>
    /// Charter rule 5: no I/O, no network, no reflection, no Harmony.
    /// </para>
    /// </remarks>
    public class Vixy_HistoryModule : AbstractEmbarkBuilderModule
    {
        /// <summary>Marks the pass as done, so a second firing cannot double the events.</summary>
        public const string DoneKey = "Vixy_HistoryPassDone";

        /// <summary>How long after the loss the recovery can fall, in years.</summary>
        public const int SoonestAfter = 2;

        /// <summary>The far end of that window.</summary>
        public const int LatestAfter = 14;

        public override object handleBootEvent(
            string id,
            XRLGame game,
            EmbarkInfo info,
            object element = null
        )
        {
            if (id != QudGameBootModule.BOOTEVENT_AFTERINITIALIZESULTANHISTORY)
            {
                return base.handleBootEvent(id, game, info, element);
            }

            if (!(element is History history) || game == null || !Raven_Options.SultanDebts)
            {
                return base.handleBootEvent(id, game, info, element);
            }

            if (game.GetIntGameState(DoneKey) != 0)
            {
                return base.handleBootEvent(id, game, info, element);
            }
            game.SetIntGameState(DoneKey, 1);

            try
            {
                DischargeDebts(history);
            }
            catch (Exception e)
            {
                // Fail toward vanilla: the history is whatever the generator made of it.
                MetricsManager.LogError("Vixy_HistoryModule could not add recovery events", e);
            }

            return base.handleBootEvent(id, game, info, element);
        }

        /// <summary>Gives back, once per sultan, something they were recorded as losing.</summary>
        /// <remarks>
        /// <para>
        /// <c>GetEntitiesWherePropertyEquals("type", "sultan")</c> is vanilla's own way of finding
        /// them — <c>QudHistoryFactory</c> uses it to hang cult names off each sultan.
        /// </para>
        /// <para>
        /// <b>Once per sultan rather than once per loss</b>, so a sultan who lost three things does
        /// not spend three of their eight events getting them back. The point is that a life has a
        /// thread running through it, not that nothing is ever finally lost.
        /// </para>
        /// <para>
        /// <b>The recovery must land inside the life it belongs to.</b> A year past the sultan's last
        /// recorded event would read as happening after they were done, so the window is clamped and
        /// the recovery is skipped when there is no room — a sultan who lost something in their last
        /// years keeps the loss, which is the right answer anyway.
        /// </para>
        /// </remarks>
        private static void DischargeDebts(History history)
        {
            foreach (HistoricEntity sultan in history.GetEntitiesWherePropertyEquals("type", "sultan"))
            {
                if (sultan?.events == null || sultan.events.Count == 0) continue;

                long last = sultan.events[sultan.events.Count - 1].year;

                foreach (HistoricEvent lost in new List<HistoricEvent>(sultan.events))
                {
                    if (lost.removedListProperties == null) continue;
                    if (!lost.removedListProperties.TryGetValue("items", out List<string> items)) continue;
                    if (items == null || items.Count == 0) continue;

                    long soonest = lost.year + SoonestAfter;
                    if (soonest > last) continue;

                    long when = Math.Min(last, lost.year + history.Random(SoonestAfter, LatestAfter));

                    sultan.ApplyEvent(Vixy_RecoverLostItem.For(items[0], lost.year), when);
                    break;
                }
            }
        }
    }
}
