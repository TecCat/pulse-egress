# Pulse Egress

**Where does your heart-rate data go?**

Pulse Egress is an independent, open-source audit of consumer health-sensing apps on iOS and Android. It observes what network traffic these apps send after reading sensitive signals (heart rate, HRV, sleep, cycle and fitness data from HealthKit, Health Connect, the camera or a wearable) and compares that behavior with what each app declares in its App Store privacy label or Google Play data-safety section.

> **Status:** early proof of concept (November 2026). The method and tooling are being written in the open.

## Why

Health-sensing apps are a fast-growing consumer category, and the data they handle is among the most sensitive a phone holds. Users cannot see where this data goes after it leaves the device, and app-store privacy labels are self-declared and rarely verified. Existing tracker research covers apps in general; little of it focuses on the path *health-platform data → third-party SDK → network*.

## What this project produces

1. **Tooling** — a reproducible capture-and-classify pipeline: mitmproxy capture, destination classification (analytics, advertising, crash reporting, first party), and heuristic detection of health-like fields in payloads.
2. **Test scripts** — the same fixed sequence of actions for every app (install, grant permissions, take a reading, idle, delete), so results are comparable.
3. **Dataset** — per-SDK and per-data-flow results across 20–30 apps, published after responsible disclosure.
4. **Label comparison** — declared privacy label vs. observed behavior.

Results are aggregated **by SDK and data flow, not as app rankings.** Individual findings go to the vendor first (see [ETHICS.md](ETHICS.md)).

## Scope

In scope: consumer apps that read heart rate, HRV, sleep, menstrual cycle, or fitness data. Out of scope: medical devices under regulatory clearance, pet apps, and anything requiring access to a vendor's servers beyond normal use.

## Method

See [METHODOLOGY.md](METHODOLOGY.md).

## Conflict of interest

The maintainer is also the independent developer of a commercial breathing app. That app is included in the audit sample under the same method, and its results are published like any other. Neither that app nor its publisher will use these findings in marketing.

## License

Code: Apache-2.0. Dataset and reports: CC BY 4.0.
