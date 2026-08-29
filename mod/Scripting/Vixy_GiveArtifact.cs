using System.Collections.Generic;
using QudExpandedCE;
using XRL.UI;

namespace XRL.World.Conversations.Parts
{
    /// <summary>
    /// Argyve's <c>[give artifact]</c> choice, with artifacts I marked important left out of the
    /// picker.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Vanilla's version has no importance check of any kind.</b> Not a weak one — none.
    /// <c>GiveArtifact</c> lists <c>The.Player.Inventory.GetObjects(IsArtifact)</c>, and
    /// <c>IsArtifact</c> matches anything with a <c>TinkerItem</c> and <c>Examiner.Complexity &gt;
    /// 0</c>: an entire category rather than a named quest item. Following the event chain confirms
    /// there is no confirmation hiding downstream either — <c>CommandRemoveObject</c> fires
    /// <c>BeginDrop</c>, then <c>BeginBeingDropped</c>, then <c>PerformDrop</c>, and no link tests
    /// importance. A marked, one-of-a-kind artifact sits in that picker beside a bit of scrap and
    /// one keystroke hands it over. See #570.
    /// </para>
    /// <para>
    /// <b>Modelled on <c>LibrarianGiveBook</c>, which is the only place vanilla does this properly.</b>
    /// It does all three parts: player-marked books are dropped from the list, the exclusion is said
    /// out loud with a way back — <i>"You only have books you've marked important. Unmark any you
    /// wish to donate."</i> — and whatever survives still gets <c>ConfirmUseImportant</c>, which
    /// catches the things the game marked rather than me. That is the rule this fork wants
    /// everywhere: <b>a mark I made means do not offer it; a mark the game made means ask.</b>
    /// </para>
    /// <para>
    /// <b>Why this replaces the part rather than subclassing it.</b>
    /// <c>GiveArtifact.HandleEvent(EnterElementEvent)</c> is virtual, so a subclass looks possible —
    /// and it is not. The method ends with <c>base.HandleEvent(E)</c> reaching
    /// <c>IConversationPart</c>, which is what advances the conversation. From a subclass,
    /// <c>base.</c> reaches <c>GiveArtifact</c> and re-runs the entire picker, and C# has no
    /// <c>base.base</c>. So this derives from <c>IConversationPart</c> directly and reuses
    /// <c>GiveArtifact.IsArtifact</c>, which is <c>public static</c> — the definition of
    /// <em>artifact</em> still comes from vanilla and cannot drift, even though none of vanilla's
    /// code is inherited. <c>docs/LESSONS.md</c> records the trap, with <c>Garbage</c> as the
    /// counter-example where the same shape was safe.
    /// </para>
    /// <para>
    /// <b>The messages are vanilla's.</b> <i>"You have no artifacts to give."</i> and <i>"You can't
    /// give that object."</i> are copied exactly, and the held-back line is the librarian's sentence
    /// with its noun changed. Only the filtering is new.
    /// </para>
    /// <para>
    /// <b>The confirm is an addition, not a port</b>, because there was nothing here to port. It is
    /// the half of the rule that protects a `QuestItem` or a `Storied` thing I never marked myself,
    /// and it is the reason a quest cannot be blocked silently: if the only artifact I own is
    /// system-important, I am asked rather than refused.
    /// </para>
    /// <para>
    /// <b>Both call sites are Argyve's knickknack quest</b>, which gates the main quest line. So the
    /// failure message matters more than it looks: excluding everything I own has to say why, and
    /// how to undo it, or the quest reads as broken. That is the librarian's shape and the reason it
    /// was worth copying rather than inventing.
    /// </para>
    /// <para>
    /// Charter rule 5: two event handlers and a list filter. No I/O, no reflection, no Harmony.
    /// </para>
    /// </remarks>
    public class Vixy_GiveArtifact : IConversationPart
    {
        public override bool WantEvent(int ID, int Propagation)
        {
            return base.WantEvent(ID, Propagation)
                || ID == GetChoiceTagEvent.ID
                || ID == EnterElementEvent.ID;
        }

        /// <summary>Vanilla's tag, kept so the choice still reads the same.</summary>
        public override bool HandleEvent(GetChoiceTagEvent E)
        {
            E.Tag = "{{g|[give artifact]}}";
            return false;
        }

        public override bool HandleEvent(EnterElementEvent E)
        {
            GameObject player = The.Player;
            if (player?.Inventory == null)
            {
                return base.HandleEvent(E);
            }

            List<GameObject> offerable = player.Inventory.GetObjects(GiveArtifact.IsArtifact);
            bool held = false;

            if (Raven_Options.ImportantArtifacts)
            {
                List<GameObject> keeping = new List<GameObject>(offerable.Count);
                foreach (GameObject artifact in offerable)
                {
                    if (artifact.IsMarkedImportantByPlayer())
                    {
                        held = true;
                    }
                    else
                    {
                        keeping.Add(artifact);
                    }
                }
                offerable = keeping;
            }

            if (offerable.Count == 0)
            {
                return player.ShowFailure(
                    held
                        ? "You only have artifacts you've marked important. Unmark any you wish to give."
                        : "You have no artifacts to give."
                );
            }

            GameObject giving = Popup.PickGameObject(
                "Choose an artifact to give.",
                offerable,
                AllowEscape: true
            );

            if (giving == null || !giving.ConfirmUseImportant(player, "give"))
            {
                return false;
            }

            giving.SplitStack(1, player);
            if (!player.FireEvent(Event.New("CommandRemoveObject", "Object", giving)))
            {
                Popup.Show("You can't give that object.");
                return false;
            }

            return base.HandleEvent(E);
        }
    }
}
