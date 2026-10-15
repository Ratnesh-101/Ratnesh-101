#!/usr/bin/env python3
"""
Render the streak / numbers card from data/contributions.json (written daily by
fetch_contributions.py) as a terminal-window SVG that sits beside avatar-ascii.svg.

The canvas is the same size as the portrait (840 x 880) so the two panels line
up when the README shows them side by side at equal widths. Fonts are sized for
that half-width display (~0.5x).

Sections:
1. Six stat tiles with count-up animations (current streak, longest streak,
   contributions, active days, best day, avg / active day).
2. Most used languages segmented progress bar and percentage legend.
3. Monthly-contributions bar chart with animated bars.

    python scripts/render_stats_svg.py [data.json] [output.svg]
"""
import datetime
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "contributions.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "stats.svg")

BG = "#0d1117"
BG2 = "#111722"
TILE = "#161b22"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#e6edf3"
GREEN = "#39d353"
BAR = "#26a641"

DEFAULT_LANGUAGES = [
    {"name": "Python", "percent": 66.7, "color": "#38bdf8"},
    {"name": "JavaScript", "percent": 19.0, "color": "#facc15"},
    {"name": "TypeScript", "percent": 11.8, "color": "#60a5fa"},
    {"name": "Other", "percent": 2.5, "color": "#8b949e"},
]

W, H = 840, 880                      # == avatar-ascii.svg canvas
PAD = 20
TITLEBAR_H = 30
COLS, ROWS = 2, 3
GAP = 14
TILE_W = (W - PAD * 2 - GAP * (COLS - 1)) / COLS
TILE_H = 116
TILES_TOP = TITLEBAR_H + 18
LANG_TOP = TILES_TOP + ROWS * TILE_H + (ROWS - 1) * GAP + GAP
LANG_H = 120
CHART_TOP = LANG_TOP + LANG_H + GAP
CHART_H = H - PAD - CHART_TOP

# timing (seconds)
TILE_STAGGER = 0.12
SLIDE_DUR = 0.42
COUNT_DUR = 1.1
FRAMES = 16
LANG_START = TILE_STAGGER * (COLS * ROWS) + 0.2
BAR_START = LANG_START + 0.35
BAR_STAGGER = 0.05
BAR_DUR = 0.55


def short(d):
    dt = datetime.date.fromisoformat(d)
    return f"{dt.strftime('%b')} {dt.day}"


def span(s):
    return f"{short(s['start'])} \u2013 {short(s['end'])}" if s["length"] else "\u2014"


with open(SRC, "r", encoding="utf-8") as f:
    data = json.load(f)

cur, lng, best = data["current_streak"], data["longest_streak"], data["best_day"]
n_days = len(data["days"])
languages = data.get("languages") or DEFAULT_LANGUAGES

# (label, value, suffix, caption, accent)
tiles = [
    ("current streak", cur["length"], " days", span(cur), GREEN),
    ("longest streak", lng["length"], " days", span(lng), INK),
    ("contributions", data["total_contributions"], "", "in the last year", INK),
    ("active days", data["active_days"], f" / {n_days}", f'{data["active_days"] / n_days:.0%} of the year', INK),
    ("best day", best["count"], "", short(best["date"]), INK),
    ("avg / active day", data["avg_per_active_day"], "", "contributions", INK),
]


def fmt(v, like):
    return f"{v:,.1f}" if isinstance(like, float) else f"{int(round(v)):,}"


parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    '<style>'
    f'.t{{opacity:0;animation:in {SLIDE_DUR}s ease-out both}}'
    '@keyframes in{0%{opacity:0;transform:translateY(12px)}100%{opacity:1;transform:translateY(0)}}'
    f'.b{{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow {BAR_DUR}s ease-out both}}'
    '@keyframes grow{to{transform:scaleY(1)}}'
    '.lb{transform-box:fill-box;transform-origin:left;transform:scaleX(0);animation:growX 0.6s ease-out both}'
    '@keyframes growX{to{transform:scaleX(1)}}'
    '@media (prefers-reduced-motion: reduce){.t,.b,.lb{opacity:1!important;transform:none!important;animation:none!important}}'
    '</style>',
    f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
parts.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
             f'text-anchor="middle">ratnesh@github: ~$ ./stats.sh</text>')

# ---- stat tiles ----------------------------------------------------------
for i, (label, value, suffix, caption, accent) in enumerate(tiles):
    col, row = i % COLS, i // COLS
    x = PAD + col * (TILE_W + GAP)
    y = TILES_TOP + row * (TILE_H + GAP)
    start = i * TILE_STAGGER
    count_start = start + SLIDE_DUR * 0.55

    parts.append(f'<g class="t" style="animation-delay:{start:.2f}s">')
    parts.append(f'<rect x="{x:.1f}" y="{y}" width="{TILE_W:.1f}" height="{TILE_H}" rx="10" '
                 f'fill="{TILE}" stroke="{FRAME}"/>')
    parts.append(f'<text x="{x+22:.1f}" y="{y+32}" fill="{MUTED}" font-size="20">$ {label}</text>')

    # count-up frames: ease-out so it decelerates into the real number
    num_y = y + 78
    for k in range(1, FRAMES + 1):
        p = k / FRAMES
        v = value * (1 - (1 - p) ** 3)
        t_on = count_start + COUNT_DUR * (k - 1) / FRAMES
        t_off = count_start + COUNT_DUR * k / FRAMES
        anim = f'<set attributeName="opacity" to="1" begin="{t_on:.3f}s"/>'
        if k < FRAMES:
            anim += f'<set attributeName="opacity" to="0" begin="{t_off:.3f}s"/>'
        parts.append(
            f'<text x="{x+22:.1f}" y="{num_y}" opacity="0" font-size="46" font-weight="700" fill="{accent}">'
            f'{fmt(v, value)}<tspan font-size="20" font-weight="400" fill="{MUTED}">{suffix}</tspan>'
            f'{anim}</text>'
        )
    parts.append(f'<text x="{x+22:.1f}" y="{y+104}" fill="{MUTED}" font-size="16">{caption}</text>')
    parts.append('</g>')

# ---- most used languages section -----------------------------------------
lang_box_w = W - PAD * 2
parts.append(f'<g class="t" style="animation-delay:{LANG_START:.2f}s">')
parts.append(f'<rect x="{PAD}" y="{LANG_TOP}" width="{lang_box_w}" height="{LANG_H}" rx="10" '
             f'fill="{TILE}" stroke="{FRAME}"/>')
parts.append(f'<text x="{PAD+24}" y="{LANG_TOP+34}" fill="{MUTED}" font-size="20">$ most used languages</text>')

bar_x = PAD + 24
bar_y = LANG_TOP + 48
bar_w = lang_box_w - 48
bar_h = 12

parts.append(f'<defs><clipPath id="lang-bar-clip">'
             f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="6"/>'
             f'</clipPath></defs>')
parts.append(f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="6" fill="#21262d"/>')
parts.append(f'<g class="lb" clip-path="url(#lang-bar-clip)" style="animation-delay:{LANG_START + 0.1:.2f}s">')

cur_x = bar_x
for lang in languages:
    seg_w = max(2.0, bar_w * (lang["percent"] / 100.0))
    parts.append(f'<rect x="{cur_x:.1f}" y="{bar_y}" width="{seg_w:.1f}" height="{bar_h}" fill="{lang["color"]}"/>')
    cur_x += seg_w
parts.append('</g>')

# language legend dots and percentages
legend_y = LANG_TOP + 92
slot_w = bar_w / len(languages)
for i, lang in enumerate(languages):
    lx = bar_x + i * slot_w
    parts.append(f'<circle cx="{lx + 6:.1f}" cy="{legend_y - 5:.1f}" r="5" fill="{lang["color"]}"/>')
    parts.append(
        f'<text x="{lx + 18:.1f}" y="{legend_y}" font-size="15" fill="{INK}">'
        f'{html.escape(lang["name"])} '
        f'<tspan fill="{MUTED}">{lang["percent"]:.1f}%</tspan></text>'
    )
parts.append('</g>')

# ---- monthly bars chart --------------------------------------------------
chart_x, chart_w = PAD, W - PAD * 2
parts.append(f'<g class="t" style="animation-delay:{BAR_START - 0.2:.2f}s">')
parts.append(f'<rect x="{chart_x}" y="{CHART_TOP}" width="{chart_w}" height="{CHART_H}" rx="10" '
             f'fill="{TILE}" stroke="{FRAME}"/>')
parts.append(f'<text x="{chart_x+24}" y="{CHART_TOP+34}" fill="{MUTED}" font-size="20">$ contributions / month</text>')
parts.append('</g>')

plot_top = CHART_TOP + 56
plot_bot = CHART_TOP + CHART_H - 34
plot_l, plot_r = chart_x + 24, chart_x + chart_w - 24
slot = (plot_r - plot_l) / len(data["monthly"])
bar_w = slot * 0.62
peak = max(m["total"] for m in data["monthly"]) or 1
for i, m in enumerate(data["monthly"]):
    h = max(2, (plot_bot - plot_top) * m["total"] / peak)
    bx = plot_l + i * slot + (slot - bar_w) / 2
    fill = GREEN if m["total"] == peak else BAR
    delay = BAR_START + i * BAR_STAGGER
    parts.append(f'<rect class="b" x="{bx:.1f}" y="{plot_bot - h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" '
                 f'rx="3" fill="{fill}" style="animation-delay:{delay:.2f}s"/>')
    mon = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")[0]
    parts.append(f'<text x="{bx + bar_w/2:.1f}" y="{plot_bot + 24}" fill="{MUTED}" font-size="16" '
                 f'text-anchor="middle">{mon}</text>')
    if m["total"] == peak:
        parts.append(f'<text class="t" style="animation-delay:{delay + BAR_DUR:.2f}s" x="{bx + bar_w/2:.1f}" '
                     f'y="{plot_bot - h - 8:.1f}" fill="{INK}" font-size="16" text-anchor="middle">{peak:,}</text>')

parts.append('</svg>')
svg = "".join(parts)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"wrote {OUT}: {W} x {H}, {len(svg)//1024} KB")
