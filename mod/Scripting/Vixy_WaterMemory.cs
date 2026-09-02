using System;
using QudExpandedCE;
using XRL.Rules;

namespace XRL.World.Parts
{
    /// <summary>
    /// Writes down where I stood with somebody's people on the day we shared water, so they have
    /// something to measure me against later.
    /// </summary>
    /// <remarks>
    /// <para>
    /// The first checkbox of #753, carried there from the closed #182. The gap it addresses: the
    /// water ritual is a one-shot menu, and afterwards the relationship is over. Nobody I have shared
    /// water with ever refers to it again, whatever I go on to do.
    /// </para>
    /// <para>
    /// <b>This half only records; <c>Vixy_WaterRemembers</c> is the half that speaks.</b> The split
    /// is forced by when the two things can happen: the reputation has to be captured at the moment
    /// of the ritual, and the reaction happens in a conversation an unknown time later.
    /// </para>
    /// <para>
    /// <b>Where the number lives.</b> <c>WaterRitualRecord</c> is an <c>IPart</c> on the creature
    /// with a <c>List&lt;string&gt; attributes</c> and prefix lookup helpers — persisted, per
    /// individual, travelling with them in the save, and already attached to the ritual. Nothing had
    /// to be built to hold this.
    /// </para>
    /// <para>
    /// <b>Read it back with <c>TryGetAttribute</c> and never <c>GetAttribute</c>.</b> Vanilla's
    /// <c>GetAttribute</c> is inverted — <c>if (!attribute.StartsWith(Prefix))</c>, where
    /// <c>TryGetAttribute</c> immediately below it has the correct test — so it returns the first
    /// attribute that does <em>not</em> match, and can throw on the <c>Substring</c> when that
    /// attribute is shorter than the prefix. Recorded in <c>docs/LESSONS.md</c>.
    /// </para>
    /// <para>
    /// <b>The snapshot is taken whether or not the option is on.</b> It is one short string on a part
    /// that already exists, invisible unless something reads it, and gating it would mean the option
    /// silently did nothing for everybody I had already shared water with — an off-switch that
    /// quietly changes what turning it back on can do is worse than a string. Charter rule 6 is
    /// satisfied by the speaking half, which is gated.
    /// </para>
    /// <para>
    /// <b>The snapshot lands after the ritual's own award, and that is what makes it mean
    /// anything.</b> <c>WaterRitual</c> calls <c>PerformRitual()</c> — which is where
    /// <c>ModifyReputation()</c> pays out <c>repValue</c>, 100 by default, to the speaker's own
    /// faction — and only then sends <c>WaterRitualStartEvent</c>. So what is recorded here is where
    /// I stood <em>once the ritual had done its work</em>. Taken a moment earlier it would capture
    /// the standing the award was about to change, and everybody would report good news of me
    /// immediately, on the strength of the water I had just shared with them. That ordering is
    /// vanilla's and not mine, so it is worth writing down rather than relying on quietly.
    /// </para>
    /// <para>
    /// <b>Why a part on the player.</b> <c>WaterRitualStartEvent.Send</c> dispatches to <c>Actor</c>
    /// and to nobody else, and <c>Actor</c> is always <c>The.Player</c>. It fires the legacy string
    /// event first, gated on <c>HasRegisteredEvent</c> — the same shape as <c>Killed</c> in #190 —
    /// and then the <c>MinEvent</c>, so registering both is what makes this reachable at all.
    /// </para>
    /// <para>
    /// Charter rule 5: no I/O, no network, no reflection, no Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_WaterMemory : IPart
    {
        /// <summary>Prefix for the stored standing. See the remarks on reading it back.</summary>
        public const string Key = "Vixy_RitualRep:";

        /// <summary>
        /// How far my standing must move before they remark on it, either way.
        /// </summary>
        /// <remarks>
        /// One <c>REPUTATION_BASE_UNIT</c>, which is 50 — the same unit vanilla prices a water
        /// ritual's own awards in, so "enough to notice" means the same here as it does there rather
        /// than being a number of mine.
        /// </remarks>
        public static readonly int Threshold = RuleSettings.REPUTATION_BASE_UNIT;

        public override bool SameAs(IPart p) => true;

        public override bool WantEvent(int ID, int cascade)
        {
            return base.WantEvent(ID, cascade) || ID == WaterRitualStartEvent.ID;
        }

        public override void Register(GameObject Object, IEventRegistrar Registrar)
        {
            // The legacy half of WaterRitualStartEvent.Send, which is gated on HasRegisteredEvent.
            Registrar.Register("WaterRitualStart");
            base.Register(Object, Registrar);
        }

        public override bool FireEvent(Event E)
        {
            if (E.ID == "WaterRitualStart" && E.HasFlag("Initial"))
            {
                Record(E.GetParameter("Record") as WaterRitualRecord);
            }
            return base.FireEvent(E);
        }

        public override bool HandleEvent(WaterRitualStartEvent E)
        {
            if (E.Initial) Record(E.Record);
            else Deepen(E.SpeakingWith, E.Record);
            return base.HandleEvent(E);
        }

        /// <summary>Prefix marking that the bond with somebody has already deepened once.</summary>
        public const string DeepenedKey = "Vixy_RitualDeepened:";

        /// <summary>
        /// Whether coming back to this person again would be worth the dram.
        /// </summary>
        /// <remarks>
        /// <para>
        /// <b>The gate is that I came back having done well by them</b>, not that I came back. That
        /// is what makes this unfarmable: the thing I would have to farm is reputation with their
        /// people, and reputation is capped by how much of the world there is. Sharing water twice
        /// is free of any such limit, so "you did it again" would have been an infinite tap.
        /// </para>
        /// <para>
        /// <b>And it happens once per person.</b> Vanilla's rewards are finite per creature and
        /// tracked on this same record — <c>secretsRemaining</c> is 2 or 3, <c>numGifts</c> is 1,
        /// <c>canGenerateItem</c> flips false and stays false, and each menu option hides itself when
        /// its pool is spent. Nothing here refills any of those. What is renewed is only the
        /// <em>reputation budget</em> to spend against them, so a deepened bond lets me reach what
        /// they still had rather than conjuring more of it.
        /// </para>
        /// </remarks>
        public static bool CanDeepen(GameObject speaker)
        {
            if (!Raven_Options.WaterBond || speaker == null) return false;

            WaterRitualRecord record = speaker.GetPart<WaterRitualRecord>();
            if (record == null || record.faction.IsNullOrEmpty()) return false;
            if (record.TryGetAttribute(DeepenedKey, out _)) return false;

            if (!record.TryGetAttribute(Key, out string stored)) return false;
            if (!int.TryParse(stored, out int then)) return false;

            return The.Game.PlayerReputation.Get(record.faction) - then >= Threshold;
        }

        /// <summary>Renews their goodwill, once, when I have earned it.</summary>
        private static void Deepen(GameObject speaker, WaterRitualRecord record)
        {
            if (record == null || !CanDeepen(speaker)) return;

            int renewed = speaker.GetPart<GivesRep>()?.repValue ?? (RuleSettings.REPUTATION_BASE_UNIT * 2);
            record.totalFactionAvailable += renewed;
            record.attributes.Add(DeepenedKey + renewed);

            IComponent<GameObject>.AddPlayerMessage(
                "{{G|" + speaker.DisplayNameOnly
                + "}} has heard what you have done, and is minded to deal with you again.");
        }

        /// <summary>Stores my standing with their people, once, on the first ritual.</summary>
        /// <remarks>
        /// Guarded against writing twice because both halves of <c>Send</c> can reach this — the
        /// legacy string event and the <c>MinEvent</c> — and a second entry would be the one
        /// <c>TryGetAttribute</c> never returns rather than an error anybody would see.
        /// </remarks>
        private static void Record(WaterRitualRecord record)
        {
            if (record == null || record.faction.IsNullOrEmpty()) return;
            if (record.TryGetAttribute(Key, out _)) return;

            record.attributes.Add(Key + The.Game.PlayerReputation.Get(record.faction));
        }
    }
}
