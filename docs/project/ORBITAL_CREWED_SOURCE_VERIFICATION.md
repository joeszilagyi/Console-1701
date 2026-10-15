# ORBITAL ISS and Crewed Spaceflight Source Verification

Checked 2026-10-15 against the agencies' own pages and exact feeds. This classifies sources for
the first pass; only separately allowlisted and tested feeds can run live.

| Source | Observed access and decision | Signal role |
| --- | --- | --- |
| [NASA Station RSS](https://www.nasa.gov/missions/station/feed/) and [Space Station blog RSS](https://www.nasa.gov/blogs/spacestation/feed/) | Exact RSS channels and parser fixtures are verified in [NASA RSS source verification](ORBITAL_NASA_RSS_SOURCE_VERIFICATION.md); both have disabled-by-default live opt-ins. | Dated station operations, docking, EVA, crew or cargo events. |
| [NASA Humans in Space](https://www.nasa.gov/humans-in-space/humans-in-space-overview/) | Official overview, reference only. No event feed is implied by the page. | Mission context, not a recent event by itself. |
| [NASA Commercial Crew blog](https://www.nasa.gov/blogs/commercialcrew/) | Exact `/feed/` URL returned HTTP 200 `application/rss+xml` on 2026-10-15. Parser channel and article filtering remain unverified; no live allowlist. | Crewed launch, docking, return, mission status after fixture review. |
| [ESA Human Spaceflight RSS](https://www.esa.int/rssfeed/Our_Activities/Human_Spaceflight) | Exact channel and parser fixture verified in [ESA RSS source verification](ORBITAL_ESA_RSS_SOURCE_VERIFICATION.md); disabled-by-default live opt-in. | Independent agency confirmation of crew/ISS events. |
| [JAXA Kibo news](https://humans-in-space.jaxa.jp/en/news/kibo/index.html) | Current dated official news page. JAXA's [older RSS guide](https://iss.jaxa.jp/help/rss.html) explicitly marks that site archived; no current feed contract was verified. Reference/source health only. | ISS/Kibo operations if a future feed or permitted adapter is verified. |
| [CSA ISS](https://www.asc-csa.gc.ca/eng/iss/) | Official ISS context. The CSA home page links a general RSS URL, but direct retrieval failed during verification; no ISS-specific feed shape established. Reference/source health only. | Canadian crew/ISS context pending a tested endpoint. |
| [NASA Spot the Station](https://www.nasa.gov/spot-the-station/) | Official location-based sighting service and trajectory-data link, not a crew event feed. Reference/source health only; no trajectory download or tracking display. | Potential future LOCAL sky-interest card after a narrow, permitted sighting contract. |

Recent operational signals require a dated, source-backed action such as launch, docking,
undocking, EVA, crew return, or major station anomaly. Mission overviews, education posts, Kibo
workshops, ordinary research features, sighting schedules, and position data are context or low
priority. Source publication time is distinct from an event time or a tentative schedule. A
schedule update must not be reported as a completed event. NASA channels count as one agency
family for corroboration; ESA, JAXA, and CSA count independently only after their own verified
items exist. Store headline metadata, official URL, mission/event IDs when explicit, bounded
summary, and timing evidence; do not ingest article bodies or crew personal details.

All sources remain disabled in the registry. Unverified page/feed candidates must stay out of the
HTTP allowlist. No homepage scraping, social fetch, page-load fetch, or live app scan was run for
this verification.
