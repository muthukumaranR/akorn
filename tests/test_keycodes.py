#!/usr/bin/env python3
"""The keycode composition rules, checked against numbers read off the board.

keycodes.json is ground truth: every entry was learned by pairing a .vil the
board already matched with its live keymap. If a rule here disagrees with any
of those, the rule is wrong, not the board.

Note the table holds no plain KC_A / KC_L: those letters only ever appear on
this board wrapped in a mod-tap, so the learner never saw them bare. The tests
below therefore verify structurally, deriving each inner keycode from the
board's own number rather than assuming a HID table.
"""
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, os.pardir, "keyboard"))

from apply_vil import MODBITS, QK_MOD_TAP, compose, resolve, check_resolver

TABLE = json.load(open(os.path.join(HERE, os.pardir, "keyboard", "keycodes.json")))
MOD_TAPS = {n: v for n, v in TABLE.items() if re.fullmatch(r"[A-Z]+_T\(.+\)", n)}


def split(name):
    mod, inner = name.split("_T(")
    return mod, inner.rstrip(")")


class TestModTapEncoding(unittest.TestCase):
    def test_the_board_has_mod_taps_to_check(self):
        self.assertGreaterEqual(len(MOD_TAPS), 10)

    def test_high_bits_are_the_range_bit_plus_the_modifier(self):
        """Everything above the low byte must be QK_MOD_TAP | mod << 8."""
        for name, code in MOD_TAPS.items():
            mod, _ = split(name)
            self.assertEqual(code & ~0xFF, QK_MOD_TAP | (MODBITS[mod] << 8), name)

    def test_the_same_letter_keeps_the_same_low_byte(self):
        """KC_A under LGUI and under LCTL must carry the identical inner code."""
        seen = {}
        for name, code in MOD_TAPS.items():
            _, inner = split(name)
            seen.setdefault(inner, []).append((name, code & 0xFF))
        shared = {k: v for k, v in seen.items() if len(v) > 1}
        self.assertTrue(shared, "no letter appears under two modifiers")
        for inner, entries in shared.items():
            lows = {low for _, low in entries}
            self.assertEqual(len(lows), 1, f"{inner} disagrees across {entries}")


class TestCompose(unittest.TestCase):
    def test_compose_reproduces_every_mod_tap_on_the_board(self):
        """Given the inner codes, compose must land on the board's own numbers."""
        full = dict(TABLE)
        for name, code in MOD_TAPS.items():
            full[split(name)[1]] = code & 0xFF
        for name, code in MOD_TAPS.items():
            self.assertEqual(compose(name, full), code, name)

    def test_a_mod_tap_the_board_has_never_seen_still_composes(self):
        self.assertNotIn("LALT_T(KC_ENT)", TABLE)
        self.assertEqual(resolve("LALT_T(KC_ENT)", TABLE),
                         QK_MOD_TAP | (MODBITS["LALT"] << 8) | TABLE["KC_ENT"])

    def test_wrapper_and_mod_tap_differ_by_the_range_bit(self):
        plain = resolve("LCTL(KC_C)", TABLE)
        tap = resolve("LCTL_T(KC_C)", TABLE)
        self.assertIsNotNone(plain)
        self.assertEqual(tap, plain | QK_MOD_TAP)

    def test_a_direct_entry_wins_over_composition(self):
        name, code = next(iter(MOD_TAPS.items()))
        self.assertEqual(resolve(name, TABLE), code)

    def test_unknown_shapes_resolve_to_nothing(self):
        """Anything the rules can't account for must fail loudly, not guess."""
        for name in ("LT(3,KC_ENT)", "NOPE(KC_A)", "LALT_T(KC_NOSUCHKEY)",
                     "KC_MADEUP", "OSM(MOD_LSFT)"):
            self.assertIsNone(compose(name, TABLE), name)

    def test_shipped_self_check_passes(self):
        check_resolver(TABLE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
