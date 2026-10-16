# CDC HAN rendered notice-page observations

Observed 2026-10-15 through the official CDC notice pages linked below. The local
machine's direct HTML requests returned HTTP 403; a browser reader displayed the
official page text. This is a manually transcribed, bounded observation of the
“At a glance” and “Summary” sections, not a raw HTML response or a live parser.
The separate three-notice HTML-fragment fixture remains the only verified raw
page-summary shape. The CDC search-index JSON is the ingest fixture.

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

The fixture retains only the short type phrase from each Summary section, the
At-a-glance labels, notice URL, and observation date. The parser checks the
notice ID, official URL, date format, type phrase, and search-index badge
agreement before joining them. Time labels are kept as printed in ET, with no
invented UTC instant. HAN-00522's page header says March 7, 2025, but the
rendered At-a-glance section omitted its distribution date and notice ID, so
the distribution date remains null. None of these observations establish a
current active alert, affected geography, recommendation URL, or public impact.

Next: obtain a legitimate raw page or approved machine-readable notice feed
for the remaining eleven notices; verify page structure, distribution time,
recommendation anchors, and source policy before considering live ingestion.
