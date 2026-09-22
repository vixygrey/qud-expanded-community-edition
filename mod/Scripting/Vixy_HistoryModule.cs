using System.Collections.Generic;
using HistoryKit;
using XRL;
using XRL.Annals;
using XRL.CharacterBuilds;
using XRL.CharacterBuilds.Qud;

namespace QudExpandedCE
{
    /// <summary>
    /// Adds a later, record-only consequence to safe sultan-history events.
    ///
    /// Qud fires BOOTEVENT_AFTERINITIALIZESULTANHISTORY after it has generated and normalized
    /// sultan history, but before it builds worlds. The history therefore feeds world generation:
    /// this module must never alter an entity, site, faction, relic, region, or existing event.
    /// It appends only a gospel-bearing HistoricEvent to the sultan who escaped bandit captivity.
    ///
    /// This is deliberately separate from Vixy_NameFlavourModule. That module joins
    /// EmbarkInfo.modules early so character-creation name re-rolls can reach it, then the builder
    /// adds it again. A history append is not idempotent under that lifecycle. This module remains
    /// normally registered and also records an exactly-once game-state marker.
    /// </summary>
    public class Vixy_HistoryModule : AbstractEmbarkBuilderModule
    {
        private const string AppliedStateKey = "Vixy_HistoryEventsApplied";
        private const string BanditEscapeResponseKey = "Vixy_BanditEscapeResponse";

        private sealed class PlannedResponse
        {
            public HistoricEntity Sultan;
            public HistoricEvent Event;
        }

        public override object handleBootEvent(
            string id,
            XRLGame game,
            EmbarkInfo info,
            object element = null
        )
        {
            if (id != QudGameBootModule.BOOTEVENT_AFTERINITIALIZESULTANHISTORY
                || !(element is History history)
                || !Raven_Options.HistoryEvents
                || The.Game == null
                || The.Game.GetIntGameState(AppliedStateKey) != 0)
            {
                return element;
            }

            List<PlannedResponse> responses;
            try
            {
                responses = PlanResponses(history);
            }
            catch
            {
                // Planning reads only completed vanilla history. If a game update changes that
                // shape, leave the generated history untouched rather than failing world creation.
                return history;
            }

            foreach (PlannedResponse response in responses)
            {
                response.Sultan.ApplyEvent(response.Event, response.Event.year);
            }

            The.Game.SetIntGameState(AppliedStateKey, 1);
            return history;
        }

        private static List<PlannedResponse> PlanResponses(History history)
        {
            HistoricEntityList sultans = history.GetEntitiesWherePropertyEquals("type", "sultan");
            List<PlannedResponse> responses = new List<PlannedResponse>(sultans.Count);

            foreach (HistoricEntity sultan in sultans)
            {
                if (HasBanditEscapeResponse(sultan))
                {
                    continue;
                }

                HistoricEvent escape = FindBanditEscape(sultan);
                if (escape == null)
                {
                    continue;
                }

                long responseYear = escape.year + escape.duration + 1;
                if (responseYear >= sultan.lastYear)
                {
                    continue;
                }

                string name = sultan.GetEntityProperty("name", responseYear);
                if (string.IsNullOrEmpty(name))
                {
                    continue;
                }

                HistoricEvent response = new HistoricEvent
                {
                    year = responseYear,
                    eventProperties = new Dictionary<string, string>
                    {
                        {
                            "gospel",
                            "After escaping captivity among bandits, " + name
                                + " ruled with a vigilance born of that hardship."
                        },
                        { BanditEscapeResponseKey, escape.id.ToString() }
                    }
                };

                responses.Add(new PlannedResponse
                {
                    Sultan = sultan,
                    Event = response
                });
            }

            return responses;
        }

        private static bool HasBanditEscapeResponse(HistoricEntity sultan)
        {
            foreach (HistoricEvent existing in sultan.events)
            {
                if (existing.HasEventProperty(BanditEscapeResponseKey))
                {
                    return true;
                }
            }

            return false;
        }

        private static HistoricEvent FindBanditEscape(HistoricEntity sultan)
        {
            foreach (HistoricEvent existing in sultan.events)
            {
                if (existing is CapturedByBandits
                    && existing.GetEventProperty("tombInscriptionCategory") == "EnduresHardship")
                {
                    return existing;
                }
            }

            return null;
        }
    }
}
