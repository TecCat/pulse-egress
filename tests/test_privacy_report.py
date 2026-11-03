import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pulse_egress.domains import DomainMap  # noqa: E402
from pulse_egress.privacy_report import aggregate, read_records, to_markdown  # noqa: E402

# Shapes follow real App Privacy Report exports; values are synthetic.
LINES = [
    {"type": "networkActivity", "bundleID": "com.example.sleepy", "domain": "api.mixpanel.com",
     "hits": 12, "initiatedType": "AppInitiated", "domainType": 2},
    {"type": "networkActivity", "bundleID": "com.example.sleepy", "domain": "Graph.Facebook.com",
     "hits": 3, "initiatedType": "AppInitiated"},
    {"type": "networkActivity", "bundleID": "com.example.sleepy", "domain": "api.sleepy-app.io", "hits": 40},
    {"type": "networkActivity", "bundleID": "com.example.sleepy", "domain": "cdn.unknown-vendor.net", "hits": 1,
     "initiatedType": "NonAppInitiated"},
    {"type": "access", "accessor": {"identifierType": "bundleID", "identifier": "com.example.sleepy"},
     "category": "microphone", "kind": "intervalBegin"},
    {"type": "access", "accessor": {"identifierType": "bundleID", "identifier": "com.example.sleepy"},
     "category": "microphone", "kind": "intervalEnd"},
    {"type": "networkActivity", "bundleID": "com.other.game", "domain": "doubleclick.net", "hits": 9},
]


def _records():
    return read_records([json.dumps(l) for l in LINES] + ["", "not json"])


def test_groups_by_sdk_and_filters_apps():
    result = aggregate(_records(), DomainMap.load(first_party=["sleepy-app.io"]), apps=["sleepy"])
    assert list(result) == ["com.example.sleepy"]
    rows = {r["sdk"]: r for r in result["com.example.sleepy"]["network"]}
    assert rows["Mixpanel"]["hits"] == 12
    assert rows["Meta SDK"]["domains"] == {"graph.facebook.com"}
    assert rows["first party"]["category"] == "first_party"
    assert rows["unknown"]["not_app_initiated"] == 1
    assert result["com.example.sleepy"]["sensors"] == {"microphone": 1}


def test_array_wrapped_export_is_accepted():
    assert len(read_records([json.dumps(LINES)])) == len(LINES)


def test_markdown_lists_third_parties_and_anonymises_hosts():
    result = aggregate(_records(), DomainMap.load(first_party=["sleepy-app.io"]), apps=["sleepy"])
    md = to_markdown(result, anonymize=True)
    assert "## App A" in md
    assert "Known third-party SDKs: Meta SDK, Mixpanel" in md
    assert "api.mixpanel.com" in md
    assert "sleepy" not in md and "unknown-vendor" not in md
    assert "(1 hidden)" in md
