#!/usr/bin/env python3
"""Draw the 25 November 2026 front page (1024x1024 PNG, deterministic).

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py
  or: python3 main.py [out.png] [variant]
Standard library only: no PIL, no network, no randomness, no timestamps.
The image is drawn from a hand-rolled 5x7 bitmap font and a zlib PNG
encoder, so the grader's bare python:3.13 image can run it twice and get
identical bytes. Variant is A, B or C (env MAKEFUN_VARIANT); A is default.
"""

import os
import struct
import sys
import zlib
from pathlib import Path

W, H = 1024, 1024
PAPER = (247, 243, 234)     # warm newsprint
INK = (20, 22, 26)          # near-black
ACCENT = (178, 34, 22)      # signal red
BLUE = (28, 68, 120)        # deep blue
TEAL = (16, 96, 92)         # teal
GOLD = (176, 124, 18)       # gold
GREY = (88, 86, 80)         # caption grey
LIGHT = (232, 226, 212)     # light panel
WHITE = (255, 255, 255)

# ---------------------------------------------------------------- font ----
# 5x7 bitmap font: each glyph is 7 rows of 5 bits, "1" = ink.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    # bullet: filled square block
    "\u2022": ("00000", "00000", "01110", "01110", "01110", "00000", "00000"),
}
CHAR_W = 6  # 5 px glyph + 1 px gap


def text_width(text, scale):
    return len(text) * CHAR_W * scale - scale


def wrap(text, scale, max_w):
    """Greedy word wrap; returns lines that fit max_w pixels."""
    max_chars = max(1, (max_w + scale) // (CHAR_W * scale))
    lines, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# -------------------------------------------------------------- canvas ----
class Canvas:
    def __init__(self):
        self.px = bytearray(PAPER) * (W * H)

    def set(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + w), min(H, y + h)
        for yy in range(y0, y1):
            base = (yy * W + x0) * 3
            self.px[base:base + (x1 - x0) * 3] = bytes(color) * (x1 - x0)

    def hline(self, x, y, w, color, t=1):
        self.rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=False):
        x, y, d = 0, r, 3 - 2 * r
        while y >= x:
            pts = [(cx + x, cy + y), (cx - x, cy + y), (cx + x, cy - y),
                   (cx - x, cy - y), (cx + y, cy + x), (cx - y, cy + x),
                   (cx + y, cy - x), (cx - y, cy - x)]
            if fill:
                for yy in (cy + y, cy - y):
                    self.hline(cx - x, yy, 2 * x + 1, color)
                for yy in (cy + x, cy - x):
                    self.hline(cx - y, yy, 2 * y + 1, color)
            else:
                for px, py in pts:
                    self.set(px, py, color)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def text(self, s, x, y, scale, color):
        for ch in s:
            glyph = FONT.get(ch, FONT["?"])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(x + col * scale, y + row * scale,
                                  scale, scale, color)
            x += CHAR_W * scale
        return x

    def text_c(self, s, cx, y, scale, color):
        self.text(s, cx - text_width(s, scale) // 2, y, scale, color)

    def para(self, s, x, y, scale, color, max_w, leading=None):
        lines = wrap(s, scale, max_w)
        lh = leading or (9 * scale)
        for ln in lines:
            self.text(ln, x, y, scale, color)
            y += lh
        return y


def png_bytes(c):
    def chunk(ctype, data):
        out = struct.pack(">I", len(data)) + ctype + data
        return out + struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += c.px[y * W * 3:(y + 1) * W * 3]
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))

# ---------------------------------------------------------- pictograms ----
def draw_shield(c, x, y, s, color):
    """Shield with a lightning bolt: cyberattack."""
    w, h = 34 * s, 40 * s
    c.rect(x, y, w, 26 * s, color)
    for i in range(14):
        c.hline(x + i * s, y + 26 * s + i * s, w - 2 * i * s, color)
    bolt = [(x + 20 * s, y + 6 * s), (x + 12 * s, y + 22 * s),
            (x + 17 * s, y + 22 * s), (x + 14 * s, y + 34 * s),
            (x + 23 * s, y + 17 * s), (x + 18 * s, y + 17 * s)]
    for i in range(len(bolt)):
        c.line(*bolt[i], *bolt[(i + 1) % len(bolt)], PAPER)


def draw_tower(c, x, y, s, color):
    """Skyscraper with a pointed crown: Riyadh tower strike."""
    c.rect(x + 8 * s, y + 18 * s, 18 * s, 22 * s, color)
    for i in range(9):
        c.hline(x + 8 * s + i * s, y + 18 * s - i * s, 18 * s - 2 * i * s,
                color)
    c.rect(x + 15 * s, y - 6 * s, 4 * s, 6 * s, color)
    for row in range(4):
        for col in range(3):
            c.rect(x + (11 + col * 5) * s, y + (21 + row * 5) * s,
                   2 * s, 2 * s, PAPER)
    c.line(x - 4 * s, y + 40 * s, x + 38 * s, y + 40 * s, color)
    c.line(x + 2 * s, y + 12 * s, x + 6 * s, y + 8 * s, ACCENT)
    c.line(x + 6 * s, y + 8 * s, x + 2 * s, y + 4 * s, ACCENT)


def draw_cross(c, x, y, s, color):
    """Medical cross in a ring: WHO / Ebola hospital."""
    c.circle(x + 17 * s, y + 17 * s, 17 * s, color)
    c.rect(x + 13 * s, y + 5 * s, 8 * s, 24 * s, color)
    c.rect(x + 5 * s, y + 13 * s, 24 * s, 8 * s, color)


def draw_scales(c, x, y, s, color):
    """Scales of justice: the Huawei verdict."""
    c.rect(x + 16 * s, y + 2 * s, 2 * s, 30 * s, color)
    c.rect(x + 4 * s, y + 2 * s, 26 * s, 2 * s, color)
    c.line(x + 5 * s, y + 4 * s, x + 1 * s, y + 16 * s, color)
    c.line(x + 5 * s, y + 4 * s, x + 9 * s, y + 16 * s, color)
    c.line(x + 29 * s, y + 4 * s, x + 25 * s, y + 16 * s, color)
    c.line(x + 29 * s, y + 4 * s, x + 33 * s, y + 16 * s, color)
    c.rect(x + 0 * s, y + 16 * s, 10 * s, 2 * s, color)
    c.rect(x + 24 * s, y + 16 * s, 10 * s, 2 * s, color)
    c.rect(x + 6 * s, y + 32 * s, 22 * s, 3 * s, color)


def draw_plane(c, x, y, s, color):
    """Early-warning aircraft over radar arcs: NATO / Poland."""
    c.line(x + 2 * s, y + 22 * s, x + 30 * s, y + 10 * s, color)
    c.line(x + 30 * s, y + 10 * s, x + 32 * s, y + 16 * s, color)
    c.line(x + 30 * s, y + 10 * s, x + 24 * s, y + 18 * s, color)
    c.line(x + 12 * s, y + 18 * s, x + 20 * s, y + 8 * s, color)
    c.circle(x + 17 * s, y + 26 * s, 6 * s, color)
    c.circle(x + 17 * s, y + 26 * s, 12 * s, color)
    c.circle(x + 17 * s, y + 26 * s, 17 * s, color)


def draw_globe(c, x, y, r, color):
    """Wireframe globe: the world in one picture."""
    c.circle(x, y, r, color)
    c.circle(x, y, r // 2, color)
    c.hline(x - r, y, 2 * r + 1, color)
    c.line(x - r, y - r // 2, x + r, y - r // 2, color)
    c.line(x - r, y + r // 2, x + r, y + r // 2, color)
    c.vline(x, y - r, 2 * r + 1, color)


def draw_quake(c, x, y, s, color):
    """Cracked ground zigzag: Nepal quake."""
    pts = [(x, y + 20 * s), (x + 6 * s, y + 12 * s), (x + 12 * s, y + 22 * s),
           (x + 18 * s, y + 8 * s), (x + 24 * s, y + 20 * s),
           (x + 30 * s, y + 10 * s), (x + 34 * s, y + 18 * s)]
    for a, b in zip(pts, pts[1:]):
        c.line(*a, *b, color)
        c.line(a[0], a[1] + s, b[0], b[1] + s, color)


# -------------------------------------------------------------- stories ----
# Every story was first reported on Wednesday 25 November 2026 (Reuters /
# CNN / AFP wires carried in that day's news summaries), or is that day's
# observance. Headlines are the day's facts, no hype, no speculation.
LEAD = ("CYBERATTACK HITS CIA",
        "AND US SPY CHIEF",
        "CNN REPORTS AN INTRUSION AT THE CIA AND THE OFFICE OF THE "
        "DIRECTOR OF NATIONAL INTELLIGENCE. CLASSIFIED SYSTEMS WERE "
        "AFFECTED.")
STORIES = [
    ("HUAWEI GUILTY ON 10 OF 12 COUNTS",
     "A NEW YORK JURY CONVICTED THE CHINESE TECH GIANT OF STEALING "
     "TRADE SECRETS, BANK FRAUD AND DEFRAUDING THE US GOVERNMENT "
     "AFTER A THREE-MONTH TRIAL. HUAWEI REJECTED THE VERDICTS.",
     "scales", BLUE),
    ("HOUTHIS HIT RIYADH TOWER, 11 HURT",
     "A STRIKE ON THE CAPITAL'S TALLEST TOWER WOUNDED 11 PEOPLE, "
     "SAUDI CIVIL DEFENCE SAID. THE SAUDI-LED COALITION CONDEMNED "
     "THE ATTACK AS TERRORISM.",
     "tower", ACCENT),
    ("WHO FLEES EBOLA HOSPITAL IN CONGO",
     "HEALTH WORKERS WERE EVACUATED FROM A HOSPITAL IN AKWE, ITURI, "
     "AFTER THREE DAYS SHELTERING FROM FIERCE FIGHTING. THE EBOLA "
     "OUTBREAK HAS KILLED 5,775 PEOPLE.",
     "cross", TEAL),
    ("NATO JETS FOR POLAND AFTER MISSILES",
     "THE ALLIANCE PLANS TO DEPLOY EARLY-WARNING AIRCRAFT IN POLAND "
     "AFTER REPORTS OF MISSILES LANDING THERE DURING AN ATTACK ON "
     "UKRAINE.",
     "plane", BLUE),
]
ALSO = ("NEPAL 5.6 QUAKE - TRUMP TARIFFS DUE - MICROSOFT 'CODE RED' "
        "OUTAGE")

ICONS = {"shield": draw_shield, "tower": draw_tower, "cross": draw_cross,
         "scales": draw_scales, "plane": draw_plane, "quake": draw_quake}


def masthead(c, tagline=True):
    c.rect(0, 0, W, 148, INK)
    c.text_c("THE WORLD", W // 2, 18, 13, WHITE)
    c.hline(48, 118, W - 96, ACCENT, 4)
    c.text_c("WEDNESDAY 25 NOVEMBER 2026", W // 2, 126, 3, GOLD)
    if tagline:
        c.text("ONE DAY", 48, 126, 3, WHITE)
        c.text("ONE PAGE", W - 48 - text_width("ONE PAGE", 3), 126, 3, WHITE)


def also_strip(c, y):
    c.rect(0, y, W, 100, INK)
    c.text("ALSO TODAY", 40, y + 12, 3, GOLD)
    c.para(ALSO, 40, y + 40, 3, WHITE, W - 80, 27)
    return y + 100


def story_block(c, x, y, w, head, deck, icon, color, hscale=4, dscale=2,
                icon_s=1, headline_lines=None):
    c.rect(x, y, w, 3, color)
    ix = x + 12
    iy = y + 16
    ICONS[icon](c, ix, iy, icon_s, color)
    tx = x + 12 + 44 * icon_s + 8
    tw = x + w - tx - 12
    lines = headline_lines or wrap(head, hscale, tw)
    yy = y + 14
    for ln in lines:
        c.text(ln, tx, yy, hscale, INK)
        yy += 9 * hscale
    yy += 4
    c.para(deck, tx, yy, dscale, GREY, tw, 9 * dscale)
    return y


# -------------------------------------------------------------- layouts ----
def layout_a(c):
    """A: classic newspaper grid. Lead left, Huawei right, three below."""
    masthead(c)
    y = 164
    # lead story, left two thirds
    c.rect(36, y, 620, 300, LIGHT)
    draw_shield(c, 60, y + 24, 2, ACCENT)
    c.text("LEAD STORY", 60, y + 150, 3, ACCENT)
    c.text(LEAD[0], 60, y + 180, 6, INK)
    c.text(LEAD[1], 60, y + 180 + 54, 6, INK)
    c.para(LEAD[2], 60, y + 180 + 54 + 52, 2, GREY, 572, 20)
    # Huawei, right third
    story_block(c, 672, y, 316, STORIES[0][0], STORIES[0][1],
                STORIES[0][2], STORIES[0][3], hscale=4, dscale=2, icon_s=1)
    # three across
    y2 = y + 316
    colw = 304
    for i, st in enumerate(STORIES[1:]):
        story_block(c, 36 + i * (colw + 16), y2, colw, st[0], st[1],
                    st[2], st[3], hscale=4, dscale=2, icon_s=1)
    also_strip(c, 924)


def layout_b(c):
    """B: lead-dominant. Full-width lead headline + globe, 2x2 below."""
    masthead(c)
    y = 164
    c.rect(36, y, 952, 248, LIGHT)
    draw_globe(c, 905, y + 124, 70, BLUE)
    c.text("LEAD STORY", 60, y + 20, 3, ACCENT)
    c.text(LEAD[0], 60, y + 52, 6, INK)
    c.text(LEAD[1], 60, y + 52 + 54, 6, INK)
    c.para(LEAD[2], 60, y + 52 + 54 + 58, 2, GREY, 700, 20)
    y2 = y + 264
    colw = 468
    for row in range(2):
        for col in range(2):
            st = STORIES[row * 2 + col]
            story_block(c, 36 + col * (colw + 16), y2 + row * 232, colw,
                        st[0], st[1], st[2], st[3], hscale=4, dscale=2,
                        icon_s=1)
    also_strip(c, 924)


def layout_c(c):
    """C: six-panel mosaic. Five stories + one 'why it matters' panel."""
    masthead(c)
    y = 164
    panels = [
        ("1", LEAD[0] + " " + LEAD[1], LEAD[2], "shield", ACCENT),
        ("2", STORIES[0][0], STORIES[0][1], "scales", BLUE),
        ("3", STORIES[1][0], STORIES[1][1], "tower", ACCENT),
        ("4", STORIES[2][0], STORIES[2][1], "cross", TEAL),
        ("5", STORIES[3][0], STORIES[3][1], "plane", BLUE),
        ("6", "THE DAY IN BRIEF",
         "A CYBERATTACK ON AMERICA'S SPIES, A GUILTY VERDICT FOR "
         "HUAWEI, A STRIKE ON RIYADH, AN EBOLA EVACUATION IN CONGO "
         "AND NATO JETS FOR POLAND: FIVE STORIES, FIVE REGIONS, ONE "
         "WEDNESDAY.", "quake", GOLD),
    ]
    colw, rowh = 304, 372
    for i, (num, head, deck, icon, color) in enumerate(panels):
        x = 36 + (i % 3) * (colw + 16)
        yy = y + (i // 3) * (rowh + 16)
        c.rect(x, yy, colw, rowh, LIGHT)
        c.rect(x, yy, colw, 3, color)
        c.text(num, x + 12, yy + 12, 5, color)
        ICONS[icon](c, x + colw - 60, yy + 12, 1, color)
        hh = wrap(head, 4, colw - 24)
        yyy = yy + 66
        for ln in hh:
            c.text(ln, x + 12, yyy, 4, INK)
            yyy += 36
        c.para(deck, x + 12, yyy + 6, 2, GREY, colw - 24, 20)
    also_strip(c, 924)


LAYOUTS = {"A": layout_a, "B": layout_b, "C": layout_c}


def render(variant):
    c = Canvas()
    LAYOUTS[variant](c)
    return png_bytes(c)


def main(argv):
    variant = (os.environ.get("MAKEFUN_VARIANT") or "B").upper()
    if len(argv) > 1:
        variant = argv[1].upper()
    if variant not in LAYOUTS:
        print(f"main.py: error: unknown variant {variant!r}", file=sys.stderr)
        return 1
    data = render(variant)
    if len(argv) > 0:
        dest = Path(argv[0])
    else:
        out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
        if not out_dir:
            print("main.py: error: MAKEFUN_OUTPUT_DIR is not set",
                  file=sys.stderr)
            return 1
        dest = Path(out_dir) / "entry.png"
    if len(data) > 1_048_576:
        print(f"main.py: error: {len(data)} bytes exceeds 1 MiB",
              file=sys.stderr)
        return 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(f"main.py: variant {variant}: wrote {dest} "
          f"({len(data)} bytes, 1024x1024 PNG)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
