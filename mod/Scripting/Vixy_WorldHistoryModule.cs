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
    /// Moves or creates eligible historical relics in structured history before vanilla builds
    /// the world from it. Every change must update the relic, location, containing region, and
    /// visible response together so the chronicle, physical relic, and quest describe one fact.
    /// </summary>
    public class Vixy_WorldHistoryModule : AbstractEmbarkBuilderModule
    {
        private const string AppliedStateKey = "Vixy_WorldHistoryEventsApplied";
        private const string BattleItemResponseKey = "Vixy_BattleItemDedicationResponse";
        private const string ForgeItemResponseKey = "Vixy_ForgeItemDedicationResponse";
        private const string MarryGiftResponseKey = "Vixy_MarryGiftDedicationResponse";
        private const string MeetFactionResponseKey = "Vixy_MeetFactionCompactResponse";

        private sealed class PlannedTransfer
        {
            public HistoricEntity Sultan;
            public HistoricEntity Destination;
            public HistoricEntity Region;
            public HistoricEvent SultanEvent;
            public HistoricEvent DestinationEvent;
            public HistoricEvent RegionEvent;
        }

        private sealed class PlannedCompact
        {
            public HistoricEntity Sultan;
            public HistoricEntity Destination;
            public HistoricEntity Region;
            public long ResponseYear;
            public HistoricEvent ItemEvent;
            public HistoricEvent SultanEvent;
            public HistoricEvent DestinationEvent;
            public HistoricEvent RegionEvent;
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
                || !Raven_Options.WorldHistoryEvents
                || The.Game == null
                || The.Game.GetIntGameState(AppliedStateKey) != 0)
            {
                return element;
            }

            List<PlannedTransfer> transfers;
            List<PlannedCompact> compacts;
            try
            {
                transfers = PlanTransfers(history);
                compacts = PlanCompacts(history);
            }
            catch
            {
                // Planning is read-only. An unfamiliar future history shape must leave vanilla's
                // completed history intact rather than risking a partial relic placement.
                return history;
            }

            foreach (PlannedTransfer transfer in transfers)
            {
                // Apply the visible response last. Vanilla only sees its marker after both
                // destination records contain the relic that the response removes from the sultan.
                transfer.Region.ApplyEvent(transfer.RegionEvent, transfer.RegionEvent.year);
                transfer.Destination.ApplyEvent(
                    transfer.DestinationEvent,
                    transfer.DestinationEvent.year
                );
                transfer.Sultan.ApplyEvent(transfer.SultanEvent, transfer.SultanEvent.year);
            }

            ApplyCompacts(history, compacts);

            The.Game.SetIntGameState(AppliedStateKey, 1);
            return history;
        }

        private static void ApplyCompacts(History history, List<PlannedCompact> compacts)
        {
            foreach (PlannedCompact compact in compacts)
            {
                // The response becomes visible only after the new relic and both ownership indexes
                // describe the same placement.
                HistoricEntity item = history.CreateEntity(compact.ResponseYear);
                item.ApplyEvent(compact.ItemEvent, compact.ItemEvent.year);
                compact.Region.ApplyEvent(compact.RegionEvent, compact.RegionEvent.year);
                compact.Destination.ApplyEvent(
                    compact.DestinationEvent,
                    compact.DestinationEvent.year
                );
                compact.Sultan.ApplyEvent(compact.SultanEvent, compact.SultanEvent.year);
            }
        }

        private static List<PlannedTransfer> PlanTransfers(History history)
        {
            HistoricEntityList sultans = history.GetEntitiesWherePropertyEquals("type", "sultan");
            List<PlannedTransfer> transfers = new List<PlannedTransfer>(sultans.Count * 3);

            foreach (HistoricEntity sultan in sultans)
            {
                PlanBattleItemDedication(history, sultan, transfers);
                PlanForgeItemDedication(history, sultan, transfers);
                PlanMarryGiftDedication(history, sultan, transfers);
            }

            return transfers;
        }

        private static List<PlannedCompact> PlanCompacts(History history)
        {
            HistoricEntityList sultans = history.GetEntitiesWherePropertyEquals("type", "sultan");
            List<PlannedCompact> compacts = new List<PlannedCompact>(sultans.Count);
            HashSet<string> plannedItemNames = new HashSet<string>();

            foreach (HistoricEntity sultan in sultans)
            {
                PlanMeetFactionCompact(history, sultan, plannedItemNames, compacts);
            }

            return compacts;
        }

        private static void PlanMeetFactionCompact(
            History history,
            HistoricEntity sultan,
            HashSet<string> plannedItemNames,
            List<PlannedCompact> compacts
        )
        {
            if (HasResponse(sultan, MeetFactionResponseKey))
            {
                return;
            }

            HistoricEvent meeting = FindEligibleMeetFaction(
                history,
                sultan,
                plannedItemNames,
                out string item,
                out string baseItemName,
                out string locationName,
                out HistoricEntity location,
                out HistoricEntity region,
                out string faction,
                out string element,
                out int period,
                out long responseYear,
                out string sultanName,
                out string revealedRegionName
            );
            if (meeting == null || !plannedItemNames.Add(item))
            {
                return;
            }

            HistoricEvent itemEvent = new HistoricEvent
            {
                year = responseYear,
                duration = 0,
                entityProperties = new Dictionary<string, string>
                {
                    { "itemType", "Curio" },
                    { "baseName", baseItemName },
                    { "article", "the" },
                    { "name", item },
                    { "descriptionAdj", "historic" },
                    { "descriptionNoun", "compact" },
                    { "period", period.ToString() }
                },
                addedListProperties = new Dictionary<string, List<string>>
                {
                    { "elements", new List<string> { element } },
                    { "likedFactions", new List<string> { faction } }
                }
            };
            HistoricEvent response = new HistoricEvent
            {
                year = responseYear,
                duration = 0,
                eventProperties = new Dictionary<string, string>
                {
                    {
                        "gospel",
                        "After " + sultanName + " befriended "
                            + Faction.GetFormattedName(faction) + " at " + locationName
                            + ", they enshrined " + item
                            + " there as a token of their compact."
                    },
                    { MeetFactionResponseKey, meeting.id.ToString() },
                    { "revealsItem", item },
                    { "revealsItemLocation", locationName },
                    { "revealsItemRegion", revealedRegionName }
                }
            };

            compacts.Add(new PlannedCompact
            {
                Sultan = sultan,
                Destination = location,
                Region = region,
                ResponseYear = responseYear,
                ItemEvent = itemEvent,
                SultanEvent = response,
                DestinationEvent = DestinationEvent(responseYear, item),
                RegionEvent = DestinationEvent(responseYear, item)
            });
        }

        private static void PlanBattleItemDedication(
            History history,
            HistoricEntity sultan,
            List<PlannedTransfer> transfers
        )
        {
            if (HasResponse(sultan, BattleItemResponseKey))
            {
                return;
            }

            HistoricEvent battle = FindEligibleBattleItem(
                history,
                sultan,
                out string item,
                out string battlefieldName,
                out HistoricEntity battlefield,
                out HistoricEntity region,
                out long responseYear,
                out string sultanName,
                out string revealedRegionName
            );
            if (battle == null)
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
                        "After winning renown at the Battle of " + battlefieldName + ", "
                            + sultanName + " dedicated " + item
                            + " at the site, so the relic would remain where its legend began."
                    },
                    { BattleItemResponseKey, battle.id.ToString() },
                    { "revealsItem", item },
                    { "revealsItemLocation", battlefieldName },
                    { "revealsItemRegion", revealedRegionName }
                },
                removedListProperties = OneItemList(item)
            };

            transfers.Add(new PlannedTransfer
            {
                Sultan = sultan,
                Destination = battlefield,
                Region = region,
                SultanEvent = response,
                DestinationEvent = DestinationEvent(responseYear, item),
                RegionEvent = DestinationEvent(responseYear, item)
            });
        }

        private static void PlanForgeItemDedication(
            History history,
            HistoricEntity sultan,
            List<PlannedTransfer> transfers
        )
        {
            if (HasResponse(sultan, ForgeItemResponseKey))
            {
                return;
            }

            HistoricEvent forge = FindEligibleForgeItem(
                history,
                sultan,
                out string item,
                out string destinationName,
                out HistoricEntity destination,
                out HistoricEntity region,
                out long responseYear,
                out string sultanName,
                out string revealedRegionName
            );
            if (forge == null)
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
                        "After " + item + " was forged, " + sultanName
                            + " dedicated it at " + destinationName
                            + ", so the relic would remain there as a testament to its making."
                    },
                    { ForgeItemResponseKey, forge.id.ToString() },
                    { "revealsItem", item },
                    { "revealsItemLocation", destinationName },
                    { "revealsItemRegion", revealedRegionName }
                },
                removedListProperties = OneItemList(item)
            };

            transfers.Add(new PlannedTransfer
            {
                Sultan = sultan,
                Destination = destination,
                Region = region,
                SultanEvent = response,
                DestinationEvent = DestinationEvent(responseYear, item),
                RegionEvent = DestinationEvent(responseYear, item)
            });
        }

        private static void PlanMarryGiftDedication(
            History history,
            HistoricEntity sultan,
            List<PlannedTransfer> transfers
        )
        {
            if (HasResponse(sultan, MarryGiftResponseKey))
            {
                return;
            }

            HistoricEvent marriage = FindEligibleMarryGift(
                history,
                sultan,
                out string item,
                out string destinationName,
                out HistoricEntity destination,
                out HistoricEntity region,
                out long responseYear,
                out string sultanName,
                out string revealedRegionName
            );
            if (marriage == null)
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
                        "After receiving " + item + " as a wedding gift, " + sultanName
                            + " dedicated it at " + destinationName
                            + ", where it stood as a testament to the marriage alliance."
                    },
                    { MarryGiftResponseKey, marriage.id.ToString() },
                    { "revealsItem", item },
                    { "revealsItemLocation", destinationName },
                    { "revealsItemRegion", revealedRegionName }
                },
                removedListProperties = OneItemList(item)
            };

            transfers.Add(new PlannedTransfer
            {
                Sultan = sultan,
                Destination = destination,
                Region = region,
                SultanEvent = response,
                DestinationEvent = DestinationEvent(responseYear, item),
                RegionEvent = DestinationEvent(responseYear, item)
            });
        }

        private static HistoricEvent FindEligibleMeetFaction(
            History history,
            HistoricEntity sultan,
            HashSet<string> plannedItemNames,
            out string item,
            out string baseItemName,
            out string locationName,
            out HistoricEntity location,
            out HistoricEntity region,
            out string faction,
            out string element,
            out int period,
            out long responseYear,
            out string sultanName,
            out string revealedRegionName
        )
        {
            HistoricEvent earliest = null;
            item = null;
            baseItemName = null;
            locationName = null;
            location = null;
            region = null;
            faction = null;
            element = null;
            period = 0;
            responseYear = 0;
            sultanName = null;
            revealedRegionName = null;
            HistoricEntitySnapshot finalSultan = sultan.GetSnapshotAtYear(sultan.lastYear);

            foreach (HistoricEvent existing in sultan.events)
            {
                if (!(existing is MeetFaction)
                    || existing.GetEventProperty("tombInscriptionCategory") != "Treats")
                {
                    continue;
                }

                string candidateLocationName = existing.GetEntityProperty("location");
                List<string> addedFactions = existing.GetListProperties("likedFactions");
                string candidateFaction = addedFactions != null && addedFactions.Count == 1
                    ? addedFactions[0]
                    : null;
                long candidateResponseYear = existing.year + existing.duration + 1;
                string candidateSultanName = sultan.GetEntityProperty(
                    "name",
                    candidateResponseYear
                );
                string candidatePeriod = sultan.GetEntityProperty(
                    "period",
                    candidateResponseYear
                );
                if (!IsRendered(candidateLocationName)
                    || !IsRendered(candidateFaction)
                    || !finalSultan.GetList("likedFactions").Contains(candidateFaction)
                    || !Factions.TryGet(candidateFaction, out Faction _)
                    || candidateResponseYear >= sultan.lastYear
                    || sultan.GetEntityProperty("isAlive", candidateResponseYear) != "true"
                    || !IsRendered(candidateSultanName)
                    || !int.TryParse(candidatePeriod, out int candidatePeriodNumber)
                    || candidatePeriodNumber < 1
                    || candidatePeriodNumber > 5)
                {
                    continue;
                }

                string candidateElement = null;
                foreach (string value in sultan.GetSnapshotAtYear(candidateResponseYear)
                    .GetList("elements"))
                {
                    if (IsRendered(value))
                    {
                        candidateElement = value;
                        break;
                    }
                }
                if (candidateElement == null)
                {
                    continue;
                }

                HistoricEntity candidateLocation = ResolveUniqueEntity(
                    history,
                    "name",
                    candidateLocationName
                );
                if (candidateLocation == null)
                {
                    continue;
                }

                HistoricEntitySnapshot locationSnapshot = candidateLocation.GetSnapshotAtYear(
                    candidateLocation.lastYear
                );
                string candidateRegionName = SnapshotValue(locationSnapshot, "region");
                if (SnapshotValue(locationSnapshot, "type") != "location"
                    || SnapshotValue(locationSnapshot, "name") != candidateLocationName
                    || !IsRendered(candidateRegionName))
                {
                    continue;
                }

                HistoricEntity candidateRegion = ResolveUniqueEntity(
                    history,
                    "name",
                    candidateRegionName
                );
                if (candidateRegion == null)
                {
                    continue;
                }

                HistoricEntitySnapshot regionSnapshot = candidateRegion.GetSnapshotAtYear(
                    candidateRegion.lastYear
                );
                string candidateRevealedRegionName = SnapshotValue(regionSnapshot, "newName");
                string candidateBaseItemName = "Compact of " + candidateLocationName;
                string candidateItem = "the " + candidateBaseItemName;
                if (SnapshotValue(regionSnapshot, "type") != "region"
                    || CountOccurrences(
                        regionSnapshot.GetList("locations"),
                        candidateLocationName
                    ) != 1
                    || !IsRendered(candidateRevealedRegionName)
                    || existing.GetEventProperty("revealsRegion")
                        != candidateRevealedRegionName
                    || history.GetEntitiesWherePropertyEquals("name", candidateItem).Count != 0
                    || plannedItemNames.Contains(candidateItem)
                    || locationSnapshot.GetList("items").Contains(candidateItem)
                    || regionSnapshot.GetList("items").Contains(candidateItem))
                {
                    continue;
                }

                if (earliest == null
                    || existing.year < earliest.year
                    || (existing.year == earliest.year && existing.id < earliest.id))
                {
                    earliest = existing;
                    item = candidateItem;
                    baseItemName = candidateBaseItemName;
                    locationName = candidateLocationName;
                    location = candidateLocation;
                    region = candidateRegion;
                    faction = candidateFaction;
                    element = candidateElement;
                    period = candidatePeriodNumber;
                    responseYear = candidateResponseYear;
                    sultanName = candidateSultanName;
                    revealedRegionName = candidateRevealedRegionName;
                }
            }

            return earliest;
        }

        private static HistoricEvent FindEligibleMarryGift(
            History history,
            HistoricEntity sultan,
            out string item,
            out string destinationName,
            out HistoricEntity destination,
            out HistoricEntity region,
            out long responseYear,
            out string sultanName,
            out string revealedRegionName
        )
        {
            HistoricEvent earliest = null;
            item = null;
            destinationName = null;
            destination = null;
            region = null;
            responseYear = 0;
            sultanName = null;
            revealedRegionName = null;
            HistoricEntitySnapshot finalSultan = sultan.GetSnapshotAtYear(sultan.lastYear);
            List<string> finalSultanItems = finalSultan.GetList("items");

            foreach (HistoricEvent existing in sultan.events)
            {
                if (!(existing is Marry)
                    || existing.GetEventProperty("tombInscriptionCategory") != "Trysts")
                {
                    continue;
                }

                List<string> addedItems = existing.GetListProperties("items");
                string candidateItem = addedItems != null && addedItems.Count == 1
                    ? addedItems[0]
                    : null;
                List<string> addedFactions = existing.GetListProperties("likedFactions");
                string candidateFaction = addedFactions != null && addedFactions.Count == 1
                    ? addedFactions[0]
                    : null;
                long candidateResponseYear = existing.year + existing.duration + 1;
                string candidateDestinationName = sultan.GetEntityProperty(
                    "location",
                    candidateResponseYear
                );
                string candidateSultanName = sultan.GetEntityProperty(
                    "name",
                    candidateResponseYear
                );
                if (!IsRendered(candidateItem)
                    || !IsRendered(candidateFaction)
                    || !finalSultanItems.Contains(candidateItem)
                    || candidateResponseYear >= sultan.lastYear
                    || sultan.GetEntityProperty("isAlive", candidateResponseYear) != "true"
                    || !IsRendered(candidateDestinationName)
                    || !IsRendered(candidateSultanName)
                    || HasOtherFinalOwner(history, sultan, candidateItem))
                {
                    continue;
                }

                HistoricEntity candidateItemEntity = ResolveUniqueEntity(
                    history,
                    "name",
                    candidateItem
                );
                HistoricEntity candidateDestination = ResolveUniqueEntity(
                    history,
                    "name",
                    candidateDestinationName
                );
                if (candidateItemEntity == null || candidateDestination == null)
                {
                    continue;
                }

                HistoricEntitySnapshot itemSnapshot = candidateItemEntity.GetSnapshotAtYear(
                    candidateItemEntity.lastYear
                );
                List<string> lovedFactions = itemSnapshot.GetList("lovedFactions");
                if (lovedFactions.Count != 1 || lovedFactions[0] != candidateFaction)
                {
                    continue;
                }

                HistoricEntitySnapshot destinationSnapshot = candidateDestination.GetSnapshotAtYear(
                    candidateDestination.lastYear
                );
                string candidateRegionName = SnapshotValue(destinationSnapshot, "region");
                if (SnapshotValue(destinationSnapshot, "type") != "location"
                    || SnapshotValue(destinationSnapshot, "name") != candidateDestinationName
                    || !IsRendered(candidateRegionName)
                    || destinationSnapshot.GetList("items").Contains(candidateItem))
                {
                    continue;
                }

                HistoricEntity candidateRegion = ResolveUniqueEntity(
                    history,
                    "name",
                    candidateRegionName
                );
                if (candidateRegion == null)
                {
                    continue;
                }

                HistoricEntitySnapshot regionSnapshot = candidateRegion.GetSnapshotAtYear(
                    candidateRegion.lastYear
                );
                string candidateRevealedRegionName = SnapshotValue(regionSnapshot, "newName");
                if (SnapshotValue(regionSnapshot, "type") != "region"
                    || CountOccurrences(
                        regionSnapshot.GetList("locations"),
                        candidateDestinationName
                    ) != 1
                    || !IsRendered(candidateRevealedRegionName)
                    || regionSnapshot.GetList("items").Contains(candidateItem))
                {
                    continue;
                }

                if (earliest == null
                    || existing.year < earliest.year
                    || (existing.year == earliest.year && existing.id < earliest.id))
                {
                    earliest = existing;
                    item = candidateItem;
                    destinationName = candidateDestinationName;
                    destination = candidateDestination;
                    region = candidateRegion;
                    responseYear = candidateResponseYear;
                    sultanName = candidateSultanName;
                    revealedRegionName = candidateRevealedRegionName;
                }
            }

            return earliest;
        }

        private static HistoricEvent FindEligibleForgeItem(
            History history,
            HistoricEntity sultan,
            out string item,
            out string destinationName,
            out HistoricEntity destination,
            out HistoricEntity region,
            out long responseYear,
            out string sultanName,
            out string revealedRegionName
        )
        {
            HistoricEvent earliest = null;
            item = null;
            destinationName = null;
            destination = null;
            region = null;
            responseYear = 0;
            sultanName = null;
            revealedRegionName = null;
            HistoricEntitySnapshot finalSultan = sultan.GetSnapshotAtYear(sultan.lastYear);
            List<string> finalSultanItems = finalSultan.GetList("items");

            foreach (HistoricEvent existing in sultan.events)
            {
                if (!(existing is ForgeItem)
                    || existing.GetEventProperty("tombInscriptionCategory")
                        != "CreatesSomething")
                {
                    continue;
                }

                List<string> addedItems = existing.GetListProperties("items");
                string candidateItem = addedItems != null && addedItems.Count == 1
                    ? addedItems[0]
                    : null;
                long candidateResponseYear = existing.year + existing.duration + 1;
                string candidateDestinationName = sultan.GetEntityProperty(
                    "location",
                    candidateResponseYear
                );
                string candidateSultanName = sultan.GetEntityProperty(
                    "name",
                    candidateResponseYear
                );
                if (!IsRendered(candidateItem)
                    || !finalSultanItems.Contains(candidateItem)
                    || candidateResponseYear >= sultan.lastYear
                    || sultan.GetEntityProperty("isAlive", candidateResponseYear) != "true"
                    || !IsRendered(candidateDestinationName)
                    || !IsRendered(candidateSultanName)
                    || HasOtherFinalOwner(history, sultan, candidateItem))
                {
                    continue;
                }

                HistoricEntity candidateItemEntity = ResolveUniqueEntity(
                    history,
                    "name",
                    candidateItem
                );
                HistoricEntity candidateDestination = ResolveUniqueEntity(
                    history,
                    "name",
                    candidateDestinationName
                );
                if (candidateItemEntity == null || candidateDestination == null)
                {
                    continue;
                }

                HistoricEntitySnapshot destinationSnapshot = candidateDestination.GetSnapshotAtYear(
                    candidateDestination.lastYear
                );
                string candidateRegionName = SnapshotValue(destinationSnapshot, "region");
                if (SnapshotValue(destinationSnapshot, "type") != "location"
                    || !IsRendered(candidateRegionName))
                {
                    continue;
                }

                HistoricEntity candidateRegion = ResolveUniqueEntity(
                    history,
                    "name",
                    candidateRegionName
                );
                if (candidateRegion == null)
                {
                    continue;
                }

                HistoricEntitySnapshot regionSnapshot = candidateRegion.GetSnapshotAtYear(
                    candidateRegion.lastYear
                );
                string candidateRevealedRegionName = SnapshotValue(regionSnapshot, "newName");
                if (SnapshotValue(regionSnapshot, "type") != "region"
                    || !regionSnapshot.GetList("locations").Contains(candidateDestinationName)
                    || !IsRendered(candidateRevealedRegionName))
                {
                    continue;
                }

                if (earliest == null
                    || existing.year < earliest.year
                    || (existing.year == earliest.year && existing.id < earliest.id))
                {
                    earliest = existing;
                    item = candidateItem;
                    destinationName = candidateDestinationName;
                    destination = candidateDestination;
                    region = candidateRegion;
                    responseYear = candidateResponseYear;
                    sultanName = candidateSultanName;
                    revealedRegionName = candidateRevealedRegionName;
                }
            }

            return earliest;
        }

        private static HistoricEvent FindEligibleBattleItem(
            History history,
            HistoricEntity sultan,
            out string item,
            out string battlefieldName,
            out HistoricEntity battlefield,
            out HistoricEntity region,
            out long responseYear,
            out string sultanName,
            out string revealedRegionName
        )
        {
            HistoricEvent earliest = null;
            item = null;
            battlefieldName = null;
            battlefield = null;
            region = null;
            responseYear = 0;
            sultanName = null;
            revealedRegionName = null;
            HistoricEntitySnapshot finalSultan = sultan.GetSnapshotAtYear(sultan.lastYear);
            List<string> finalSultanItems = finalSultan.GetList("items");

            foreach (HistoricEvent existing in sultan.events)
            {
                if (!(existing is BattleItem)
                    || existing.GetEventProperty("tombInscriptionCategory")
                        != "WieldsItemInBattle")
                {
                    continue;
                }

                List<string> addedItems = existing.GetListProperties("items");
                string candidateItem = addedItems != null && addedItems.Count == 1
                    ? addedItems[0]
                    : null;
                string candidateBattlefieldName = existing.GetEntityProperty("location");
                if (!IsRendered(candidateItem)
                    || !IsRendered(candidateBattlefieldName)
                    || !finalSultanItems.Contains(candidateItem))
                {
                    continue;
                }

                HistoricEntity candidateItemEntity = ResolveUniqueEntity(
                    history,
                    "name",
                    candidateItem
                );
                HistoricEntity candidateBattlefield = ResolveUniqueEntity(
                    history,
                    "name",
                    candidateBattlefieldName
                );
                if (candidateItemEntity == null || candidateBattlefield == null)
                {
                    continue;
                }

                HistoricEntitySnapshot battlefieldSnapshot = candidateBattlefield.GetSnapshotAtYear(
                    candidateBattlefield.lastYear
                );
                string candidateRegionName = SnapshotValue(battlefieldSnapshot, "region");
                if (SnapshotValue(battlefieldSnapshot, "type") != "location"
                    || !IsRendered(candidateRegionName))
                {
                    continue;
                }

                HistoricEntity candidateRegion = ResolveUniqueEntity(
                    history,
                    "name",
                    candidateRegionName
                );
                if (candidateRegion == null)
                {
                    continue;
                }

                HistoricEntitySnapshot regionSnapshot = candidateRegion.GetSnapshotAtYear(
                    candidateRegion.lastYear
                );
                long candidateResponseYear = existing.year + existing.duration + 1;
                string candidateSultanName = sultan.GetEntityProperty(
                    "name",
                    candidateResponseYear
                );
                string candidateRevealedRegionName = SnapshotValue(regionSnapshot, "newName");
                if (SnapshotValue(regionSnapshot, "type") != "region"
                    || !regionSnapshot.GetList("locations").Contains(candidateBattlefieldName)
                    || battlefieldSnapshot.GetList("items").Contains(candidateItem)
                    || regionSnapshot.GetList("items").Contains(candidateItem)
                    || candidateResponseYear >= sultan.lastYear
                    || !IsRendered(candidateSultanName)
                    || !IsRendered(candidateRevealedRegionName))
                {
                    continue;
                }

                if (earliest == null
                    || existing.year < earliest.year
                    || (existing.year == earliest.year && existing.id < earliest.id))
                {
                    earliest = existing;
                    item = candidateItem;
                    battlefieldName = candidateBattlefieldName;
                    battlefield = candidateBattlefield;
                    region = candidateRegion;
                    responseYear = candidateResponseYear;
                    sultanName = candidateSultanName;
                    revealedRegionName = candidateRevealedRegionName;
                }
            }

            return earliest;
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

        private static string SnapshotValue(HistoricEntitySnapshot snapshot, string property)
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

        private static bool HasOtherFinalOwner(
            History history,
            HistoricEntity sultan,
            string item
        )
        {
            HistoricEntityList owners = history.GetEntitiesWithListPropertyThatContains(
                "items",
                item
            );
            foreach (HistoricEntity owner in owners)
            {
                if (owner != sultan)
                {
                    return true;
                }
            }

            return false;
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

        private static bool IsRendered(string value)
        {
            return !string.IsNullOrEmpty(value)
                && value.IndexOf('<') < 0
                && value.IndexOf('%') < 0
                && value.IndexOf('=') < 0;
        }

        private static Dictionary<string, List<string>> OneItemList(string item)
        {
            return new Dictionary<string, List<string>>
            {
                { "items", new List<string> { item } }
            };
        }

        private static HistoricEvent DestinationEvent(long year, string item)
        {
            return new HistoricEvent
            {
                year = year,
                duration = 0,
                addedListProperties = OneItemList(item)
            };
        }
    }
}
