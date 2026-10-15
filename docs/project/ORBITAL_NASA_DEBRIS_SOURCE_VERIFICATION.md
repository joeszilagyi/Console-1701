# ORBITAL NASA Orbital Debris Source Verification

Checked 2026-10-15 against the official [NASA Orbital Debris Program Office](https://orbitaldebris.jsc.nasa.gov/),
[Quarterly News index](https://orbitaldebris.jsc.nasa.gov/quarterly-news/),
[Debris Reentry page](https://orbitaldebris.jsc.nasa.gov/reentry/), and
[reference documents](https://orbitaldebris.jsc.nasa.gov/reference-documents/).
NASA identifies the office as its orbital debris measurement, modeling, mitigation and mission
support program. The quarterly index offers issue links to PDFs and shows issue topics and dates.
The reentry page explains assessment methods and links to DAS and ORSAT tools. It is not a public
object-by-object reentry prediction feed.

| Registry key | Decision | Reason |
| --- | --- | --- |
| `nasa_orbital_debris_home` | Reference/source health only | Official program context; no event fields or feed established. |
| `nasa_orbital_debris_news` | Reference/source health only | Quarterly PDF index, not a verified RSS/Atom feed. The observed cadence is quarterly; individual PDFs are not first-pass article bodies. |
| `nasa_orbital_debris_reentry` | Reference/source health only | Describes risk methods, not predictions for specific current objects. |

The registry retains all three disabled. The quarterly entry is now classified as a manual,
source-health-only PDF index instead of an RSS candidate; the reentry entry is likewise a manual
reference. No exact machine-readable metadata endpoint, rate policy, or response contract was
verified for live ingestion, so none is allowlisted. A future metadata adapter would need an
official stable feed or documented API, bounded polling, publication-time and issue identity
fields, response limits, and offline fixture tests. Do not download PDFs or derive live reentry
warnings from methodology pages.

NASA ODPO and other NASA/JPL feeds are one agency family for independent corroboration. Any future
event item should store only title, official URL, issue/publication time, source, and a bounded
description. General debris research stays low priority; reentry or hazard language must pass the
ORBITAL sensitivity and public-impact rules before display. Disabled, unsupported, and
source-health-only states should remain explicit in the UI.
