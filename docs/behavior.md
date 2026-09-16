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
