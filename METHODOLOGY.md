# Methodology

> Draft v0.1 — November 2026. Will change as the proof of concept runs.

## 1. Sample selection

- 20–30 consumer apps that request at least one of: heart rate, HRV, resting heart rate, sleep, menstrual cycle, workouts (HealthKit / Health Connect), or the camera for pulse measurement.
- Spread across categories: sleep, fitness, cycle tracking, stress/HRV, meditation/breathing. **No single category exceeds one third of the sample.**
- Selection by App Store / Google Play chart position in a fixed set of regions (US, TW, JP) on a fixed date, recorded in `sample.yaml`.
- The maintainer's own commercial app is included.

## 2. Test environment

- Dedicated test devices (one iPhone, one Android phone) with no personal data, a fresh test Apple ID / Google account, and synthetic Health data.
- mitmproxy with a user-installed CA certificate. No jailbreak or root by default.
- Device clock, region and language are recorded per run.

## 3. Fixed test script (per app)

| Step | Action | Capture window |
|---|---|---|
| 1 | Install and first launch, decline all optional prompts | 2 min |
| 2 | Grant health permissions requested by the app | 2 min |
| 3 | Perform one core reading or session | until done + 2 min |
| 4 | Idle in background | 10 min |
| 5 | Re-open, accept analytics/consent if offered, repeat step 3 | until done + 2 min |
| 6 | Delete account (if any) and app | 2 min |

Each step's traffic is saved separately (`.mitm` files plus a JSON summary).

## 4. Classification

1. **Destination** — map each host to first party / analytics / advertising / crash reporting / attribution / unknown, using public tracker lists (Exodus Privacy, DuckDuckGo Tracker Radar) plus manual review.
2. **Health-like fields** — rule-based detection in JSON, form and protobuf payloads: field names (`hr`, `bpm`, `hrv`, `rmssd`, `sdnn`, `sleep`, `cycle` …) and value ranges (e.g. 30–220 for bpm, 5–300 for ms).
3. **Label comparison** — the app's declared privacy label is recorded in YAML and compared with observed destinations and data types.

## 5. Limits (reported, not hidden)

- **Certificate pinning:** traffic that cannot be decrypted is recorded as "not observable", together with destination hosts from DNS/SNI. Pinning is not bypassed in the default method.
- Server-side processing is invisible to this method.
- Results describe one app version on one date.

## 6. Reproducibility

Every run stores app version, OS version, date, region and the raw capture hash. Scripts in this repo regenerate the published tables from the raw summaries.
