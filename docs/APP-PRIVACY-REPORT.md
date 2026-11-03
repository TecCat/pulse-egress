# Zero-cost check with the iOS App Privacy Report

No proxy, no certificate, no device wipe. iOS records which domains each app contacts; this shows **destinations only, not payload contents**, and it is not affected by certificate pinning.

## 1. On the iPhone

1. **Settings → Privacy & Security → App Privacy Report** → turn on.
2. Install the apps under test from the App Store. Use each one normally for 1–2 days: grant permissions, take a reading, leave it in the background.
3. Back in **App Privacy Report**, scroll to the bottom → **Save App Privacy Report** → AirDrop the `.ndjson` file to the Mac.

The report covers the last 7 days for every app on the phone. Keep the raw file on the Mac; do not commit it (`captures/` is gitignored, so store it there).

## 2. On the Mac

Find the bundle IDs in the report:

```bash
python3 tools/pe_privacy_report.py captures/App_Privacy_Report.ndjson --list-apps
```

Summarise the apps under test (fragments of their bundle IDs, comma-separated):

```bash
python3 tools/pe_privacy_report.py captures/App_Privacy_Report.ndjson --apps sleep,calm
```

Anonymised version for publishing:

```bash
python3 tools/pe_privacy_report.py captures/App_Privacy_Report.ndjson --apps sleep,calm --anonymize
```

## 3. Compare with the privacy label

For each app, note the App Store **App Privacy** section, then compare it with the "Known third-party SDKs" line. A third-party analytics or advertising SDK under an app whose label says "Data Not Collected" is a candidate finding for vendor disclosure (see ETHICS.md), not a conclusion: the report shows that a connection happened, not what was sent.
