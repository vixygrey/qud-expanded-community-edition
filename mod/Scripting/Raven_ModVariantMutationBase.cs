using System;
using XRL.World.Parts.Mutation;

namespace XRL.World.Parts
{
    /// <summary>
    /// A chip granting a mutation that needs a <c>Variant</c>, which the stock base class does not
    /// supply.
    ///
    /// `ModImprovedMutationBase&lt;T&gt;` calls
    /// <c>AddMutationMod(typeof(T), null, Tier, …)</c> — and that second argument is the variant.
    /// For the 34 mutations this mod grants that have no variants, null is correct and nothing is
    /// wrong. For `FlamingRay` and `FreezingRay` it is the whole defect (#411):
    ///
    ///   1. Those two derive <c>BodyPartType</c> from the chosen variant's `Armor.WornOn`, inside
    ///      their own <c>SetVariant()</c> override.
    ///   2. <c>BaseMutation.Create(Type, Variant)</c> calls <c>SetVariant</c> **only when the
    ///      variant is non-empty**, so passing null skips it and <c>BodyPartType</c> stays null.
    ///   3. <c>Mutate()</c> has a fallback that picks a random variant — but it assigns the
    ///      <c>Variant</c> *field* directly rather than going through <c>SetVariant</c>, so
    ///      <c>BodyPartType</c> is still null afterwards.
    ///   4. Activating the ability then fails <c>CheckObjectProperlyEquipped()</c>, which needs a
    ///      registered slot for <c>BodyPartType</c>, and prints
    ///      <c>"Your " + BodyPartType + " is too damaged to do that!"</c> — with a null in the
    ///      middle, which is exactly the *"Your is too damaged"* a player reported.
    ///
    /// Vanilla never reaches this. Its only three users of that base class are the Enigma Cone, the
    /// Enigma Cap and the Leyline Puppeteers, which grant Confusion and Temporal Fugue — neither
    /// has variants.
    ///
    /// So this overrides both grant paths to pass the variant, then rebuilds the body's default
    /// equipment. The second half matters as much as the first: <c>OnDecorateDefaultEquipment</c>
    /// is what registers the slot and creates the mutation's own object (the icy vapour, the
    /// ghostly flames), and it runs off <c>DecorateDefaultEquipmentEvent</c>, which only
    /// <c>Body.RegenerateDefaultEquipment()</c> sends. Setting the body part without registering a
    /// slot would leave <c>CheckObjectProperlyEquipped</c> failing for a different reason.
    ///
    /// The base class's removal path is untouched and still works, because <c>mutationMod</c> is a
    /// public field on it and this sets the same one.
    ///
    /// Charter rule 5: no file I/O, no network, no reflection, no Harmony. This calls public methods
    /// on the object being equipped.
    /// </summary>
    /// <remarks>
    /// No instance fields, deliberately — <c>[Serializable]</c> field layout is written into every
    /// save (charter rule 5), and the variant is a compile-time constant per subclass rather than
    /// state. `serializable-shape` in tools/validate_mod.py holds that line.
    /// </remarks>
    [Serializable]
    public abstract class Raven_ModVariantMutationBase<T> : ModImprovedMutationBase<T>
        where T : BaseMutation, new()
    {
        /// <summary>
        /// The blueprint whose `Armor.WornOn` becomes the mutation's body part.
        ///
        /// Each of these mutations has exactly one, so there is no player choice being made here:
        /// `FlamingRay` has `Ghostly Flames` and `FreezingRay` has `Icy Vapor`, both worn on Hands.
        /// A blueprint qualifies by carrying `&lt;tag Name="MutationEquipment" Value="…" /&gt;`
        /// naming the mutation, which is how `BaseMutation.CreateVariants()` finds them.
        /// </summary>
        protected abstract string VariantBlueprint { get; }

        public override bool HandleEvent(EquippedEvent E)
        {
            if (ParentObject.IsEquippedProperly())
            {
                Grant(E.Actor);
            }

            return true;
        }

        public override bool HandleEvent(ImplantedEvent E)
        {
            if (ParentObject.IsEquippedProperly())
            {
                Grant(E.Implantee);
            }

            return true;
        }

        private void Grant(GameObject Wearer)
        {
            if (Wearer == null)
            {
                return;
            }

            mutationMod = Wearer
                .RequirePart<Mutations>()
                .AddMutationMod(
                    typeof(T),
                    VariantBlueprint,
                    Tier,
                    Mutations.MutationModifierTracker.SourceType.Equipment,
                    ParentObject.DisplayName
                );

            // Registers the slot and creates the mutation's own object. Without this the body part
            // is named but has nothing in it, and the ability still refuses to fire.
            Wearer.Body?.RegenerateDefaultEquipment();
        }
    }
}
