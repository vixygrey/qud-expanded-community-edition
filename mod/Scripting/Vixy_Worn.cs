using System;
using QudExpandedCE;

namespace XRL.World.Parts
{
    /// <summary>
    /// Wear on a weapon. Holds the shared wear arithmetic for both halves of the feature, marks a
    /// worn weapon in its display name, and — on a missile weapon, where it is merged — spends a
    /// point of wear per shot fired.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The gap this closes.</b> Everything you *wear* degrades from wearing it: armour takes the
    /// damage of being hit, and at a quarter of its hitpoints `Physics` applies <c>Broken</c>.
    /// Nothing you *wield* degrades from wielding it — <c>Combat</c> and <c>MeleeWeapon</c> contain
    /// no path that damages the weapon, so a sword swung ten thousand times is identical to a new
    /// one. This makes the two halves of a loadout follow the same rule. See #195.
    /// </para>
    /// <para>
    /// <b>The capacity is vanilla's, not a design lever.</b> Weapons are hitpoints <b>25</b> — 84 of
    /// 86 missile weapons and the melee line alike — and `Broken` fires at
    /// <c>CurrentHP &lt;= MaxHP / 4</c>, which integer division puts at 6. So a weapon holds exactly
    /// <b>19 points of wear</b> before it breaks, and that is identical for a bronze dagger and a
    /// carbide greataxe. Only the <em>interval</em> was ours to choose.
    /// </para>
    /// <para>
    /// <b>Deterministic, not a chance roll.</b> A per-hit chance breaks a weapon mid-fight on bad
    /// luck, which is the specific thing that makes durability systems hated, and which
    /// <c>DESIGN_difficulty_systems.md</c> Part C already rejects for permanent destruction. A
    /// counter does the same economic work and never ambushes anybody.
    /// </para>
    /// <para>
    /// <b>The interval reads the weapon's tier, because tier is where vanilla keeps material.</b>
    /// <c>10 + 5 × Tier</c> uses, so bronze at tier 0 wears every 10 and zetachrome at tier 8 every
    /// 50 — a five-fold spread that comes off a tag the weapon already declares rather than out of a
    /// table somebody wrote. A weapon shows <c>[worn]</c> after 60 to 300 hits and breaks after 190
    /// to 950, so every tier reaches both states in a real run.
    /// </para>
    /// <para>
    /// Putting durability in the blueprint instead — differing hitpoints per material — was the
    /// better instinct and does not work here. Of 1,935 carried weapons with a numeric tier, 718
    /// sit at 25 hitpoints and only 277 declare it; the rest inherit from <c>PhysicalObject</c>,
    /// the root every object in the game descends from. There is no bronze base to merge onto, so
    /// that route is ~718 vanilla merges <em>and</em> it changes how those weapons answer blasts
    /// and acid the moment it ships.
    /// </para>
    /// <para>
    /// <b>Two exemptions, both exact rather than heuristic.</b> <c>NaturalGear</c> — 357 blueprints,
    /// every one a <c>MeleeWeapon</c> carrier — so nobody's fangs wear out. And anything with no
    /// <c>Tier</c> tag, which is 2,061 carried <c>MeleeWeapon</c> blueprints that are largely
    /// corpses and oddments rather than weapons. The tag is the opt-in.
    /// </para>
    /// <para>
    /// <b>The counter is an int property, not a field.</b> Charter rule 5 and
    /// <c>validate_mod.py</c>'s <c>serializable-shape</c> check both refuse instance state on a
    /// <c>[Serializable]</c> part, and a melee weapon has no part of ours to hold it anyway — this
    /// one is attached only once a weapon has actually been used.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Worn : IPart
    {
        /// <summary>Uses accumulated since the last point of wear was spent.</summary>
        public const string CounterProperty = "Vixy_WeaponUses";

        /// <summary>Uses per point of wear at tier 0, before <see cref="TierStep"/> is added.</summary>
        public const int BaseInterval = 10;

        /// <summary>Extra uses per point of wear for each tier above 0.</summary>
        /// <remarks>
        /// <c>10 + 5 × Tier</c> rather than the <c>20 × (Tier + 1)</c> this first shipped with. That
        /// version was tuned by asking how long one weapon should last and never checking what the
        /// multiplier did at the top of the range: a zetachrome weapon showed no wear for 1,080 hits
        /// and broke at 3,420, which is never in a real run.
        ///
        /// **That inverted the point of the feature.** The repair economy is meant to engage with
        /// gear worth keeping, and the steeper curve meant the better the weapon the less it ever
        /// participated — bronze wore out while the things anybody would actually pay a tinker to
        /// fix did not. A 5× spread keeps a bronze axe disposable and a zetachrome one durable
        /// while landing every tier somewhere a player reaches.
        /// </remarks>
        public const int TierStep = 5;

        /// <summary>
        /// Points of wear a weapon holds: 25 hitpoints down to the 6 at which `Broken` fires.
        /// Not used to decide anything — recorded so the `[worn]` threshold below has a stated
        /// denominator rather than a magic number.
        /// </summary>
        public const int WearCapacity = 19;

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade)
                || ID == PooledEvent<GetDisplayNameEvent>.ID
                || ID == PooledEvent<ShotCompleteEvent>.ID;
        }

        /// <summary>
        /// A missile weapon spends wear once per shot, not once per projectile.
        /// </summary>
        /// <remarks>
        /// <c>ShotCompleteEvent</c> is sent from <c>MissileWeapon</c> at the same brace depth as the
        /// projectile loop rather than inside it, so it fires once per attack however many
        /// projectiles went out. That is what makes this per-shot rather than per-projectile, and it
        /// is the one place this could silently become per-projectile, so it is worth a test.
        ///
        /// Per shot is right on both of the shapes vanilla ships. A Swarm Rack burns ten rounds for
        /// ten projectiles, so charging per projectile would double-bill a cost the game already
        /// levies in ammunition; and a pump shotgun puts eight pellets out of one shell in one
        /// discharge, so per projectile would claim the barrel wore eight times for one trigger
        /// pull.
        /// </remarks>
        public override bool HandleEvent(ShotCompleteEvent E)
        {
            Use(ParentObject);
            return base.HandleEvent(E);
        }

        public override bool HandleEvent(GetDisplayNameEvent E)
        {
            if (!E.Reference && IsWorn(ParentObject))
            {
                E.AddTag("[{{y|worn}}]", 25);
            }

            return base.HandleEvent(E);
        }

        /// <summary>
        /// Spend one use of <paramref name="Weapon"/>, and a point of wear if the interval is up.
        /// </summary>
        /// <remarks>
        /// Static, and the entry point for both halves: a missile weapon calls it on its own behalf
        /// through <c>ShotCompleteEvent</c>, and <c>Vixy_WeaponWear</c> calls it on the player's
        /// behalf for melee, where there is no part on the weapon to hear anything.
        /// </remarks>
        public static void Use(GameObject Weapon)
        {
            int interval = IntervalFor(Weapon);
            if (interval <= 0)
            {
                return;
            }

            int uses = Weapon.GetIntProperty(CounterProperty) + 1;
            if (uses < interval)
            {
                Weapon.SetIntProperty(CounterProperty, uses);
                return;
            }

            Weapon.SetIntProperty(CounterProperty, 0);

            // Attach on first wear rather than up front, so the marker and its display tag only
            // ever reach weapons somebody has actually used.
            Weapon.RequirePart<Vixy_Worn>();

            // Spending hitpoints is what reaches vanilla's own threshold: Physics applies Broken at
            // a quarter of maximum. Nothing here decides when a weapon breaks - the game does.
            //
            // Penalty rather than the base value, which is how Stomach spends hitpoints for thirst,
            // and it leaves the weapon's maximum intact so a repair restores it. CheckHP is then
            // vanilla's own gate: it reads ParentObject.hitpoints when passed nothing and applies
            // Broken itself at a quarter of maximum.
            Weapon.GetStat("Hitpoints").Penalty++;
            Weapon.Physics?.CheckHP();
        }

        /// <summary>
        /// Uses per point of wear, or 0 when this weapon does not wear at all.
        /// </summary>
        public static int IntervalFor(GameObject Weapon)
        {
            if (Weapon == null || !Raven_Options.WeaponWear)
            {
                return 0;
            }

            // Claws, horns and fangs are MeleeWeapon carriers too. All 357 NaturalGear blueprints
            // are, and a mutant whose hands wore out would be absurd.
            if (Weapon.HasTagOrProperty("NaturalGear"))
            {
                return 0;
            }

            string tier = Weapon.GetTag("Tier");
            if (!int.TryParse(tier, out var Tier))
            {
                return 0;
            }

            int interval = BaseInterval + TierStep * Tier;
            return Raven_Options.ScaleWeaponWearInterval(interval);
        }

        /// <summary>
        /// True once a weapon has spent a third of the wear it holds — the point at which it is
        /// worth telling the player, while there is still time to do something about it.
        /// </summary>
        /// <remarks>
        /// Vanilla shows no item condition at all: armour simply breaks. That is tolerable when the
        /// cause is visibly being hit and much worse when it is a counter nobody can see, so this
        /// half is not decoration. `Broken` appends its own tag through the same event.
        /// </remarks>
        public static bool IsWorn(GameObject Weapon)
        {
            if (Weapon == null)
            {
                return false;
            }

            return Weapon.GetStat("Hitpoints")?.Penalty >= WearCapacity / 3;
        }
    }
}
