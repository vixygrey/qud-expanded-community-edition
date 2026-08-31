using System;
using QudExpandedCE;

namespace XRL.World.Parts
{
    /// <summary>
    /// A creature that picks something up works out whether to use it — if it plausibly could.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Nothing in Qud re-equips an NPC after it acquires an item.</b> <c>Brain.PerformReequip</c>
    /// does scan inventory properly through <c>SharedWeaponSorter</c>, but it only runs when
    /// <c>Brain.DoReequip</c> is set, and none of the four things that set it sits on the
    /// acquisition path: <c>Reequip</c> (a goal pushed only by <c>ModPsionic</c>),
    /// <c>EquipCharge</c>, <c>MechaPlayer</c>, and <c>Brain.WantToReequip()</c> — whose own callers
    /// are all body-plan changes, the multi-limb mutations and two cybernetics. <c>Inventory</c>,
    /// <c>Body</c>, <c>Combat</c> and <c>Physics</c> mention neither name. So a creature that picks
    /// up a carbine keeps swinging its axe. See #588.
    /// </para>
    /// <para>
    /// <b><c>TookEvent</c> is the hook, and its sibling is not.</b> <c>TakenEvent</c> and
    /// <c>TookEvent</c> are sent together from the one <c>CommandTakeObject</c> handler in
    /// <c>Inventory</c>, and they are a passive/active pair: <c>TakenEvent</c> dispatches to the
    /// <em>item</em>, <c>TookEvent</c> to the <em>actor</em>. <c>AddedToInventoryEvent</c> reaches
    /// only the item too, so it cannot carry a rule about who is doing the taking. All four
    /// <c>CommandTakeObject</c> variants share one event ID and differ only in flags, so the silent
    /// path counts — which is what <c>Rummager</c> uses, via <c>GameObject.TakeObject</c>.
    /// </para>
    /// <para>
    /// <b>The creature side is the Tinkering skill, and the item side is
    /// <c>Examiner.Complexity</c>.</b> Intelligence cannot do this job: <c>Creature</c> declares 16
    /// and <c>BaseHumanoid</c> overrides it with <c>sValue="14,1d3,(t)d1"</c>, so every humanoid
    /// lands in one band whatever it is holding — while <c>Goatfolk Yurtwarden</c> inherits
    /// <c>Animal</c> at 6 and carries a Desert Rifle. The stat tracks nothing useful in either
    /// direction. Tinkering does: 57 of 849 creatures carry it, and <em>two of the three</em>
    /// creatures vanilla gives <c>Rummager</c> to are among them. The creatures Qud already lets
    /// scavenge are the ones it credits with understanding technology, and that agreement was not
    /// designed for this.
    /// </para>
    /// <para>
    /// <b>Complexity, not <c>Examiner</c>'s presence.</b> #588 was scoped on the reading that
    /// mundane weapons have no <c>Examiner</c>. They do — <c>BaseDagger</c>, <c>BaseLongBlade</c>
    /// and <c>BaseAxe</c> all carry one, for the <c>Alternate="UnknownKnife"</c> display before
    /// identification — and the count only looks right if <c>Inherits</c> is left unresolved.
    /// <c>Complexity</c> defaults to 0 and separates cleanly: across 3,959 weapon blueprints, 917
    /// resolve to 0 and 457 to 1 or more. Dagger, Long Sword and Steel Battle Axe are all 0;
    /// Carbine 1, Vibro Dagger 4, Nullray Pistol 8.
    /// </para>
    /// <para>
    /// <b>Nothing hand-authored moves.</b> The rule fires on acquisition only, so a loadout the game
    /// spawned a creature holding is never re-evaluated — the yurtwarden keeps its rifle and the
    /// snapjaw shotgunner keeps its shotgun.
    /// </para>
    /// <para>
    /// <b>No instance fields, deliberately.</b> This part is merged onto <c>Creature</c>, so its
    /// layout would otherwise land in every save on every creature in the game;
    /// <c>docs/CHARTER.md</c> rule 5 treats a shipped part's shape as frozen, and
    /// <c>serializable-shape</c> in <c>tools/validate_mod.py</c> enforces it. Everything here is
    /// derived at the moment of the event.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Reequip : IPart
    {
        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == TookEvent.ID;
        }

        public override bool HandleEvent(TookEvent E)
        {
            if (Raven_Options.ReequipOnPickup && ShouldReconsider(E.Item))
            {
                ParentObject.WantToReequip();
            }

            return base.HandleEvent(E);
        }

        /// <summary>
        /// Whether this creature would work out what to do with <paramref name="Item"/>.
        /// </summary>
        /// <remarks>
        /// The player is excluded because <c>WantToReequip</c> already refuses them — deciding what
        /// to hold is the player's business, and doing it for them would be the opposite of a
        /// feature. A creature with no <c>Brain</c> has nothing to re-equip with, and one with no
        /// <c>Combat</c> part is not fighting, so neither is asked.
        /// </remarks>
        private bool ShouldReconsider(GameObject Item)
        {
            if (Item == null || ParentObject == null || ParentObject.IsPlayer())
            {
                return false;
            }

            if (ParentObject.Brain == null || !ParentObject.HasPart<Combat>())
            {
                return false;
            }

            // Tier A: a creature credited with understanding technology reconsiders anything.
            if (ParentObject.HasSkill("Tinkering"))
            {
                return true;
            }

            // Tier B: everyone else reconsiders a stick with an edge, and not a gun.
            return !IsArtifact(Item);
        }

        /// <summary>
        /// An artifact is an item whose <c>Examiner</c> asks something of the examiner.
        /// </summary>
        /// <remarks>
        /// Absent <c>Examiner</c> is mundane — natural weapons and thrown objects sit here — and so
        /// is <c>Complexity</c> 0, which is what <c>BaseDagger</c> and friends resolve to. Reading
        /// the part off the object rather than the blueprint is deliberate: <c>Examiner</c> is a
        /// live part and an item's complexity is a property of the item.
        /// </remarks>
        private static bool IsArtifact(GameObject Item)
        {
            Examiner examiner = Item.GetPart<Examiner>();
            return examiner != null && examiner.Complexity > 0;
        }
    }
}
