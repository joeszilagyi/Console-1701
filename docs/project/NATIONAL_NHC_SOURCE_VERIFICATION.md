# NATIONAL NHC advisory feed verification

Checked 2026-10-15 against NHC's official public documentation. This is source planning only;
no NHC URL is enabled or added to the live HTTP allowlist.

## Ownership and candidate feeds

- NHC/CPHC [lists basin-wide RSS feeds](https://www.nhc.noaa.gov/aboutrss.shtml) for the
  [Atlantic](https://www.nhc.noaa.gov/index-at.xml),
  [Eastern Pacific](https://www.nhc.noaa.gov/index-ep.xml), and
  [Central Pacific](https://www.nhc.noaa.gov/index-cp.xml). The page also lists per-storm wallet
  and per-product feeds. These are the candidate basin feed URLs; the NHC homepage and data archive
  are discovery/reference pages, not interchangeable feed endpoints.
- The official page calls these RSS 2.0 and describes basin-wide versus storm-specific feeds.
  Parser planning should use an RSS item identity, publication time, title, and official link,
  then inspect a captured official XML example before assuming optional item fields. The web
  research tool did not expose the live XML body, so exact item field names beyond RSS basics
  remain unverified here.
- NHC's [GIS RSS documentation](https://www.nhc.noaa.gov/gis/rss.php) documents separate GIS
  feeds with `guid`, `pubDate`, storm wallet, and ATCF identifiers. Those are a different product
  family; its optional `nhc:Cyclone` fields must not be assumed in the basin text RSS parser.

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
- Storm wallet numbers are reused. Use an explicit storm identifier such as ATCF ID, when an
  official item/product supplies it; otherwise retain the source item GUID plus basin and issue
  time, and avoid treating a wallet number as permanent storm identity.

## Policy and source health

- Proposed candidate poll interval: 10 minutes during active ingest, still disabled by default.
  This is shorter than the normal advisory cycle to allow for intermediate/special products; it
  is a local policy choice, not an NHC guarantee. Confirm conditions and backoff before enabling.
- A valid feed with no active cyclone is a healthy empty result. Invalid XML is parser failure;
  authorization failure, rate limiting, and transport failure receive their existing source-health
  states. Never turn a missing active storm into a fabricated alert.
- Before live admission: capture a bounded official feed response as a local fixture, verify item
  shape and identity across an update, add an exact URL allowlist entry, and run a no-page-load
  fetch regression. Keep GIS files and homepage extraction outside the first text-feed adapter.
