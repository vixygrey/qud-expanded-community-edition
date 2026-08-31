using System;
using System.Collections.Generic;
using XRL.World.Tinkering;

namespace XRL.World.Parts
{
    /// <summary>
    /// Keeps the four upgrade recipes off data disks found in the world, without touching disks that
    /// were minted deliberately.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Why a part rather than an attribute.</b> There is no per-recipe way to say "tinkerable but
    /// not findable". Every consumer — the tinker tree, data disks, the water ritual, psychometry,
    /// schemasofts — reads the single <c>TinkerData.TinkerRecipes</c> list, and the only gate on that
    /// list is <c>TinkerAllowed</c>, which removes the recipe from *all* of them at once, tinkering
    /// included. So the exclusion has to happen where a disk chooses. See #723.
    /// </para>
    /// <para>
    /// <b>The two-event shape is the whole point, and a one-event version would break quest
    /// rewards.</b> <c>GameObjectFactory.CreateObject</c> runs, in order:
    /// </para>
    /// <code>
    /// BeforeObjectCreated?.Invoke(gameObject);            // TinkerData.createDataDisk sets Data here
    /// BeforeObjectCreatedEvent.Process(…);
    /// ObjectCreatedEvent.Process(…);                      // vanilla DataDisk rolls a recipe, if Data == null
    /// AfterObjectCreatedEvent.Process(…);
    /// </code>
    /// <para>
    /// A disk minted on purpose already carries its recipe before vanilla's roll, and vanilla's
    /// handler is guarded by <c>if (Data == null)</c>, so it keeps it. Re-rolling on
    /// <c>ObjectCreatedEvent</c> alone could not tell the two apart and would destroy exactly the
    /// deliberate disk a quest or a teacher hands over. Recording <c>Data == null</c> *before* and
    /// checking again *after* separates them on ordering the engine guarantees, rather than on the
    /// order parts happen to be registered in.
    /// </para>
    /// <para>
    /// <b>Two kinds of deliberate disk are left alone</b>, not one: a disk whose <c>Data</c> is
    /// already set before vanilla rolls, and a disk carrying a <c>TargetBlueprint</c>, which
    /// vanilla's handler honours inside the same <c>Data == null</c> branch it would otherwise draw
    /// in. No vanilla blueprint targets these four — they could not be targeted before they
    /// existed — but a later one or another mod could, and overriding that would be this part
    /// deciding something it was not asked to.
    /// </para>
    /// <para>
    /// Loot generation is closed separately and by data: <c>MinTier="99"</c> in
    /// <c>mod/Core/Mods.xml</c>. This part is only about the schematic, not the item.
    /// </para>
    /// <para>
    /// <b>What is deliberately still reachable.</b> The water ritual and psychometry both draw from
    /// the same pool and are untouched, so a recipe can still arrive that way. That is wanted: those
    /// are people and artefacts telling you something, which is the fiction here. What is closed is
    /// finding the schematic lying on a corpse.
    /// </para>
    /// <para>
    /// <b>Reverse engineering was never open.</b> <c>Disassembly</c> teaches any mod on the object
    /// taken apart, and with no loot route nothing in the world carries one — so the first keen
    /// blade in existence is the one the player makes. That is the reason this feature reads as
    /// knowledge rather than as an item.
    /// </para>
    /// <para>
    /// Charter rule 5: no instance state beyond one <c>[NonSerialized]</c> flag that lives for the
    /// duration of a single object's creation, no Harmony, no reflection.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_UpgradeDiskFilter : IPart
    {
        /// <summary>The recipes this keeps off found disks.</summary>
        /// <remarks>
        /// Blueprint form, which is how <c>TinkerData</c> names a mod: <c>"[mod]" + mod.Part</c>.
        /// </remarks>
        public static readonly string[] Restricted =
        {
            "[mod]ModKeen",
            "[mod]ModLegendary",
            "[mod]ModMicroserrated",
            "[mod]ModMassivelyOverloaded",
        };

        /// <summary>
        /// Whether this disk arrived without a recipe and therefore had one rolled for it.
        /// </summary>
        /// <remarks>
        /// <c>[NonSerialized]</c> deliberately: it is meaningful only between two events during one
        /// object's creation and must never reach a save. <c>validate_mod.py</c>'s
        /// <c>serializable-shape</c> check reads declared instance fields, so this is the kind of
        /// state rule 5 asks to be a considered decision — it is, and it is the narrowest possible.
        /// </remarks>
        [NonSerialized]
        private bool WasRolled;

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade)
                || ID == BeforeObjectCreatedEvent.ID
                || ID == AfterObjectCreatedEvent.ID;
        }

        public override bool HandleEvent(BeforeObjectCreatedEvent E)
        {
            DataDisk disk = ParentObject?.GetPart<DataDisk>();

            // A disk that already carries a recipe was minted deliberately, and one that names a
            // TargetBlueprint was authored to hold that recipe - vanilla's handler honours it in the
            // same branch it would otherwise roll in. Both are somebody's decision, not a draw.
            WasRolled = disk != null
                && disk.Data == null
                && disk.TargetBlueprint.IsNullOrEmpty();

            return base.HandleEvent(E);
        }

        public override bool HandleEvent(AfterObjectCreatedEvent E)
        {
            if (WasRolled)
            {
                DataDisk disk = ParentObject?.GetPart<DataDisk>();
                if (disk?.Data != null && IsRestricted(disk.Data))
                {
                    disk.Data = Substitute();
                }
            }

            return base.HandleEvent(E);
        }

        /// <summary>True when this recipe should never be found lying about.</summary>
        public static bool IsRestricted(TinkerData Data)
        {
            if (Data?.Blueprint == null)
            {
                return false;
            }

            for (int i = 0; i < Restricted.Length; i++)
            {
                if (Restricted[i] == Data.Blueprint)
                {
                    return true;
                }
            }

            return false;
        }

        /// <summary>
        /// Any other recipe, so the disk is still a disk rather than an empty one.
        /// </summary>
        /// <remarks>
        /// A plain shuffle rather than a re-run of <c>GetDataScore</c>: that scorer reads the disk's
        /// own target tier and category fields, which is more coupling than a fallback needs, and
        /// four recipes out of the whole pool is a rounding error in the distribution. Returning the
        /// original unchanged if somehow nothing else exists is the safe failure.
        /// </remarks>
        private static TinkerData Substitute()
        {
            List<TinkerData> pool = new List<TinkerData>(TinkerData.TinkerRecipes);
            pool.ShuffleInPlace();

            foreach (TinkerData candidate in pool)
            {
                if (!IsRestricted(candidate))
                {
                    return candidate;
                }
            }

            return null;
        }
    }
}
