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
    /// Moves eligible historical relics between structured history records before vanilla builds
    /// the world from them. Every transfer must update the sultan, location, and containing region
    /// together so the chronicle, physical relic, and relic quest continue to describe one fact.
    /// </summary>
    public class Vixy_WorldHistoryModule : AbstractEmbarkBuilderModule
    {
        private const string AppliedStateKey = "Vixy_WorldHistoryEventsApplied";
        private const string BattleItemResponseKey = "Vixy_BattleItemDedicationResponse";
        private const string ForgeItemResponseKey = "Vixy_ForgeItemDedicationResponse";

        private sealed class PlannedTransfer
        {
            public HistoricEntity Sultan;
            public HistoricEntity Destination;
            public HistoricEntity Region;
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
            try
            {
                transfers = PlanTransfers(history);
            }
            catch
            {
                // Planning is read-only. An unfamiliar future history shape must leave vanilla's
                // completed history intact rather than risking a one-sided relic transfer.
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

            The.Game.SetIntGameState(AppliedStateKey, 1);
            return history;
        }

        private static List<PlannedTransfer> PlanTransfers(History history)
        {
            HistoricEntityList sultans = history.GetEntitiesWherePropertyEquals("type", "sultan");
            List<PlannedTransfer> transfers = new List<PlannedTransfer>(sultans.Count * 2);

            foreach (HistoricEntity sultan in sultans)
            {
                PlanBattleItemDedication(history, sultan, transfers);
                PlanForgeItemDedication(history, sultan, transfers);
            }

            return transfers;
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
