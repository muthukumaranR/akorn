# Operations

Everything runs from the `keyboard/` directory on the Linux host. Standard
library only, no root.

## Files

| File | What it is |
|---|---|
| `corne-ergo.vil` | The layout. Load with Vial → File → Load Saved Layout. |
| `gen_vil.py` | Regenerates `corne-ergo.vil` from the tables at the top of the file. |
| `apply_vil.py` | Diff the board against the layout file, push only what changed, verify. |
| `rgbd.py` | Layer-aware per-key RGB daemon. Runs as a systemd user service. |
| `restore_stock.py` | Writes `stock_keymap_backup.json` back to the board over raw HID. |
| `keycodes.json` | Keycode name → number, learned from the board. Rebuild with `--learn`. |
| `stock_keymap_backup.json` | Raw keycodes read off the board on 2026-08-16, before any changes. |

## The edit loop

```
$EDITOR keyboard/gen_vil.py            # edit the layer tables at the top
python3 keyboard/gen_vil.py keyboard/corne-ergo.vil
python3 keyboard/apply_vil.py          # review the diff
python3 keyboard/apply_vil.py --write  # push only what differs, then verify
```

`apply_vil.py` defaults to `corne-ergo.vil` next to itself, so the bare command
is usually enough.

| Flag | Does |
|---|---|
| *(none)* | Show what differs between the board and the layout file. |
| `--write` | Apply the diff and verify it. Only touches keys that differ. |
| `--verify` | After a Vial load: find keycodes that silently became `KC_NO`. |
| `--learn` | Rebuild `keycodes.json` by pairing the file with the board. |

## Caps Word does not exist here

Vial resolves an unknown keycode name to `KC_NO` and says nothing, so `CW_TOGG`
looked installed while doing nothing at all. The `,` + `.` combo is Caps Lock
now, and `NAV + Q` is a one-shot Shift.

**After any Vial load, run:**

```
python3 keyboard/apply_vil.py corne-ergo.vil --verify
```

which flags every keycode that silently became `KC_NO`.

## Lighting

The firmware has no layer indicator, so `rgbd.py` does it from the host: it
polls the switch matrix over raw HID, works out the active layer from which
thumb keys are held, and paints only the keys that do something on that layer.

| State | Looks like |
|---|---|
| at rest | home-row mods tinted by which modifier they hold, the three layer thumbs in their layer colours, everything else a faint cool wash |
| NAV | teal — arrows and Home/PgDn/PgUp/End |
| SYM | violet — every symbol position |
| NUM | amber — the numpad block |
| FUN | rose — F-keys, media, the two base-layer keys |

Palette (`LAYER_COLOR` / `MOD_COLOR` in `rgbd.py`):

| | RGB | | | RGB |
|---|---|---|---|---|
| NAV teal | `0, 205, 180` | | GUI / Cmd | `230, 80, 200` |
| SYM violet | `150, 110, 255` | | Alt | `255, 150, 30` |
| NUM amber | `255, 155, 20` | | Ctrl | `60, 190, 255` |
| FUN rose | `255, 75, 110` | | Shift | `90, 230, 120` |
| ground wash | `130, 150, 200` | | | |

Because the mod colours are decoded from the live keymap, the Linux and macOS
base layers light up differently on their own. **That is the OS-mode
indicator.**

| Command | Does |
|---|---|
| `systemctl --user status corne-rgb` | Is it running. |
| `systemctl --user restart corne-rgb` | The fix for most lighting oddities. |
| `systemctl --user reload corne-rgb` | Re-read the keymap without restarting. |
| `systemctl --user stop corne-rgb` | Hand the LEDs back to the firmware. |
| `journalctl --user -u corne-rgb -f` | Watch the daemon. |
| `python3 rgbd.py --watch` | Print live layer / matrix state, leave LEDs alone. |
| `python3 rgbd.py --base mac` | Tell it macOS is the default base layer. |

Other flags: `--brightness` (0.0–1.0, default 0.38), `--idle` (seconds before
LEDs sleep, default 300, 0 = never), `--hz` (matrix poll rate, default 60),
`--leds-per-packet`.

Costs about 0.7% of one core. LEDs sleep after 5 minutes idle and wake on a
keypress. On exit it restores whatever effect the board had before; if killed
outright it recovers the real effect from `.rgbd-state.json` on next start.

**Vial:** nothing to remember. Vial and the daemon both talk to the same raw HID
endpoint, and two readers steal each other's replies — which is what made Vial
throw errors. The daemon now watches for the Vial GUI and releases the device
entirely while it is open, then reconnects and re-reads the keymap when Vial
closes, so edits land in the lighting for free.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Stray letters instead of modifiers | Raise Tapping Term to 220 for a week. |
| Stray modifiers when typing fast | Check Hold On Other Key Press is off. Then try Flow Tap 150. |
| `fffff` when holding a home key | Quick Tap Term isn't 0. |
| Ctrl+C does nothing | Home-row Ctrl with a left-hand letter — Chordal Hold refuses it. Use `K`, or the plain Ctrl in the bottom-left corner. |
| Vial throws errors | Shouldn't happen; the daemon yields. If it does, `systemctl --user stop corne-rgb`. |
| LEDs stuck or wrong | `systemctl --user restart corne-rgb`. |
| Knob scrolls the wrong way | Swap the two entries on that encoder line in `gen_vil.py`. |
| Every 9th key dark | Firmware takes fewer LEDs per packet than assumed: run `--leds-per-packet 8` and edit `LEDS_PER_PACKET` in `rgbd.py`. |
| Keymap scrambled | `python3 apply_vil.py --write`, or `restore_stock.py` for the factory map. |
| A key silently does nothing after a Vial load | `apply_vil.py --verify` — it became `KC_NO`. |

## Recovery

1. `FUN + Esc` puts the board in the bootloader (`QK_BOOT`).
2. `python3 restore_stock.py` restores the 2026-08-16 factory keymap.
3. `python3 apply_vil.py --write` puts this repo's layout back on.

## History

Kinto was removed on 2026-08-16 — it did macOS-style remapping in software,
which double-swapped against layer 1. Archived at
`~/backups/kinto-removed-2026-08-16.tar.gz`.
