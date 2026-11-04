"""Parse an iOS App Privacy Report export (.ndjson) into per-app, per-SDK rows.

iOS (15+) records which domains each app contacted and which sensors it used.
Export: Settings > Privacy & Security > App Privacy Report > Save App Privacy Report.
The format is undocumented, so unknown record types and fields are skipped, not errors.
"""
import json
from collections import defaultdict
from typing import Dict, Iterable, List, Optional

from pulse_egress.domains import DomainMap


def read_records(lines: Iterable[str]) -> List[dict]:
    records = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        # Some iOS versions wrap everything in one JSON array.
        records.extend(obj if isinstance(obj, list) else [obj])
    return [r for r in records if isinstance(r, dict)]


def _bundle(rec: dict) -> Optional[str]:
    if rec.get("bundleID"):
        return rec["bundleID"]
    accessor = rec.get("accessor") or {}
    return accessor.get("identifier")


def _wanted(bundle: str, apps: Optional[List[str]]) -> bool:
    return not apps or any(a.lower() in bundle.lower() for a in apps)


def aggregate(records: List[dict], domains: DomainMap, apps: Optional[List[str]] = None) -> Dict[str, Dict]:
    """Return {bundle_id: {"network": [rows], "sensors": {category: count}}}."""
    network: Dict[tuple, Dict] = {}
    sensors: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for rec in records:
        bundle = _bundle(rec)
        if not bundle or not _wanted(bundle, apps):
            continue
        kind = rec.get("type")
        if kind == "networkActivity" and rec.get("domain"):
            host = rec["domain"].lower()
            sdk = domains.classify(host)
            key = (bundle, sdk["sdk"], sdk["category"])
            row = network.setdefault(key, {
                "sdk": sdk["sdk"], "category": sdk["category"],
                "hits": 0, "domains": set(), "not_app_initiated": 0,
            })
            row["hits"] += int(rec.get("hits") or 1)
            row["domains"].add(host)
            if rec.get("initiatedType") == "NonAppInitiated":
                row["not_app_initiated"] += 1
        elif kind == "access" and rec.get("kind") in ("intervalBegin", None):
            sensors[bundle][rec.get("category", "unknown")] += 1

    out: Dict[str, Dict] = {}
    for (bundle, _, _), row in network.items():
        out.setdefault(bundle, {"network": [], "sensors": {}})["network"].append(row)
    for bundle, cats in sensors.items():
        out.setdefault(bundle, {"network": [], "sensors": {}})["sensors"] = dict(cats)
    for entry in out.values():
        # Third parties first: that is what the label comparison is about.
        entry["network"].sort(key=lambda r: (r["category"] in ("first_party", "platform"), r["category"], r["sdk"]))
    return dict(sorted(out.items()))


THIRD_PARTY = {"analytics", "advertising", "attribution", "crash_reporting", "messaging", "payments", "remote_config", "ip_lookup"}


def to_markdown(apps: Dict[str, Dict], anonymize: bool = False) -> str:
    lines = []
    for i, (bundle, entry) in enumerate(apps.items()):
        name = f"App {chr(ord('A') + i)}" if anonymize else f"`{bundle}`"
        third = sorted({r["sdk"] for r in entry["network"] if r["category"] in THIRD_PARTY})
        unknown = sum(len(r["domains"]) for r in entry["network"] if r["category"] == "unknown")
        lines.append(f"## {name}\n")
        lines.append(f"- Known third-party SDKs: {', '.join(third) if third else 'none'}")
        lines.append(f"- Unclassified domains: {unknown}")
        if entry["sensors"]:
            used = ", ".join(f"{c} ×{n}" for c, n in sorted(entry["sensors"].items()))
            lines.append(f"- Sensor/data access: {used}")
        lines.append("")
        lines.append("| SDK | Category | Hits | Domains |")
        lines.append("|---|---|---|---|")
        for row in entry["network"]:
            hosts = sorted(row["domains"])
            # Vendor and unclassified hosts usually name the app, so hide them when anonymising.
            if anonymize and row["category"] in ("first_party", "unknown"):
                shown = f"({len(hosts)} hidden)"
            else:
                shown = ", ".join(hosts[:4]) + (" …" if len(hosts) > 4 else "")
            lines.append(f"| {row['sdk']} | {row['category']} | {row['hits']} | {shown} |")
        lines.append("")
    return "\n".join(lines) if lines else "No matching apps in the report.\n"
