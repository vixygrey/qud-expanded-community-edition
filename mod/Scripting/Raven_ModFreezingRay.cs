using System;
using XRL.World.Parts.Mutation;

namespace XRL.World.Parts
{
    /// <summary>
    /// FreezingRay needs a variant to know which body part it fires from. See
    /// Raven_ModVariantMutationBase for why the stock base class does not supply one (#411).
    /// </summary>
    [Serializable]
    public class Raven_ModFreezingRay : Raven_ModVariantMutationBase<FreezingRay>
    {
        protected override string VariantBlueprint => "Icy Vapor";
    }
}
