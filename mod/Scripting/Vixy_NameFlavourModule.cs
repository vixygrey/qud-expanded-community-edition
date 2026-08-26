using XRL;
using XRL.CharacterBuilds;
using XRL.CharacterBuilds.Qud;
using XRL.Names;
using XRL.World;
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
            JoinTheBootEventList();
            base.Init();
        }

        /// <summary>
        /// Put this module into EmbarkInfo's list early, so the Name row's re-roll reaches it.
        ///
        /// EmbarkBuilder fills that list with `embarkInfo.modules.AddRange(...)` at the very END of
        /// character creation, after the player has finished choosing. Until then it is empty - so
        /// the re-roll, which calls `builder.info.fireBootEvent(...)`, consults nobody and hands
        /// back the name the game generated the old way. A setting whose re-roll button ignores it
        /// is worse than no setting, so this adds itself and the preview starts working.
        ///
        /// DO NOT DELETE THIS AS REDUNDANT. It looks redundant precisely because the framework does
        /// add this module later; the point is that "later" is after the only moment it matters.
        ///
        /// The cost is that the module appears in the list twice once EmbarkBuilder adds it too, so
        /// handleBootEvent fires twice per boot event. That is survivable and was checked rather
        /// than assumed:
        ///
        ///   - build codes never see it. generateCode() reads EmbarkBuilder's own list, not this
        ///     one, and IncludeInBuildCodes() returns getData() != null - which is null here,
        ///     because this module deliberately declares no data.
        ///   - embarkInfo._data gains nothing, for the same reason.
        ///   - the two handlers are idempotent: setting NamingTag twice writes the same string, and
        ///     generating a name twice only wastes a draw, since BEFOREBOOTPLAYEROBJECT restores
        ///     whatever the player was actually shown.
        ///
        /// If Freehold ever changes EmbarkInfo.modules, this stops compiling and
        /// tools/compile_scripting.py says so on the next Qud update - which is the reason to reach
        /// for a public member rather than a Harmony patch. The other two ways this could rot -
        /// the list being filled earlier, or the preview learning to consult modules itself - both
        /// degrade to the behaviour that shipped before this method existed.
        /// </summary>
        private void JoinTheBootEventList()
        {
            EmbarkInfo info = builder?.info;
            if (info != null && !info.modules.Contains(this))
            {
                info.modules.Add(this);
            }
        }

        public override object handleBootEvent(
            string id,
            XRLGame game,
            EmbarkInfo info,
            object element = null
        )
        {
            if (id == QudGameBootModule.BOOTEVENT_AFTERBOOTPLAYEROBJECT)
            {
                // Renaming yourself in game goes through GameObject.GiveProperName, which calls
                // NameMaker.MakeName(this, ...) - a valid `For`, so Generate reads Gender, Species
                // and Tag off the object and an option is invisible to it. Putting the tag on the
                // player is what makes a rename follow the choice rather than the gender.
                if (element is GameObject player)
                {
                    string chosen = Raven_Options.NameFlavourTag();
                    if (chosen == null)
                    {
                        player.RemoveStringProperty("NamingTag");
                    }
                    else
                    {
                        player.SetStringProperty("NamingTag", chosen);
                    }
                }
                return base.handleBootEvent(id, game, info, element);
            }

            if (id != QudGameBootModule.BOOTEVENT_GENERATERANDOMPLAYERNAME)
            {
                return base.handleBootEvent(id, game, info, element);
            }

            string tag = Raven_Options.NameFlavourTag();
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

    }
}
