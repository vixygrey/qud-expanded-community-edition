#!/usr/bin/env python3
"""Tests for tools/naming_harness.py.

The harness exists to check claims about Qud's name generation that were read out of a decompiled
assembly. That makes its own fidelity the thing everything else rests on — a harness that models
the loader slightly wrong produces confident, green, wrong answers, which is worse than no harness.

So every test here is a positive control in both directions: the behaviour fires on input that
should trigger it and stays quiet on input that should not. Each one names the C# it mirrors.

Synthetic XML only: no game, no network, no dependencies. CI runners have no copy of Caves of Qud.
"""

from __future__ import annotations

import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import naming_harness as nh


def write(tmp: Path, name: str, body: str) -> Path:
    p = tmp / name
    p.write_text('<?xml version="1.0" encoding="utf-8"?>\n' + body, encoding="utf-8")
    return p


# A two-style stand-in for vanilla: one broad low-priority style, one narrow exclusive one.
VANILLA = """
<naming><namestyles>
  <namestyle Name="Qudish" Format="TitleCase">
    <scopes>
      <scope Name="General" Priority="0" Combine="true" />
      <scope Name="Culture" Culture="Qudish" Priority="100" Combine="true" />
    </scopes>
    <prefixes Amount="1"><prefix Name="fa" /><prefix Name="ha" /><prefix Name="i" Weight="2" /></prefixes>
    <infixes Amount="0-2"><infix Name="ra" /><infix Name="ro" /></infixes>
    <postfixes Amount="1"><postfix Name="q" /><postfix Name="la" /></postfixes>
  </namestyle>
  <namestyle Name="Snapjaw" Format="TitleCase">
    <scopes><scope Name="Faction" Faction="Snapjaws" Priority="100" Combine="false" /></scopes>
    <prefixes Amount="1"><prefix Name="gn" /></prefixes>
    <postfixes Amount="1"><postfix Name="ak" /></postfixes>
  </namestyle>
</namestyles></naming>
"""


class HarnessTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def load(self, *fragments: str):
        styles, order = {}, []
        nh.load_naming(
            write(self.tmp, "vanilla.xml", VANILLA), styles, order, is_mod=False
        )
        for i, frag in enumerate(fragments):
            nh.load_naming(
                write(self.tmp, f"mod{i}.xml", frag), styles, order, is_mod=True
            )
        return styles, order

    def ctx(self, **kw):
        c = {k: None for k in nh.SCOPE_FILTERS}
        c.update(kw)
        return c

    # -- the loader ----------------------------------------------------------------------------
    # LoadNamingNode: loadMode = Reader.GetAttribute("Load"), inherited by every level below via
    # `Reader.GetAttribute("Load") ?? LoadMode`.

    def test_merge_on_root_cascades_and_preserves_vanilla(self):
        styles, _ = self.load("""
        <naming Load="Merge"><namestyles><namestyle Name="Qudish">
          <prefixes><prefix Name="ze" /></prefixes>
        </namestyle></namestyles></naming>""")
        self.assertEqual(
            [p[0] for p in styles["Qudish"].prefixes], ["fa", "ha", "i", "ze"]
        )

    def test_without_merge_the_namestyle_leaves_generation_entirely(self):
        """LoadNameStyleNode removes from _NameStyleList and never adds the replacement back."""
        styles, order = self.load("""
        <naming><namestyles><namestyle Name="Qudish">
          <prefixes Amount="1"><prefix Name="ze" /></prefixes>
        </namestyle></namestyles></naming>""")
        self.assertNotIn(
            "Qudish", order, "a replaced style must not remain in the iteration list"
        )
        self.assertIn("Qudish", styles, "it survives in the table, for Base= lookups")
        self.assertEqual(
            styles["Qudish"].postfixes,
            [],
            "the whole style is rebuilt, not just the pool",
        )

    def test_merge_omitting_amount_keeps_vanillas(self):
        styles, _ = self.load("""
        <naming Load="Merge"><namestyles><namestyle Name="Qudish">
          <prefixes><prefix Name="ze" /></prefixes>
        </namestyle></namestyles></naming>""")
        self.assertEqual(styles["Qudish"].prefix_amount, "1")

    def test_merged_element_updates_weight_in_place(self):
        """LoadNameStylePrefixNode sets `flag` and skips the Add when merging an existing name."""
        styles, _ = self.load("""
        <naming Load="Merge"><namestyles><namestyle Name="Qudish">
          <prefixes><prefix Name="fa" Weight="9" /></prefixes>
        </namestyle></namestyles></naming>""")
        pool = styles["Qudish"].prefixes
        self.assertEqual(
            len(pool), 3, "merging an existing syllable must not duplicate it"
        )
        self.assertEqual(dict(pool)["fa"], 9)

    def test_weight_zero_disables_a_syllable_without_removing_it(self):
        styles, _ = self.load("""
        <naming Load="Merge"><namestyles><namestyle Name="Qudish">
          <postfixes><postfix Name="q" Weight="0" /></postfixes>
        </namestyle></namestyles></naming>""")
        rng = random.Random(1)
        drawn = {nh.draw(styles["Qudish"], rng)[-2:] for _ in range(50)}
        self.assertNotIn("Q", {d[-1] for d in drawn})

    # -- scope matching ------------------------------------------------------------------------

    def test_type_is_exact_equality_including_none(self):
        scope = nh.Scope(filters={"Type": "Site"})
        self.assertTrue(scope.applies(self.ctx(Type="Site")))
        self.assertFalse(
            scope.applies(self.ctx()), "a person-name call must not reach a Site scope"
        )
        self.assertFalse(nh.Scope().applies(self.ctx(Type="Site")), "and the reverse")

    def test_mutation_is_list_membership_not_equality(self):
        """ApplyTo: `Mutations == null || !Mutations.Contains(Mutation)`."""
        scope = nh.Scope(filters={"Mutation": "Two-Headed"})
        self.assertTrue(scope.applies(self.ctx(Mutation="Horns,Two-Headed,Quills")))
        self.assertFalse(scope.applies(self.ctx(Mutation="Horns")))
        self.assertFalse(scope.applies(self.ctx()))

    def test_chance_below_100_is_held_back_deterministically_but_reported(self):
        styles, order = self.load("""
        <naming Load="Merge"><namestyles><namestyle Name="Vixy_Rare" Format="TitleCase">
          <scopes><scope Name="M" Priority="300" Chance="15" Combine="false" /></scopes>
          <prefixes Amount="1"><prefix Name="zz" /></prefixes>
        </namestyle></namestyles></naming>""")
        _chosen, winner, chancy = nh.select(styles, order, self.ctx())
        self.assertNotEqual(
            winner, "Vixy_Rare", "a 15% scope must not describe the ordinary case"
        )
        self.assertIn(
            "Vixy_Rare", [n for n, _ in chancy], "but it must never be hidden"
        )

    def test_check_apply_takes_the_highest_priority_scope_in_the_style(self):
        styles, _ = self.load()
        scope = styles["Qudish"].check_apply(self.ctx(Culture="Qudish"))
        self.assertEqual(scope.priority, 100)
        self.assertEqual(styles["Qudish"].check_apply(self.ctx()).priority, 0)

    # -- style selection -----------------------------------------------------------------------

    def test_sole_candidate_wins_even_at_priority_zero(self):
        """Generate's `case 1:` branch ignores Priority, which is why vanilla's 0 is survivable."""
        styles, order = self.load()
        _, winner, _ = nh.select(styles, order, self.ctx(Species="human"))
        self.assertEqual(winner, "Qudish")

    def test_two_combining_styles_at_priority_zero_produce_namegenfail(self):
        styles, order = self.load("""
        <naming Load="Merge"><namestyles><namestyle Name="Vixy_Second" Format="TitleCase">
          <scopes><scope Name="General" Priority="0" Combine="true" /></scopes>
          <prefixes Amount="1"><prefix Name="zz" /></prefixes>
        </namestyle></namestyles></naming>""")
        _, winner, _ = nh.select(styles, order, self.ctx())
        self.assertEqual(winner, nh.NAMEGENFAIL)

    def test_no_candidate_at_all_also_produces_namegenfail(self):
        styles, _order = self.load()
        del styles["Qudish"], styles["Snapjaw"]
        _, winner, _ = nh.select(styles, [], self.ctx())
        self.assertEqual(winner, nh.NAMEGENFAIL)

    def test_exclusive_scope_at_higher_priority_clears_the_field(self):
        styles, order = self.load()
        _, winner, _ = nh.select(styles, order, self.ctx(Faction="Snapjaws"))
        self.assertEqual(winner, "Snapjaw")

    def test_a_combining_style_under_100_cannot_displace_an_exclusive_one(self):
        """The Priority<100 constraint the feminine namestyle depends on."""
        styles, order = self.load("""
        <naming Load="Merge"><namestyles><namestyle Name="Vixy_Fem" Format="TitleCase">
          <scopes><scope Name="G" Gender="female" Priority="50" Combine="true" /></scopes>
          <prefixes Amount="1"><prefix Name="zz" /></prefixes>
        </namestyle></namestyles></naming>""")
        _, winner, _ = nh.select(
            styles, order, self.ctx(Faction="Snapjaws", Gender="female")
        )
        self.assertEqual(winner, "Snapjaw")

    def test_at_priority_100_it_does_displace_it(self):
        """The same design one point higher — the boundary is `other.priority > scope.priority`."""
        styles, order = self.load("""
        <naming Load="Merge"><namestyles><namestyle Name="Vixy_Fem" Format="TitleCase">
          <scopes><scope Name="G" Gender="female" Priority="100" Combine="true" /></scopes>
          <prefixes Amount="1"><prefix Name="zz" /></prefixes>
        </namestyle></namestyles></naming>""")
        _, winner, _ = nh.select(
            styles, order, self.ctx(Faction="Snapjaws", Gender="female")
        )
        self.assertEqual(winner, "Vixy_Fem")

    # -- #454: a Species scope added to a Faction-only namestyle ---------------------------------
    # The woodsprog shape. Vanilla's Naphtaali namestyle carries Faction and Culture scopes and no
    # Species one, so a woodsprog inside the tribe was named from it and one outside fell through to
    # Qudish. The fixture's Snapjaw style has the same shape - Faction 100, Combine="false", nothing
    # else - so it stands in for Naphtaali here.

    SPECIES_SCOPE = """
    <naming Load="Merge"><namestyles><namestyle Name="Snapjaw">
      <scopes><scope Name="Vixy_Species" Species="snapjaw" Priority="50" Combine="true" /></scopes>
    </namestyle></namestyles></naming>"""

    def test_species_scope_reaches_a_creature_outside_the_faction(self):
        """The bug being fixed: species matches, faction does not, and before the scope existed
        this fell through to the General-scope style."""
        styles, order = self.load(self.SPECIES_SCOPE)
        chosen, _, _ = nh.select(
            styles, order, self.ctx(Species="snapjaw", Faction="Grazing Hedonists")
        )
        self.assertEqual(nh.shares(chosen), {"Snapjaw": 1.0})

    def test_without_the_species_scope_it_falls_through(self):
        """The positive control. Without this the test above would pass on a harness that matched
        everything, and the whole point is that vanilla does not reach here."""
        styles, order = self.load()
        chosen, _, _ = nh.select(
            styles, order, self.ctx(Species="snapjaw", Faction="Grazing Hedonists")
        )
        self.assertNotIn("Snapjaw", nh.shares(chosen))

    def test_the_faction_scope_still_wins_for_faction_members(self):
        """Priority 50 is what keeps the change surgical. Exclusion is
        `other.priority > scope.priority`, so Faction at 100 with Combine="false" still clears the
        field for a creature actually in the tribe - it is named exactly as it was before."""
        styles, order = self.load(self.SPECIES_SCOPE)
        _, winner, _ = nh.select(
            styles, order, self.ctx(Species="snapjaw", Faction="Snapjaws")
        )
        self.assertEqual(winner, "Snapjaw")

    def test_the_added_scope_does_not_replace_the_vanilla_scopes(self):
        """Charter rule 1. Scopes are matched by Name, so the Vixy_ prefix is load-bearing: an
        unprefixed `Faction` would rewrite vanilla's in place instead of adding one."""
        styles, _ = self.load(self.SPECIES_SCOPE)
        names = [sc.name for sc in styles["Snapjaw"].scopes]
        self.assertIn(
            "Faction", names, "vanilla's faction scope must survive the merge"
        )
        self.assertIn("Vixy_Species", names)

    def test_the_pools_survive_a_scope_only_merge(self):
        """The other half of rule 1, and the thing the byte-identical sample proves in the game: a
        merge that states only scopes must not touch the syllables."""
        styles, _ = self.load(self.SPECIES_SCOPE)
        self.assertEqual([p[0] for p in styles["Snapjaw"].prefixes], ["gn"])
        self.assertEqual([p[0] for p in styles["Snapjaw"].postfixes], ["ak"])

    # -- Base= delegation ----------------------------------------------------------------------
    # NameStyle.Generate delegates before it builds anything: a style with a Base owns no pools and
    # hands the whole job to another style. #566; the harness could not follow this, so a fragment
    # using it measured as `0 0 0` and generated empty strings - indistinguishable from broken.

    def test_a_named_base_generates_from_the_delegated_style(self):
        styles, order = self.load(
            "<naming><namestyles>"
            '<namestyle Name="Vixy_Deleg" Base="Qudish" />'
            "</namestyles></naming>"
        )
        rng = random.Random(1)
        drawn = {
            nh.draw(styles["Vixy_Deleg"], rng, styles, order, self.ctx())
            for _ in range(30)
        }
        self.assertNotIn("", drawn, "a delegating style generated nothing")
        qudish = {nh.draw(styles["Qudish"], random.Random(1)) for _ in range(30)}
        self.assertTrue(
            drawn & qudish or drawn,
            "delegated names should come from the base style's pools",
        )

    def test_an_unresolvable_base_reports_the_games_own_string(self):
        """Vanilla returns "InvalidBase:" + Base as the creature's NAME, not as a log line."""
        styles, order = self.load(
            "<naming><namestyles>"
            '<namestyle Name="Vixy_Deleg" Base="Nonesuch" />'
            "</namestyles></naming>"
        )
        self.assertEqual(
            nh.draw(styles["Vixy_Deleg"], random.Random(1), styles, order, self.ctx()),
            "InvalidBase:Nonesuch",
        )

    def test_a_two_style_cycle_is_refused_rather_than_hanging(self):
        """The deliberate divergence. Vanilla accumulates Skip/SkipList on the named path and reads
        them only in NameStyles.Generate, which a named base never reaches - so the game recurses
        until the stack overflows (#625). A tool that hangs is worth less than one that reports."""
        styles, order = self.load(
            "<naming><namestyles>"
            '<namestyle Name="Vixy_A" Base="Vixy_B" />'
            '<namestyle Name="Vixy_B" Base="Vixy_A" />'
            "</namestyles></naming>"
        )
        with self.assertRaises(nh.BaseCycle) as caught:
            nh.draw(styles["Vixy_A"], random.Random(1), styles, order, self.ctx())
        self.assertIn("Vixy_A", str(caught.exception))
        self.assertIn("Vixy_B", str(caught.exception))

    def test_a_style_basing_on_itself_is_refused(self):
        styles, order = self.load(
            "<naming><namestyles>"
            '<namestyle Name="Vixy_Self" Base="Vixy_Self" />'
            "</namestyles></naming>"
        )
        with self.assertRaises(nh.BaseCycle):
            nh.draw(styles["Vixy_Self"], random.Random(1), styles, order, self.ctx())

    def test_star_base_re_enters_selection_and_skips_the_delegator(self):
        """Base="*" hands selection back. The skip set is what stops it choosing itself forever."""
        styles, order = self.load(
            "<naming><namestyles>"
            '<namestyle Name="Vixy_Star" Base="*">'
            '<scopes><scope Name="Vixy_Star" Species="frog" Priority="500" Combine="false" /></scopes>'
            "</namestyle>"
            "</namestyles></naming>"
        )
        ctx = self.ctx(Species="frog")
        drawn = nh.draw(styles["Vixy_Star"], random.Random(1), styles, order, ctx)
        self.assertNotIn("InvalidBase", drawn)

    def test_selection_honours_the_skip_set(self):
        """The one place vanilla reads Skip/SkipList: `if (nameStyle == Skip ...) continue`."""
        styles, order = self.load()
        ctx = self.ctx()
        _, winner, _ = nh.select(styles, order, ctx)
        self.assertEqual(winner, "Qudish")
        _, skipped, _ = nh.select(styles, order, ctx, skip={"Qudish"})
        self.assertNotEqual(skipped, "Qudish")

    def test_a_flat_style_still_draws_without_the_table(self):
        """The signature grew three optional arguments; every existing caller passes none of them."""
        styles, _ = self.load()
        self.assertTrue(nh.draw(styles["Qudish"], random.Random(1)))

    def test_priority_zero_is_skipped_in_a_weighted_draw(self):
        """Qudish at General/0 loses every share to any positive-priority combining style."""
        styles, order = self.load("""
        <naming Load="Merge"><namestyles><namestyle Name="Vixy_Fem" Format="TitleCase">
          <scopes><scope Name="G" Gender="female" Priority="50" Combine="true" /></scopes>
          <prefixes Amount="1"><prefix Name="zz" /></prefixes>
        </namestyle></namestyles></naming>""")
        chosen, _, _ = nh.select(styles, order, self.ctx(Gender="female"))
        self.assertEqual(nh.shares(chosen), {"Vixy_Fem": 1.0})

    def test_shares_split_by_priority_when_both_are_positive(self):
        styles, order = self.load("""
        <naming Load="Merge"><namestyles><namestyle Name="Vixy_Fem" Format="TitleCase">
          <scopes><scope Name="G" Gender="female" Priority="50" Combine="true" /></scopes>
          <prefixes Amount="1"><prefix Name="zz" /></prefixes>
        </namestyle></namestyles></naming>""")
        chosen, _, _ = nh.select(
            styles, order, self.ctx(Gender="female", Culture="Qudish")
        )
        self.assertEqual(nh.shares(chosen), {"Qudish": 100 / 150, "Vixy_Fem": 50 / 150})

    def test_a_tag_scope_only_fires_when_the_tag_is_set(self):
        styles, order = self.load("""
        <naming Load="Merge"><namestyles><namestyle Name="Vixy_Fem" Format="TitleCase">
          <scopes><scope Name="T" Tag="Vixy_Femme" Priority="200" Combine="false" /></scopes>
          <prefixes Amount="1"><prefix Name="zz" /></prefixes>
        </namestyle></namestyles></naming>""")
        _, without, _ = nh.select(styles, order, self.ctx(Gender="male"))
        _, with_tag, _ = nh.select(
            styles, order, self.ctx(Gender="male", Tag="Vixy_Femme")
        )
        self.assertEqual(without, "Qudish")
        self.assertEqual(with_tag, "Vixy_Fem")

    # -- reporting -----------------------------------------------------------------------------

    def test_ascii_violations_finds_diacritics(self):
        styles, _ = self.load("""
        <naming Load="Merge"><namestyles><namestyle Name="Qudish">
          <prefixes><prefix Name="née" /></prefixes>
        </namestyle></namestyles></naming>""")
        self.assertEqual(nh.ascii_violations(styles), [("Qudish", "née")])

    def test_ascii_violations_quiet_on_clean_input(self):
        styles, _ = self.load()
        self.assertEqual(nh.ascii_violations(styles), [])

    def test_amount_spec_rolls_a_range(self):
        rng = random.Random(3)
        self.assertEqual(nh.roll("1", rng), 1)
        self.assertTrue(all(0 <= nh.roll("0-2", rng) <= 2 for _ in range(30)))

    def test_parse_ctx_rejects_an_unknown_field(self):
        with self.assertRaises(SystemExit):
            nh.parse_ctx("Speceis=human")


VANILLA_GENDERS = """
<genders EnableSelection="false">
  <gender Name="neuter" Subjective="it" Objective="it" PossessiveAdjective="its"
          SubstantivePossessive="its" Reflexive="itself" UseBareIndicative="true"
          DoNotReplicateAsPronounSet="true" />
  <gender Name="male" Subjective="he" Objective="him" PossessiveAdjective="his"
          SubstantivePossessive="his" Reflexive="himself" PersonTerm="man" />
  <gender Name="plural" Subjective="they" Objective="them" PossessiveAdjective="their"
          SubstantivePossessive="theirs" Reflexive="themselves" Plural="true" />
  <gender Name="elverson" Generic="false" Subjective="ey" Objective="em"
          PossessiveAdjective="eir" SubstantivePossessive="eirs" Reflexive="emself"
          PersonTerm="person" SiblingTerm="sibling" ParentTerm="parent" />
</genders>
"""

XE = (
    '<genders><gender Name="xe" Subjective="xe" Objective="xem" PossessiveAdjective="xyr"'
    ' SubstantivePossessive="xyrs" Reflexive="xemself" PersonTerm="person"'
    ' SiblingTerm="sibling" ParentTerm="parent" %s /></genders>'
)

HANDWRITTEN = [
    {"Name": "player", "Abstract": "true", "Subjective": "you"},
    {
        "Subjective": "xe",
        "Objective": "xem",
        "PossessiveAdjective": "xyr",
        "SubstantivePossessive": "xyrs",
        "Reflexive": "xemself",
    },
]


class GenderTest(unittest.TestCase):
    """The chargen lists, predicted.

    Both failure modes here are silent: a gender that never appears in the row, and two entries a
    player cannot tell apart. Neither errors, and neither is visible without starting a new game.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def load(self, *fragments: str):
        genders: dict[str, dict] = {}
        nh.load_genders(
            write(self.tmp, "g.xml", VANILLA_GENDERS), genders, is_mod=False
        )
        for i, frag in enumerate(fragments):
            nh.load_genders(write(self.tmp, f"m{i}.xml", frag), genders, is_mod=True)
        return genders

    # -- the loader ----------------------------------------------------------------------------

    def test_touching_one_attribute_leaves_the_rest(self):
        """LoadGenderNode has no Load attribute: it reuses the entry and overwrites only what is
        stated. Merge is the only behaviour, so unhiding a gender cannot lose its pronouns."""
        genders = self.load(
            '<genders><gender Name="elverson" Generic="true" /></genders>'
        )
        self.assertEqual(genders["elverson"]["Generic"], "true")
        self.assertEqual(genders["elverson"]["Subjective"], "ey")
        self.assertEqual(genders["elverson"]["ParentTerm"], "parent")

    def test_a_new_gender_defaults_to_generic(self):
        """new Gender(name, _Generic: true) -- an addition reaches chargen without saying so."""
        genders = self.load('<genders><gender Name="fae" Subjective="fae" /></genders>')
        self.assertIn("fae", nh.chargen_genders(genders))

    # -- the gender row ------------------------------------------------------------------------

    def test_the_gender_row_filter(self):
        """Generic && !UseBareIndicative && !Plural, so this fixture offers only male."""
        self.assertEqual(nh.chargen_genders(self.load()), ["male"])

    def test_unhiding_elverson_puts_it_in_the_row(self):
        genders = self.load(
            '<genders><gender Name="elverson" Generic="true" /></genders>'
        )
        self.assertIn("elverson", nh.chargen_genders(genders))

    # -- the pronoun set row -------------------------------------------------------------------

    def test_an_abstract_hand_written_set_is_not_offered(self):
        sets = nh.chargen_pronoun_sets(self.load(), HANDWRITTEN)
        self.assertFalse(any(entry.startswith("you/") for entry in sets), sets)

    def test_promoting_without_the_flag_duplicates_the_hand_written_set(self):
        """The replica's name carries the person terms, so a promoted gender whose terms differ
        does NOT collide with the set it was promoted from -- it appears twice."""
        sets = nh.chargen_pronoun_sets(self.load(XE % ""), HANDWRITTEN)
        self.assertEqual(nh.duplicate_pronouns(sets), ["xe/xem/xyr/xyrs/xemself"])

    def test_the_flag_prevents_the_duplicate(self):
        genders = self.load(XE % 'DoNotReplicateAsPronounSet="true"')
        sets = nh.chargen_pronoun_sets(genders, HANDWRITTEN)
        self.assertEqual(nh.duplicate_pronouns(sets), [])
        self.assertIn("xe", nh.chargen_genders(genders), "the gender is still offered")

    def test_a_genuinely_new_gender_brings_its_pronoun_set_with_it(self):
        genders = self.load(
            '<genders><gender Name="fae" Subjective="fae" Objective="faer"'
            ' PossessiveAdjective="faer" SubstantivePossessive="faers"'
            ' Reflexive="faerself" /></genders>'
        )
        sets = nh.chargen_pronoun_sets(genders, HANDWRITTEN)
        self.assertTrue(any(e.startswith("fae/faer/") for e in sets), sets)

    def test_pronoun_set_name_fills_the_term_defaults(self):
        """A gender stating no person terms still names its replica with all eleven forms."""
        name = nh.pronoun_set_name({"Subjective": "ne", "Objective": "nem"})
        self.assertTrue(name.endswith("/human/child/friend/child/sib/progenitor"), name)

    def test_enable_selection_is_read_from_the_root(self):
        genders: dict[str, dict] = {}
        base = write(self.tmp, "v.xml", VANILLA_GENDERS)
        mod = write(self.tmp, "m.xml", '<genders EnableSelection="true"></genders>')
        self.assertIs(nh.load_genders(base, genders, is_mod=False), False)
        self.assertIs(nh.load_genders(mod, genders, is_mod=True), True)

    def test_a_fragment_stating_nothing_leaves_selection_alone(self):
        genders: dict[str, dict] = {}
        mod = write(self.tmp, "m.xml", '<genders><gender Name="fae" /></genders>')
        self.assertIsNone(nh.load_genders(mod, genders, is_mod=True))


if __name__ == "__main__":
    unittest.main()
