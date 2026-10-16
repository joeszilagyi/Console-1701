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

This fixture does not add live event-detail or product downloads. The existing exact USGS feed remains the only live USGS news request. A live DYFI enrichment path requires a separate exact-request, version-selection, payload-cap, failure, cache, and rate design before signoff; it cannot fetch during page loads, host scans, or tests. The observed historical event is used to verify source fields and routing, not to claim a current 2026-10-15 emergency.
