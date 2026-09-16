#!/usr/bin/env python3
"""Push a .vil onto the board, writing only the keys that actually changed.

Vial's GUI can load a .vil perfectly well; this exists so a keymap edit can be
applied and verified from a script, without the GUI in the loop.

It never guesses a keycode. Encodings come from keycodes.json, which is learned
from the board itself: point --learn at a .vil the board already matches and it
pairs the two, refusing if any name maps to more than one number. A name it has
never seen is an error, not a guess -- load the file in Vial instead.

Only real key positions are touched. The matrix has holes (60 keys in a 10x7
grid) and those cells are left alone.

    python3 apply_vil.py                     # show the diff, change nothing
    python3 apply_vil.py --write             # apply it, then verify
    python3 apply_vil.py old.vil --learn     # rebuild keycodes.json
"""

import argparse
import collections
import re
import glob
import json
import os
import select
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_vil import ROWS, COLS, LAYERS, L, R

CODES_FILE = os.path.join(HERE, "keycodes.json")

# every (row, col) that is a real key
REAL = {pos for half in (L, R) for row in half.values() for pos in row}

MSG_LEN = 32
CMD_GET_PROTOCOL = 0x01
CMD_SET_KEYCODE = 0x05
CMD_KEYMAP_GET_BUFFER = 0x12
CMD_VIAL_PREFIX = 0xFE
CMD_VIAL_GET_ENCODER = 0x03
CMD_VIAL_SET_ENCODER = 0x04


class Board:
    def __init__(self):
        self.fd = None
        self.poller = None
        self.path = None

    def open(self):
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
            self.fd = fd
            self.poller = select.poll()
            self.poller.register(fd, select.POLLIN)
            probe = self.rw(bytes([CMD_GET_PROTOCOL]), retries=3)
            # a sibling interface will echo but report protocol 0; insist on a
            # sane version and on the keymap channel actually answering
            if probe and struct.unpack(">H", probe[1:3])[0] >= 9 \
                    and self.rw(struct.pack(">BHB", CMD_KEYMAP_GET_BUFFER, 0, 4)):
                self.path = path
                return True
            os.close(fd)
            self.fd = None
        return False

    def rw(self, data, retries=6, timeout_ms=250):
        if self.fd is None:
            return None
        expect = data[0]
        for _ in range(retries):
            try:
                os.write(self.fd, b"\x00" + data + b"\x00" * (MSG_LEN - len(data)))
            except OSError:
                return None
            deadline = time.monotonic() + timeout_ms / 1000.0
            while True:
                left = (deadline - time.monotonic()) * 1000
                if left <= 0 or not self.poller.poll(left):
                    break
                try:
                    r = os.read(self.fd, MSG_LEN)
                except BlockingIOError:
                    continue
                except OSError:
                    return None
                if r and r[0] == expect:
                    return r
        return None

    def keymap(self):
        total = LAYERS * ROWS * COLS * 2
        buf, off = b"", 0
        while off < total:
            n = min(28, total - off)
            r = self.rw(struct.pack(">BHB", CMD_KEYMAP_GET_BUFFER, off, n))
            if r is None:
                return None
            buf += r[4:4 + n]
            off += n
        km = []
        for l in range(LAYERS):
            layer = []
            for row in range(ROWS):
                base = ((l * ROWS + row) * COLS) * 2
                layer.append([struct.unpack(">H", buf[base + c * 2: base + c * 2 + 2])[0]
                              for c in range(COLS)])
            km.append(layer)
        return km

    def encoder(self, layer, idx):
        """(ccw, cw) for one encoder on one layer. Vial-prefixed commands do not
        echo, so this reads from byte 0 rather than filtering on the command."""
        while self.poller.poll(0):
            try:
                os.read(self.fd, MSG_LEN)
            except OSError:
                return None
        req = struct.pack("BBBB", CMD_VIAL_PREFIX, CMD_VIAL_GET_ENCODER, layer, idx)
        os.write(self.fd, b"\x00" + req + b"\x00" * (MSG_LEN - len(req)))
        if not self.poller.poll(300):
            return None
        d = os.read(self.fd, MSG_LEN)
        return (d[0] << 8 | d[1], d[2] << 8 | d[3])

    def set_key(self, layer, row, col, code):
        return self.rw(struct.pack(">BBBBH", CMD_SET_KEYCODE, layer, row, col, code)) is not None

    def set_encoder(self, layer, idx, direction, code):
        while self.poller.poll(0):
            try:
                os.read(self.fd, MSG_LEN)
            except OSError:
                return False
        req = struct.pack(">BBBBBH", CMD_VIAL_PREFIX, CMD_VIAL_SET_ENCODER,
                          layer, idx, direction, code)
        for _ in range(8):
            os.write(self.fd, b"\x00" + req + b"\x00" * (MSG_LEN - len(req)))
            if self.poller.poll(300):
                os.read(self.fd, MSG_LEN)
                return True
        return False


# A modifier-wrapped keycode is (mod bits << 8) | the inner keycode. Verified
# against values read off this board: LCA(KC_LEFT)=0x0550, LCTL(KC_LEFT)=0x0150.
MODBITS = {"LCTL": 0x01, "LSFT": 0x02, "LALT": 0x04, "LGUI": 0x08,
           "RCTL": 0x11, "RSFT": 0x12, "RALT": 0x14, "RGUI": 0x18,
           "LCS": 0x03, "LCA": 0x05, "LSA": 0x06, "MEH": 0x07,
           "LSG": 0x0A, "LAG": 0x0C, "LCAG": 0x0D, "HYPR": 0x0F}

# A mod-tap is the same, plus the tap-hold range bit.
QK_MOD_TAP = 0x2000


def compose(name, table):
    """Number for a composed keycode name, ignoring any direct entry for it.

    Two shapes, both verified against values read off this board:
      modifier wrapper  LCTL(KC_LEFT)   -> (mod << 8) | inner
      mod-tap           LGUI_T(KC_A)    -> QK_MOD_TAP | (mod << 8) | inner

    Layer-taps LT(n, kc) are deliberately absent: the board has never reported
    one, so the encoding is unverified here. Set one in Vial, run --learn, and
    it arrives in keycodes.json as a plain entry.
    """
    m = re.fullmatch(r"([A-Z]+)(_T)?\((.+)\)", name)
    if not m or m.group(1) not in MODBITS:
        return None
    inner = resolve(m.group(3), table)
    if inner is None or inner > 0xFF:
        return None
    code = (MODBITS[m.group(1)] << 8) | inner
    return (QK_MOD_TAP | code) if m.group(2) else code


def resolve(name, table):
    """Number for a keycode name: straight from the learned table, or composed
    for a wrapper or mod-tap whose inner keycode the table already knows."""
    if name in table:
        return table[name]
    return compose(name, table)


def check_resolver(table):
    """Prove the composition rules against every composed name already observed."""
    for name, code in table.items():
        got = compose(name, table)
        if got is not None and got != code:
            raise SystemExit(f"composition rule disagrees with the board on {name}: "
                             f"computed 0x{got:04X}, board has 0x{code:04X}")


def learn_codes(live, want):
    """Pair a .vil the board already matches with the live keymap.

    Every name must resolve to exactly one number; anything else means the board
    and the file have drifted, and guessing would corrupt the keymap.
    """
    seen = collections.defaultdict(set)
    for l in range(LAYERS):
        for r, c in REAL:
            seen[want[l][r][c]].add(live[l][r][c])
    clashes = {n: v for n, v in seen.items() if len(v) != 1}
    if clashes:
        for n, v in sorted(clashes.items()):
            print(f"  {n} -> {sorted(hex(x) for x in v)}", file=sys.stderr)
        raise SystemExit("board does not match that file; cannot learn encodings from it")
    return {n: v.pop() for n, v in seen.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vil", nargs="?", default=os.path.join(HERE, "corne-ergo.vil"))
    ap.add_argument("--write", action="store_true", help="actually apply the diff")
    ap.add_argument("--learn", action="store_true",
                    help="rebuild keycodes.json by pairing this file with the board")
    ap.add_argument("--verify", action="store_true",
                    help="after a Vial load: find keycodes that silently became KC_NO")
    args = ap.parse_args()

    want = json.load(open(args.vil))["layout"]

    board = Board()
    if not board.open():
        print("keyboard not found", file=sys.stderr)
        return 1
    live = board.keymap()
    if live is None:
        print("could not read the keymap", file=sys.stderr)
        return 1

    if args.verify:
        # Vial resolves a keycode name it does not know to KC_NO and says nothing.
        # That is how Caps Word looked installed for a week while doing nothing.
        dead = []
        for l in range(LAYERS):
            for r, c in sorted(REAL):
                name = want[l][r][c]
                if name not in ("KC_NO", "KC_TRNS") and live[l][r][c] == 0:
                    dead.append(f"layer {l} ({r},{c}) expected {name}")
        encs = json.load(open(args.vil)).get("encoder_layout", [])
        for l, layer in enumerate(encs):
            for i, pair in enumerate(layer):
                got = board.encoder(l, i)
                if got is None:
                    continue
                for d, name in enumerate(pair):
                    if name not in ("KC_NO", "KC_TRNS") and got[d] == 0:
                        dead.append(f"layer {l} encoder {i} {'ccw' if d == 0 else 'cw'} expected {name}")
        if dead:
            print(f"{len(dead)} keycode(s) did not survive the load — this firmware "
                  f"does not support them:")
            for d in dead:
                print("  " + d)
            return 1
        print("every keycode in the file is live on the board")
        return 0

    if args.learn:
        table = learn_codes(live, want)
        json.dump({k: table[k] for k in sorted(table)}, open(CODES_FILE, "w"), indent=1)
        print(f"learned {len(table)} encodings -> {os.path.basename(CODES_FILE)}")
        return 0

    try:
        table = json.load(open(CODES_FILE))
    except OSError:
        print(f"no {os.path.basename(CODES_FILE)} yet — run with --learn against a "
              f"file the board already matches", file=sys.stderr)
        return 2

    check_resolver(table)

    diff = []
    for l in range(LAYERS):
        for r, c in sorted(REAL):
            name = want[l][r][c]
            if resolve(name, table) is None:
                print(f"cannot encode {name!r} — not in {os.path.basename(CODES_FILE)}.\n"
                      f"Load {os.path.basename(args.vil)} in Vial instead.", file=sys.stderr)
                return 2
            code = resolve(name, table)
            if live[l][r][c] != code:
                diff.append((l, r, c, live[l][r][c], code, name))

    ediff = []
    for l, layer in enumerate(json.load(open(args.vil)).get("encoder_layout", [])):
        got_layer = [board.encoder(l, i) for i in range(len(layer))]
        for i, pair in enumerate(layer):
            if got_layer[i] is None:
                continue
            for d, name in enumerate(pair):
                code = resolve(name, table)
                if code is None:
                    print(f"cannot encode encoder keycode {name!r}", file=sys.stderr)
                    return 2
                if got_layer[i][d] != code:
                    ediff.append((l, i, d, got_layer[i][d], code, name))

    if not diff and not ediff:
        print("board already matches the file — nothing to do")
        return 0

    if diff:
        print(f"{len(diff)} key(s) differ:")
        for l, r, c, was, now, name in diff:
            print(f"  layer {l}  ({r},{c})  0x{was:04X} -> 0x{now:04X}  {name}")
    if ediff:
        print(f"{len(ediff)} encoder direction(s) differ:")
        for l, i, d, was, now, name in ediff:
            print(f"  layer {l}  encoder {i} {'ccw' if d == 0 else 'cw '}  "
                  f"0x{was:04X} -> 0x{now:04X}  {name}")
    if not args.write:
        print("\ndry run — pass --write to apply")
        return 0

    for l, r, c, _was, code, _name in diff:
        if not board.set_key(l, r, c, code):
            print(f"write failed at layer {l} ({r},{c})", file=sys.stderr)
            return 1

    for l, i, d, _was, code, _name in ediff:
        if not board.set_encoder(l, i, d, code):
            print(f"encoder write failed at layer {l} encoder {i}", file=sys.stderr)
            return 1

    check = board.keymap()
    bad = [d for d in diff if check[d[0]][d[1]][d[2]] != d[4]]
    for l, i, d, _was, code, _name in ediff:
        got = board.encoder(l, i)
        if got is None or got[d] != code:
            bad.append((l, i, d))
    if bad:
        print(f"{len(bad)} change(s) did not stick", file=sys.stderr)
        return 1
    print(f"\napplied and verified {len(diff)} key(s) and {len(ediff)} encoder direction(s)")
    return 0



if __name__ == "__main__":
    sys.exit(main())
