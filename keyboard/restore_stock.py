#!/usr/bin/env python3
"""Undo button.

Writes the keymap that was on the BCORNE before any of this back onto the board,
straight over raw HID. Reads stock_keymap_backup.json (raw numeric keycodes,
captured 2026-08-16 before the new layout was applied).

    python3 restore_stock.py

Nothing to install; plain hidraw + stdlib. Keyboard must be plugged in.
"""
import glob, json, os, struct, sys, time

MSG_LEN = 32
CMD_VIA_GET_PROTOCOL_VERSION = 0x01
CMD_VIA_SET_KEYCODE = 0x05

HERE = os.path.dirname(os.path.abspath(__file__))


def find_device():
    # numeric order: string sorting puts hidraw22 before hidraw9, and the
    # board re-enumerates often enough for that to matter
    paths = sorted(glob.glob("/dev/hidraw*"),
                   key=lambda p: int(p.rsplit("hidraw", 1)[1]))
    for path in paths:
        node = os.path.basename(path)
        try:
            with open(f"/sys/class/hidraw/{node}/device/uevent") as f:
                uevent = f.read().upper()
        except OSError:
            continue
        if "45D4" not in uevent or "6401" not in uevent:
            continue
        try:
            fd = os.open(path, os.O_RDWR | os.O_NONBLOCK)
        except OSError:
            continue
        if rw(fd, struct.pack("B", CMD_VIA_GET_PROTOCOL_VERSION), retries=5):
            return path, fd
        os.close(fd)
    return None, None


def rw(fd, data, retries=40):
    payload = data + b"\x00" * (MSG_LEN - len(data))
    for _ in range(retries):
        os.write(fd, b"\x00" + payload)
        for _ in range(200):
            try:
                r = os.read(fd, MSG_LEN)
                if r:
                    return r
            except BlockingIOError:
                time.sleep(0.002)
        time.sleep(0.01)
    return None


def main():
    backup = json.load(open(os.path.join(HERE, "stock_keymap_backup.json")))
    keymap = backup["keymap_raw"]

    path, fd = find_device()
    if fd is None:
        print("BCORNE not found (is it plugged in?)", file=sys.stderr)
        return 1
    print(f"found keyboard on {path}")

    written = 0
    for layer, rows in enumerate(keymap):
        for row, cols in enumerate(rows):
            for col, kc in enumerate(cols):
                if rw(fd, struct.pack(">BBBBH", CMD_VIA_SET_KEYCODE, layer, row, col, kc)) is None:
                    print(f"write failed at layer {layer} row {row} col {col}", file=sys.stderr)
                    return 1
                written += 1
    os.close(fd)
    print(f"restored {written} keycodes across {len(keymap)} layers")
    print("note: combos are not touched by this script - clear them in Vial's Combos tab if needed")
    return 0


sys.exit(main())
