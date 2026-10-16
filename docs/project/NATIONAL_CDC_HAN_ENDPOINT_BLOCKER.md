# CDC HAN Parser Endpoint Blocker

Reviewed 2026-10-15 while preparing RS-039. The [CDC HAN overview](https://www.cdc.gov/han/php/about/index.html)
defines Health Alert, Advisory and Update types. The official
[HAN notice archive](https://www.cdc.gov/han/php/notices/index.html) exposes individual public
notices with stable-looking `CDCHAN` numbers and publication dates. That verifies source ownership
and page content, but not an authorized machine-readable feed or API.

Bounded HEAD checks of the older `https://emergency.cdc.gov/han/rss.asp` and `.xml` addresses
redirected to the general CDC emergency page. Candidate current paths
`https://www.cdc.gov/han/rss.xml` and
`https://www.cdc.gov/han/php/notices/index.xml` returned 404. An older CDC source described a
HAN RSS feed, but that does not verify an endpoint in 2026. CDC currently advertises email
subscription on its HAN page. No current exact public HAN feed/API or stable paginated data
shape was established.

CDC's documented [Content Services API](https://tools.cdc.gov/api/docs/info.aspx) was also
checked with bounded five-row media queries for `sourceUrlContains=/han/php/notices/` and
`q=Health Alert Network`. Both returned HTTP 200 JSON with `meta.pagination.total=0`. This API
does not currently provide a verified HAN notice shape or a replacement for the archive feed.

CDC's [Stacks help](https://stacks.cdc.gov/help) documents machine-readable OAI-PMH and
collection exports, and Stacks has a [HAN collection](https://stacks.cdc.gov/cbrowse?parentId=cdc%3A24915).
The collection explicitly describes its entries as archived past alerts, says they may be
superseded or expired, and directs readers to CDC HAN or email for current notices. Its
machine-readable metadata is therefore an archive path, not a current-alert discovery feed
for this Recent Signal parser. It does not clear the RS-039 gate.

Initial decision: keep `cdc_han` and `cdc_han_notices` disabled; treat their official pages as manual
references, not working ingest sources. Do not scrape the notice archive,
automate email signup, or invent a fixture schema. To resume RS-039, find an official current
feed/API documented by CDC, inspect a bounded response with ID, time, alert type, jurisdiction
and public instruction URL, then add a synthetic fixture and parser. The resulting live source
would still need a separate exact-URL signoff. The existing public notice pages remain useful as
human references.

## Follow-up: first-party search JSON, 2026-10-15

The official [HAN notice archive](https://www.cdc.gov/han/php/notices/index.html) now serves a
`content-collection` element pointing to `/han/php/modules/han-archive.json`. That collection
configuration names the HAN notices folder and a 20-row page size. CDC's own collection widget
uses `https://search.cdc.gov/srch/internet_wcms/select`; a bounded request with the exact
`permalink:*han/php/notices/*` filter, 20 rows, descending last-reviewed date and eight selected
metadata fields returned HTTP 200 JSON. It contained 15 records: 14 HAN notice permalinks and
the archive index. The newest eight notice rows were dated in 2026. The older static JSON
fallback was stale at 2025, so it is not the fixture source.

The observed response is stored at
`tests/fixtures/national/cdc_han_search_2026_10_15.json`. The fixture-only parser validates
the echoed query, bounded shape, unique `hanNNNNN.html` URLs, and CDC-hosted source identity.
It stores titles, short index excerpts, notice IDs and both index date fields. The index's
`cdc_last_reviewed_date_dt` matched the visible notice date in three bounded page checks, but
is still labeled as an index review date rather than a verified distribution timestamp.
The image filename hints at the message type, cross-checked against three notice badges, but
is not a semantic type field. No jurisdiction, affected population, public instruction link,
active-alert state or public impact is inferred from titles or badge art. An offline scan
verifies persistence without HTTP.

The search service is a general CDC site index used by the archive widget, not a documented
HAN feed. The earlier prohibition on inventing a fixture shape is superseded by the observed
JSON shape above; the earlier live-source decision remains. No live URL is in the allowlist and the
registry source stays disabled. Finish RS-039 after a notice-level type/date contract and
source use policy are verified, then seek a separate exact live-query release decision.
