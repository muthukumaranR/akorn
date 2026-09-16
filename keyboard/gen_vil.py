#!/usr/bin/env python3
"""Generate a .vil for the DH747 BCORNE (4x6+3+1 split, 10x7 matrix, 6 layers, 2 encoders).

Physical -> matrix map was read directly off the device (Vial definition), not guessed.
Columns per half: c0=outer pinky, c1=pinky, c2=ring, c3=middle, c4=index,
c5=inner index, c6=extra inner.  Rows A(number) B C(home) D, then 3 thumbs.
"""
import json

UID = 5010774632021243529
ROWS, COLS, LAYERS, ENCODERS = 10, 7, 6, 2

L = {  # left half: physical -> (matrix_row, matrix_col)
    "A": [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (1, 6)],
    "B": [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (2, 6)],
    "C": [(2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (3, 6)],
    "D": [(3, 0), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5)],
    "T": [(4, 3), (4, 4), (4, 5)],          # outer, middle, inner(big)
}
R = {  # right half
    "A": [(6, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6)],
    "B": [(7, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6)],
    "C": [(8, 0), (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6)],
    "D": [(8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 6)],
    "T": [(9, 1), (9, 2), (9, 3)],          # inner(big), middle, outer
}

_ = "KC_TRNS"

# ---------------------------------------------------------------- layer 0: base (Linux)
BASE_L = {
    "A": ["KC_ESC", "KC_1", "KC_2", "KC_3", "KC_4", "KC_5", "KC_GRV"],
    "B": ["KC_TAB", "KC_Q", "KC_W", "KC_E", "KC_R", "KC_T", "KC_LBRC"],
    # inner-column home keys carry media transport (your edit, kept):
    # - and = still live on SYM+F and SYM+J
    "C": ["KC_LSFT", "LGUI_T(KC_A)", "LALT_T(KC_S)", "LCTL_T(KC_D)", "LSFT_T(KC_F)", "KC_G", "KC_MS_BTN3"],
    "D": ["KC_LCTL", "KC_Z", "KC_X", "KC_C", "KC_V", "KC_B"],
    "T": ["LT(4,KC_TAB)", "LT(2,KC_ESC)", "KC_BSPC"],  # hold NUM/NAV, tap Tab/Esc. inner: Bksp
}
BASE_R = {
    "A": ["KC_BSLS", "KC_6", "KC_7", "KC_8", "KC_9", "KC_0", "KC_BSPC"],
    "B": ["KC_RBRC", "KC_Y", "KC_U", "KC_I", "KC_O", "KC_P", "KC_DEL"],
    "C": ["KC_MS_BTN1", "KC_H", "RSFT_T(KC_J)", "RCTL_T(KC_K)", "LALT_T(KC_L)", "RGUI_T(KC_SCLN)", "KC_QUOT"],
    "D": ["KC_N", "KC_M", "KC_COMM", "KC_DOT", "KC_SLSH", "KC_ENT"],
    "T": ["KC_SPC", "MO(3)", "LT(5,KC_ENT)"],  # inner: Space. outer: hold FUN / tap Enter
}

# ---------------------------------------------------------------- layer 1: base (macOS)
# Same board, primary modifier stays on the middle finger: Cmd where Ctrl was.
MAC_L = dict(BASE_L)
MAC_L["D"] = ["KC_LGUI", "KC_Z", "KC_X", "KC_C", "KC_V", "KC_B"]
MAC_L["C"] = ["KC_LSFT", "LCTL_T(KC_A)", "LALT_T(KC_S)", "LGUI_T(KC_D)", "LSFT_T(KC_F)", "KC_G", "KC_MS_BTN3"]
MAC_R = dict(BASE_R)
MAC_R["C"] = ["KC_MS_BTN1", "KC_H", "RSFT_T(KC_J)", "RGUI_T(KC_K)", "LALT_T(KC_L)", "RCTL_T(KC_SCLN)", "KC_QUOT"]

# ---------------------------------------------------------------- layer 2: NAV (left middle thumb)
NAV_L = {
    "A": [_] * 7,
    "B": [_, "OSM(MOD_LSFT)", "KC_CAPS", "KC_INS", "KC_PSCR", _, _],
    "C": [_, "KC_LGUI", "KC_LALT", "KC_LCTL", "KC_LSFT", _, "LCTL(KC_C)"],
    "D": [_] * 6,
    "T": [_, _, _],
}
NAV_R = {
    "A": [_] * 7,
    "B": [_, _, "KC_HOME", "KC_PGDN", "KC_PGUP", "KC_END", _],
    "C": [_, "KC_DEL", "KC_LEFT", "KC_DOWN", "KC_UP", "KC_RGHT", _],
    "D": [_] * 6,
    "T": [_, "MO(5)", _],
}

# ---------------------------------------------------------------- layer 3: SYM (right middle thumb)
SYM_L = {
    "A": [_] * 7,
    "B": [_, "KC_EXLM", "KC_AT", "KC_HASH", "KC_DLR", "KC_PERC", _],
    "C": [_, "KC_GRV", "KC_TILD", "KC_PIPE", "KC_MINS", "KC_BSLS", "LCTL(KC_V)"],
    "D": [_] * 6,
    "T": [_, "MO(5)", _],
}
SYM_R = {
    "A": [_] * 7,
    "B": [_, "KC_CIRC", "KC_AMPR", "KC_ASTR", "KC_LPRN", "KC_RPRN", _],
    "C": [_, "KC_PLUS", "KC_EQL", "KC_UNDS", "KC_LCBR", "KC_RCBR", _],
    "D": [_, _, "KC_LT", "KC_GT", "KC_QUES", _],
    "T": [_, _, _],
}

# ---------------------------------------------------------------- layer 4: NUM (left outer thumb)
NUM_L = {
    "A": [_] * 7,
    "B": [_] * 7,
    "C": [_, "KC_LGUI", "KC_LALT", "KC_LCTL", "KC_LSFT", _, _],
    "D": [_] * 6,
    "T": [_, _, _],
}
NUM_R = {
    "A": [_] * 7,
    "B": [_, "KC_ASTR", "KC_7", "KC_8", "KC_9", "KC_MINS", _],
    "C": [_, "KC_SLSH", "KC_4", "KC_5", "KC_6", "KC_PLUS", _],
    "D": ["KC_COMM", "KC_1", "KC_2", "KC_3", "KC_EQL", _],
    "T": ["KC_0", "KC_DOT", "KC_ENT"],
}

# ---------------------------------------------------------------- layer 5: FUN (NAV + SYM)
FUN_L = {
    "A": ["QK_BOOT", "KC_F1", "KC_F2", "KC_F3", "KC_F4", "KC_F5", "KC_F11"],
    "B": [_, "RGB_TOG", "RGB_MOD", "RGB_VAD", "RGB_VAI", _, _],
    "C": [_, "KC_LGUI", "KC_LALT", "KC_LCTL", "KC_LSFT", _, "KC_MUTE"],
    "D": [_, "DF(0)", "DF(1)", _, _, _],
    "T": [_, _, _],
}
FUN_R = {
    "A": ["KC_F12", "KC_F6", "KC_F7", "KC_F8", "KC_F9", "KC_F10", _],
    "B": [_, _, "KC_MPRV", "KC_MPLY", "KC_MNXT", _, _],
    "C": ["KC_MPLY", _, "KC_VOLD", "KC_MUTE", "KC_VOLU", _, _],
    "D": [_, "KC_BRID", _, "KC_BRIU", _, _],
    "T": [_, _, _],
}

LAYER_DEFS = [
    ("BASE-LINUX", BASE_L, BASE_R),
    ("BASE-MACOS", MAC_L, MAC_R),
    ("NAV", NAV_L, NAV_R),
    ("SYM", SYM_L, SYM_R),
    ("NUM", NUM_L, NUM_R),
    ("FUN", FUN_L, FUN_R),
]

# [layer][encoder idx] = [ccw, cw];  idx 0 = left half, 1 = right half.
#
# The left knob is the editing knob. It sends bare arrows, so the modifiers you
# are already holding do the work: Ctrl turns character into word, Shift turns
# movement into selection, both together select by word. Only the four rows
# below need configuring; every combination composes on top of them for free.
ENCODER = [
    [["TD(0)", "TD(1)"], ["KC_MS_WH_UP", "KC_MS_WH_DOWN"]],       # base: char  | scroll
    [["TD(0)", "TD(1)"], ["KC_MS_WH_UP", "KC_MS_WH_DOWN"]],       # mac
    [["KC_UP", "KC_DOWN"],   ["KC_MS_UP", "KC_MS_DOWN"]],         # NAV:  line  | pointer
    [["KC_BSPC", "KC_DEL"],  [_, _]],                             # SYM:  delete
    [["KC_HOME", "KC_END"],  [_, _]],                             # NUM:  line ends
    [["KC_MPRV", "KC_MNXT"], ["KC_VOLD", "KC_VOLU"]],             # FUN:  media | volume
]

COMBOS = [
    ["KC_COMM", "KC_DOT", "KC_NO", "KC_NO", "KC_CAPS"],   # , + .  -> Caps Lock (Caps Word is unsupported here)
    ["KC_Y", "KC_H", "KC_NO", "KC_NO", "KC_ESC"],         # Y + H  -> Esc
]
COMBOS += [["KC_NO"] * 5] * (16 - len(COMBOS))

TAP_DANCE = [["KC_NO", "KC_NO", "KC_NO", "KC_NO", 200] for _i in range(16)]
# [on_tap, on_hold, on_double_tap, on_tap_hold, term]
# A single stray pulse does nothing; the pair the encoder actually sends
# resolves as a double tap and emits exactly one arrow.
TAP_DANCE[0] = ["KC_NO", "KC_NO", "KC_LEFT", "KC_NO", 45]
TAP_DANCE[1] = ["KC_NO", "KC_NO", "KC_RGHT", "KC_NO", 45]
MACRO = [[] for _i in range(15)]


def build():
    layout = []
    for name, left, right in LAYER_DEFS:
        grid = [["KC_NO"] * COLS for _r in range(ROWS)]
        for half, posmap in ((left, L), (right, R)):
            for rowname, positions in posmap.items():
                keys = half[rowname]
                assert len(keys) == len(positions), f"{name} {rowname}: {len(keys)} vs {len(positions)}"
                for kc, (mr, mc) in zip(keys, positions):
                    assert grid[mr][mc] == "KC_NO", f"collision at {mr},{mc}"
                    grid[mr][mc] = kc
        layout.append(grid)
    return {
        "version": 1,
        "uid": UID,
        "layout": layout,
        "encoder_layout": ENCODER,
        "layout_options": -1,
        "macro": MACRO,
        "vial_protocol": 6,
        "via_protocol": 9,
        "tap_dance": TAP_DANCE,
        "combo": COMBOS,
        "settings": {},
    }


if __name__ == "__main__":
    import sys
    data = build()
    with open(sys.argv[1], "w") as f:
        json.dump(data, f, indent=1)
    print(f"wrote {sys.argv[1]}")
