# bcorne

Layout, tuning and host tooling for my **BCORNE (DH747)** — a 4x6+3+1 split
running Vial-compatible QMK, with two rotary encoders on the inner home row.

Nothing here reflashes the board. The layout goes over raw HID and the QMK
settings are tunable over the wire, so the normal loop never leaves userspace.

## Start here

| I want to… | Go to |
|---|---|
| Find a key | [`docs/layout.md`](docs/layout.md) |
| Understand why a chord misfired | [`docs/behavior.md`](docs/behavior.md) |
| Change the layout, or fix the lighting | [`docs/operations.md`](docs/operations.md) |

Interactive reference — pick a layer, or just type and the board follows:
<https://claude.ai/artifact/SYVLcd56Qw2yRW53JY6Yxv>

Generated from `gen_vil.py`, so it cannot disagree with the firmware. It
replaces the earlier hand-built reference, which was missing F2–F4, F7–F9, the
RGB controls on FUN's top row, `FUN+K` mute, the NUM thumb row, and the macOS
Cmd swap.

## The shape of it

```
 Esc    1     2     3     4     5   |   `             \   |   6     7     8     9     0    Bksp
 Tab    Q     W     E     R     T   |   [             ]   |   Y     U     I     O     P    Del
 Shift  A     S     D     F     G   | (o)MClk    LClk(o)  |   H     J     K     L     ;     '
        gui   alt   ctl   sft                                       sft   ctl   alt   gui
 Ctrl   Z     X     C     V     B   |                     |   N     M     ,     .     /    Enter

                          NUM   NAV   Space       Bksp   SYM   FUN
```

Home-row mods chord **across hands** — left-hand modifier, right-hand key.
Chordal Hold enforces it in firmware. The outer-column `Shift` and `Ctrl` are
plain modifiers and ignore that rule, which is the escape hatch.

## Setup on the Linux host

The tooling expects to live at `~/keyboard`:

```
git clone git@github.com:muthukumaranR/akorn.git ~/src/akorn
ln -s ~/src/akorn/keyboard ~/keyboard
```

Then Vial → File → Load Saved Layout → `corne-ergo.vil`, and set the QMK
Settings listed in [`docs/behavior.md`](docs/behavior.md#tap-hold-settings).

## Repo map

| Path | Holds |
|---|---|
| `keyboard/` | The working directory: scripts, layout, keycode table, factory backup |
| `docs/` | Layout, behavior, operations |
| `LICENSE` | Unlicense (public domain) |

## Board facts

Read from the device, not guessed.

- USB `6401:45d4`, Vial protocol 6, VIA protocol 9, UID `5010774632021243529`
- Matrix 10 rows x 7 cols, 60 keys + 2 encoders, 6 layers
- 16 combo / 16 tap-dance / 16 key-override slots, 15 macros
- QMK Settings supported over the wire, so tapping term is tunable in the GUI — no reflash

## Known gaps

- **`corne-rgb.service` is not in this repo.** The unit file lives only on the
  Linux host. Copy it into `systemd/` so a rebuild doesn't lose it.
- `docs/` is written by hand from the tables in `gen_vil.py`. Nothing checks
  that the two agree — if you change a layer, change both.
