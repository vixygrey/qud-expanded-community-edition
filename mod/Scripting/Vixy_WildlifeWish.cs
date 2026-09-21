using System.Text;
using XRL.UI;
using XRL.Wish;
using XRL.World;

namespace XRL
{
    /// <summary>Reports the active zone's wildlife-recovery record without changing it.</summary>
    /// <remarks>
    /// The recovery system is intentionally silent in normal play. This wish makes its persisted
    /// pool, time gate, and budget visible for QA without adding a player-facing message or a test
    /// bypass that could turn wildlife into a farm.
    /// </remarks>
    [HasWishCommand]
    public class Vixy_WildlifeWish
    {
        [WishCommand("vixywildlife", null)]
        public static void Report()
        {
            StringBuilder sb = new StringBuilder();
            bool installed = The.Game?.GetSystem<Vixy_WildlifeRecovery>() != null;
            sb.Append("{{Y|Wildlife recovery}}  system ")
              .Append(installed ? "{{G|installed}}" : "{{R|MISSING}}")
              .Append("   interval ").Append(Vixy_WildlifeRecovery.RecoveryInterval)
              .Append(" rounds   cohort budget ").Append(Vixy_WildlifeRecovery.CohortBudget)
              .Append('\n');

            if (!installed)
            {
                sb.Append("\n{{R|Nothing below can be trusted.}} The system was not installed on this save.");
            }
            else
            {
                sb.Append('\n').Append(Vixy_WildlifeRecovery.Describe(The.Player?.CurrentZone));
            }

            Popup.Show(sb.ToString());
        }
    }
}
