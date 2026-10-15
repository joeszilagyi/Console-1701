# NATIONAL NHC advisory feed verification

Checked 2026-10-15 against NHC's official public documentation and bounded basin-feed responses.
The three basin URLs are now registered as disabled, fixture-only NATIONAL sources;
no NHC URL is enabled or added to the live HTTP allowlist.

## Ownership and candidate feeds

- NHC/CPHC [lists basin-wide RSS feeds](https://www.nhc.noaa.gov/aboutrss.shtml) for the
  [Atlantic](https://www.nhc.noaa.gov/index-at.xml),
  [Eastern Pacific](https://www.nhc.noaa.gov/index-ep.xml), and
  [Central Pacific](https://www.nhc.noaa.gov/index-cp.xml). The page also lists per-storm wallet
  and per-product feeds. These are the candidate basin feed URLs; the NHC homepage and data archive
  are discovery/reference pages, not interchangeable feed endpoints.
- The official page calls these RSS 2.0 and describes basin-wide versus storm-specific feeds.
  A bounded read of all three exact basin XML URLs confirmed the channel and item structure below.
- NHC's [GIS RSS documentation](https://www.nhc.noaa.gov/gis/rss.php) documents separate GIS
  feeds. Those are a different product family and should not be combined with the basin text feed
  merely because both use RSS.

## Bounded basin XML observation

On 2026-10-15 each URL returned HTTP 200 `text/xml`, RSS version 2.0, with a channel title matching
its basin. The Atlantic response was 2,088 bytes with two items, Eastern Pacific was 37,973 bytes
with 13 items, and Central Pacific was 2,489 bytes with two items. Responses supplied `ETag`,
`Last-Modified` and a five-minute cache maximum. The site's `robots.txt` showed no disallow
rule for these feeds. These are point observations, not a guaranteed size/cadence contract.

Items expose `title`, `description`, RFC 822 `pubDate`, official `link`, `guid` and `author`.
The Eastern Pacific feed included a basin tropical-weather outlook, cyclone summary items,
Public and Forecast Advisories, Forecast Discussions, wind probabilities and graphics. A summary
item carried an NHC namespace `Cyclone` element with `center`, `type`, `name`, `wallet`, `atcf`,
`datetime`, `movement`, `pressure`, `wind` and `headline`. The advisory items in that response had
the standard fields but no `Cyclone` element. The summary GUID included ATCF identity and issue
time; advisory GUIDs were official product URLs. A future parser must handle these two shapes
separately and bound long descriptions (observed advisory/discussion descriptions ran to several
thousand characters). No raw feed copy is committed as a test fixture here.

The Atlantic and Central Pacific feeds each had a tropical-weather outlook plus a "There are no
tropical cyclones at this time" sentinel. The sentinel's `pubDate` was ahead of the observation
date in both feeds, so it must be excluded from active-event and recency ranking. A valid feed
with this sentinel is healthy with zero active storms, not a parser failure.

## Advisory and watch/warning interpretation

- NHC's [product description](https://www.nhc.noaa.gov/pdf/NHC_Product_Description.pdf)
  specifies the regular six-hour advisory cycle at 0300, 0900, 1500, and 2100 UTC. It describes
  intermediate Public Advisories at three-hour intervals when coastal watches or warnings are in
  effect. Special advisories may arrive outside that cycle, so an ingest interval is a polling
  choice rather than a claim about issuance time.
- NHC's [product examples](https://www.nhc.noaa.gov/productexamples/) distinguish Public
  Advisories from TCV watch/warning products. A future parser should retain basin, storm name,
  advisory number, product type, issued time, official URL, and watch/warning text only when those
  fields are present in the actual product. Do not infer U.S. watch/warning coverage solely from a
  basin feed headline.
- Storm wallet numbers are reused. Summary items expose an ATCF ID; use it to correlate that
  storm's products only when there is an explicit, defensible association. Advisory item GUIDs
  are product/update identities, not permanent storm IDs. Retain GUID, basin and issue time when
  an advisory has no ATCF field; avoid treating a wallet number as permanent storm identity.

## Policy and source health

- Proposed candidate poll interval: 10 minutes during active ingest, still disabled by default.
  This is shorter than the normal advisory cycle to allow for intermediate/special products; it
  is a local policy choice, not an NHC guarantee. Confirm conditions and backoff before enabling.
- A valid feed with no active cyclone is a healthy empty result. Invalid XML is parser failure;
  authorization failure, rate limiting, and transport failure receive their existing source-health
  states. Never turn a missing active storm into a fabricated alert.
- Before live admission: add an exact URL allowlist entry, verify current response/policy and
  polling backoff, and run a no-page-load fetch regression. The observed feed had no structured U.S.
  watch/warning geography; do not infer it from a storm name or basin. Keep GIS files and homepage
  extraction outside the first text-feed adapter.

## Fixture implementation

The synthetic Eastern Pacific fixture now runs through the NATIONAL parser, alongside Atlantic
and Central Pacific empty-basin fixtures. Only the matching basin/source pair is accepted; the
feed must be a local file of at most 64 KiB and 50 entries, without DTD/entities. Admitted
product links stay within NHC's HTTPS `/text/` tree. The parser retains ATCF IDs, advisory number,
storm type, issue time, official product URL, and watch/warning terms while omitting the product
body. A storm type contributes bounded official severity, but basin location and unlocated
watch/warning terms do not establish U.S. or multi-state impact. Atlantic and Central Pacific
empty-sentinel fixtures yield healthy scans with no item. A live URL is rejected before HTTP.
An advisory URL/number revision still groups by the explicit ATCF ID, while a second storm
stays separate and same-family revisions do not count as independent corroboration.
Live signoff remains open, including a separate current response and policy review.
