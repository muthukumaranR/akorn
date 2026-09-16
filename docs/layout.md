# Layout

Six layers. Source of truth is the tables at the top of
[`../keyboard/gen_vil.py`](../keyboard/gen_vil.py) — this file is written from
them. Edit there, regenerate, then update here.

| # | Layer | Reached by |
|---|---|---|
| 0 | Base — Linux | default (`FUN + Z`) |
| 1 | Base — macOS | `FUN + X` |
| 2 | NAV | hold left middle thumb |
| 3 | SYM | hold right middle thumb |
| 4 | NUM | hold left outer thumb |
| 5 | FUN | hold right outer thumb, **or** NAV + SYM together |

## Physical shape

Per half: 4 rows x 6 columns, plus a 3-key extra inner column whose home-row
position is a rotary encoder, plus 3 thumb keys. 60 keys + 2 encoders on a
10x7 matrix.

Rows are named `A` (number), `B`, `C` (home), `D` in `gen_vil.py`.
Columns: `c0` outer pinky, `c1` pinky, `c2` ring, `c3` middle, `c4` index,
`c5` inner index, `c6` extra inner.

## Layer 0 — Base (Linux)

```
 Esc    1     2     3     4     5   |   `             \   |   6     7     8     9     0    Bksp
 Tab    Q     W     E     R     T   |   [             ]   |   Y     U     I     O     P    Del
 Shift  A     S     D     F     G   | (o)MClk    LClk(o)  |   H     J     K     L     ;     '
        gui   alt   ctl   sft                                       sft   ctl   alt   gui
 Ctrl   Z     X     C     V     B   |                     |   N     M     ,     .     /    Enter

                          NUM   NAV   Bksp       Space   SYM   FUN
                          Tab                                        <- tap
                         outer   mid   inner      inner   mid  outer
```

`(o)` is a rotary encoder; the label is what pressing it does.
Small labels under the home row are the **hold** modifiers on those keys.

The outer column carries **plain** `Shift` and `Ctrl` — real modifiers, not
mod-taps. See [behavior.md](behavior.md#escape-hatch).

Reachable without holding anything:
`` ` `` `[` `]` `\` `'` `;` `,` `.` `/` `Esc` `Tab` `Enter` `Bksp` `Del` `Space`

> **Thumb taps:** the left outer thumb is `LT(4, KC_TAB)` — hold for NUM, tap
> for Tab. The other three layer thumbs are pure holds for now; see
> [behavior.md](behavior.md#thumb-taps) for why.

> **Thumbs:** Space is the **right** inner thumb, Backspace the **left** —
> swapped from the stock Corne arrangement so Space lands under the thumb that
> already spaced on a row-staggered board. Backspace also stays in its
> traditional spot at the top-right outer column.

## Layer 1 — Base (macOS)

Identical to Base except the primary modifier stays on the middle finger, so
**Cmd sits where Ctrl was**:

| | A | S | D | F | | J | K | L | ; | bottom-left outer |
|---|---|---|---|---|---|---|---|---|---|---|
| Linux | GUI | Alt | **Ctrl** | Shift | | Shift | **Ctrl** | Alt | GUI | Ctrl |
| macOS | **Ctrl** | Alt | **GUI** | Shift | | Shift | **GUI** | Alt | **Ctrl** | GUI |

> Every shortcut table in [behavior.md](behavior.md) names the *Linux* keys.
> On macOS the same shortcuts move to `D` and `K` as Cmd.

## Layer 2 — NAV (hold left middle thumb)

| Key | Does | Key | Does |
|---|---|---|---|
| `Q` | One-shot Shift | `U` | Home |
| `W` | Caps Lock | `I` | PgDn |
| `E` | Insert | `O` | PgUp |
| `R` | PrtSc | `P` | End |
| `A` `S` `D` `F` | plain GUI / Alt / Ctrl / Shift | `H` | Delete |
| left encoder press | Copy (Ctrl+C) | `J` `K` `L` `;` | left / down / up / right |

Holding the **SYM** thumb as well reaches FUN.

## Layer 3 — SYM (hold right middle thumb)

| Key | Sym | Key | Sym |
|---|---|---|---|
| `Q` | `!` | `Y` | `^` |
| `W` | `@` | `U` | `&` |
| `E` | `#` | `I` | `*` |
| `R` | `$` | `O` | `(` |
| `T` | `%` | `P` | `)` |
| `A` | `` ` `` | `H` | `+` |
| `S` | `~` | `J` | `=` |
| `D` | `\|` | `K` | `_` |
| `F` | `-` | `L` | `{` |
| `G` | `\` | `;` | `}` |
| `,` | `<` | `.` | `>` |
| `/` | `?` | left encoder press | Paste (Ctrl+V) |

Holding the **NAV** thumb as well reaches FUN.

## Layer 4 — NUM (hold left outer thumb)

Numpad lives entirely on the right hand, so the left thumb holds and the right
hand types.

```
                    |   *     7     8     9     -
                    |   /     4     5     6     +
                    |   ,     1     2     3     =

                                  0     .    Enter      <- right thumbs
```

| Key | Num | Key | Num |
|---|---|---|---|
| `Y` | `*` | `N` | `,` |
| `U` `I` `O` | 7 8 9 | `M` `,` `.` | 1 2 3 |
| `H` | `/` | `/` | `=` |
| `J` `K` `L` | 4 5 6 | `P` | `-` |
| `;` | `+` | | |
| right inner thumb (Space) | `0` | SYM thumb | `.` |
| FUN thumb | Enter | `A` `S` `D` `F` | plain GUI / Alt / Ctrl / Shift |

## Layer 5 — FUN (hold right outer thumb, or NAV + SYM)

| Key | Does | Key | Does |
|---|---|---|---|
| `1`–`5` | F1–F5 | `6`–`0` | F6–F10 |
| `` ` `` | F11 | `\` | F12 |
| `Esc` | **Bootloader** (`QK_BOOT`) | `U` `I` `O` | prev / play-pause / next |
| `Q` | RGB on/off | `J` `K` `L` | Vol- / Mute / Vol+ |
| `W` | RGB next effect | `M` `.` | Brightness - / + |
| `E` `R` | RGB dimmer / brighter | left encoder press | Mute |
| `Z` | Linux base (`DF(0)`) | right encoder press | Play / Pause |
| `X` | macOS base (`DF(1)`) | `A` `S` `D` `F` | plain GUI / Alt / Ctrl / Shift |

> `Q` `W` `E` `R` drive the **firmware's** RGB. While `rgbd.py` is running it
> owns the LEDs and overrides them — stop the daemon to use these.

## Encoders

Index 0 is the left knob, 1 the right.

| Layer | Left knob (ccw / cw) | Right knob (ccw / cw) |
|---|---|---|
| Base, macOS | left / right arrow | scroll up / down |
| NAV | up / down (by line) | pointer up / down |
| SYM | Backspace / Delete | *transparent* — scrolls |
| NUM | Home / End | *transparent* — scrolls |
| FUN | prev / next track | volume - / + |

| Layer | Left press | Right press |
|---|---|---|
| Base, macOS | middle click | left click |
| NAV | Copy | *transparent* — left click |
| SYM | Paste | *transparent* — left click |
| NUM | *transparent* — middle click | *transparent* — left click |
| FUN | Mute | Play / Pause |

The base-layer arrows go through tap dance `TD(0)` / `TD(1)` with a 45 ms term,
firing on **double tap**. Each detent of this encoder sends a pair of pulses;
routing them through a double-tap makes the pair emit exactly one arrow, and a
single stray pulse emit nothing.

## Combos

Two of the 16 combo slots are used. Combo Term is 40 ms — tight enough that
ordinary typing never triggers them.

| Combo | Does |
|---|---|
| `,` + `.` | Caps Lock |
| `Y` + `H` | Esc, without the pinky |

Caps Word does not exist on this firmware — see
[operations.md](operations.md#caps-word-does-not-exist-here).
