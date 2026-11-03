# Ethics and disclosure policy

## What this project does

- Observes network traffic **from devices and accounts the researcher owns**, during normal use of publicly available apps.
- Uses only synthetic health data on dedicated test devices.

## What this project does not do

- No access to vendor servers beyond what normal app use generates. No API fuzzing, credential testing, or scraping.
- No decompiling, cracking or redistribution of app binaries.
- No collection of other people's data.
- No bypassing certificate pinning in the default method.

## Responsible disclosure

1. A finding about a specific app (for example, health data sent to a third party not declared in its privacy label) is reported privately to the vendor's security or privacy contact.
2. The vendor gets **90 days** before the finding is published. Fixes released earlier shorten the window.
3. Published results are aggregated by SDK and data flow. Individual apps are named only after the disclosure window, and only when the finding is material.
4. Vendor responses are published alongside the finding if the vendor agrees.

## Conflict of interest

The maintainer independently develops a commercial breathing app. To keep this research independent:

- That app is audited with the same method and its results are published without special treatment.
- Results are never framed as product comparisons or rankings.
- Neither that app nor its publisher uses these findings in marketing, app-store copy or websites.

## Contact

Security and privacy reports about this project: [to be added]
