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


if __name__ == "__main__":
    unittest.main()
