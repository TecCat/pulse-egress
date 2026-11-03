# Capturing an iOS app

Use a **dedicated test iPhone** with no personal data and a test Apple ID. Do not do this on a phone you use for anything else: the mitmproxy CA certificate can decrypt all of that phone's HTTPS traffic while it is trusted.

## 1. Mac

```bash
brew install mitmproxy
```

Find the Mac's LAN address (the phone and the Mac must be on the same Wi-Fi):

```bash
ipconfig getifaddr en0
```

Start a capture (replace the app label and the vendor's own domains):

```bash
PE_APP=sample-sleep-app PE_FIRST_PARTY=example-sleep.com mitmdump -s tools/pe_capture.py --listen-port 8080 -w captures/raw-sample-sleep-app.mitm
```

Output goes to `captures/<date>-<app>/flows.jsonl` (`captures/` is gitignored and must never be committed: it holds raw payloads).

## 2. iPhone (one-time)

1. **Settings → Wi-Fi → (i) on your network → Configure Proxy → Manual**: server = the Mac's LAN address, port `8080`.
2. In Safari open `http://mitm.it`, download the iOS profile.
3. **Settings → General → VPN & Device Management** → install the mitmproxy profile.
4. **Settings → General → About → Certificate Trust Settings** → turn on full trust for the mitmproxy certificate.

Check: open any HTTPS website in Safari; it should load and appear in the mitmdump output.

## 3. Run the fixed test script

In a second terminal, switch steps as you go (see METHODOLOGY.md §3):

```bash
python3 tools/pe_step.py captures/2026-11-05-sample-sleep-app 1
```

| Step | Action on the phone |
|---|---|
| 1 | Install, first launch, decline optional prompts — 2 min |
| 2 | Grant the health permissions the app asks for — 2 min |
| 3 | Take one reading or complete one session, then wait 2 min |
| 4 | Send the app to background, wait 10 min |
| 5 | Reopen, accept analytics consent if offered, repeat step 3 |
| 6 | Delete the account (if any) and the app — 2 min |

Stop mitmdump with `Ctrl+C`.

## 4. Summarise

```bash
python3 tools/pe_summary.py captures/*/flows.jsonl --anonymize
```

Rows with **Not observable > 0** mean the app refused the mitmproxy certificate (usually certificate pinning). That is recorded as a finding; the default method does not bypass it.

## 5. Clean up afterwards

- iPhone: Wi-Fi proxy → **Off**; remove the mitmproxy profile in **VPN & Device Management**.
- Keep `captures/` on the Mac only.
