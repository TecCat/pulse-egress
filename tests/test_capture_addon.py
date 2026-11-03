"""Exercise tools/pe_capture.py without mitmproxy, using stand-in flow objects."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ADDON = Path(__file__).resolve().parent.parent / "tools" / "pe_capture.py"


class FakeQuery(dict):
    def items(self, multi=False):
        return super().items()


def _load_addon(monkeypatch, tmp_path):
    monkeypatch.setenv("PE_APP", "fake-app")
    monkeypatch.setenv("PE_RUN_DIR", str(tmp_path))
    monkeypatch.setenv("PE_FIRST_PARTY", "fake-app.com")
    spec = importlib.util.spec_from_file_location("pe_capture", ADDON)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.addons[0]


def _flow(host, path, body=b"", ctype="", query=None):
    request = SimpleNamespace(
        pretty_host=host, method="POST", path=path,
        query=FakeQuery(query or {}), headers={"content-type": ctype},
        get_content=lambda strict=False: body,
    )
    return SimpleNamespace(request=request)


def test_request_and_pinning_records(monkeypatch, tmp_path):
    addon = _load_addon(monkeypatch, tmp_path)
    (tmp_path / "STEP").write_text("3-core-reading\n")

    body = json.dumps({"event": "hrv_measured", "props": {"heartRate": 72}}).encode()
    addon.request(_flow("api.mixpanel.com", "/track?ip=1", body, "application/json", {"ip": "1"}))
    addon.request(_flow("api.fake-app.com", "/sync"))
    addon.tls_failed_client(SimpleNamespace(conn=SimpleNamespace(sni="pinned.vendor.io")))
    addon.done()

    recs = [json.loads(l) for l in (tmp_path / "flows.jsonl").read_text().splitlines()]
    mix, first, pinned = recs
    assert (mix["sdk"], mix["step"], mix["path"], mix["query_keys"]) == ("Mixpanel", "3-core-reading", "/track", ["ip"])
    assert {h["category"] for h in mix["health_hits"]} == {"hrv", "cardio"}
    assert first["category"] == "first_party" and first["format"] == "empty"
    assert (pinned["observable"], pinned["host"]) == (False, "pinned.vendor.io")
