using System.Collections.Generic;
using HistoryKit;
using XRL;
using XRL.Annals;
using XRL.CharacterBuilds;
using XRL.CharacterBuilds.Qud;
using XRL.World;

namespace QudExpandedCE
{
    /// <summary>
    /// Adds later, record-only consequences to safe sultan-history events.
    ///
    /// Qud fires BOOTEVENT_AFTERINITIALIZESULTANHISTORY after it has generated and normalized
    /// sultan history, but before it builds worlds. The history therefore feeds world generation:
    /// this module must never alter an entity, site, faction, relic, region, or existing event.
    /// It appends only gospel-bearing HistoricEvents that answer eligible vanilla experiences.
    /// This is deliberately separate from Vixy_NameFlavourModule. That module joins
    /// EmbarkInfo.modules early so character-creation name re-rolls can reach it, then the builder
    /// adds it again. A history append is not idempotent under that lifecycle. This module remains
    /// normally registered and also records an exactly-once game-state marker.
    /// </summary>
    public class Vixy_HistoryModule : AbstractEmbarkBuilderModule
    {
        private const string AppliedStateKey = "Vixy_HistoryEventsApplied";
        private const string BanditEscapeResponseKey = "Vixy_BanditEscapeResponse";
        private const string ChallengeSultanResponseKey = "Vixy_ChallengeSultanResponse";
        private const string SecretRitualResponseKey = "Vixy_SecretRitualResponse";
        private const string InspirationResponseKey = "Vixy_InspiringExperienceResponse";
        private const string UnderWeirdSkyResponseKey = "Vixy_UnderWeirdSkyResponse";

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
            List<PlannedResponse> responses = new List<PlannedResponse>(sultans.Count * 5);

            foreach (HistoricEntity sultan in sultans)
            {
                PlanBanditEscapeResponse(sultan, responses);
                PlanChallengeSultanResponse(sultan, responses);
                PlanInspirationResponse(sultan, responses);
                PlanSecretRitualResponse(sultan, responses);
                PlanUnderWeirdSkyResponse(history, sultan, responses);
            }

            return responses;
        }

        private static void PlanBanditEscapeResponse(
            HistoricEntity sultan,
            List<PlannedResponse> responses
        )
        {
            if (HasResponse(sultan, BanditEscapeResponseKey))
            {
                return;
            }

            HistoricEvent escape = FindBanditEscape(sultan);
            if (escape == null)
            {
                return;
            }

            long responseYear = escape.year + escape.duration + 1;
            if (responseYear >= sultan.lastYear)
            {
                return;
            }

            string name = sultan.GetEntityProperty("name", responseYear);
            if (string.IsNullOrEmpty(name))
            {
                return;
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

        private static void PlanInspirationResponse(
            HistoricEntity sultan,
            List<PlannedResponse> responses
        )
        {
            if (HasResponse(sultan, InspirationResponseKey))
            {
                return;
            }

            HistoricEvent inspiration = FindInspiringExperience(sultan, out string element);
            if (inspiration == null)
            {
                return;
            }

            long responseYear = inspiration.year + inspiration.duration + 1;
            if (responseYear >= sultan.lastYear)
            {
                return;
            }

            string name = sultan.GetEntityProperty("name", responseYear);
            if (string.IsNullOrEmpty(name))
            {
                return;
            }

            HistoricEvent response = new HistoricEvent
            {
                year = responseYear,
                eventProperties = new Dictionary<string, string>
                {
                    {
                        "gospel",
                        "After an experience awakened in " + name
                            + " a lasting fascination with " + element + ", " + name
                            + " let that memory guide every later judgment."
                    },
                    { InspirationResponseKey, inspiration.id.ToString() }
                }
            };

            responses.Add(new PlannedResponse
            {
                Sultan = sultan,
                Event = response
            });
        }

        private static void PlanSecretRitualResponse(
            HistoricEntity sultan,
            List<PlannedResponse> responses
        )
        {
            if (HasResponse(sultan, SecretRitualResponseKey))
            {
                return;
            }

            HistoricEvent ritual = FindAcceptedSecretRitual(sultan, out string faction);
            if (ritual == null)
            {
                return;
            }

            long responseYear = ritual.year + ritual.duration + 1;
            if (responseYear >= sultan.lastYear)
            {
                return;
            }

            string name = sultan.GetEntityProperty("name", responseYear);
            string factionName = Faction.GetFormattedName(faction);
            if (string.IsNullOrEmpty(name) || string.IsNullOrEmpty(factionName))
            {
                return;
            }

            HistoricEvent response = new HistoricEvent
            {
                year = responseYear,
                eventProperties = new Dictionary<string, string>
                {
                    {
                        "gospel",
                        "After a clan of " + factionName + " welcomed " + name
                            + " into its secret rite, " + name
                            + " measured every later judgment against the clan's hidden precepts."
                    },
                    { SecretRitualResponseKey, ritual.id.ToString() }
                }
            };

            responses.Add(new PlannedResponse
            {
                Sultan = sultan,
                Event = response
            });
        }

        private static void PlanChallengeSultanResponse(
            HistoricEntity sultan,
            List<PlannedResponse> responses
        )
        {
            if (HasResponse(sultan, ChallengeSultanResponseKey))
            {
                return;
            }

            HistoricEvent challenge = FindEligibleChallengeSultan(sultan);
            if (challenge == null)
            {
                return;
            }

            long responseYear = challenge.year + challenge.duration + 1;
            string name = sultan.GetEntityProperty("name", responseYear);
            if (!IsRendered(name))
            {
                return;
            }

            HistoricEvent response = new HistoricEvent
            {
                year = responseYear,
                eventProperties = new Dictionary<string, string>
                {
                    {
                        "gospel",
                        "After prevailing in a challenge to the crown, " + name
                            + " treated every later act of rule as proof of " + name
                            + "'s legitimacy."
                    },
                    { ChallengeSultanResponseKey, challenge.id.ToString() }
                }
            };

            responses.Add(new PlannedResponse
            {
                Sultan = sultan,
                Event = response
            });
        }

        private static void PlanUnderWeirdSkyResponse(
            History history,
            HistoricEntity sultan,
            List<PlannedResponse> responses
        )
        {
            if (HasResponse(sultan, UnderWeirdSkyResponseKey))
            {
                return;
            }

            HistoricEvent apparition = FindEligibleUnderWeirdSky(
                history,
                sultan,
                out string name,
                out string location,
                out string color,
                out string cognomen,
                out long responseYear
            );
            if (apparition == null)
            {
                return;
            }

            HistoricEvent response = new HistoricEvent
            {
                year = responseYear,
                eventProperties = new Dictionary<string, string>
                {
                    {
                        "gospel",
                        "After the people of " + location + " beheld " + name
                            + " beneath a sky of " + color + ", raised a monument, and called "
                            + name + " " + cognomen
                            + ", that apparition shaped every later telling of " + name
                            + "'s legend."
                    },
                    { UnderWeirdSkyResponseKey, apparition.id.ToString() }
                }
            };

            responses.Add(new PlannedResponse
            {
                Sultan = sultan,
                Event = response
            });
        }

        private static bool HasResponse(HistoricEntity sultan, string responseKey)
        {
            foreach (HistoricEvent existing in sultan.events)
            {
                if (existing.HasEventProperty(responseKey))
                {
                    return true;
                }
            }

            return false;
        }

        private static bool IsEarlierSource(HistoricEvent candidate, HistoricEvent earliest)
        {
            return earliest == null
                || candidate.year < earliest.year
                || (candidate.year == earliest.year && candidate.id < earliest.id);
        }

        private static string SnapshotValue(
            HistoricEntitySnapshot snapshot,
            string property
        )
        {
            return snapshot.properties.TryGetValue(property, out string value) ? value : null;
        }

        private static HistoricEntity ResolveUniqueEntity(
            History history,
            string property,
            string value
        )
        {
            HistoricEntityList matches = history.GetEntitiesWherePropertyEquals(property, value);
            return matches.Count == 1 ? matches.entities[0] : null;
        }

        private static bool IsRendered(string value)
        {
            return !string.IsNullOrEmpty(value)
                && value.IndexOf('<') < 0
                && value.IndexOf('%') < 0
                && value.IndexOf('=') < 0;
        }

        private static int CountOccurrences(List<string> values, string value)
        {
            int count = 0;
            foreach (string candidate in values)
            {
                if (candidate == value)
                {
                    count++;
                }
            }

            return count;
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

        private static HistoricEvent FindInspiringExperience(
            HistoricEntity sultan,
            out string element
        )
        {
            HistoricEvent earliest = null;
            element = null;

            foreach (HistoricEvent existing in sultan.events)
            {
                if (!(existing is InspiringExperience)
                    || existing.GetEventProperty("tombInscriptionCategory")
                        != "HasInspiringExperience")
                {
                    continue;
                }

                List<string> addedElements = existing.GetListProperties("elements");
                if (addedElements == null
                    || addedElements.Count != 1
                    || string.IsNullOrEmpty(addedElements[0]))
                {
                    continue;
                }

                if (IsEarlierSource(existing, earliest))
                {
                    earliest = existing;
                    element = addedElements[0];
                }
            }

            return earliest;
        }

        private static HistoricEvent FindAcceptedSecretRitual(
            HistoricEntity sultan,
            out string faction
        )
        {
            HistoricEvent earliest = null;
            faction = null;
            HistoricEntitySnapshot finalSnapshot = sultan.GetSnapshotAtYear(sultan.lastYear);
            List<string> finalLikedFactions = finalSnapshot.GetList("likedFactions");

            foreach (HistoricEvent existing in sultan.events)
            {
                if (!(existing is SecretRitual)
                    || existing.GetEventProperty("tombInscriptionCategory") != "LearnsSecret")
                {
                    continue;
                }

                List<string> addedFactions = existing.GetListProperties("likedFactions");
                if (addedFactions == null
                    || addedFactions.Count != 1
                    || string.IsNullOrEmpty(addedFactions[0])
                    || !finalLikedFactions.Contains(addedFactions[0]))
                {
                    continue;
                }

                if (IsEarlierSource(existing, earliest))
                {
                    earliest = existing;
                    faction = addedFactions[0];
                }
            }

            return earliest;
        }

        private static HistoricEvent FindEligibleChallengeSultan(HistoricEntity sultan)
        {
            HistoricEvent earliest = null;

            foreach (HistoricEvent existing in sultan.events)
            {
                if (!(existing is ChallengeSultan))
                {
                    continue;
                }

                string category = existing.GetEventProperty("tombInscriptionCategory");
                bool crowned = category == "CrownedSultan"
                    && existing.GetEntityProperty("isSultan") == "true";
                if (!crowned && category != "Slays")
                {
                    continue;
                }

                long responseYear = existing.year + existing.duration + 1;
                if (responseYear >= sultan.lastYear)
                {
                    continue;
                }

                if (IsEarlierSource(existing, earliest))
                {
                    earliest = existing;
                }
            }

            return earliest;
        }

        private static HistoricEvent FindEligibleUnderWeirdSky(
            History history,
            HistoricEntity sultan,
            out string name,
            out string location,
            out string color,
            out string cognomen,
            out long responseYear
        )
        {
            HistoricEvent earliest = null;
            name = null;
            location = null;
            color = null;
            cognomen = null;
            responseYear = 0;

            foreach (HistoricEvent existing in sultan.events)
            {
                if (!(existing is UnderWeirdSky)
                    || existing.GetEventProperty("tombInscriptionCategory") != "DoesSomethingRad")
                {
                    continue;
                }

                List<string> addedColors = existing.GetListProperties("colors");
                List<string> addedCognomens = existing.GetListProperties("cognomen");
                string candidateColor = addedColors != null && addedColors.Count == 1
                    ? addedColors[0]
                    : null;
                string candidateCognomen = addedCognomens != null && addedCognomens.Count == 1
                    ? addedCognomens[0]
                    : null;
                string candidateLocationName = existing.GetEntityProperty("location");
                long candidateResponseYear = existing.year + existing.duration + 1;
                string candidateName = sultan.GetEntityProperty("name", existing.year);
                string candidateRegionName = sultan.GetEntityProperty("region", existing.year);
                if (!IsRendered(candidateColor)
                    || !IsRendered(candidateCognomen)
                    || !IsRendered(candidateLocationName)
                    || !IsRendered(candidateName)
                    || !IsRendered(candidateRegionName)
                    || candidateResponseYear >= sultan.lastYear)
                {
                    continue;
                }

                HistoricEntity candidateLocation = ResolveUniqueEntity(
                    history,
                    "name",
                    candidateLocationName
                );
                HistoricEntity candidateRegion = ResolveUniqueEntity(
                    history,
                    "name",
                    candidateRegionName
                );
                if (candidateLocation == null || candidateRegion == null)
                {
                    continue;
                }

                HistoricEntitySnapshot locationSnapshot = candidateLocation.GetSnapshotAtYear(
                    candidateLocation.lastYear
                );
                HistoricEntitySnapshot regionSnapshot = candidateRegion.GetSnapshotAtYear(
                    candidateRegion.lastYear
                );
                if (SnapshotValue(locationSnapshot, "type") != "location"
                    || SnapshotValue(locationSnapshot, "region") != candidateRegionName
                    || SnapshotValue(regionSnapshot, "type") != "region"
                    || !regionSnapshot.GetList("locations").Contains(candidateLocationName)
                    || CountOccurrences(locationSnapshot.GetList("monuments"), candidateName) != 1)
                {
                    continue;
                }

                if (IsEarlierSource(existing, earliest))
                {
                    earliest = existing;
                    name = candidateName;
                    location = candidateLocationName;
                    color = candidateColor;
                    cognomen = candidateCognomen;
                    responseYear = candidateResponseYear;
                }
            }

            return earliest;
        }
    }
}
