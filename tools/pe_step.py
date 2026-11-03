"""Set the current test-script step for a running capture.

    python3 tools/pe_step.py captures/2026-11-05-sample-sleep-app 3
"""
import sys
from pathlib import Path

STEPS = {
    "1": "1-install-first-launch",
    "2": "2-grant-health-permissions",
    "3": "3-core-reading",
    "4": "4-background-idle",
    "5": "5-reopen-consent-reading",
    "6": "6-delete",
}

if len(sys.argv) != 3 or sys.argv[2] not in STEPS:
    sys.exit(f"usage: pe_step.py <run_dir> <{'|'.join(STEPS)}>")

run_dir = Path(sys.argv[1])
run_dir.mkdir(parents=True, exist_ok=True)
(run_dir / "STEP").write_text(STEPS[sys.argv[2]] + "\n", encoding="utf-8")
print(f"step -> {STEPS[sys.argv[2]]}")
