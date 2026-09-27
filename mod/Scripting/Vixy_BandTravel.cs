using System;

namespace XRL.World.Parts
{
    /// <summary>
    /// World-map travel that advances only while its zone is the active zone.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <c>AIWorldMapTravel</c> uses <c>TurnTick</c>, and the action manager ticks every live object
    /// in every cached, unsuspended zone. Suspension is zone-wide: another object can pin the shared
    /// world map and keep every traveller there live. Checking the active zone here is therefore the
    /// movement invariant; leaving this part unpinned only lets the ordinary cache lifecycle run.
    /// </para>
    /// <para>
    /// This subtype declares no state. The route, partial segment count, and arrival behavior remain
    /// the vanilla base part's serialized fields and implementation.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_BandTravel : AIWorldMapTravel
    {
        public override void TurnTick(long TimeTick, int Amount)
        {
            Zone zone = ParentObject.CurrentZone;
            if (zone != null && zone == The.ActiveZone)
            {
                base.TurnTick(TimeTick, Amount);
            }
        }

        /// <summary>
        /// Replace exact vanilla travel parts saved before #1010.
        /// </summary>
        /// <remarks>
        /// <c>GetPart&lt;T&gt;</c> compares exact runtime types, so this finds legacy parts and skips
        /// tokens already carrying this subtype. The two private base caches are nonserialized and
        /// rebuild normally; every serialized route field is copied before the old part is removed.
        /// </remarks>
        public static void MigrateLegacyTokens()
        {
            if (The.ZoneManager == null) return;

            foreach (GameObject token in The.ZoneManager.FindObjects(
                         (GameObject o) => o.HasPart<Vixy_Band>()))
            {
                AIWorldMapTravel legacy = token.GetPart<AIWorldMapTravel>();
                if (legacy == null) continue;

                Vixy_BandTravel replacement = new Vixy_BandTravel
                {
                    ParasangX = legacy.ParasangX,
                    ParasangY = legacy.ParasangY,
                    ZoneX = legacy.ZoneX,
                    ZoneY = legacy.ZoneY,
                    Segments = legacy.Segments,
                    Cardinal = legacy.Cardinal,
                    Pinned = false,
                };
                token.RemovePart(legacy);
                token.AddPart(replacement);
            }
        }
    }
}
