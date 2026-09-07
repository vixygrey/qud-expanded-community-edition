using System;
using XRL;
using XRL.World.AI;

namespace XRL.World.Parts
{
    /// <summary>
    /// Notices when I kill something that was hunting somebody else, and lets them remember it.
    /// #921.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b><c>Registrar.Register</c>, not <c>WantEvent</c>, and that is the whole trick.</b>
    /// <c>AIHelpBroadcastEvent</c> declares <c>Cascade = 64</c>, which is
    /// <c>CASCADE_STOP_AT_REGISTRY</c>, and <c>GameObject.HandleEventInner</c> opens with:
    /// <code>
    /// if (MinEvent.CascadeTo(cascadeLevel, 64))
    ///     return RegisteredEvents?.Dispatch(E) ?? true;   // early return
    /// </code>
    /// <c>64 &amp; 64</c> is non-zero, so it takes that return and never walks <c>PartsList</c> —
    /// <c>WantEvent</c> is not called at all. A part written the way the other ten in this directory
    /// are written would compile, load, validate clean and <b>receive nothing</b>. That is
    /// <c>docs/LESSONS.md</c>'s <i>containment is not dispatch</i>, one variant over: not a part
    /// outside the cascade, but a part outside the registry.
    /// </para>
    /// <para>
    /// <b><c>Brain</c> is not the model to copy here</b>, which is the second half of the same trap.
    /// It handles this event without registering for it, because
    /// <c>AIHelpBroadcastEvent.Send</c> calls <c>item2.Brain.HandleEvent(E)</c> <em>directly</em>
    /// after the object-level dispatch. Reading <c>Brain</c> and following it would produce the
    /// silent version.
    /// </para>
    /// <para>
    /// <b>Why this hears anything at all.</b> <c>Send</c> floods visibility radius 20 for everything
    /// carrying a <c>Brain</c> and dispatches to each. The player has one and is not the
    /// <c>Actor</c>, so the player is in that flood whenever something dies nearby.
    /// </para>
    /// <para>
    /// <b>The dying creature's target is still readable, and this is the only moment it is.</b>
    /// <c>Brain.HandleEvent(BeforeDeathRemovalEvent)</c> is what sends the broadcast, it runs while
    /// the creature still exists, <c>GameObject.Die</c> calls <c>Destroy</c> only after every death
    /// event, and <c>Brain.Target</c> is cleared solely by <c>StopFighting</c>, which is not on that
    /// path. So <c>E.Actor.Brain.Target</c> names who the dying thing was fighting — no
    /// capture-then-credit bookkeeping, and no part on all 957 creature blueprints.
    /// </para>
    /// <para>
    /// <b>No option, and the trigger is narrow instead.</b> Charter rule 6 asks whether anybody
    /// would turn this off; the answer depends entirely on how often it fires, and every condition
    /// below is there to keep that low. In ordinary combat hostiles target <em>you</em> — something
    /// targeting an NPC at the moment you kill it means you intervened in somebody else's fight,
    /// which is exactly the act being rewarded. See #921 for the reasoning that chose narrowing over
    /// a menu line.
    /// </para>
    /// <para>
    /// <b>A led creature resolves to its leader rather than being refused.</b>
    /// <c>Brain.GetFeeling</c> reads the final leader's opinion map, so an opinion on a bodyguard can
    /// never be observed. <c>Vixy_Gift</c> refuses and says why because it has a conversation to say
    /// it in; here there is no message, so refusing would silently discard a real act. Crediting the
    /// leader is what the game would read anyway.
    /// </para>
    /// <para>
    /// Charter rule 5: one registration, one event handler, no instance state, no I/O, no
    /// reflection, no Harmony.
    /// </para>
    /// </remarks>
    [Serializable]
    public class Vixy_Defends : IPart
    {
        public override void Register(GameObject Object, IEventRegistrar Registrar)
        {
            Registrar.Register(AIHelpBroadcastEvent.ID);
            base.Register(Object, Registrar);
        }

        public override bool HandleEvent(AIHelpBroadcastEvent E)
        {
            Credit(E);
            return base.HandleEvent(E);
        }

        /// <summary>
        /// Record the defence, if this death was one.
        /// </summary>
        /// <remarks>
        /// Every early return is a narrowing that #921 chose deliberately over an option. The
        /// <c>IsTemporary</c> test is the summon farm: conjure something hostile, let it pick a
        /// fight, kill it, repeat. It catches summons and not every creature a player made — a clone
        /// or a charmed-and-released creature is not temporary — which is a gap recorded rather than
        /// closed, since nobody has run it.
        /// </remarks>
        private void Credit(AIHelpBroadcastEvent E)
        {
            // Somebody else's death, or a theft or a trespass. Not mine and not a rescue.
            if (E.Target != ParentObject) return;
            if (E.Cause != HelpCause.Killed && E.Cause != HelpCause.Murder) return;

            GameObject dying = E.Actor;
            if (dying == null || dying.IsTemporary) return;

            GameObject defended = dying.Brain?.Target;
            if (defended == null || defended == ParentObject) return;
            if (defended.IsTemporary) return;

            // A bat is not grateful. See Vixy_Regard for what separates a people from an animal
            // that was in the way, and for the one character this deliberately says no to.
            if (!Vixy_Regard.CanHold(defended)) return;

            // An opinion on a follower is never read - GetFeeling delegates to the final leader
            // before it touches the map - so credit whoever actually holds the feeling.
            GameObject holder = defended.Brain?.GetFinalLeader() ?? defended;
            if (holder == ParentObject) return;

            holder.Brain?.AddOpinion<Vixy_OpinionDefended>(ParentObject);
            Announce(holder, defended);
        }

        /// <summary>
        /// Say that it landed, because nothing else does.
        /// </summary>
        /// <remarks>
        /// <para>
        /// <b>Without this the feature is invisible in play.</b> The gift has
        /// <i>"Tam takes the waterskin"</i> and a reply node; a defence happens mid-fight with no
        /// conversation to put anything in, so the only way to learn it worked would be to suspect
        /// it and go examine somebody. That is <c>docs/LESSONS.md</c>'s <i>an effect that reports
        /// nothing</i>, and it is the same failure that moved §62's ceiling from +40 to +50 —
        /// a number nobody can see is not a feature.
        /// </para>
        /// <para>
        /// <b>A log line rather than a popup</b>, per <c>Vixy_Trinket</c>: this fires in combat, and
        /// a popup mid-fight would be an interruption rather than a notice.
        /// </para>
        /// <para>
        /// <b>It names the holder, not the creature I defended</b>, on the rare occasion they
        /// differ. A led creature's regard *is* its leader's, so naming the follower would report a
        /// feeling that nothing will ever show. Saving somebody's bodyguard and being told their
        /// captain noticed is the honest version, and it teaches the rule.
        /// </para>
        /// <para>
        /// Gated on the rescue having been visible rather than on the holder being visible, because
        /// the message is about a thing I watched happen. A leader across the zone can still be the
        /// one who remembers it.
        /// </para>
        /// </remarks>
        private static void Announce(GameObject Holder, GameObject Defended)
        {
            if (!Defended.IsVisible()) return;

            IComponent<GameObject>.AddPlayerMessage(
                "{{G|" + Holder.DisplayNameOnly + "}} will remember that."
            );
        }
    }
}
