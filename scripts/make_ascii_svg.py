#!/usr/bin/env python3
"""
Convert prepped portrait image (source-prepped.png) into a self-contained,
animated monochrome ASCII SVG terminal panel (avatar-ascii.svg).

Row-by-row SMIL wipe animation with a traveling block cursor, plays once and freezes.
Supports STATIC=1 env var for a frozen snapshot.
"""
import html
import os
import sys
from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "avatar-ascii.svg")

COLS = int(os.environ.get("COLS", 100))
ROWS = int(os.environ.get("ROWS", 53))
RAMP = " .`:-=+*cs#%@"

# Layout dimensions
CANVAS_W = 740
PAD_X = 22
ART_W = CANVAS_W - PAD_X * 2
CELL_W = ART_W / COLS
CELL_H = 12.5
ART_H = ROWS * CELL_H
TITLEBAR_H = 34
STATUS_H = 32
CANVAS_H = int(TITLEBAR_H + 8 + ART_H + STATUS_H + 12)

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"
CURSOR = "#c9d1d9"

STATIC = bool(os.environ.get("STATIC"))

# Revealing timing
ROW_DUR = 4.8 / ROWS
STAGGER = ROW_DUR


def generate_ascii_svg(src_path, out_path):
    if not os.path.exists(src_path):
        # Fallback to preparing it if missing
        import prep_photo
        prep_photo.prep(
            os.path.join(HERE, "..", "assets", "avatar-dog.jpg"),
            src_path
        )

    im = Image.open(src_path).convert("L")
    im = im.resize((COLS, ROWS), Image.LANCZOS)
    px = im.load()

    rows_txt = []
    for y in range(ROWS):
        chars = []
        for x in range(COLS):
            lum = px[x, y] / 255.0
            if lum >= 0.94:
                chars.append(" ")
                continue
            idx = int((1.0 - lum) * (len(RAMP) - 1) + 0.5)
            idx = max(0, min(len(RAMP) - 1, idx))
            chars.append(RAMP[idx])
        rows_txt.append("".join(chars))

    art_top = TITLEBAR_H + 8
    font_size = CELL_H * 0.86

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
        f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<defs>'
        f'<linearGradient id="abg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
        '</linearGradient></defs>',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#abg)"/>',
        f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD_X + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
    parts.append(f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
                 f'text-anchor="middle">ratnesh@github: ~$ ./avatar.sh</text>')

    for ry, line in enumerate(rows_txt):
        y = art_top + ry * CELL_H + CELL_H * 0.74
        row_y = art_top + ry * CELL_H
        delay = ry * STAGGER
        safe = html.escape(line)
        text = (f'<text xml:space="preserve" x="{PAD_X}" y="{y:.1f}" fill="{INK}" '
                f'font-size="{font_size:.1f}" textLength="{ART_W}" lengthAdjust="spacing">{safe}</text>')

        if STATIC:
            parts.append(text)
            continue

        parts.append(
            f'<clipPath id="r{ry}"><rect x="{PAD_X}" y="{row_y:.1f}" height="{CELL_H:.1f}" width="0">'
            f'<animate attributeName="width" from="0" to="{ART_W}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.2f}s" fill="freeze"/></rect></clipPath>'
        )
        parts.append(f'<g clip-path="url(#r{ry})">{text}</g>')
        parts.append(
            f'<rect y="{row_y+1:.1f}" width="{CELL_W:.1f}" height="{CELL_H-2:.1f}" fill="{CURSOR}" opacity="0">'
            f'<animate attributeName="x" from="{PAD_X}" to="{PAD_X+ART_W}" begin="{delay:.3f}s" '
            f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>'
        )

    status_line_y = art_top + ART_H + 6
    status_y = status_line_y + 20
    parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W}" y2="{status_line_y:.1f}" stroke="{FRAME}"/>')
    parts.append(f'<text x="{PAD_X}" y="{status_y:.1f}" fill="{TITLE_TEXT}" font-size="13">'
                 f'ratnesh@github:~$ whoami <tspan fill="{INK}">Ratnesh Singh</tspan></text>')
    status_chars = len("ratnesh@github:~$ whoami Ratnesh Singh ")
    cursor_x = PAD_X + status_chars * 13 * 0.58
    parts.append(f'<rect x="{cursor_x:.1f}" y="{status_y-12:.1f}" width="8" height="14" fill="{INK}">'
                 f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
                 f'dur="1s" repeatCount="indefinite"/></rect>')

    parts.append("</svg>")
    svg = "".join(parts)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {out_path} ({len(svg)} bytes, {CANVAS_W}x{CANVAS_H})")


if __name__ == "__main__":
    generate_ascii_svg(SRC, OUT)
