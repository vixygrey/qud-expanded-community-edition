using System;
using QudExpandedCE;

namespace XRL.World.Conversations.Parts
{
    /// <summary>
    /// Hides a social-system conversation choice while the combined option is disabled.
    /// </summary>
    /// <remarks>
    /// <para>
    /// The introduction marker persists when the option is disabled. Choices that depend on that
    /// marker therefore need this live gate in addition to their property predicate.
    /// </para>
    /// <para>
    /// This part has no instance state. It does not change names, introductions, gift opinions,
    /// trade, or water rituals.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_SocialEnabled : IConversationPart
    {
        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == IsElementVisibleEvent.ID;
        }

        public override bool HandleEvent(IsElementVisibleEvent E)
        {
            if (!Raven_Options.AskName) return false;
            return base.HandleEvent(E);
        }
    }
}
