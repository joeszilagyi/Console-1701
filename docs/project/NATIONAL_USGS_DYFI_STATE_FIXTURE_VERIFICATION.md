# NATIONAL USGS DYFI state fixture verification

Checked 2026-10-15 against the official [USGS event page](https://earthquake.usgs.gov/earthquakes/eventpage/nc75382936/dyfi/zip) for the M5.6 earthquake near Redwood Valley, California, and its [FDSN event detail](https://earthquake.usgs.gov/fdsnws/event/1/query?eventid=nc75382936&format=geojson). The detail returned HTTP 200, 115,477 bytes and listed a preferred DYFI product for event `nc75382936` from source `us`. The product included an exact `cdi_zip.xml` URL and its recorded size of 84,498 bytes. A bounded GET to that [official product](https://earthquake.usgs.gov/product/dyfi/nc75382936/us/1790984474973/cdi_zip.xml) returned HTTP 200, `application/xml`, and 84,498 bytes. The product version timestamp in its URL is 2026-10-02 23:41:14 UTC.

The ZIP intensity XML has `cdidata/cdi[@type="zip"]/location` rows with a ZIP location name, `state`, community decimal intensity (`cdi`), and response count (`nresp`). The observed product has 374 distinct ZIP rows. Summing responses by state gives:

| State | ZIP rows | Responses | Highest CDI | First-pass routing |
| --- | ---: | ---: | ---: | --- |
| California | 359 | 1,704 | 6.3745 | Reported felt state |
| Nevada | 10 | 11 | 2.2372 | Reported felt state |
| Oregon | 5 | 6 | 2.0 | Below ten-response threshold |

The fixture at `tests/fixtures/news/national_usgs_redwood_dyfi.json` combines one reduced observed USGS summary feature with the observed DYFI XML and its exact official product URL. It is admitted only through a local NATIONAL fixture. The parser caps the XML at 128 KiB and 1,000 ZIP rows, rejects DTD/entity declarations, validates a product URL tied to the USGS event ID, and checks distinct five-digit ZIP aggregates, state codes, response counts, and CDI bounds. It drops ZIP identifiers, city labels, coordinates, and raw XML before SQLite persistence. It stores only per-state totals, the official product link/version, and the threshold decision.

For first-pass routing, a state counts as a reported felt state only with at least ten DYFI responses and maximum CDI at least 2.0. Two qualifying U.S. states set `multi_state_impact` with an explicit **self-reported shaking** basis. This is not a claim of damage, casualties, disruption, or a measured shaking footprint. A single low-count state cannot create the multi-state label. The ordinary USGS summary `felt` count still has no state distribution by itself.

At the fixture stage, no live event-detail or product downloads were added. The observed
historical event verifies source fields and routing; it is not a current emergency.

## Bounded live opt-in proposed for owner review

The follow-up branch adds `dyfi_state_enrichment: true` only for the exact, verified, live
NATIONAL USGS summary source, with `interval_minutes: 60` or longer. It remains off by default.
The [USGS GeoJSON detail format](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson_detail.php)
documents a summary-provided detail link and product metadata. The
[ComCat product preference rule](https://earthquake.usgs.gov/data/catalog/products.php)
selects the largest preferred weight, breaking ties by latest update. A bounded 2026-10-16 UTC
read of the current summary feed returned 43 features with exact per-event detail URLs. A bounded
GET of the historical event's feed-detail URL returned HTTP 200, `application/json`, 115,477 bytes,
the same event ID, and two DYFI product versions; the preferred `us` version identified the
observed 84,498-byte XML product. A second bounded product GET returned HTTP 200 and
`application/xml`.

Only a parser-eligible U.S./territory event with magnitude at least 5, summary `felt` count at
least 20, and an exact summary detail URL is considered. The scan first selects an event without
an unchanged cached DYFI summary, breaking ties by the most summary felt responses, and makes at
most one detail GET (256 KiB, eight seconds) and one preferred
`us` ZIP-product GET (128 KiB, eight seconds). The detail ID and event URL must match the feed;
the product URL, source, version, type, and declared byte length must agree before download.
Requests use HTTPS, no redirects, and no environment proxy. Other products and arbitrary links
are never followed. The XML parser applies the existing 1,000-ZIP, DTD/entity, state and CDI
limits, retaining only state totals, product URL/version, and the self-reported shaking basis.

The source interval and base-feed HTTP 304 prevent most repeat lookups. On a subsequent 200, a
detail response naming the same exact product URL reuses the validated state summary already in
SQLite, without downloading the XML again. Other feed events retain their cached state totals
only while the summary `updated` timestamp is unchanged; a changed update clears stale totals
until that event receives a new detail check. Missing/unsupported products or failures leave the
summary-feed item with its existing unknown felt-state distribution; the run records the reason.
HTTP 429 pauses DYFI enrichment for two hours while base-feed scans continue. GeoServe and DYFI
can be enabled together and retain distinct epicenter and felt-state evidence. No page load,
host scan, fixture test, or pytest performs a network request. This new outbound path awaits
owner review before merge.

After review, an operator who has already enabled the parent NATIONAL and official-HTTP gates
can opt in on the exact source entry:

```yaml
news:
  scopes:
    NATIONAL:
      sources:
        - id: usgs_eq_geojson
          enabled: true
          interval_minutes: 60
          dyfi_state_enrichment: true
```
