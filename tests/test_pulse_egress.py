import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pulse_egress.detect import key_category, scan_request  # noqa: E402
from pulse_egress.domains import DomainMap  # noqa: E402
from pulse_egress.summary import aggregate, to_markdown  # noqa: E402


# --- detect ---------------------------------------------------------------

def test_short_keys_need_an_exact_token():
    assert key_category("hr") == "cardio"
    assert key_category("avg_hr") == "cardio"
    assert key_category("chrome") is None
    assert key_category("thread") is None


def test_camel_case_and_fragments():
    assert key_category("restingHeartRate") == "cardio"
    assert key_category("hrvRMSSD") == "hrv"
    assert key_category("sleep_stage") == "sleep"
    assert key_category("lastMenstrualPeriod") == "reproductive"
    assert key_category("user_id") is None


def test_json_body_with_plausible_values_is_high_confidence():
    body = json.dumps({"event": "session_end", "props": {"heartRate": 72, "rmssd": 41.5}}).encode()
    hits = scan_request({}, body, "application/json")["hits"]
    by_key = {h["key"]: h for h in hits}
    assert by_key["heartRate"]["confidence"] == "high"
    assert by_key["rmssd"]["category"] == "hrv"


def test_implausible_value_is_low_confidence():
    body = json.dumps({"bpm": 9000}).encode()
    hit = scan_request({}, body, "application/json")["hits"][0]
    assert hit["confidence"] == "low"


def test_event_name_values_are_detected():
    body = json.dumps({"event": "hrv_measured"}).encode()
    hit = scan_request({}, body, "application/json")["hits"][0]
    assert (hit["kind"], hit["category"]) == ("value", "hrv")


def test_ndjson_batches_and_form_and_query():
    ndjson = b'{"sleep_minutes": 420}\n{"mood": "anxious"}\n'
    assert len(scan_request({}, ndjson, "application/x-ndjson")["hits"]) >= 2
    form = b"uid=1&pulse=66"
    assert scan_request({}, form, "application/x-www-form-urlencoded")["hits"][0]["category"] == "cardio"
    assert scan_request({"bpm": "70"}, None, "")["hits"][0]["path"] == "$query.bpm"


def test_binary_body_is_opaque_not_an_error():
    result = scan_request({}, b"\x08\x96\x01\xff\xfe", "application/x-protobuf")
    assert result == {"format": "opaque", "hits": []}


def test_values_are_truncated():
    body = json.dumps({"sleep": "x" * 500}).encode()
    hit = scan_request({}, body, "application/json")["hits"][0]
    assert len(hit["value"]) <= 41


# --- domains --------------------------------------------------------------

def test_longest_suffix_wins_and_first_party_overrides():
    dm = DomainMap.load(first_party=["example-sleep.com"])
    assert dm.classify("firebaselogging-pa.googleapis.com")["sdk"] == "Firebase"
    assert dm.classify("www.googleapis.com")["category"] == "platform"
    assert dm.classify("api.mixpanel.com")["sdk"] == "Mixpanel"
    assert dm.classify("api.example-sleep.com")["category"] == "first_party"
    assert dm.classify("notmixpanel.com")["sdk"] == "unknown"


# --- summary --------------------------------------------------------------

def test_summary_counts_and_never_publishes_values():
    records = [
        {"app": "sleepy", "sdk": "Mixpanel", "category": "analytics", "host": "api.mixpanel.com",
         "step": "3-core-reading", "bytes": 2048, "observable": True,
         "health_hits": [{"category": "cardio", "confidence": "high", "value": "SECRET-72"}]},
        {"app": "sleepy", "sdk": "Mixpanel", "category": "analytics", "host": "api.mixpanel.com",
         "step": "4-background-idle", "bytes": 1024, "observable": True, "health_hits": []},
        {"app": "sleepy", "sdk": "unknown", "category": "unknown", "host": "pinned.example",
         "step": "1-install-first-launch", "observable": False, "health_hits": []},
    ]
    md = to_markdown(aggregate(records), anonymize=True)
    assert "| App A | Mixpanel | analytics | 2 | 0 | 3.0 | 3, 4 | cardio (1h) |" in md
    assert "| App A | unknown | unknown | 1 | 1 |" in md
    assert "sleepy" not in md and "SECRET" not in md
