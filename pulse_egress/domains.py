"""Map a destination host to a known SDK and category."""
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

DEFAULT_MAP = Path(__file__).resolve().parent.parent / "data" / "sdk_domains.json"


class DomainMap:
    def __init__(self, entries: List[Dict[str, str]], first_party: Iterable[str] = ()):
        # Longest suffix first, so "firebaselogging.googleapis.com" beats "googleapis.com".
        self.entries = sorted(entries, key=lambda e: len(e["suffix"]), reverse=True)
        self.first_party = [s.lower().lstrip(".") for s in first_party]

    @classmethod
    def load(cls, path: Optional[Path] = None, first_party: Iterable[str] = ()) -> "DomainMap":
        with open(path or DEFAULT_MAP, encoding="utf-8") as fh:
            return cls(json.load(fh)["domains"], first_party)

    @staticmethod
    def _matches(host: str, suffix: str) -> bool:
        return host == suffix or host.endswith("." + suffix)

    def classify(self, host: str) -> Dict[str, str]:
        host = (host or "").lower().rstrip(".")
        for suffix in self.first_party:
            if self._matches(host, suffix):
                return {"sdk": "first party", "category": "first_party"}
        for entry in self.entries:
            if self._matches(host, entry["suffix"]):
                return {"sdk": entry["sdk"], "category": entry["category"]}
        return {"sdk": "unknown", "category": "unknown"}
