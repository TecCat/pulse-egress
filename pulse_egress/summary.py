"""Aggregate flows.jsonl records into a per-SDK summary.

The summary never contains payload values, only counts and categories,
so it is safe to publish after the disclosure window.
"""
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

CONFIDENCE_ORDER = ("high", "medium", "low")


def load(paths: Iterable[Path]) -> List[dict]:
    records = []
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            records.extend(json.loads(line) for line in fh if line.strip())
    return records


def aggregate(records: List[dict]) -> List[Dict]:
    rows: Dict[tuple, Dict] = {}
    for rec in records:
        key = (rec.get("app", "?"), rec.get("sdk", "unknown"), rec.get("category", "unknown"))
        row = rows.setdefault(key, {
            "app": key[0], "sdk": key[1], "category": key[2],
            "requests": 0, "not_observable": 0, "bytes": 0,
            "hosts": set(), "steps": set(),
            "health": defaultdict(lambda: defaultdict(int)),
        })
        row["requests"] += 1
        row["bytes"] += rec.get("bytes", 0)
        row["hosts"].add(rec.get("host", "?"))
        row["steps"].add(rec.get("step", "unset"))
        if not rec.get("observable", True):
            row["not_observable"] += 1
        for hit in rec.get("health_hits", []):
            row["health"][hit["category"]][hit["confidence"]] += 1
    return sorted(rows.values(), key=lambda r: (r["app"], r["category"] == "first_party", r["sdk"]))


def _health_cell(health: Dict) -> str:
    if not health:
        return "—"
    parts = []
    for cat in sorted(health):
        counts = health[cat]
        detail = "/".join(f"{counts[c]}{c[0]}" for c in CONFIDENCE_ORDER if counts.get(c))
        parts.append(f"{cat} ({detail})")
    return ", ".join(parts)


def to_markdown(rows: List[Dict], anonymize: bool = False) -> str:
    aliases: Dict[str, str] = {}
    lines = [
        "| App | SDK | Category | Requests | Not observable | KB | Steps | Health-like data (h/m/l confidence) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        app = row["app"]
        if anonymize:
            app = aliases.setdefault(app, f"App {chr(ord('A') + len(aliases))}")
        steps = ", ".join(sorted(s.split("-", 1)[0] for s in row["steps"]))
        lines.append(
            f"| {app} | {row['sdk']} | {row['category']} | {row['requests']} | {row['not_observable']} "
            f"| {row['bytes'] / 1024:.1f} | {steps} | {_health_cell(row['health'])} |"
        )
    return "\n".join(lines) + "\n"
