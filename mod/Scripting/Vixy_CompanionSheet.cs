using System;
using System.Collections.Generic;
using System.Text;
using XRL.UI;
using XRL.World.Parts.Mutation;
using XRL.World.Parts.Skill;
using XRL.World.Skills;

namespace XRL.World.Parts
{
    /// <summary>
    /// Adds a `look over` companion action that shows a follower's own numbers. Sits on the player,
    /// because that is where the companion action menu is assembled.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>Zero vanilla records, for the same reason weapon wear needed none.</b>
    /// <c>OwnerGetInventoryActionsEvent</c> fires on the <em>actor</em> — <c>GameObject</c> gates its
    /// own handler on <c>E.Actor == this &amp;&amp; IsPlayer()</c> — and carries the companion as
    /// <c>E.Object</c>. <c>InventoryActionEvent</c> comes back the same way as <c>E.Item</c>. So both
    /// halves reach one part on the player rather than a part on every recruitable creature, exactly
    /// the shape <c>WieldedWeaponHit</c> has. See #592.
    /// </para>
    /// <para>
    /// <b>This does not use the game's own character sheet, and that is the whole finding.</b> The
    /// issue proposed <c>Screens.Show(GameObject)</c>, which is written generically, honours its
    /// parameter in both UI branches, and has never once been passed anything but
    /// <c>The.Player</c>. It renders a follower correctly. It is still wrong: <c>Show</c> is a
    /// <em>cycler</em>, not a viewer — the classic path loops <c>ScreenList</c> until you exit and
    /// the modern path builds all eight as tabs — so every entry point reaches
    /// <c>TinkeringScreen</c>, which mixes the two subjects inside single operations:
    /// <c>ModificationApplicable(…, obj, The.Player)</c>, an <c>ItemModdingSifrah</c> seeded from
    /// <c>The.Player.Stat("Intelligence")</c>, and <c>ProcessTinkeredItem(…, The.Player)</c>. Aimed
    /// at a follower that lists <em>their</em> items while modding against <em>my</em> Intelligence
    /// and delivering the result to <em>me</em>. No crash and no error — a coherent-looking screen
    /// performing a hybrid action. <c>ShowPopup</c> is no escape either: its dictionary holds only
    /// <c>"Factions"</c>, and the modern branch routes it back through the same tabbed host.
    /// </para>
    /// <para>
    /// So this renders its own panel. That is a cost — it will not track a future vanilla screen —
    /// and it is the price of not shipping the hybrid above.
    /// </para>
    /// <para>
    /// <b>Followers by any route, because vanilla already treats them alike.</b> The gate is
    /// <c>IsPlayerLed()</c>, which walks the party-leader chain and accepts
    /// <c>LeftBehindByPlayer()</c>, so beguiled, proselytised and tamed creatures qualify. The issue
    /// asked whether they should, having not shared water. They should: this is the same test that
    /// already gives them <c>Attack Target</c>, <c>Come</c>, <c>Stay</c> and the rest, and drawing a
    /// line here would invent a distinction the game does not make anywhere else.
    /// </para>
    /// <para>
    /// <b>Free, and it exits nothing.</b> Modelled on <c>ShowEffects</c>, the one existing
    /// companion action that is purely read-only: no <c>UseEnergy</c>, no
    /// <c>RequestInterfaceExit</c>. Reading what a follower is does not take a turn.
    /// </para>
    /// <para>
    /// <c>'l'</c> is free. The companion menu already spends a, c, e, f, g, m, r, s, t, u and w.
    /// </para>
    /// <para>
    /// Equipment is deliberately absent: <c>Description</c> already appends an <c>Equipped:</c> line
    /// to any creature's examine text, so repeating it here would be the one part of this panel that
    /// duplicates something a player can already read.
    /// </para>
    /// <para>
    /// Charter rule 5: no instance state, two event handlers, no Harmony and no reflection.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_CompanionSheet : IPart
    {
        /// <summary>The command both halves agree on.</summary>
        public const string Command = "Vixy_CompanionSheet";

        /// <summary>The six that <c>CharacterStatusScreen</c> calls primary, in its order.</summary>
        private static readonly string[] Attributes =
        {
            "Strength", "Agility", "Toughness", "Intelligence", "Willpower", "Ego"
        };

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade)
                || ID == OwnerGetInventoryActionsEvent.ID
                || ID == InventoryActionEvent.ID;
        }

        public override bool HandleEvent(OwnerGetInventoryActionsEvent E)
        {
            if (E.Actor == ParentObject
                && ParentObject.IsPlayer()
                && E.Object != null
                && !E.Object.IsPlayer()
                && E.Object.IsPlayerLed())
            {
                E.AddAction(
                    "Look Over", "look over", Command, null, 'l',
                    FireOnActor: true, 0, 0, Override: false, WorksAtDistance: true);
            }

            return base.HandleEvent(E);
        }

        public override bool HandleEvent(InventoryActionEvent E)
        {
            if (E.Command == Command && E.Item != null)
            {
                Popup.Show(Describe(E.Item));
            }

            return base.HandleEvent(E);
        }

        /// <summary>
        /// The panel: who they are, what they can take, what they hit with, and what they know.
        /// </summary>
        private static string Describe(GameObject Follower)
        {
            var SB = new StringBuilder();

            SB.Append("{{W|").Append(Follower.GetDisplayName()).Append("}}")
              .Append("  {{K|level}} ").Append(Follower.Stat("Level")).Append("\n\n");

            // Current from Stat, maximum from BaseValue - the same two sources
            // CharacterStatusScreen reads for the player's own header.
            SB.Append("{{K|Hit points}}  ").Append(Follower.Stat("Hitpoints"))
              .Append(" / ").Append(Follower.GetStat("Hitpoints")?.BaseValue ?? 0).Append('\n');

            SB.Append("{{K|AV}} ").Append(Follower.Stat("AV"))
              .Append("   {{K|DV}} ").Append(Follower.Stat("DV"))
              .Append("   {{K|MA}} ").Append(Follower.Stat("MA")).Append("\n\n");

            for (int i = 0; i < Attributes.Length; i++)
            {
                SB.Append("{{K|").Append(Attributes[i].PadRight(12)).Append("}}")
                  .Append(Follower.Stat(Attributes[i]).ToString().PadLeft(3));
                SB.Append((i % 2 == 1) ? "\n" : "    ");
            }

            AppendList(SB, "Mutations", Mutations(Follower));
            AppendList(SB, "Skills", SkillNames(Follower));

            return SB.ToString();
        }

        private static void AppendList(StringBuilder SB, string Label, List<string> Items)
        {
            if (Items.Count == 0)
            {
                return;
            }

            Items.Sort(StringComparer.Ordinal);
            SB.Append("\n{{K|").Append(Label).Append("}}  ").Append(string.Join(", ", Items)).Append('\n');
        }

        /// <summary>
        /// Active mutations with their level, which is what distinguishes two followers who read the
        /// same on paper.
        /// </summary>
        private static List<string> Mutations(GameObject Follower)
        {
            var Names = new List<string>();
            var Part = Follower.GetPart<XRL.World.Parts.Mutations>();
            if (Part == null)
            {
                return Names;
            }

            foreach (BaseMutation Mutation in Part.MutationList)
            {
                if (Mutation.Level > 0)
                {
                    Names.Add(Mutation.GetDisplayName() + " " + Mutation.Level);
                }
            }

            return Names;
        }

        /// <summary>
        /// Top-level skills only, not the powers beneath them.
        /// </summary>
        /// <remarks>
        /// <c>Skills.SkillList</c> holds both — a purchased power is a <c>BaseSkill</c> part on the
        /// object exactly as its parent skill is — so listing it raw would render Axe beside every
        /// individual axe power. <c>SkillFactory.Factory.SkillByClass</c> is keyed on the top-level
        /// classes only, with powers held under each entry's own <c>Powers</c>, so a lookup that
        /// misses is the test for "this is a power". That is also where the readable name lives:
        /// the part's own <c>Name</c> is its class.
        /// </remarks>
        private static List<string> SkillNames(GameObject Follower)
        {
            var Names = new List<string>();
            var Part = Follower.GetPart<XRL.World.Parts.Skills>();
            if (Part == null)
            {
                return Names;
            }

            foreach (BaseSkill Skill in Part.SkillList)
            {
                if (SkillFactory.Factory.SkillByClass.TryGetValue(Skill.Name, out SkillEntry Entry)
                    && !Entry.Name.IsNullOrEmpty())
                {
                    Names.Add(Entry.Name);
                }
            }

            return Names;
        }
    }
}
