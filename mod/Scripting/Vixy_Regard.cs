using System.Collections.Generic;
using XRL.World.Conversations;
using XRL.World.Conversations.Parts;
using XRL.World.Parts;

namespace XRL.World
{
    /// <summary>
    /// Who is capable of thinking better of you, and who is only an animal that was in the way.
    /// </summary>
    /// <remarks>
    /// <para>
    /// <b>The question this answers is not the one <c>docs/FEATURES.md</c> §61.2 could not.</b> That
    /// one was about <em>register</em> — what an NPC says back — and it has no answer, because 102 of
    /// vanilla's 200 conversations are a single node with no live choice and that set holds
    /// <c>Snapjaw</c> and <c>Goatfolk</c> beside <c>JoppaFarmer</c> and <c>GenericMerchant</c>. This
    /// one is about whether a creature is a <em>person</em>, and that does partition: kill a dog
    /// that was harrying a bat and the bat does not become your friend; kill a snapjaw that was
    /// harrying a villager and the villager thinks better of you. See #921.
    /// </para>
    /// <para>
    /// <b>Two tests, unioned, and neither alone is enough.</b>
    /// </para>
    /// <para>
    /// <b>Speaking.</b> Measured across all 199 vanilla conversations: strip <c>{{emote|…}}</c> from
    /// every line a conversation owns, and <b>29 fall silent</b> — <c>Animals</c>, <c>Antelopes</c>,
    /// <c>Apes</c>, <c>Clams</c>, <c>Crabs</c>, <c>Fish</c>, <c>Frogs</c>, <c>Goats</c>,
    /// <c>Insects</c>, <c>Oozes</c>, <c>Reptiles</c>, <c>Spiders</c>, <c>Tortoises</c>,
    /// <c>Worms</c>, <c>Fungi</c>, <c>Plants</c>, <c>Crystals</c>, <c>Robots</c> and a few more.
    /// That is the cave, and the 170 that speak include <c>Snapjaw</c> — <i>"you food?"</i> — so the
    /// test keeps everything anybody would call a people.
    /// </para>
    /// <para>
    /// <b>The water ritual.</b> Speaking alone loses a handful of characters who are silent on
    /// purpose. <c>GivesRep</c> rescues three of them — <c>Oboroqoru</c>, <c>Dreamer</c> and
    /// <c>Warden 1-FF</c> — and admits no animal at all: <c>Bat</c>, <c>Dog</c> and <c>Glowfish</c>
    /// are all <c>GivesRep=False</c>. Sharing water is vanilla's own marker for a people you can
    /// have standing with, so it is the right second question.
    /// </para>
    /// <para>
    /// <b>Known miss: <c>Sparafucile</c>, and it is deliberate.</b> Twenty-three emote lines, mute
    /// by characterisation, and <c>GivesRep=False</c> — so this says no to a real person.
    /// <c>AppleFarmerDaughter</c>, <c>TauChime</c> and <c>Star</c> are the same shape. The union
    /// that would rescue them is <c>HasProperName</c>, and it cannot be used: <c>HeroMaker</c> hands
    /// proper names to legendary beasts, so it would admit a legendary bat — the same leak that
    /// forced §62.6's reply to go wordless. One mute assassin is the price, and it is cheaper than
    /// vermin with opinions.
    /// </para>
    /// <para>
    /// <b>The speaking test is <c>Vixy_AskName.SaysNothing</c>, not a copy of it.</b> That method
    /// walks reachable nodes from the seed, resolves <c>Inherits</c> at bake, excludes the nodes
    /// <c>BaseConversation</c> contributes to everybody, and errs toward "speaks" when a
    /// conversation is built at runtime — four pieces of reasoning from #881 and #885 that a second
    /// implementation would get wrong differently. It wants a live <c>Conversation</c> and there is
    /// none open at the moment somebody dies, so one is built from the blueprint with
    /// <c>new Conversation(bp)</c>, which is the same constructor <c>ConversationUI.HaveConversation</c>
    /// uses.
    /// </para>
    /// <para>
    /// Cached per conversation ID, and <c>[ModSensitiveStaticCache]</c> because it is derived from
    /// <c>Conversation.Blueprints</c> and must not outlive it — the same rule
    /// <c>Vixy_AskName.ContributedNodes</c> follows for the same reason.
    /// </para>
    /// <para>
    /// Charter rule 5: two lookups and a cache. No I/O, no reflection, no Harmony.
    /// </para>
    /// </remarks>
    public static class Vixy_Regard
    {
        [ModSensitiveStaticCache]
        private static Dictionary<string, bool> SpeakingByConversation;

        /// <summary>
        /// Whether this creature could think better of somebody at all.
        /// </summary>
        public static bool CanHold(GameObject Creature)
        {
            if (Creature == null || !Creature.IsCreature) return false;

            // Vanilla's own marker for a people you can have standing with. Cheaper than the
            // conversation walk and answers the silent-but-real cases, so it goes first.
            if (Creature.HasPart<GivesRep>()) return true;

            return Speaks(Creature);
        }

        /// <summary>Whether this creature's conversation contains a word rather than only emotes.</summary>
        private static bool Speaks(GameObject Creature)
        {
            string id = Creature.GetPart<ConversationScript>()?.ConversationID;
            if (id.IsNullOrEmpty()) return false;

            SpeakingByConversation ??= new Dictionary<string, bool>();
            if (SpeakingByConversation.TryGetValue(id, out bool known)) return known;

            bool speaks = false;
            if (Conversation.Blueprints != null
                && Conversation.Blueprints.TryGetValue(id, out ConversationXMLBlueprint blueprint)
                && blueprint != null)
            {
                speaks = !Vixy_AskName.SaysNothing(new Conversation(blueprint));
            }

            SpeakingByConversation[id] = speaks;
            return speaks;
        }
    }
}
