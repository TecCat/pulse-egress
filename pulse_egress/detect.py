"""Heuristic detection of health-like data in captured request payloads.

Pure Python (3.9+), no mitmproxy dependency, so it can be unit-tested and
reused offline on saved captures.
"""
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qsl

# Short keys only count as an exact token ("hr" must not match "chrome").
EXACT_KEYS = {
    "hr": "cardio", "bpm": "cardio", "pulse": "cardio",
    "hrv": "hrv", "ibi": "hrv", "rr": "hrv",
    "spo2": "respiratory",
    "bmi": "body",
}

# Longer fragments match anywhere in the normalised key.
FRAGMENT_KEYS = {
    "heartrate": "cardio", "restingheart": "cardio", "restinghr": "cardio",
    "rmssd": "hrv", "sdnn": "hrv", "heartratevariability": "hrv", "rrinterval": "hrv",
    "sleep": "sleep",
    "menstrua": "reproductive", "ovulat": "reproductive", "pregnan": "reproductive",
    "fertil": "reproductive", "periodstart": "reproductive", "cyclelength": "reproductive",
    "respiratory": "respiratory", "breathrate": "respiratory", "oxygensat": "respiratory",
    "systolic": "body", "diastolic": "body", "bloodpressure": "body",
    "glucose": "body", "bodytemp": "body", "bodyweight": "body",
    "vo2max": "activity",
    "mood": "mental", "stresslevel": "mental", "anxiety": "mental", "mindful": "mental",
}

# Plausible numeric ranges per category; values outside lower the confidence.
RANGES = {
    "cardio": (25.0, 250.0),
    "hrv": (1.0, 2000.0),
    "respiratory": (4.0, 100.0),
}

# Health words inside string values, e.g. analytics event names like "hrv_measured".
VALUE_WORDS = re.compile(
    r"(?<![a-z])(heart[_ ]?rate|hrv|rmssd|sdnn|bpm|pulse|sleep|menstrua\w*|ovulat\w*|"
    r"pregnan\w*|breath\w*|stress|anxiety|mood|spo2|glucose)(?![a-z])",
    re.IGNORECASE,
)

MAX_VALUE_REPR = 40


def _normalise(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


def _tokens(key: str) -> List[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", key)
    return [t for t in re.split(r"[^a-zA-Z0-9]+", spaced.lower()) if t]


def key_category(key: str) -> Optional[str]:
    for tok in _tokens(key):
        if tok in EXACT_KEYS:
            return EXACT_KEYS[tok]
    norm = _normalise(key)
    for frag, cat in FRAGMENT_KEYS.items():
        if frag in norm:
            return cat
    return None


def _as_number(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _repr(value: Any) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    return text if len(text) <= MAX_VALUE_REPR else text[:MAX_VALUE_REPR] + "…"


def _hit(path: str, key: str, value: Any, category: str, kind: str) -> Dict[str, Any]:
    confidence = "medium"
    if kind == "key":
        number = _as_number(value)
        bounds = RANGES.get(category)
        if number is not None and bounds:
            confidence = "high" if bounds[0] <= number <= bounds[1] else "low"
    elif kind == "value":
        confidence = "low"
    return {
        "path": path, "key": key, "category": category, "kind": kind,
        "confidence": confidence, "value": _repr(value),
    }


def scan(obj: Any, path: str = "$") -> List[Dict[str, Any]]:
    """Walk a decoded payload and return health-like hits."""
    hits: List[Dict[str, Any]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}"
            cat = key_category(str(key))
            if cat and not isinstance(value, (dict, list)):
                hits.append(_hit(child, str(key), value, cat, "key"))
            hits.extend(scan(value, child))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            hits.extend(scan(value, f"{path}[{i}]"))
    elif isinstance(obj, str):
        match = VALUE_WORDS.search(obj)
        if match:
            word = match.group(1).lower()
            cat = key_category(word) or ("respiratory" if word.startswith("breath") else "mental")
            hits.append(_hit(path, word, obj, cat, "value"))
    return hits


def decode_body(content: Optional[bytes], content_type: str) -> Tuple[Any, str]:
    """Return (decoded payload, format). Format is json/form/text/opaque/empty."""
    if not content:
        return None, "empty"
    ctype = (content_type or "").lower()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return None, "opaque"
    stripped = text.lstrip()
    if "json" in ctype or stripped[:1] in ("{", "["):
        try:
            return json.loads(text), "json"
        except ValueError:
            # Batched analytics often send newline-delimited JSON.
            lines = [ln for ln in text.splitlines() if ln.strip()]
            try:
                return [json.loads(ln) for ln in lines], "json"
            except ValueError:
                pass
    if "x-www-form-urlencoded" in ctype:
        return dict(parse_qsl(text, keep_blank_values=True)), "form"
    if "protobuf" in ctype or "octet-stream" in ctype:
        return None, "opaque"
    return text, "text"


def scan_request(query: Dict[str, str], content: Optional[bytes], content_type: str) -> Dict[str, Any]:
    payload, fmt = decode_body(content, content_type)
    hits = scan(query, "$query") if query else []
    if fmt in ("json", "form", "text"):
        hits.extend(scan(payload, "$body"))
    return {"format": fmt, "hits": hits}
