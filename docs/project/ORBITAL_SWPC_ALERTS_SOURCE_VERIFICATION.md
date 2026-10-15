# ORBITAL SWPC Alerts JSON Source Verification

Checked 2026-10-15 against NOAA SWPC's public [alerts JSON product](https://services.swpc.noaa.gov/products/alerts.json) and [product directory](https://services.swpc.noaa.gov/products/).

The observed JSON is an array. Each product has `product_id`, `issue_datetime`, and `message`.
The message is a NOAA text product with a message code, serial number, issue time, headline,
optional validity bounds, optional G/R/S scale, and source-provided potential-impact lines.
Observed samples included K-index warnings and alerts, geomagnetic watches and cancellations,
and an X-ray summary. The feed supplies no product-specific article URL; normalized items link
to the official feed with identity parameters and retain the exact feed URL separately.

The fixture contains a warning, a cancelled watch, and a malformed row. The parser skips
incomplete rows and stores bounded parsed facts, not the full message. `cancelled` is explicit so
later ranking cannot treat a cancelled watch as an active warning. A malformed top-level payload
reports parser failure. The local scan and facet tests make no HTTP request.

On 2026-10-15, a read-only HEAD request to the exact NOAA endpoint returned HTTP 200,
`application/json`, approximately 52 KB, `ETag`, and `Last-Modified`. NOAA's public product
directory listed the same endpoint with a current update time. The parser and response-size cap
cover the observed format and size. The source is now in the exact live allowlist, but the
registry/config defaults remain disabled. A live scan requires all of `orbital.enabled`,
`news.enabled`, `news.scopes.ORBITAL.enabled`, `news.fetch_policy.allow_official_http`, and this
individual source's `enabled` plus `verification_status: verified`. The URL, parser, kind, and
absence of auth must match the allowlist exactly. `console-1701 news-scan` is the only live entry
point; page loads and tests do not fetch.

Live alerts older than 72 hours or more than one hour in the future are dropped before storage.
An alert's ranking active-window bonus ends after its source-reported validity time or 72 hours
from issuance, whichever comes first. Fixture and mocked-transport tests cover opt-in gates,
conditional HTTP 304, freshness, stored provenance, and GET-only views. No live app scan was run
as part of this change.

Example local opt-in, subject to the normal configuration location:

```yaml
orbital:
  enabled: true
news:
  enabled: true
  fetch_policy:
    allow_official_http: true
  scopes:
    ORBITAL:
      enabled: true
      sources:
        - id: swpc_alerts_json
          enabled: true
          verification_status: verified
          url: https://services.swpc.noaa.gov/products/alerts.json
```
