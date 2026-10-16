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

Decision: keep `cdc_han` and `cdc_han_notices` disabled; treat their official pages as manual
references, not working ingest sources. Do not scrape the notice archive,
automate email signup, or invent a fixture schema. To resume RS-039, find an official current
feed/API documented by CDC, inspect a bounded response with ID, time, alert type, jurisdiction
and public instruction URL, then add a synthetic fixture and parser. The resulting live source
would still need a separate exact-URL signoff. The existing public notice pages remain useful as
human references.
