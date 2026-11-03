"""Summarise an iOS App Privacy Report export per app and SDK.

    python3 tools/pe_privacy_report.py ~/Downloads/App_Privacy_Report.ndjson --apps sleep,calm
    python3 tools/pe_privacy_report.py report.ndjson --apps sleep --anonymize > results/apr-summary.md
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pulse_egress.domains import DomainMap  # noqa: E402
from pulse_egress.privacy_report import aggregate, read_records, to_markdown  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("report", type=Path, help="App Privacy Report .ndjson")
parser.add_argument("--apps", default="", help="comma-separated bundle-ID fragments to keep (default: all apps)")
parser.add_argument("--first-party", default="", help="comma-separated vendor domains to label first party")
parser.add_argument("--list-apps", action="store_true", help="only list bundle IDs found in the report")
parser.add_argument("--anonymize", action="store_true", help="App A, App B …; hide vendor and unclassified hosts")
args = parser.parse_args()

with open(args.report, encoding="utf-8") as fh:
    records = read_records(fh)

domains = DomainMap.load(first_party=[d for d in args.first_party.split(",") if d.strip()])
apps = [a.strip() for a in args.apps.split(",") if a.strip()] or None
result = aggregate(records, domains, apps)

if args.list_apps:
    for bundle, entry in result.items():
        print(f"{bundle}\t{sum(r['hits'] for r in entry['network'])} hits")
else:
    sys.stdout.write(to_markdown(result, anonymize=args.anonymize))
