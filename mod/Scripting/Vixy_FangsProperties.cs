using System;
using System.Text;
using XRL.World.Effects;

namespace XRL.World.Parts
{
    /// <summary>
    /// What a bite is worth, and how often it lands — vanilla's <c>HornsProperties</c> without the
    /// part that made training the Multiweapon line pointless.
    /// </summary>
    /// <remarks>
    /// <para>
    /// Part of #819, found in play: the bite almost never landed. It was not a low number in
    /// isolation, it was a low number beside a high one. <c>Vixy_Fangs</c> is a secondary intrinsic
    /// attack, and every secondary attack rolls through <c>GetMeleeAttackChanceEvent</c>. All three
    /// passive Multiweapon skills raise that roll on the <em>identical</em> condition
    /// <c>HornsProperties</c> matches — <c>Proficiency</c> +20, <c>Expertise</c> +15,
    /// <c>Mastery</c> +15, on an engine base of 15.
    /// </para>
    /// <para>
    /// <b>And <c>HornsProperties</c> threw all fifty away.</b> It calls
    /// <c>E.SetFinalizedChance(20)</c> and returns <c>false</c>, so the accumulated value is
    /// overwritten, <c>Multiplier</c> is reset, and the event stops. A trained character's other
    /// offhand attacks land at 65% while the bite stayed at 20 — so investing in the one skill line
    /// a bite character would obviously take made the bite <em>relatively worse</em>, invisibly.
    /// Vanilla's own Horns have this too; it is inherited rather than introduced, but reusing that
    /// part was this fork's choice and so the answer is this fork's as well.
    /// </para>
    /// <para>
    /// <b>The floor does not move and the ceiling does.</b> Untrained is 20 exactly as before —
    /// nobody's existing character gets worse — and full training reaches 40. That keeps the bite
    /// under a real offhand weapon's 65, and it keeps it under <c>Horns</c> where <c>Horns</c> should
    /// win: horns carry <c>MaxStrengthBonus="100"</c> against these fangs' 5, so a high-Strength
    /// character still prefers 20% of <c>2d3 + all</c> of their Strength to 40% of <c>1d6 + 5</c>.
    /// The two mutations cross over around a Strength modifier of 10 to 15, which is the shape worth
    /// having: <b>horns for strength builds, fangs for everyone else</b>, and fangs a point cheaper
    /// because they stop scaling.
    /// </para>
    /// <para>
    /// <b>The bonus is spread rather than clamped, and that is a deliberate second decision.</b>
    /// Simply capping the accumulated value at 40 would let <c>Proficiency</c> alone reach the
    /// ceiling and leave <c>Expertise</c> and <c>Mastery</c> doing nothing — a smaller copy of the
    /// defect this part exists to fix. Scaling the line's own weights into the 20 points of room
    /// gives <b>20 → 28 → 34 → 40</b>, so every rank is felt and the last one lands exactly on the
    /// cap.
    /// </para>
    /// <para>
    /// <b>Why the skills are read here rather than allowed to accumulate.</b> An additive handler
    /// with a clamp cannot work: the event is dispatched from the actor, <c>Body</c> is a part added
    /// at creation while skills are learned later, so this part runs <em>before</em> them. A clamp
    /// here would freeze the value at 20 and <c>return false</c> would stop the skills outright —
    /// the original bug with more steps. Computing the answer and finalising it is order-independent,
    /// which is the property that matters.
    /// </para>
    /// <para>
    /// <b>The cost of that is a hard-coded list</b>, and it is the one thing here that can rot: a
    /// fourth Multiweapon skill would not be seen. It is named in <see cref="Training"/> so the next
    /// person finds it, and <c>docs/LESSONS.md</c> records the shape.
    /// </para>
    /// <para>
    /// <b>Single Weapon Fighting suppresses the bite, and getting that right meant not calling
    /// <c>SetFinalizedChance</c>.</b> The skill is a toggle, and while it is on
    /// <c>SingleWeaponFighting_Ability</c> sets <c>E.Multiplier = 0.0</c> on every intrinsic
    /// non-primary attack — that is its cost, paid for a chance at an extra primary attack. It
    /// registers at <c>EventOrder.VERY_EARLY</c> (-1000), and <c>HandleEventInner</c> dispatches
    /// negative-order handlers in a pass <em>before</em> any part, so it is guaranteed to run first.
    /// </para>
    /// <para>
    /// <b>And <c>SetFinalizedChance</c> resets <c>Multiplier</c> to 1.0.</b> So vanilla's
    /// <c>HornsProperties</c> silently undoes that suppression: a character with Single Weapon
    /// Fighting toggled on still gets their horn attacks, having already paid for turning them off.
    /// Assigning <c>E.Chance</c> instead leaves the multiplier alone, so the fangs go quiet exactly
    /// as the skill intends. Found by a player question during #819 rather than by reading, which is
    /// the usual way round for this file.
    /// </para>
    /// <para>
    /// Everything else is <c>HornsProperties</c>' behaviour reproduced rather than inherited, because
    /// <c>docs/LESSONS.md</c> already records that subclassing that family is a trap — its useful
    /// methods are non-virtual while the methods calling them are virtual, so a subclass gets the
    /// parent's values back through <c>base</c>. Charter rule 5: no I/O, no network, no reflection,
    /// no Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_FangsProperties : IPart
    {
        /// <summary>Where the mutation's rank lives, written by <c>Vixy_Fangs</c>.</summary>
        /// <remarks>
        /// <b>An int property on the fangs rather than a field on this part.</b>
        /// <c>HornsProperties</c> keeps a <c>public int HornLevel</c>, and copying that would have
        /// made this the first <c>[Serializable]</c> part in the mod to declare instance state —
        /// which <c>serializable-shape</c> refuses, because a part's field layout is written into
        /// every save and is frozen the moment it ships. The property carries the same number with
        /// no layout to freeze, and it is the shape <c>Vixy_Introduce</c> already uses.
        ///
        /// Vanilla's other fallback — looking up a mutation named <c>Horns</c> — is dropped rather
        /// than copied: it could never match this mutation, so it was dead weight on every call.
        /// </remarks>
        public const string RankProperty = "Vixy_FangsRank";

        /// <summary>The untrained chance, and the number this fork already shipped.</summary>
        public const int BaseChance = 20;

        /// <summary>The chance at full Multiweapon training.</summary>
        public const int MaxChance = 40;

        /// <summary>Vanilla's own figure for a charging natural weapon, kept deliberately.</summary>
        public const int ChargingChance = 100;

        /// <summary>No instance state, so every copy of this part is the same part.</summary>
        public override bool SameAs(IPart p) => true;

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade)
                || ID == SingletonEvent<GetDebugInternalsEvent>.ID
                || ID == PooledEvent<GetToHitModifierEvent>.ID
                || ID == GetShortDescriptionEvent.ID
                || ID == PooledEvent<GetMeleeAttackChanceEvent>.ID;
        }

        public override bool HandleEvent(GetMeleeAttackChanceEvent E)
        {
            if (!E.Intrinsic || E.Primary || E.Weapon != ParentObject)
            {
                return base.HandleEvent(E);
            }

            // Charging is vanilla's, and a lunging bite reads as well as a lunging horn.
            // Chance is assigned rather than finalised - see the remarks on Single Weapon Fighting.
            E.Chance = E.Properties.HasDelimitedSubstring(',', "Charging")
                ? ChargingChance
                : BaseChance + Training(E.Actor);
            return false;
        }

        /// <summary>
        /// How much of the gap between <see cref="BaseChance"/> and <see cref="MaxChance"/> this
        /// character's Multiweapon training has earned.
        /// </summary>
        /// <remarks>
        /// The weights are vanilla's own — <c>Proficiency</c> +20, <c>Expertise</c> +15,
        /// <c>Mastery</c> +15 — scaled into the 20 points of room rather than used raw, so full
        /// training lands exactly on the cap: <b>0, 8, 14, 20</b>.
        /// <b>This list is the part that can rot.</b> A fourth Multiweapon skill would be invisible
        /// here, because there is no event that reports what the line contributes without also
        /// applying it.
        /// </remarks>
        private static int Training(GameObject Actor)
        {
            if (Actor == null) return 0;

            int earned = 0;
            if (Actor.HasSkill("Multiweapon_Proficiency")) earned += 20;
            if (Actor.HasSkill("Multiweapon_Expertise")) earned += 15;
            if (Actor.HasSkill("Multiweapon_Mastery")) earned += 15;

            return earned * (MaxChance - BaseChance) / 50;
        }

        public override bool HandleEvent(GetToHitModifierEvent E)
        {
            if (E.Weapon == ParentObject && E.Checking == "Actor")
            {
                E.Modifier += GetToHitBonus();
            }
            return base.HandleEvent(E);
        }

        public override bool HandleEvent(GetShortDescriptionEvent E)
        {
            GetBleedingPerformance(out string Damage, out int SaveTarget);
            StringBuilder sb = Event.NewStringBuilder();
            sb.Append("+").Append(GetToHitBonus()).Append(" to hit").AppendLine()
              .Append("On penetration, this weapon causes bleeding: ").Append(Damage)
              .Append(" damage per round; save difficulty ").Append(SaveTarget).Append(".");
            E.Postfix.AppendRules(sb.ToString());
            return base.HandleEvent(E);
        }

        public override bool HandleEvent(GetDebugInternalsEvent E)
        {
            // HornLevel only. The chance depends on the wielder's skills, and these fangs are the
            // Face part's DefaultBehavior rather than equipment, so ParentObject.Equipped is null
            // here and any number derived from it would be a confident lie.
            E.AddEntry(this, RankProperty, GetHornLevel());
            return base.HandleEvent(E);
        }

        public override void Register(GameObject Object, IEventRegistrar Registrar)
        {
            Registrar.Register("WeaponDealDamage");
            base.Register(Object, Registrar);
        }

        public override bool FireEvent(Event E)
        {
            if (E.ID == "WeaponDealDamage" && E.GetIntParameter("Penetrations") > 0)
            {
                GameObject defender = E.GetGameObjectParameter("Defender");
                if (defender != null)
                {
                    GetBleedingPerformance(out string Damage, out int SaveTarget);
                    defender.ApplyEffect(
                        new Bleeding(Damage, SaveTarget, E.GetGameObjectParameter("Attacker")));
                }
            }
            return base.FireEvent(E);
        }

        /// <summary>Vanilla's bleed curve, reproduced so rank still moves it.</summary>
        public void GetBleedingPerformance(out string Damage, out int SaveTarget)
        {
            int level = GetHornLevel();
            Damage = "1";
            if (level > 4)
            {
                Damage = "1d2";
                int step = (level - 4) / 4;
                if (step > 0) Damage += step.Signed();
            }
            SaveTarget = 20 + 2 * level;
        }

        public int GetToHitBonus() => GetHornLevel() / 2 + 1;

        /// <summary>The mutation's rank, or 1 before <c>Vixy_Fangs</c> has written one.</summary>
        public int GetHornLevel()
        {
            int rank = ParentObject?.GetIntProperty(RankProperty) ?? 0;
            return rank != 0 ? rank : 1;
        }

        /// <summary>Record the mutation's rank on the fangs. Called by <c>Vixy_Fangs</c>.</summary>
        public static void SetRank(GameObject Fangs, int Rank) =>
            Fangs?.SetIntProperty(RankProperty, Rank);
    }
}
