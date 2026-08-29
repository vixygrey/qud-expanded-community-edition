using System;
using System.Collections.Generic;
using System.Text;
using XRL.UI;

namespace XRL.World.Parts
{
    /// <summary>
    /// Adds a <c>gather</c> action to a liquid container, pulling every matching dram out of the
    /// rest of the inventory and into that one — so the containers it drains come free for a
    /// different liquid.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Vanilla already performs this transfer.</b> <c>fill</c> pours one container into another
    /// and always could. What it will not do is filter the target list: it offers every unsealed
    /// container, compatible or not, and picking an incompatible one prompts <i>"empty it first?"</i>
    /// and then mixes. So this is a safe, promptless form of an existing action rather than a new
    /// capability, and it earns its place on three differences — only exact-match targets, no dram
    /// prompt, and every matching container in one press. See #561.
    /// </para>
    /// <para>
    /// <b>What it is for, since the obvious answer is wrong.</b> The water economy is already pooled:
    /// <c>GetFreeDramsEvent</c> sums <c>Volume</c> across every unsealed container holding the pure
    /// liquid and <c>UseDramsEvent</c> drains them in sequence, so 12 + 40 + 3 + 61 + 8 drams already
    /// spends exactly like 124 at a merchant. Nor does gathering reduce the item count —
    /// <c>LiquidVolume.SameAs</c> is unconditionally <c>false</c>, so two liquid containers never
    /// stack, empty ones included. What it does buy is real and narrower: <c>GetStorableDramsEvent</c>,
    /// <c>GetAutoCollectDramsEvent</c> and <c>GiveDrams</c> all gate on
    /// <c>IsPureLiquid(Liquid) || IsEmpty()</c>, so a skin holding three drams of honey cannot accept
    /// anything else at all. Emptying it is what unlocks it.
    /// </para>
    /// <para>
    /// <b>Exact match is safe by arithmetic, not by guard.</b> Water is currency, and merging 50 drams
    /// of fresh into 2 of salty would destroy it. <c>LiquidSameAs</c> compares the
    /// <c>ComponentLiquids</c> proportion maps for equality and ignores volume, and <c>MixWith</c> on
    /// two identical maps computes <c>floor((p·v1 + p·v2) / (v1 + v2))</c> per component, which is
    /// <c>p</c>. An exact-match merge cannot change a mixture, so there is no downgrade path to guard
    /// against rather than a guard that has to stay correct.
    /// </para>
    /// <para>
    /// <b>On the player rather than on the containers.</b> <c>GetInventoryActionsEvent</c> and
    /// <c>GetInventoryActionsAlwaysEvent</c> are sent to the object only, so hanging this off a
    /// container would mean merging a part onto eight base blueprints — and blueprint parts are baked
    /// in at creation, so every waterskin already in a save would silently never get the action.
    /// <c>OwnerGetInventoryActionsEvent</c> is fired on the <b>actor</b> by <c>EquipmentAPI</c>
    /// alongside the other two, which is how <c>Telekinesis</c> and <c>Psychometry</c> reach somebody
    /// else's object. One part, attached through <c>Vixy_PlayerParts</c>, no merges, and existing
    /// saves get it on load.
    /// </para>
    /// <para>
    /// <b>Guards are vanilla's own.</b> Sources come from <c>GetInventoryAndEquipment</c>, exactly as
    /// <c>PerformFill</c> does, so followers stay out. Sealed, in stasis, auto-collecting a different
    /// liquid and liquid-producing containers are all skipped — a self-refilling jug is a tap, not a
    /// stash. Ownership takes one yes/no/cancel for the whole run, following <c>CleanWithLiquid</c>
    /// rather than <c>PerformFill</c>'s per-container prompt, and the transfer itself goes through
    /// <c>MixWith</c> so the three liquids with per-fill side effects — acid eating its container,
    /// warm static glitching, neutron flux detonating — behave as they always have.
    /// <c>RequestInterfaceExit</c> stops the loop rather than running it through an explosion.
    /// </para>
    /// <para>
    /// <b>No off-switch.</b> Charter rule 6 asks whether anybody would actually turn a thing off
    /// before it gets a switch. This changes no number, no loot table and no character creation, it
    /// takes nothing away — <c>fill</c> is untouched and still does everything it did — and it
    /// reaches nothing <c>fill</c> could not reach. There is nothing here to refuse but a menu entry
    /// that does the same job with fewer keystrokes, so an option would have spent a line in the
    /// menu, a <c>helptext</c> to keep true and a branch to carry forever, and bought nothing.
    /// </para>
    /// <para>
    /// Charter rule 5: no instance state, so nothing is added to the save. One event handler, one
    /// pass over an inventory, and no I/O, reflection or Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_LiquidGather : IScribedPart
    {
        /// <summary>
        /// The command this part's action fires. Mod-prefixed because the action is dispatched by
        /// name into <c>InventoryActionEvent</c>, where a collision with a vanilla command would
        /// silently run the wrong thing.
        /// </summary>
        public const string CommandID = "Vixy_GatherLiquid";

        /// <summary>
        /// One turn at base Quickness, matching <c>CleanAll</c> — the other vanilla action that
        /// sweeps the whole inventory in one press. Vanilla's <c>fill</c>, <c>pour</c> and
        /// <c>drain</c> are all free, so this is deliberately stricter than the action it replaces:
        /// draining four containers at once is doing more than one fill, and a turn is the cheapest
        /// price the game has.
        /// </summary>
        private const int GatherEnergy = 1000;

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade)
                || ID == OwnerGetInventoryActionsEvent.ID
                || ID == InventoryActionEvent.ID;
        }

        public override bool HandleEvent(OwnerGetInventoryActionsEvent E)
        {
            // Ordered by cost. This fires for every item the actor looks at, and almost none of
            // them are liquid containers — so the field read comes first, and the pass over the
            // inventory happens only for something that could actually take a dram.
            LiquidVolume into = E.Object?.LiquidVolume;
            if (into != null && CanGatherInto(E.Actor, E.Object, into))
            {
                E.AddAction(
                    "Vixy_Gather",
                    "gather liquid",
                    CommandID,
                    null,
                    'g',
                    FireOnActor: true
                );
            }

            return base.HandleEvent(E);
        }

        public override bool HandleEvent(InventoryActionEvent E)
        {
            if (E.Command == CommandID)
            {
                Gather(E.Actor, E.Item, ref E.InterfaceExit, E.OwnershipHandled);
            }

            return base.HandleEvent(E);
        }

        /// <summary>
        /// True when <paramref name="target"/> holds a liquid and something else in the actor's
        /// inventory holds exactly the same one.
        /// </summary>
        /// <remarks>
        /// Not offered on an empty container. Gathering <em>into</em> an empty one would have to ask
        /// which liquid, and that question is what <c>fill</c> is already for.
        /// </remarks>
        private static bool CanGatherInto(GameObject actor, GameObject target, LiquidVolume into)
        {
            if (actor == null || into == null || into.Volume <= 0 || !CanReceive(into, actor))
            {
                return false;
            }

            List<GameObject> candidates = Event.NewGameObjectList();
            actor.GetInventoryAndEquipment(candidates);
            for (int i = 0; i < candidates.Count; i++)
            {
                if (IsSource(candidates[i], target, into))
                {
                    return true;
                }
            }

            return false;
        }

        /// <summary>Pull every matching dram in the actor's inventory into one container.</summary>
        private static void Gather(
            GameObject actor,
            GameObject target,
            ref bool interfaceExit,
            bool ownershipHandled
        )
        {
            LiquidVolume into = target?.LiquidVolume;
            if (actor == null || into == null || into.Volume <= 0 || !CanReceive(into, actor))
            {
                return;
            }

            if (target.IsInStasis())
            {
                actor.Fail("You cannot seem to interact with " + target.t() + " in any way.");
                return;
            }

            if (!actor.CheckFrozen(Telepathic: false, Telekinetic: true))
            {
                return;
            }

            List<GameObject> sources = Event.NewGameObjectList();
            List<GameObject> inventory = Event.NewGameObjectList();
            actor.GetInventoryAndEquipment(inventory);
            for (int i = 0; i < inventory.Count; i++)
            {
                if (IsSource(inventory[i], target, into))
                {
                    sources.Add(inventory[i]);
                }
            }

            if (sources.Count == 0)
            {
                actor.Fail(
                    "You have nothing else holding " + into.GetLiquidName() + "."
                );
                return;
            }

            // Smallest first, so the number of containers that come away empty is the largest the
            // remaining capacity allows. That is the whole point of the action.
            sources.Sort(BySmallestVolume);

            if (!ConfirmOwnership(actor, target, sources, ownershipHandled))
            {
                return;
            }

            int gathered = 0;
            int emptied = 0;
            for (int i = 0; i < sources.Count; i++)
            {
                int room = into.MaxVolume - into.Volume;
                if (room <= 0)
                {
                    break;
                }

                GameObject source = sources[i];
                LiquidVolume from = source.LiquidVolume;
                int amount = Math.Min(room, from.Volume);
                if (amount <= 0)
                {
                    continue;
                }

                // Measured rather than assumed. MixWith returns false when a liquid's own
                // MixingWith refuses the pour, and it caps at MaxVolume — so the amount asked for
                // is not always the amount that moved, and the summary line has to be true.
                int before = into.Volume;
                bool mixed = into.MixWith(
                    from,
                    ref interfaceExit,
                    PouredFrom: source,
                    PouredBy: actor,
                    Amount: amount
                );
                int moved = into.Volume - before;

                // Validity first: acid can eat the container it was poured into or out of, and
                // CheckImage on a released object is not a question worth asking.
                bool intact = GameObject.Validate(target) && GameObject.Validate(source);
                if (moved > 0)
                {
                    gathered += moved;
                    if (intact && from.Volume <= 0)
                    {
                        emptied++;
                    }

                    if (intact)
                    {
                        from.CheckImage();
                    }
                }

                // Acid eats its container, warm static glitches, and neutron flux detonates — all
                // three run through MixWith. A refusal or a request to close the interface ends the
                // sweep rather than being carried into the next container.
                if (!mixed || interfaceExit || !intact)
                {
                    break;
                }
            }

            if (gathered <= 0)
            {
                actor.Fail("Nothing would pour into " + target.t() + ".");
                return;
            }

            // The container being gathered into can be gone by now — acid eats what it is poured
            // into. Drams still moved and a turn was still spent, so the charge stands; there is
            // simply nothing left to repaint or name.
            if (GameObject.Validate(target))
            {
                into.CheckImage();
                target.PlayWorldSound("Sounds/Interact/sfx_interact_liquidContainer_fill");
                Report(actor, target, into, gathered, emptied);
            }

            actor.UseEnergy(GatherEnergy, "Item Liquid Gather");
        }

        /// <summary>
        /// True when <paramref name="candidate"/> may be drained into <paramref name="target"/>.
        /// </summary>
        /// <remarks>
        /// <c>LiquidSameAs</c> is the exact-match test and the whole of the safety argument;
        /// everything else here is a vanilla guard <c>PerformFill</c> or <c>GiveDrams</c> already
        /// applies. <c>ProducesLiquidEvent</c> is the one addition: a container that refills itself
        /// is a source of supply rather than a stash, and emptying it into a skin every time the
        /// action is pressed would be a pump rather than a tidy-up.
        /// </remarks>
        private static bool IsSource(GameObject candidate, GameObject target, LiquidVolume into)
        {
            if (candidate == null || candidate == target)
            {
                return false;
            }

            LiquidVolume from = candidate.LiquidVolume;
            if (from == null || from.Volume <= 0 || from.IsOpenVolume() || from.EffectivelySealed())
            {
                return false;
            }

            if (candidate.IsInStasis() || ProducesLiquidEvent.Check(candidate, from.GetPrimaryLiquidID()))
            {
                return false;
            }

            return from.LiquidSameAs(into);
        }

        /// <summary>Whether a container is in a state to be poured into at all.</summary>
        private static bool CanReceive(LiquidVolume into, GameObject actor)
        {
            return !into.IsOpenVolume()
                && !into.EffectivelySealed()
                && into.Volume < into.MaxVolume
                && into.ParentObject.AllowLiquidCollection(into.GetPrimaryLiquidID(), actor);
        }

        /// <summary>
        /// One prompt for the whole run if anything involved is owned by somebody else.
        /// </summary>
        /// <remarks>
        /// <c>PerformFill</c> asks per container, which is right when a fill touches one. Sweeping
        /// four would ask four times for a single decision, so this follows <c>CleanWithLiquid</c>
        /// instead: ask once, then broadcast for help once per owned container exactly as vanilla
        /// does, because that part is the owner noticing rather than the player being asked.
        /// </remarks>
        private static bool ConfirmOwnership(
            GameObject actor,
            GameObject target,
            List<GameObject> sources,
            bool ownershipHandled
        )
        {
            if (ownershipHandled || !actor.IsPlayer())
            {
                return true;
            }

            List<GameObject> owned = Event.NewGameObjectList();
            if (target.Owner != null)
            {
                owned.Add(target);
            }

            for (int i = 0; i < sources.Count; i++)
            {
                if (sources[i].Owner != null)
                {
                    owned.Add(sources[i]);
                }
            }

            if (owned.Count == 0)
            {
                return true;
            }

            string subject = owned.Count == 1 ? owned[0].t() : "some of those containers";
            if (
                Popup.ShowYesNoCancel(
                    "You do not own " + subject + ". Are you sure you want to take from "
                        + (owned.Count == 1 ? owned[0].them : "them") + "?"
                ) != DialogResult.Yes
            )
            {
                return false;
            }

            for (int i = 0; i < owned.Count; i++)
            {
                owned[i].Physics?.BroadcastForHelp(actor);
            }

            return true;
        }

        /// <summary>
        /// One line saying what moved and how many containers came free, since the freed containers
        /// are the reason to press this at all.
        /// </summary>
        private static void Report(
            GameObject actor,
            GameObject target,
            LiquidVolume into,
            int gathered,
            int emptied
        )
        {
            if (!actor.IsPlayer())
            {
                return;
            }

            StringBuilder sb = Event.NewStringBuilder();
            sb.Append("You gather ")
                .Append(gathered)
                .Append(gathered == 1 ? " dram of " : " drams of ")
                .Append(into.GetLiquidName())
                .Append(" into ")
                .Append(target.t())
                .Append('.');

            if (emptied > 0)
            {
                sb.Append(' ')
                    .Append(emptied == 1 ? "One container is" : emptied + " containers are")
                    .Append(" now empty.");
            }

            IComponent<GameObject>.AddPlayerMessage(sb.ToString());
        }

        /// <summary>Least full first. Ties broken by nothing — order among equals does not matter.</summary>
        private static int BySmallestVolume(GameObject a, GameObject b)
        {
            return a.LiquidVolume.Volume.CompareTo(b.LiquidVolume.Volume);
        }

        /// <summary>
        /// Writes and reads nothing, symmetrically, so this part occupies no bytes in a save.
        /// Same reasoning as <c>Vixy_Burden</c>: <c>IScribedPart</c> writes a field count and this
        /// class has no serialisable state, so suppressing both halves keeps one on-disk shape in
        /// every version. Delete both overrides when it gains a field.
        /// </summary>
        public override void Write(GameObject Basis, SerializationWriter Writer)
        {
        }

        /// <summary>The other half of the pair above. Symmetry is the whole mechanism.</summary>
        public override void Read(GameObject Basis, SerializationReader Reader)
        {
        }
    }
}
