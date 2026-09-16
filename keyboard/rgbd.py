#!/usr/bin/env python3
"""Layer-aware per-key RGB for the DH747 BCORNE.

The firmware has no idea what a layer indicator is, so this does it from the host:

  * poll the switch matrix over raw HID (Vial's matrix-tester channel) to see
    which thumb keys are physically held right now
  * derive the active layer from that, exactly the way QMK does
  * read the real keymap off the board and light only the keys that actually
    do something on that layer, in that layer's colour

So holding NAV lights up the arrow cluster. Holding SYM lights up the symbols.
The board teaches you its own layout while you learn it.

At rest it shows a legend instead of going dark: the four home row mods on each
hand tinted by which modifier they hold, and the three layer thumbs in their
layer colours. Because the mod colours are decoded from the live keymap, the
Linux and macOS base layers light up differently on their own -- that's your
"which OS mode am I in" indicator, with no extra logic.

Usage:
    python3 rgbd.py                 run it
    python3 rgbd.py --watch         print live matrix + layer state, no LEDs
    python3 rgbd.py --base mac      tell it the macOS base layer is default
    python3 rgbd.py --brightness .5

It gets out of the way on its own while the Vial GUI is open, and re-reads your
keymap when Vial closes, so edits show up in the lighting with no extra step.

No dependencies. /dev/hidraw* is world-rw on this machine, so no root either.
"""

import argparse
import glob
import json
import os
import select
import signal
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_vil import L, R, ROWS, COLS, LAYERS  # physical -> matrix map, one source of truth

STATE_FILE = os.path.join(HERE, ".rgbd-state.json")

MSG_LEN = 32
CMD_GET_PROTOCOL = 0x01
CMD_GET_KB_VALUE = 0x02
CMD_LIGHTING_SET = 0x07
CMD_LIGHTING_GET = 0x08
CMD_KEYMAP_GET_BUFFER = 0x12
VIA_SWITCH_MATRIX_STATE = 0x03
VIALRGB_GET_MODE = 0x41
VIALRGB_GET_NUMBER_LEDS = 0x43
VIALRGB_GET_LED_INFO = 0x44
VIALRGB_SET_MODE = 0x41
VIALRGB_DIRECT_FASTSET = 0x42
VIALRGB_EFFECT_DIRECT = 1

LEDS_PER_PACKET = 9  # 32-byte report: cmd, subcmd, uint16 index, then 9 x RGB

# ---------------------------------------------------------------- keycodes
KC_NO, KC_TRNS = 0x0000, 0x0001
MOD_FIRST, MOD_LAST = 0x00E0, 0x00E7
MODTAP_FIRST, MODTAP_LAST = 0x2000, 0x3FFF
LAYERTAP_FIRST, LAYERTAP_LAST = 0x4000, 0x4FFF
QK_MO, QK_DF, QK_TG, QK_OSL = 0x5220, 0x5240, 0x5260, 0x5280

ARROWS = {0x4F, 0x50, 0x51, 0x52}
DIGITS = set(range(0x1E, 0x28))
EMPHASIS = ARROWS | DIGITS

# ---------------------------------------------------------------- palette
LAYER_COLOR = {
    2: (0, 205, 180),      # NAV   teal
    3: (150, 110, 255),    # SYM   violet
    4: (255, 155, 20),     # NUM   amber
    5: (255, 75, 110),     # FUN   rose
}
MOD_COLOR = {
    "gui": (230, 80, 200),
    "alt": (255, 150, 30),
    "ctl": (60, 190, 255),
    "sft": (90, 230, 120),
}
BASE_GROUND = (130, 150, 200)  # cool wash under the alphas at rest

FULL, MID, DIM, GHOST = 1.0, 0.5, 0.24, 0.12


def mods_of(kc):
    """Which modifier a mod-tap key holds."""
    bits = (kc >> 8) & 0x0F
    if bits & 0x08:
        return "gui"
    if bits & 0x04:
        return "alt"
    if bits & 0x02:
        return "sft"
    if bits & 0x01:
        return "ctl"
    return None


def layer_target(kc):
    """Target layer of a layer-switching keycode, or None."""
    for base in (QK_MO, QK_DF, QK_TG, QK_OSL):
        if base <= kc <= base + 0x1F:
            return kc - base
    if LAYERTAP_FIRST <= kc <= LAYERTAP_LAST:
        return (kc >> 8) & 0x0F
    return None


def scale(color, factor):
    return tuple(min(255, int(c * factor)) for c in color)


# ---------------------------------------------------------------- transport
class Board:
    def __init__(self):
        self.fd = None
        self.path = None
        self.poller = None

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
            self.poller = None
        return False

    def close(self):
        if self.fd is not None:
            try:
                os.close(self.fd)
            except OSError:
                pass
        self.fd = None
        self.poller = None

    def _write(self, data):
        os.write(self.fd, b"\x00" + data + b"\x00" * (MSG_LEN - len(data)))

    def _drain(self):
        """Discard queued replies so a later read can't return a stale one."""
        while self.poller.poll(0):
            try:
                os.read(self.fd, MSG_LEN)
            except OSError:
                return

    def rw(self, data, retries=6, timeout_ms=200):
        """Write, then wait for the reply that echoes this command back."""
        if self.fd is None:
            return None
        expect = data[0]
        for _ in range(retries):
            try:
                self._write(data)
            except OSError:
                return None
            deadline = time.monotonic() + timeout_ms / 1000.0
            while True:
                remaining = (deadline - time.monotonic()) * 1000
                if remaining <= 0 or not self.poller.poll(remaining):
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

    # ---- reads
    def led_count(self):
        r = self.rw(bytes([CMD_LIGHTING_GET, VIALRGB_GET_NUMBER_LEDS]))
        return struct.unpack("<H", r[2:4])[0]

    def led_info(self, i):
        r = self.rw(bytes([CMD_LIGHTING_GET, VIALRGB_GET_LED_INFO]) + struct.pack("<H", i))
        return dict(i=i, x=r[2], y=r[3], flags=r[4])

    def get_mode(self):
        r = self.rw(bytes([CMD_LIGHTING_GET, VIALRGB_GET_MODE]))
        return struct.unpack("<H", r[2:4])[0], r[4], r[5], r[6], r[7]

    def set_mode(self, mode, speed, hue, sat, val):
        self.rw(bytes([CMD_LIGHTING_SET, VIALRGB_SET_MODE])
                + struct.pack("<H", mode) + bytes([speed, hue, sat, val]))

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

    def matrix(self):
        r = self.rw(bytes([CMD_GET_KB_VALUE, VIA_SWITCH_MATRIX_STATE]), retries=3)
        if r is None:
            return None
        return {(row, col) for row in range(ROWS) for col in range(COLS)
                if (r[2 + row] >> col) & 1}

    def push(self, frame, per_packet=LEDS_PER_PACKET):
        if self.fd is None:
            return
        """Repaint the whole strip. Fire-and-forget: the acks are drained rather
        than waited on, which is the difference between 7 ms and 300 ms."""
        n = len(frame)
        for start in range(0, n, per_packet):
            window = b"".join(bytes(frame[j]) if j < n else b"\x00\x00\x00"
                              for j in range(start, start + per_packet))
            try:
                self._write(bytes([CMD_LIGHTING_SET, VIALRGB_DIRECT_FASTSET])
                            + struct.pack("<H", start) + window)
            except OSError:
                return
        self._drain()


# ---------------------------------------------------------------- geometry
def build_led_map(leds):
    """LED index -> matrix (row, col), derived from physical LED coordinates.

    The firmware's own led->matrix table disagrees with the keyboard's Vial
    layout definition (vendor bug), so position is the only thing to trust.
    Columns are on a 16-unit pitch; the right half starts at unit 7.
    """
    bands = sorted({l["y"] for l in leds})
    if len(bands) != 5:
        raise SystemExit(f"expected 5 LED rows, found {len(bands)}: {bands}")
    rownames = ["A", "B", "C", "D", "T"]
    split = 104  # px; left half ends well before this, right half starts after

    mapping = {}
    for led in leds:
        rn = rownames[bands.index(led["y"])]
        left = led["x"] < split
        positions = (L if left else R)[rn]

        if rn == "T":
            siblings = sorted([o for o in leds
                               if o["y"] == led["y"] and (o["x"] < split) == left],
                              key=lambda o: o["x"])
            idx = siblings.index(led)
        else:
            # right half: rows A and D have no inner-column key, so their
            # position lists start one column further in
            base = 0 if left else (8 if rn == "D" else 7)
            idx = round(led["x"] / 16) - base

        if 0 <= idx < len(positions):
            mapping[led["i"]] = positions[idx]
    return mapping


# ---------------------------------------------------------------- rendering
def active_layer(held):
    """Mirror QMK's layer stack for the thumb keys this keymap uses."""
    nav = L["T"][1] in held      # left middle thumb  -> MO(2)
    num = L["T"][0] in held      # left outer thumb   -> MO(4)
    sym = R["T"][1] in held      # right middle thumb -> MO(3)
    if nav and sym:
        return 5                 # both -> FUN, whichever order you press them
    if num:
        return 4
    if sym:
        return 3
    if nav:
        return 2
    return None


def render(keymap, led_map, n_leds, base, layer, held, bright):
    frame = [(0, 0, 0)] * n_leds

    if layer is None:
        # At rest: a legend, not a light show.
        for led, rc in led_map.items():
            kc = keymap[base][rc[0]][rc[1]]
            if MODTAP_FIRST <= kc <= MODTAP_LAST:
                mod = mods_of(kc)
                if mod:
                    frame[led] = scale(MOD_COLOR[mod], MID * bright)
                    continue
            target = layer_target(kc)
            if target in LAYER_COLOR:
                frame[led] = scale(LAYER_COLOR[target], MID * bright)
            elif kc not in (KC_NO, KC_TRNS):
                frame[led] = scale(BASE_GROUND, GHOST * bright)
        return frame

    hue = LAYER_COLOR.get(layer, (255, 255, 255))
    for led, rc in led_map.items():
        kc = keymap[layer][rc[0]][rc[1]]
        if rc in held:
            frame[led] = scale(hue, FULL * bright)
        elif kc in (KC_NO, KC_TRNS):
            frame[led] = (0, 0, 0)
        elif MOD_FIRST <= kc <= MOD_LAST:
            frame[led] = scale(hue, DIM * bright)
        elif layer_target(kc) is not None or kc in EMPHASIS:
            frame[led] = scale(hue, FULL * bright)
        else:
            frame[led] = scale(hue, MID * bright)
    return frame


def vial_running():
    """Is the Vial GUI open?

    Vial and this daemon both talk to the same raw HID endpoint, and two readers
    steal each other's replies -- this one retries and survives, Vial throws an
    error dialog. So while Vial is open we get out of the way entirely.
    """
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/comm") as f:
                if f.read().strip().startswith("Vial"):
                    return True
        except OSError:
            continue
    return False


# ---------------------------------------------------------------- state file
DEFAULT_EFFECT = (15, 127, 0, 255, 50)


def _state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _write_state(**kw):
    data = _state()
    data.update(kw)
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(data, f)
    except OSError:
        pass


def load_base():
    return int(_state().get("base", 0))


def save_base(base):
    _write_state(base=base)


def take_over(board):
    """Switch the board to direct mode, returning the effect to put back.

    If a previous run was killed rather than stopped, the board is still in
    direct mode and reading it back would 'restore' to direct forever -- so
    remember the real effect the first time we see one.
    """
    current = board.get_mode()
    if current[0] == VIALRGB_EFFECT_DIRECT:
        saved = _state().get("effect")
        current = tuple(saved) if saved else DEFAULT_EFFECT
    else:
        _write_state(effect=list(current))
    board.set_mode(VIALRGB_EFFECT_DIRECT, *current[1:])
    return current


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Layer-aware RGB for the BCORNE")
    ap.add_argument("--brightness", type=float, default=0.38, help="0.0-1.0 (default 0.38)")
    ap.add_argument("--idle", type=float, default=300, help="seconds before LEDs sleep (0 = never)")
    ap.add_argument("--hz", type=float, default=60, help="matrix poll rate")
    ap.add_argument("--base", choices=["linux", "mac"], help="which base layer is default")
    ap.add_argument("--leds-per-packet", type=int, default=LEDS_PER_PACKET,
                    help="LEDs the firmware accepts per RGB packet (default 9; if every "
                         "9th key stays dark, lower this)")
    ap.add_argument("--watch", action="store_true", help="print state, leave LEDs alone")
    args = ap.parse_args()

    if args.base:
        save_base(0 if args.base == "linux" else 1)
        print(f"base layer set to {args.base}")

    board = Board()
    while vial_running():
        print("Vial is open, waiting for it to close...", flush=True)
        while vial_running():
            time.sleep(2)
    print("waiting for keyboard...", flush=True)
    while not board.open():
        time.sleep(2)
    print(f"connected on {board.path}", flush=True)

    n_leds = board.led_count()
    leds = [board.led_info(i) for i in range(n_leds)]
    led_map = build_led_map(leds)
    keymap = board.keymap()
    if keymap is None:
        raise SystemExit("could not read keymap")
    print(f"{n_leds} LEDs, {len(led_map)} mapped to keys", flush=True)

    original = None
    if not args.watch:
        original = take_over(board)

    def restore(*_):
        if original and board.fd is not None:
            board.set_mode(*original)
            time.sleep(0.1)
        board.close()
        print("\nrestored original lighting")
        sys.exit(0)

    reload_wanted = []

    def on_hup(*_):
        reload_wanted.append(True)

    signal.signal(signal.SIGINT, restore)
    signal.signal(signal.SIGTERM, restore)
    signal.signal(signal.SIGHUP, on_hup)

    base = load_base()
    last_key_time = time.time()
    last_state = None
    period = 1.0 / args.hz
    standing_by = False
    next_vial_check = 0.0

    while True:
        if time.monotonic() >= next_vial_check:
            next_vial_check = time.monotonic() + 1.0
            busy = vial_running()
            if busy and not standing_by:
                if original and board.fd is not None:
                    board.set_mode(*original)
                board.close()
                standing_by = True
                print("Vial is open, standing by", flush=True)
            elif not busy and standing_by:
                while not board.open():
                    time.sleep(1)
                # Vial may well have changed the keymap; pick that up for free
                keymap = board.keymap() or keymap
                if not args.watch:
                    original = take_over(board)
                standing_by = False
                last_state = None
                print(f"Vial closed, resuming on {board.path}", flush=True)

        if standing_by:
            time.sleep(0.5)
            continue

        held = board.matrix()
        if held is None:                       # unplugged
            board.close()
            print("lost keyboard, reconnecting...", flush=True)
            last_state = None
            while not board.open():
                time.sleep(2)
            print(f"reconnected on {board.path}", flush=True)
            keymap = board.keymap() or keymap
            if not args.watch:
                original = take_over(board)
            continue

        if reload_wanted:
            reload_wanted.clear()
            keymap = board.keymap() or keymap
            last_state = None
            print("keymap reloaded", flush=True)

        now = time.time()
        if held:
            last_key_time = now
        layer = active_layer(held)

        # watch for the base-layer swap on the FUN layer (Z = Linux, X = macOS)
        if layer == 5:
            if L["D"][1] in held and base != 0:
                base = 0
                save_base(base)
            elif L["D"][2] in held and base != 1:
                base = 1
                save_base(base)

        idle = args.idle > 0 and (now - last_key_time) > args.idle
        state = (base, layer, frozenset(held) if layer else frozenset(), idle)

        if state != last_state:
            last_state = state
            if args.watch:
                names = {None: "base", 2: "NAV", 3: "SYM", 4: "NUM", 5: "FUN"}
                pressed = " ".join(f"{r},{c}" for r, c in sorted(held)) or "-"
                print(f"layer={names[layer]:<4} base={'mac' if base else 'linux':<5} "
                      f"idle={int(idle)} held=[{pressed}]", flush=True)
            else:
                frame = ([(0, 0, 0)] * n_leds if idle else
                         render(keymap, led_map, n_leds, base, layer, held, args.brightness))
                board.push(frame, args.leds_per_packet)

        time.sleep(period if not idle else 0.05)


if __name__ == "__main__":
    main()
