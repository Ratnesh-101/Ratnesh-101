#!/usr/bin/env python3
"""
Scrape daily contribution counts from GitHub's public contributions endpoint
and write data/contributions.json with raw days, derived statistics,
and repository language statistics.

No token or authentication required.
"""
import datetime
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_PROFILE_USER", "Ratnesh-101")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")

DEFAULT_LANGUAGES = [
    {"name": "Python", "percent": 66.8, "color": "#38bdf8"},
    {"name": "JavaScript", "percent": 18.9, "color": "#facc15"},
    {"name": "TypeScript", "percent": 11.9, "color": "#60a5fa"},
    {"name": "Other", "percent": 2.4, "color": "#8b949e"},
]

LANG_COLORS = {
    "Python": "#38bdf8",
    "JavaScript": "#facc15",
    "TypeScript": "#60a5fa",
    "C++": "#f43f5e",
    "C": "#94a3b8",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Shell": "#89e051",
}


def fetch_days():
    resp = requests.get(URL, headers={"User-Agent": "profile-readme-bot/1.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        print("no calendar cells found -- github markup may have changed", file=sys.stderr)
        sys.exit(1)

    days = []
    for td in cells:
        date = td.get("data-date")
        if not date:
            continue
        td_id = td.get("id")
        tooltip_el = soup.find("tool-tip", attrs={"for": td_id}) if td_id else None
        text = tooltip_el.get_text(strip=True) if tooltip_el else ""
        if re.search(r"no contributions", text, re.I):
            count = 0
        else:
            m = re.match(r"(\d+)", text)
            count = int(m.group(1)) if m else 0
        days.append({"date": date, "count": count, "level": int(td.get("data-level") or 0)})

    days.sort(key=lambda d: d["date"])
    return days


def fetch_languages():
    try:
        resp = requests.get(
            f"https://api.github.com/users/{USERNAME}/repos?per_page=100",
            headers={"User-Agent": "profile-readme-bot/1.0"},
            timeout=15,
        )
        if resp.status_code != 200:
            return DEFAULT_LANGUAGES
        repos = resp.json()
        lang_totals = {}
        for r in repos:
            if r.get("fork"):
                continue
            lang_url = r.get("languages_url")
            if lang_url:
                try:
                    l_resp = requests.get(lang_url, headers={"User-Agent": "profile-readme-bot/1.0"}, timeout=8)
                    if l_resp.status_code == 200:
                        for l, cnt in l_resp.json().items():
                            lang_totals[l] = lang_totals.get(l, 0) + cnt
                except Exception:
                    continue

        total_bytes = sum(lang_totals.values())
        if not total_bytes:
            return DEFAULT_LANGUAGES

        sorted_langs = sorted(lang_totals.items(), key=lambda x: x[1], reverse=True)
        top3 = sorted_langs[:3]
        other_bytes = sum(cnt for _, cnt in sorted_langs[3:])

        result = []
        for l, cnt in top3:
            pct = round((cnt / total_bytes) * 100, 1)
            result.append({
                "name": l,
                "percent": pct,
                "color": LANG_COLORS.get(l, "#22d3ee"),
            })
        if other_bytes > 0:
            oth_pct = round((other_bytes / total_bytes) * 100, 1)
            result.append({"name": "Other", "percent": oth_pct, "color": "#8b949e"})
        return result
    except Exception as e:
        print(f"Notice fetching languages: {e}, using default breakdown", file=sys.stderr)
        return DEFAULT_LANGUAGES


def compute_current_streak(days):
    if not days:
        return 0, None, None
    idx = len(days) - 1
    if days[idx]["count"] == 0:
        idx -= 1  # today isn't over yet -- don't break the streak on it
    streak = 0
    end_idx = idx
    while idx >= 0 and days[idx]["count"] > 0:
        streak += 1
        idx -= 1
    start_idx = idx + 1
    if streak == 0:
        return 0, None, None
    return streak, days[start_idx]["date"], days[end_idx]["date"]


def compute_longest_streak(days):
    longest = run = 0
    longest_start = longest_end = None
    run_start_idx = None
    for i, d in enumerate(days):
        if d["count"] > 0:
            if run == 0:
                run_start_idx = i
            run += 1
            if run > longest:
                longest = run
                longest_start = days[run_start_idx]["date"]
                longest_end = days[i]["date"]
        else:
            run = 0
    return longest, longest_start, longest_end


def build_data(days, languages):
    total = sum(d["count"] for d in days)
    active_days = sum(1 for d in days if d["count"] > 0)
    best = max(days, key=lambda d: d["count"]) if days else {"date": "", "count": 0}
    cur_len, cur_start, cur_end = compute_current_streak(days)
    long_len, long_start, long_end = compute_longest_streak(days)

    monthly = {}
    for d in days:
        key = d["date"][:7]
        monthly[key] = monthly.get(key, 0) + d["count"]
    monthly_list = [{"month": k, "total": v} for k, v in sorted(monthly.items())]

    return {
        "username": USERNAME,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"] if days else "", "end": days[-1]["date"] if days else ""},
        "total_contributions": total,
        "active_days": active_days,
        "avg_per_active_day": round(total / active_days, 1) if active_days else 0,
        "current_streak": {"length": cur_len, "start": cur_start, "end": cur_end},
        "longest_streak": {"length": long_len, "start": long_start, "end": long_end},
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly_list,
        "languages": languages,
        "days": days,
    }


if __name__ == "__main__":
    days = fetch_days()
    languages = fetch_languages()
    data = build_data(days, languages)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {OUT_PATH}: {data['total_contributions']} contributions, "
          f"current streak {data['current_streak']['length']}, "
          f"longest streak {data['longest_streak']['length']}, "
          f"languages: {[l['name'] for l in data['languages']]}")
