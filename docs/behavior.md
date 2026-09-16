# Behavior

## Home-row modifiers

| | A | S | D | F | | J | K | L | ; |
|---|---|---|---|---|---|---|---|---|---|
| **Linux** hold | GUI | Alt | Ctrl | Shift | | Shift | Ctrl | Alt | GUI |
| **macOS** hold | Ctrl | Alt | Cmd | Shift | | Shift | Cmd | Alt | Ctrl |

**The modifier goes on the hand opposite the letter.** Chordal Hold enforces
this in firmware: a same-hand chord resolves as a *tap*, which is what stops
"sad" and "ask" misfiring — and also means a same-hand chord produces no
modifier at all.

Shortcuts below name the **Linux** keys. On macOS the command key moves to
`D` / `K`.

| Want | Hold | Press |
|---|---|---|
| Undo, cut, copy, paste | `K` (right Ctrl) | Z X C V |
| Select all, save, find | `K` (right Ctrl) | A S F |
| New tab, close tab | `K` (right Ctrl) | T W |
| Reopen closed tab | `K` + `J` | T |
| Print, new, open | `D` (left Ctrl) | P N O |
| Alt+Tab | `L` (right Alt) | Tab |

### Escape hatch

The outer column carries plain `Shift` and `Ctrl` — real modifiers, not
mod-taps. No tapping term, no Chordal Hold, no handedness rule, so same-hand
`Ctrl+C` and `Shift+A` both work exactly as on a normal board. Shift sits at
the Caps Lock position with Ctrl below it, matching the order your hand already
knows.

The NAV, NUM and FUN layers also put plain `GUI Alt Ctrl Shift` on `A S D F`,
so you can hold a layer and chord one-handed there too. SYM is the exception —
those four keys carry `` ` `` `~` `|` `-` instead.

## The knobs

The left knob is the editing knob. It sends **bare arrows**, so the modifiers
you are already holding do the composing:

| Hold while turning | Get |
|---|---|
| nothing | move by character |
| `K` (right Ctrl) | move by word |
| `J` (right Shift) | select by character |
| `K` + `J` | select by word |
| NAV | move by line — add Shift to select lines |
| NUM | jump to start / end of line — add Shift to select to there |
| SYM | delete backwards / forwards — add Ctrl to delete whole words |

Only the four layer rows are configured; the rest fall out of the OS composing
modifiers with arrow keys. Use the **right hand's** Ctrl and Shift — the knob
sits under your left index, and same-hand chords produce no modifier.

Right knob: scroll. NAV = pointer up/down. FUN = volume. Press = left click.

Full per-layer table: [layout.md](layout.md#encoders).

## Tap-hold settings

Set these in Vial's **QMK Settings** tab. Home row mods do not work properly
without them. Supported over the wire, so no reflash is needed.

Verified applied on the board **2026-08-17**. This is the record if anything
resets.

| Setting | Value | Why |
|---|---|---|
| Tapping Term | 200 ms | Raise to 220 if you get stray letters. |
| Permissive Hold | **on** | Resolves a chord the moment the other key is released, so fast chords work. Rolls don't trigger it. |
| Chordal Hold | **on** | Same-hand chord = tap, never a modifier. Stops rolls misfiring. |
| Hold On Other Key Press | **off** | Must stay off — it turns cross-hand rolls like "an" into GUI+N. |
| Quick Tap Term | 0 ms | Stops tap-then-hold repeating the letter. |
| Retro Tapping | **off** | Would turn aborted chords into stray letters. |
| Flow Tap | 0 | Spare lever. 150 ms if misfires persist. |
| Combo Term | 40 ms | Tight enough that typing never triggers the combos. |

The Tap-Hold tab has four checkboxes and only two want ticking: Permissive Hold
and Chordal Hold on, Hold On Other Key Press and Retro Tapping off.

## Thumb taps

Each thumb key has two slots, a hold and a tap. The four layer thumbs use only
the hold; the two inner thumbs use only the tap. Filling the empty slots is
where the remaining room on this board is.

**The inner thumbs stay plain.** Space and Backspace are ordinary keycodes so
that holding them repeats. A mod-tap cannot repeat: Quick Tap Term is 0, which
is the same setting that stops `fffff` on the home row, and it is global — per
key control needs `get_quick_tap_term()` in firmware. Holding Backspace to
delete a run is worth more than any modifier that key could carry.

**The layer thumbs can take taps, with one caveat.** Chordal Hold applies to
layer-taps too, so if a thumb inherits its half's handedness, `LT()` refuses
same-hand keys and resolves as a tap instead. What that costs depends on where
the layer's keys live:

| Tap on | That layer's keys | Survives handedness |
|---|---|---|
| **NUM** (left outer) | entirely right hand | **yes, always** |
| NAV (left middle) | arrows right, `Q W E R` left | partly |
| FUN (right outer) | both hands | partly |
| SYM (right middle) | both hands | no — right-hand symbols break |

`LT(4, KC_TAB)` is therefore safe whatever the firmware does: NUM lives wholly
on the right hand, so holding it is always a cross-hand chord.

To settle the rest, set the right outer thumb to `LSFT_T(KC_ENT)` in Vial, then
hold it and tap `a` (expect `A`), then hold it and tap `j`. A capital `J` means
thumbs are exempt and all four taps are available. A newline means handedness
is enforced, and only the rows above marked yes or partly are.

`apply_vil.py` cannot encode `LT()` — the board has never reported one, so the
number is unverified. It refuses with a message pointing at Vial rather than
guessing. Load the `.vil` through Vial, then `--learn` on the Linux box.
