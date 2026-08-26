using XRL;
using XRL.CharacterBuilds;
using XRL.CharacterBuilds.Qud;
using XRL.Names;
using XRL.UI;

namespace QudExpandedCE
{
    /// <summary>
    /// Lets a player choose how their own randomly generated name sounds.
    ///
    /// This exists because the player is the one character mod/Naming.xml cannot reach.
    /// GenerateRandomPlayerName calls NameMaker.MakeName(null, null, Type) - `For` is null, so
    /// NameStyles.Generate never populates Gender, Species or Tag from a GameObject, and the name
    /// is drawn gender-blind from Qudish however the namestyles are scoped. There is no object to
    /// hang a NamingTag on, because the name is generated before the player object exists.
    ///
    /// What there is, is a boot event. QudGameBootModule fires
    /// BOOTEVENT_GENERATERANDOMPLAYERNAME through EmbarkInfo.fireBootEvent with the default name
    /// as its element, and takes back whatever the modules return. So this replaces it.
    ///
    /// Both call sites are covered, which is the reason this is a module rather than a handler on
    /// EmbarkEvent. fireBootEvent iterates enabledModules regardless of `game`, while
    /// EmbarkEvent.Send dispatches through `Game?.HandleEvent` - and character creation's own
    /// "roll me another name" passes game: null. An EmbarkEvent handler would have changed the
    /// final name and not the one previewed while choosing it.
    ///
    /// Charter rule 5, deliberately: no file I/O, no network, no reflection, no Harmony, no game
    /// internals. AbstractEmbarkBuilderModule declares no abstract members, so this overrides one
    /// public virtual method and nothing else, and the game instantiates it from the class name in
    /// mod/EmbarkModules.xml exactly as it instantiates a part from a blueprint.
    ///
    /// It deliberately declares no module data. AbstractEmbarkBuilderModuleData is [Serializable]
    /// and travels in build codes, so a module carrying state would put this mod's shape into
    /// other people's saved characters. The choice lives in an option instead, which also makes it
    /// a setting rather than something re-picked every run.
    /// </summary>
    public class Vixy_NameFlavourModule : AbstractEmbarkBuilderModule
    {
        /// <summary>
        /// The NamingTag each choice asks for. These are identifiers: mod/Naming.xml scopes on
        /// them by name, and STYLEGUIDE.md section 1 applies - renaming one here without renaming
        /// it there fails silently, because a tag nothing scopes on simply selects nothing.
        ///
        /// "Random" is absent on purpose. It is not a fourth pool; it is the absence of a
        /// preference, and it works by asking for Vixy_Random, which all three namestyles scope
        /// at equal priority so the weighted draw splits evenly between them.
        /// </summary>
        private const string MascTag = "Vixy_Masc";
        private const string FemmeTag = "Vixy_Femme";
        private const string NeutralTag = "Vixy_Neutral";
        private const string RandomTag = "Vixy_Random";

        /// <summary>
        /// Put the chargen selection flags back after character creation has cleared one of them.
        ///
        /// QudCustomizeCharacterModule.Init calls PronounSet.Reinit(), which clears every pronoun
        /// set and re-reads PronounSets.xml - whose root carries EnableSelection="false". So
        /// whatever Raven_Options set at option-update time is gone by the time GetSelections asks,
        /// and the Pronoun Set row never appears. Gender has no equivalent Reinit, which is why the
        /// symptom was one row present and the other missing rather than both.
        ///
        /// EmbarkBuilder Inits every module in EmbarkBuilderConfiguration.activeModules order,
        /// which is XML load order, and DataFile.CompareTo sorts base files before mod files
        /// unconditionally. So a base module's Init always runs before this one's, and this always
        /// runs after the Reinit that clears the flag.
        ///
        /// Found by launching the game. The harness models how a name resolves, not the lifecycle
        /// of a character-creation module, so nothing short of opening the screen could have.
        /// </summary>
        public override void Init()
        {
            Raven_Options.ApplyChargenSelection();
            base.Init();
        }

        public override object handleBootEvent(
            string id,
            XRLGame game,
            EmbarkInfo info,
            object element = null
        )
        {
            if (id != QudGameBootModule.BOOTEVENT_GENERATERANDOMPLAYERNAME)
            {
                return base.handleBootEvent(id, game, info, element);
            }

            string tag = TagFor(Options.GetOption(Raven_Options.NameFlavourID, "Random"));
            if (tag == null)
            {
                return base.handleBootEvent(id, game, info, element);
            }

            // The default name is generated with the subtype and nothing else, so this passes the
            // same one. getModule returns null when a build has no subtype module, which is not a
            // reason to fail - a name generated without it is still a name.
            string subtype = info?.getModule<QudSubtypeModule>()?.data?.Subtype;
            string name = NameMaker.MakeName(Subtype: subtype, Tag: tag, FailureOkay: true);

            // Keep the game's own name rather than returning nothing. NameStyles.Generate hands
            // back null only when no style matched, and a player whose name came back empty would
            // have no way to tell what happened.
            return string.IsNullOrEmpty(name) ? base.handleBootEvent(id, game, info, element) : name;
        }

        /// <summary>
        /// null means "leave the default alone", which is what an unrecognised value gets. The
        /// option is a Combo whose Values are held against this by validate_mod.py, so an
        /// unrecognised value should be impossible - but silently doing nothing is the right
        /// failure for a cosmetic choice, and it is what a player who has never opened the options
        /// menu would want anyway.
        /// </summary>
        private static string TagFor(string choice)
        {
            switch (choice)
            {
                case "Masc":
                    return MascTag;
                case "Femme":
                    return FemmeTag;
                case "Neutral":
                    return NeutralTag;
                case "Random":
                    return RandomTag;
                default:
                    return null;
            }
        }
    }
}
