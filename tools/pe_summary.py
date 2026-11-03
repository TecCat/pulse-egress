"""Print a per-SDK markdown summary of one or more captures.

    python3 tools/pe_summary.py captures/*/flows.jsonl --anonymize > results/poc-summary.md
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pulse_egress.summary import aggregate, load, to_markdown  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("flows", nargs="+", type=Path, help="flows.jsonl files")
parser.add_argument("--anonymize", action="store_true", help="replace app names with App A, App B …")
args = parser.parse_args()

sys.stdout.write(to_markdown(aggregate(load(args.flows)), anonymize=args.anonymize))
