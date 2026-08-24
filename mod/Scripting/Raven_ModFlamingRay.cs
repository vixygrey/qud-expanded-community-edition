using System;
using XRL.World.Parts.Mutation;

namespace XRL.World.Parts
{
    /// <summary>
    /// FlamingRay needs a variant to know which body part it fires from. See
    /// Raven_ModVariantMutationBase for why the stock base class does not supply one (#411).
    /// </summary>
    [Serializable]
    public class Raven_ModFlamingRay : Raven_ModVariantMutationBase<FlamingRay>
    {
        protected override string VariantBlueprint => "Ghostly Flames";
    }
}
