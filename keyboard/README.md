# BCORNE (DH747) — Vial config

Full visual reference, tuning values, and the transition plan:
https://claude.ai/code/artifact/34fdc244-9b67-4be9-a69b-d23635e9f4e2

## Files

| File | What it is |
| --- | --- |
| `corne-ergo.vil` | The layout. Load with Vial → File → Load Saved Layout. |
| `stock_keymap_backup.json` | Raw keycodes read off the board on 2026-08-16, before any changes. |
| `restore_stock.py` | Writes that backup back to the board over raw HID. `python3 restore_stock.py` |
| `gen_vil.py` | Regenerates `corne-ergo.vil`. Edit the layer tables at the top, then `python3 gen_vil.py corne-ergo.vil`. |
| `rgbd.py` | Layer-aware per-key RGB daemon. Runs as a systemd user service. |
| `apply_vil.py` | Diff the board against the layout file, push only what changed, verify. |
| `keycodes.json` | Keycode name → number, learned from the board. Rebuild with `--learn`. |

## RGB

The firmware has no layer indicator, so `rgbd.py` does it from the host: it polls
the switch matrix over raw HID, works out the active layer from which thumb keys
are held, and paints only the keys that do something on that layer.

    at rest   home row mods tinted by which modifier they hold
              (magenta GUI, amber Alt, cyan Ctrl, green Shift),
              the three layer thumbs in their layer colours,
              everything else a faint cool wash
    NAV       teal — arrows and Home/PgDn/PgUp/End light up
    SYM       violet — every symbol position
    NUM       amber — the numpad block
    FUN       rose — F-keys, media, the two base-layer keys

Because the mod colours are decoded from the live keymap, the Linux and macOS
base layers light up differently on their own. That's the OS-mode indicator.

    systemctl --user status corne-rgb     is it running
    systemctl --user stop corne-rgb       hand the LEDs back to the firmware
    systemctl --user reload corne-rgb     re-read the keymap without restarting
    python3 rgbd.py --watch               print live layer/matrix state, no LEDs
    python3 rgbd.py --base mac            tell it macOS is the default base layer

**Vial**: nothing to remember. Vial and this daemon both talk to the same raw HID
endpoint, and two readers steal each other's replies — which is what made Vial
throw errors. The daemon now watches for the Vial GUI and releases the device
entirely while it's open, then reconnects and re-reads your keymap when Vial
closes, so edits land in the lighting for free.

On exit it puts back whatever effect the board had before. If it's ever killed
outright it remembers the real effect in `.rgbd-state.json`, so the next start
restores that rather than getting stuck in direct mode.

Costs about 0.7% of one core. LEDs sleep after 5 minutes idle and wake on a keypress.

If every 9th key stays dark, the firmware takes fewer LEDs per packet than assumed:
run with `--leds-per-packet 8` and edit `LEDS_PER_PACKET` in `rgbd.py`.

## Board facts (read from the device, not guessed)

- USB `6401:45d4`, Vial protocol 6, VIA protocol 9, UID `5010774632021243529`
- Matrix 10 rows × 7 cols, 60 keys + 2 encoders, 6 layers
- 16 combo / 16 tap-dance / 16 key-override slots, 15 macros
- QMK Settings supported over the wire, so tapping term is tunable in the GUI — no reflash

## After loading

Set these in Vial's **QMK Settings** tab. Home row mods do not work properly without them.

    Tapping Term             200 ms
    Permissive Hold          ON
    Chordal Hold             ON     <- bilateral rule enforced in firmware
    Hold On Other Key Press  OFF    <- must be off, it breaks cross-hand rolls
    Quick Tap Term           0 ms
    Retro Tapping            OFF
    Combo Term               40 ms

The Tap-Hold tab has four checkboxes and only two want ticking: Permissive Hold
and Chordal Hold on, Hold On Other Key Press and Retro Tapping off.
Verified applied on the board 2026-08-17.

## Knobs

Left knob is the editing knob. It sends bare arrows, so modifiers compose:

    turn                     move by character
    right Ctrl (K) + turn    move by word
    right Shift (J) + turn   select by character
    K + J + turn             select by word
    NAV + turn               move by line      (+Shift selects lines)
    NUM + turn               Home / End        (+Shift selects to line end)
    SYM + turn               Backspace/Delete  (+Ctrl deletes words)
    FUN + turn               previous / next track

    press                    middle click
    NAV + press              copy
    SYM + press              paste
    FUN + press              mute

Right knob: scroll. NAV = pointer up/down. FUN = volume. Press = left click.

Use the *right* hand's Ctrl and Shift — the knob sits under your left index and
same-hand chords produce no modifier.

## Caps Word does not exist on this firmware

Vial resolves an unknown keycode name to `KC_NO` and says nothing, so `CW_TOGG`
looked installed while doing nothing at all. The `,`+`.` combo is Caps Lock now,
and NAV+Q is a one-shot Shift. After any Vial load, run:

    python3 apply_vil.py corne-ergo.vil --verify

which flags every keycode that silently became `KC_NO`.

## Layers

    0  Base — Linux    default
    1  Base — macOS    FUN + X to switch (FUN + Z back to Linux)
    2  Nav             hold left middle thumb
    3  Sym             hold right middle thumb
    4  Num             hold left outer thumb
    5  Fun             hold right outer thumb

Home row mods: `A S D F` = GUI Alt Ctrl Shift, mirrored on `; L K J`.
Always chord across hands — left-hand modifier, right-hand key.

## Note

Kinto was removed on 2026-08-16 (it did macOS-style remapping in software, which
double-swapped against layer 1). Archived at
`~/backups/kinto-removed-2026-08-16.tar.gz`.
