using System;
using QudExpandedCE;

namespace XRL.World.Conversations.Parts
{
    /// <summary>Hides choices that depend on the name-sharing and gift systems.</summary>
    [Serializable]
    public class Vixy_NameSharingGate : IConversationPart
    {
        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == IsElementVisibleEvent.ID;
        }

        public override bool HandleEvent(IsElementVisibleEvent E)
        {
            if (!Raven_Options.NameSharingAndGifts) return false;
            return base.HandleEvent(E);
        }
    }
}
