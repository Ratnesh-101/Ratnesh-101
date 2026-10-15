#!/usr/bin/env python3
"""
Generate a hand-authored neofetch-style terminal info-card SVG (info-card.svg).
Features:
  - Title bar with terminal dots
  - Colored key/value rows pulling real content from Ratnesh's profile:
    Now, Education, Highlights/projects, Focus, Status
  - NO tech-stack row
  - Staggered line-by-line fade and slide in animation
  - Neofetch ANSI color palette blocks
  - Supports STATIC=1 env var for frozen frame
  - Width 980 x Height 748 (scales to 490 x 374 in README)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "info-card.svg")

STATIC = bool(os.environ.get("STATIC"))

CANVAS_W = 980
CANVAS_H = 748
TITLEBAR_H = 34
PAD_X = 36
ROW_START_Y = 82
ROW_GAP = 34

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"

# Neofetch color scheme
KEY_COLOR = "#58a6ff"       # Blue key
VAL_COLOR = "#e6edf3"       # Crisp text
ACCENT = "#22d3ee"          # Cyan accent
GREEN = "#39d353"           # Green
GOLD = "#f2cc60"            # Gold / yellow
PURPLE = "#bc8cff"          # Soft purple
MUTED = "#8b949e"           # Muted text

ROWS = [
    # (type, label, value, val_color, optional_badge)
    ("header", "ratnesh", "github", ACCENT, None),
    ("sep", "", "", MUTED, None),
    ("kv", "OS", "Ubuntu / Linux Workspace (Arch & GitHub)", VAL_COLOR, None),
    ("kv", "Host", "Autonomous Agentic Systems x64", VAL_COLOR, None),
    ("kv", "Role", "AI/ML Engineer & Systems Developer", GOLD, None),
    ("kv", "Now", "Building Compass (autonomous AI agent with memory)", ACCENT, None),
    ("kv", "Education", "B.Tech in Computer Science & Engineering", VAL_COLOR, None),
    ("kv", "Highlights", "Compass — persistent memory agent across repos", GREEN, None),
    ("kv", "Projects", "Syngenta Kheti Compass — 8-signal visit priority", GREEN, None),
    ("kv", "Policy AI", "news-360-feedback — Gov of India ministries (SIH)", PURPLE, None),
    ("kv", "Focus", "Multi-Agent Orchestration & Low-Latency Inference", VAL_COLOR, None),
    ("kv", "Status", "Open to SWE Internships & Full-Time AI/ML Roles", GOLD, None),
    ("kv", "Connect", "linkedin.com/in/ratnesh-singh-307ab2267", VAL_COLOR, None),
]

ANSI_COLORS_NORMAL = [
    "#161b22", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#b1bac4"
]
ANSI_COLORS_BRIGHT = [
    "#484f58", "#ffa198", "#56d364", "#e3b341", "#79c0ff", "#d2a8ff", "#56d4dd", "#ffffff"
]


def render():
    css = """
@keyframes slideIn {
  0% { opacity: 0; transform: translateX(-16px); }
  100% { opacity: 1; transform: translateX(0); }
}
.row {
  opacity: 0;
  animation: slideIn 0.42s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@media (prefers-reduced-motion: reduce) {
  .row { opacity: 1 !important; transform: none !important; animation: none !important; }
}
""".strip()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" '
        f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<style>{css}</style>',
        '<defs>'
        f'<linearGradient id="cbg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
        '</linearGradient></defs>',
        f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="url(#cbg)"/>',
        f'<rect x="0.5" y="0.5" width="{CANVAS_W-1}" height="{CANVAS_H-1}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]

    # Terminal buttons
    for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{PAD_X + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>')
    parts.append(f'<text x="{CANVAS_W/2}" y="{TITLEBAR_H/2 + 4}" fill="{TITLE_TEXT}" font-size="12" '
                 f'text-anchor="middle">ratnesh@github: ~ (neofetch)</text>')

    # Rows
    y = ROW_START_Y
    anim_delay = 0.08
    stagger = 0.065

    for item in ROWS:
        kind = item[0]
        delay_attr = f'style="animation-delay:{anim_delay:.3f}s"' if not STATIC else ''
        row_cls = 'class="row"' if not STATIC else ''

        if kind == "header":
            user, host = item[1], item[2]
            parts.append(
                f'<g {row_cls} {delay_attr}>'
                f'<text x="{PAD_X}" y="{y}" font-size="18" font-weight="700">'
                f'<tspan fill="{ACCENT}">{user}</tspan>'
                f'<tspan fill="{MUTED}">@</tspan>'
                f'<tspan fill="{GREEN}">{host}</tspan></text>'
                '</g>'
            )
            y += 18
        elif kind == "sep":
            parts.append(
                f'<g {row_cls} {delay_attr}>'
                f'<line x1="{PAD_X}" y1="{y}" x2="{CANVAS_W - PAD_X}" y2="{y}" stroke="{FRAME}" stroke-opacity="0.8"/>'
                '</g>'
            )
            y += 24
        elif kind == "kv":
            k, v, v_col = item[1], item[2], item[3]
            # Key width padding
            key_x = PAD_X
            val_x = PAD_X + 130
            parts.append(
                f'<g {row_cls} {delay_attr}>'
                f'<text x="{key_x}" y="{y}" font-size="15" font-weight="700" fill="{KEY_COLOR}">{k}:</text>'
                f'<text x="{val_x}" y="{y}" font-size="15" fill="{v_col}">{v}</text>'
                '</g>'
            )
            y += ROW_GAP
        anim_delay += stagger

    # ANSI palette color blocks at bottom
    palette_y = y + 14
    block_w = 40
    block_h = 18
    block_gap = 6
    total_pal_w = len(ANSI_COLORS_NORMAL) * (block_w + block_gap)
    pal_start_x = (CANVAS_W - total_pal_w) / 2

    pal_delay_attr = f'style="animation-delay:{anim_delay:.3f}s"' if not STATIC else ''
    pal_cls = 'class="row"' if not STATIC else ''

    parts.append(f'<g {pal_cls} {pal_delay_attr}>')
    for i, col in enumerate(ANSI_COLORS_NORMAL):
        bx = pal_start_x + i * (block_w + block_gap)
        parts.append(f'<rect x="{bx:.1f}" y="{palette_y:.1f}" width="{block_w}" height="{block_h}" rx="3" fill="{col}"/>')
    for i, col in enumerate(ANSI_COLORS_BRIGHT):
        bx = pal_start_x + i * (block_w + block_gap)
        parts.append(f'<rect x="{bx:.1f}" y="{palette_y + block_h + 5:.1f}" width="{block_w}" height="{block_h}" rx="3" fill="{col}"/>')
    parts.append('</g>')

    parts.append('</svg>')
    return "".join(parts)


if __name__ == "__main__":
    svg = render()
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT} ({len(svg)} bytes, {CANVAS_W}x{CANVAS_H})")
