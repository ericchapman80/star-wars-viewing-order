#!/usr/bin/env python3

from __future__ import annotations

import re
from pathlib import Path


README_PATH = Path(__file__).resolve().parents[1] / "README.md"

FAMILY_TRACKER_START = "<!-- family-tracker:start -->"
FAMILY_TRACKER_END = "<!-- family-tracker:end -->"
STATS_BADGES_START = "<!-- stats-badges:start -->"
STATS_BADGES_END = "<!-- stats-badges:end -->"
PROGRESS_TABLE_START = "<!-- progress-table:start -->"
PROGRESS_TABLE_END = "<!-- progress-table:end -->"

CHECKBOX_RE = re.compile(r"^- \[(?P<done>[ xX])\] (?P<label>.+)$")

CANON_TITLES = {
    "The Acolyte",
    "Star Wars Episode I: The Phantom Menace",
    "Star Wars Episode II: Attack of the Clones",
    "Star Wars: The Clone Wars animated movie",
    "Star Wars: The Clone Wars series",
    "Tales of the Jedi",
    "Star Wars Episode III: Revenge of the Sith",
    "Tales of the Empire",
    "Tales of the Underworld",
    "Star Wars: The Bad Batch",
    "Solo: A Star Wars Story",
    "Obi-Wan Kenobi",
    "Andor",
    "Star Wars: Rebels",
    "Rogue One: A Star Wars Story",
    "Star Wars Episode IV: A New Hope",
    "Star Wars Episode V: The Empire Strikes Back",
    "Star Wars Episode VI: Return of the Jedi",
    "The Mandalorian",
    "The Book of Boba Fett",
    "Ahsoka",
    "Skeleton Crew",
    "Star Wars: Resistance",
    "Star Wars Episode VII: The Force Awakens",
    "Star Wars Episode VIII: The Last Jedi",
    "Star Wars Episode IX: The Rise of Skywalker",
}

SKYWALKER_TITLES = {
    "Star Wars Episode I: The Phantom Menace",
    "Star Wars Episode II: Attack of the Clones",
    "Star Wars Episode III: Revenge of the Sith",
    "Star Wars Episode IV: A New Hope",
    "Star Wars Episode V: The Empire Strikes Back",
    "Star Wars Episode VI: Return of the Jedi",
    "Star Wars Episode VII: The Force Awakens",
    "Star Wars Episode VIII: The Last Jedi",
    "Star Wars Episode IX: The Rise of Skywalker",
}

EXTRA_TITLES = {
    "Lego Star Wars: The Yoda Chronicles",
    "Lego Star Wars: The Padawan Menace",
    "Star Wars: Droids",
    "Star Wars Holiday Special",
    "Lego Star Wars: The Empire Strikes Out",
    "Lego Star Wars: The Freemaker Adventures",
    "Lego Star Wars: Droid Tales",
    "Ewoks",
    "Lego Star Wars: The Resistance Rises",
    "Star Wars: Forces of Destiny",
}


def extract_block(text: str, start_marker: str, end_marker: str) -> tuple[int, int, str]:
    start = text.index(start_marker)
    end = text.index(end_marker)
    block_start = start + len(start_marker)
    return start, end, text[block_start:end]


def replace_block(text: str, start_marker: str, end_marker: str, new_content: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker)
    before = text[: start + len(start_marker)]
    after = text[end:]
    return f"{before}\n{new_content}\n{after}"


def parse_family_tracker(text: str) -> list[tuple[str, bool]]:
    _, _, block = extract_block(text, FAMILY_TRACKER_START, FAMILY_TRACKER_END)
    items: list[tuple[str, bool]] = []
    for raw_line in block.splitlines():
        line = raw_line.strip()
        match = CHECKBOX_RE.match(line)
        if not match:
            continue
        title = match.group("label").replace("**", "").strip()
        done = match.group("done").lower() == "x"
        items.append((title, done))
    return items


def compute_stats(items: list[tuple[str, bool]]) -> dict[str, tuple[int, int]]:
    title_map = {title: done for title, done in items}

    def count(group: set[str]) -> tuple[int, int]:
        present = [title for title in group if title in title_map]
        watched = sum(1 for title in present if title_map[title])
        return watched, len(present)

    family_total = len(items)
    family_watched = sum(1 for _, done in items if done)

    return {
        "family": (family_watched, family_total),
        "canon": count(CANON_TITLES),
        "skywalker": count(SKYWALKER_TITLES),
        "extras": count(EXTRA_TITLES),
    }


def percent(watched: int, total: int) -> int:
    if total == 0:
        return 0
    return round((watched / total) * 100)


def color_for(pct: int, palette: tuple[str, str, str]) -> str:
    low, mid, high = palette
    if pct >= 80:
        return high
    if pct >= 50:
        return mid
    return low


def build_badges(stats: dict[str, tuple[int, int]]) -> str:
    family = stats["family"]
    canon = stats["canon"]
    skywalker = stats["skywalker"]

    family_color = color_for(percent(*family), ("8B1E2D", "8C6A00", "2F6B3B"))
    canon_color = color_for(percent(*canon), ("8B1E2D", "8C6A00", "2F6B3B"))
    skywalker_color = color_for(percent(*skywalker), ("8B1E2D", "0F4C81", "2F6B3B"))

    return "\n".join(
        [
            "<p>",
            f'  <img alt="Family tracker progress" src="https://img.shields.io/badge/Family%20Tracker-{family[0]}%2F{family[1]}%20watched-{family_color}?style=flat-square" />',
            f'  <img alt="Canon tracker progress" src="https://img.shields.io/badge/Canon%20Tracker-{canon[0]}%2F{canon[1]}%20watched-{canon_color}?style=flat-square" />',
            f'  <img alt="Skywalker Saga progress" src="https://img.shields.io/badge/Skywalker%20Saga-{skywalker[0]}%2F{skywalker[1]}%20watched-{skywalker_color}?style=flat-square" />',
            "</p>",
        ]
    )


def build_progress_table(stats: dict[str, tuple[int, int]]) -> str:
    rows = [
        ("Family tracker", stats["family"]),
        ("Canon core tracker", stats["canon"]),
        ("Skywalker Saga films", stats["skywalker"]),
        ("Lego, legacy, and bonus extras", stats["extras"]),
    ]

    lines = [
        "| Collection | Watched | Total | Progress |",
        "| --- | ---: | ---: | ---: |",
    ]
    for label, (watched, total) in rows:
        lines.append(f"| {label} | {watched} | {total} | {percent(watched, total)}% |")
    return "\n".join(lines)


def main() -> None:
    text = README_PATH.read_text()
    items = parse_family_tracker(text)
    stats = compute_stats(items)

    text = replace_block(text, STATS_BADGES_START, STATS_BADGES_END, build_badges(stats))
    text = replace_block(text, PROGRESS_TABLE_START, PROGRESS_TABLE_END, build_progress_table(stats))

    README_PATH.write_text(text)


if __name__ == "__main__":
    main()
