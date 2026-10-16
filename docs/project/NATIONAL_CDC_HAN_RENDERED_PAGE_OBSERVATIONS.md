# CDC HAN rendered notice-page observations

Observed 2026-10-15 through the official CDC notice pages linked below. The local
machine's initial direct HTML requests returned HTTP 403; a browser reader displayed
the official page text. This file records those earlier manually transcribed,
bounded observations of the “At a glance” and “Summary” sections. Later direct
requests returned HTTP 200 for all 14 notice pages. The active fixture now retains
short raw HTML fragments from all 14 pages; see
`NATIONAL_CDC_HAN_ENDPOINT_BLOCKER.md` for the verified shape and remaining gates.

| Notice | Summary type | At-a-glance distribution label |
| --- | --- | --- |
| [00532](https://www.cdc.gov/han/php/notices/han00532.html) | Health Advisory | August 11, 2026 |
| [00531](https://www.cdc.gov/han/php/notices/han00531.html) | Health Advisory | July 14, 2026 |
| [00530](https://www.cdc.gov/han/php/notices/han00530.html) | Health Advisory | May 19, 2026 |
| [00527](https://www.cdc.gov/han/php/notices/han00527.html) | Health Advisory | April 2, 2026, 10:00 AM ET |
| [00526](https://www.cdc.gov/han/php/notices/han00526.html) | Health Advisory | January 20, 2026, 12:30 PM ET |
| [00525](https://www.cdc.gov/han/php/notices/han00525.html) | Health Advisory | December 3, 2025, 12:30 PM ET |
| [00524](https://www.cdc.gov/han/php/notices/han00524.html) | Health Advisory | September 18, 2025, 12:00 PM ET |
| [00523](https://www.cdc.gov/han/php/notices/han00523.html) | Health Update | March 18, 2025 |
| [00522](https://www.cdc.gov/han/php/notices/han00522.html) | Health Advisory | Not shown in the rendered At-a-glance section |
| [00521](https://www.cdc.gov/han/php/notices/han00521.html) | Health Advisory | February 06, 2025, 11:15 AM ET |
| [00520](https://www.cdc.gov/han/php/notices/han00520.html) | Health Advisory | January 16, 2025 |

The active fixture pairs the raw At-a-glance block, first Summary paragraph and
any exact public-recommendations anchor with the index permalink. The parser checks
the notice ID where printed, official URL, date and type evidence, and search-index
badge agreement before joining them. Time labels remain available exactly as
printed in ET. For the five pages that print both a date and time, the parser
interprets ET with the `America/New_York` daylight rules and records the calculated
UTC distribution instant as `source_published_at`. This is an explicit time-zone
conversion, not a separately printed UTC time. The search index's last-reviewed
timestamp remains separately stored. Date-only pages continue to use that index
timestamp as their item time, labeled as such; no distribution hour is inferred.
HAN-00522's page header says March 7, 2025, but the
rendered At-a-glance section omitted its distribution date and notice ID, so
the distribution date remains null. None of these observations establish a
current active alert, affected geography, recommendation URL, or public impact.

Next: establish an approved bounded discovery and page transport, source-use policy,
refresh cadence, and current-alert semantics before considering live ingestion.
