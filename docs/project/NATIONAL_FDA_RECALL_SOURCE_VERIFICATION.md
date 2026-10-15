# FDA Recall Source Verification

Reviewed 2026-10-15 for RS-040. Decision: **official RSS metadata candidates verified;
no live ingest enabled**. The openFDA enforcement API is a separate data product and must not be
treated as a public alert feed.

## Ownership and bounded feed shape

The FDA [agency RSS directory](https://www.fda.gov/about-fda/contact-fda/subscribe-podcasts-and-news-feeds)
links exact [Recalls](https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/recalls/rss.xml),
[Food Safety Recalls](https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/food-safety-recalls/rss.xml),
and [MedWatch Safety Alerts](https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medwatch/rss.xml)
feeds. A bounded read of each returned HTTP 200 `application/rss+xml` on 2026-10-15, RSS channel
plus 20 items, and `ETag`/`Last-Modified` headers. Each item carried title, link, description,
`pubDate`, creator and GUID. Descriptions were short metadata in the sampled first items; a
parser must still bound them. The sampled item links/GUIDs used `http://www.fda.gov/`; a future
parser should verify the official HTTPS canonical target and avoid arbitrary redirects. Items
from the general Recalls and Food Safety feeds overlapped, so they are not independent sources
for convergence scoring. A Spanish-language item was also present; do not silently treat a
translation as a second recall.

These feeds do **not** expose a structured recall classification, distribution geography, product
lot, hazard level or lifecycle status in the observed item fields. Do not infer those from a
headline or the feed name. The FDA [public recalls page](https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts)
says its notices are selected press releases and public notices, not all monitored recalls. A
future feed parser can store bounded headline metadata and source URL, while richer evidence
requires a separately verified source and contract. No raw live response was committed.

## Enforcement report data is a different use case

The official [openFDA food enforcement overview](https://open.fda.gov/apis/food/enforcement/)
documents weekly data from FDA's Recall Enterprise System. It includes classifications and
reported distributions, can revise old records, and may appear after recall initiation. Its
[searchable fields](https://open.fda.gov/apis/food/enforcement/searchable-fields/) include
`classification`, `reason_for_recall`, `distribution_pattern`, `report_date`, `recall_number`,
`status` and product description. The openFDA response is not equivalent to a selected FDA
public-safety notice. Most decisively, the overview says enforcement data must not be used as
a method to collect data for public alerts or to track a recall's lifecycle; the published status
may remain unchanged. Keep this endpoint research/reference-only for the Recent Signal alert UI.
Do not join it to RSS headlines by fuzzy product names.

The [openFDA terms](https://open.fda.gov/terms/) and
[authentication/limits page](https://open.fda.gov/apis/authentication/) govern any separate
analytical use. The latter currently lists both no-key and API-key request limits, while also
saying a key is required, so access behavior would need a direct signoff before implementation.
No key or openFDA request was made in this review.

## Policy, health and release gate

The FDA `robots.txt` general crawler section did not disallow these RSS paths and declared a
30-second crawl delay. A conservative proposed refresh is at least 30 minutes, with conditional
requests and backoff. Before live admission, record the exact URL and redirect/canonical behavior,
fixture XML, duplicate-GUID handling across feeds and translations, retention, health states,
and whether a zero-item response is valid. Use only an explicit opt-in `news-scan` against an exact
allowlisted URL. Page loads, host scans and tests remain offline.

Ranking should require explicit evidence of serious public hazard or national distribution; a
routine firm recall headline alone is a low-to-moderate signal. The feeds may include manufacturer
statements, so preserve FDA's hosting/source provenance without implying FDA authored every
notice or independently verified every claim. No article body or private customer information
belongs in storage. A current official RSS item can be displayed as an FDA-hosted notice with its
original link and a freshness limit; if the feed fails, report source-health failure and retain
last good rows only under configured retention.
