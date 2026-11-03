"""mitmproxy addon: log every request from the device under test as one JSON line.

Usage (see docs/SETUP-iOS.md):
    PE_APP=sample-sleep-app PE_FIRST_PARTY=example.com \
        mitmdump -s tools/pe_capture.py -w captures/<run>/raw.mitm

Environment:
    PE_APP          label for the app under test (required)
    PE_RUN_DIR      output folder (default: captures/<YYYY-MM-DD>-<PE_APP>)
    PE_FIRST_PARTY  comma-separated domains owned by the app vendor

The current test-script step is read from <PE_RUN_DIR>/STEP on every request;
change it with `python3 tools/pe_step.py <PE_RUN_DIR> <step>`.
"""
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pulse_egress.detect import scan_request  # noqa: E402
from pulse_egress.domains import DomainMap  # noqa: E402


class PulseEgressCapture:
    def __init__(self):
        app = os.environ.get("PE_APP")
        if not app:
            raise SystemExit("PE_APP is not set: name the app under test, e.g. PE_APP=sample-sleep-app")
        self.app = app
        default_dir = ROOT / "captures" / f"{date.today().isoformat()}-{app}"
        self.run_dir = Path(os.environ.get("PE_RUN_DIR", default_dir))
        self.run_dir.mkdir(parents=True, exist_ok=True)
        first_party = [d for d in os.environ.get("PE_FIRST_PARTY", "").split(",") if d.strip()]
        self.domains = DomainMap.load(first_party=first_party)
        self.out = open(self.run_dir / "flows.jsonl", "a", encoding="utf-8")

    def _step(self) -> str:
        try:
            return (self.run_dir / "STEP").read_text(encoding="utf-8").strip() or "unset"
        except FileNotFoundError:
            return "unset"

    def _write(self, record: dict) -> None:
        self.out.write(json.dumps(record, ensure_ascii=False) + "\n")
        self.out.flush()

    def request(self, flow) -> None:
        req = flow.request
        host = req.pretty_host
        query = {k: v for k, v in req.query.items()}
        content = req.get_content(strict=False)
        ctype = req.headers.get("content-type", "")
        found = scan_request(query, content, ctype)
        self._write({
            "ts": round(time.time(), 3),
            "app": self.app,
            "step": self._step(),
            "observable": True,
            "method": req.method,
            "host": host,
            "path": req.path.split("?", 1)[0],
            "query_keys": sorted(query),
            "content_type": ctype,
            "bytes": len(content or b""),
            "format": found["format"],
            **self.domains.classify(host),
            "health_hits": found["hits"],
        })

    def tls_failed_client(self, data) -> None:
        # The app rejected our certificate: usually certificate pinning.
        conn = getattr(data, "conn", None) or getattr(getattr(data, "context", None), "client", None)
        host = getattr(conn, "sni", None) or "unknown"
        self._write({
            "ts": round(time.time(), 3),
            "app": self.app,
            "step": self._step(),
            "observable": False,
            "reason": "tls_failed_client",
            "host": host,
            **self.domains.classify(host),
            "health_hits": [],
        })

    def done(self) -> None:
        self.out.close()


addons = [PulseEgressCapture()]
