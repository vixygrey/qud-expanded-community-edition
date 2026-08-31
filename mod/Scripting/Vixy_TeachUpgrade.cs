using System;
using System.Linq;
using XRL.UI;
using XRL.World.Parts;
using XRL.World.Tinkering;

namespace XRL.World.Conversations.Parts
{
    /// <summary>
    /// Lets one named tinker teach one upgrade recipe, once I have earned the right to be told.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>These four recipes cannot be found, so they have to come from a person.</b> Six vanilla
    /// item mods are complete, gated and presented while nothing can apply them; four of the six are
    /// genuine second rungs. <c>mod/Core/Mods.xml</c> makes them tinkerable and
    /// <c>Vixy_UpgradeDiskFilter</c> keeps them off found data disks, which leaves teaching as the
    /// route — and closes the fiction, because <c>Disassembly</c> teaches any mod on the object
    /// taken apart and nothing in the world carries one. **The first keen blade in existence is the
    /// one the player makes.** See #723.
    /// </para>
    /// <para>
    /// <b>One teacher each, which is the maintainer's call and has a cost.</b> A tinker who dies
    /// takes their recipe out of that save permanently. That is accepted deliberately: a recipe with
    /// four interchangeable sources is a checklist, and one with a single source is a person worth
    /// finding. Barathrum replaced Pax Klanq in that list partly on this — Pax Klanq is an explicit
    /// quest target.
    /// </para>
    /// <para>
    /// <b>Three gates, and the rank is the real one.</b> The choice appears only when I already know
    /// the base recipe, do not yet know the upgrade, and hold the Tinkering rank the recipe's tier
    /// demands — <c>DataDisk.GetRequiredSkill</c> puts every one of these at Tinker II, one rank
    /// above the Tinker I their bases sit at. The schematic says what to do; the rank is whether I
    /// am good enough to do it.
    /// </para>
    /// <para>
    /// <b>And no reputation price, deliberately.</b> The water ritual charges
    /// <c>50 × Tier / 3</c> for a recipe, but two of these four teachers have no water ritual at
    /// all, so borrowing that mechanism would make the feature inconsistent between them. The cost
    /// here is already real and already paid: finding the person, knowing the base, and buying a
    /// 200-point skill rank.
    /// </para>
    /// <para>
    /// <b>Four subclasses rather than two XML attributes.</b> Configuration fields would be
    /// instance state on a <c>[Serializable]</c> type, which <c>validate_mod.py</c>'s
    /// <c>serializable-shape</c> check refuses on sight and rule 5 asks to be justified — a field
    /// layout is written into every save. Expression-bodied overrides on four four-line subclasses
    /// carry the same information with no layout at all, which is the shape <c>Vixy_Trinket</c>
    /// already uses for eighteen of them (#411, #603).
    /// </para>
    /// <para>
    /// Charter rule 5: no instance state, no Harmony, no reflection.
    /// </para>
    /// </remarks>
    [Serializable]
    public abstract class Vixy_TeachUpgrade : IConversationPart
    {
        /// <summary>Mod part name of the prerequisite, e.g. <c>ModSharp</c>.</summary>
        protected abstract string Base { get; }

        /// <summary>Mod part name of the recipe taught, e.g. <c>ModKeen</c>.</summary>
        protected abstract string Upgrade { get; }

        public override bool WantEvent(int ID, int Propagation)
        {
            return base.WantEvent(ID, Propagation)
                || ID == IsElementVisibleEvent.ID
                || ID == EnteredElementEvent.ID;
        }

        public override bool HandleEvent(IsElementVisibleEvent E)
        {
            if (!Ready(out TinkerData upgrade) || upgrade.Known() || !BaseKnown())
            {
                return false;
            }

            // The rank is the gate that makes this an achievement rather than an errand.
            if (!The.Player.HasSkill(DataDisk.GetRequiredSkill(upgrade.Tier)))
            {
                return false;
            }

            return base.HandleEvent(E);
        }

        public override bool HandleEvent(EnteredElementEvent E)
        {
            if (Ready(out TinkerData upgrade) && !upgrade.Known())
            {
                TinkerData.LearnMod(Upgrade);
                Popup.Show("You learn to make " + upgrade.DisplayName + " modifications.");
            }

            return base.HandleEvent(E);
        }

        /// <summary>The upgrade's recipe, if this part is configured and the recipe exists.</summary>
        private bool Ready(out TinkerData Data)
        {
            Data = null;

            if (Base.IsNullOrEmpty() || Upgrade.IsNullOrEmpty() || The.Player == null)
            {
                return false;
            }

            string blueprint = "[mod]" + Upgrade;
            Data = TinkerData.TinkerRecipes.FirstOrDefault(
                t => t.Type == "Mod" && t.Blueprint == blueprint);

            return Data != null;
        }

        /// <summary>
        /// Whether I already know the rung below this one.
        /// </summary>
        /// <remarks>
        /// Asking to be taught what lies past sharp only makes sense once I can make a sharp blade,
        /// and it keeps the choice out of a conversation where it would read as a non sequitur.
        /// </remarks>
        private bool BaseKnown()
        {
            string blueprint = "[mod]" + Base;
            return TinkerData.KnownRecipes.Any(r => r.Blueprint == blueprint);
        }
    }


    /// <summary>Yla Haj teaches ModKeen, past ModSharp.</summary>
    [Serializable]
    public class Vixy_TeachKeen : Vixy_TeachUpgrade
    {
        protected override string Base => "ModSharp";
        protected override string Upgrade => "ModKeen";
    }

    /// <summary>Barathrum the Old teaches ModLegendary, past ModMasterwork.</summary>
    [Serializable]
    public class Vixy_TeachLegendary : Vixy_TeachUpgrade
    {
        protected override string Base => "ModMasterwork";
        protected override string Upgrade => "ModLegendary";
    }

    /// <summary>Bep teaches ModMicroserrated, past ModSerrated.</summary>
    [Serializable]
    public class Vixy_TeachMicroserrated : Vixy_TeachUpgrade
    {
        protected override string Base => "ModSerrated";
        protected override string Upgrade => "ModMicroserrated";
    }

    /// <summary>Q Girl teaches ModMassivelyOverloaded, past ModOverloaded.</summary>
    [Serializable]
    public class Vixy_TeachMassivelyOverloaded : Vixy_TeachUpgrade
    {
        protected override string Base => "ModOverloaded";
        protected override string Upgrade => "ModMassivelyOverloaded";
    }
}
