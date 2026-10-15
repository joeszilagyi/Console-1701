# ORBITAL SWPC NOAA Scales JSON Source Verification

Checked 2026-10-15 against NOAA SWPC's public [NOAA scales JSON product](https://services.swpc.noaa.gov/products/noaa-scales.json), [product directory](https://services.swpc.noaa.gov/products/), and [NOAA scale explanation](https://www.swpc.noaa.gov/node/1085).

The observed JSON is keyed by `-1`, `0`, `1`, `2`, and `3`. Each period has `DateStamp` and
`TimeStamp`, plus `G`, `R`, and `S` objects with `Scale` and `Text`; R and S may carry probability
fields. Period `0` is treated as current and `1` through `3` as forecast in the first-pass
parser. This period interpretation follows the product layout and NOAA's current/forecast
presentation; it should be confirmed again before live admission.

The parser stores only nonzero explicit G/R/S scale entries. It preserves source text and
probability fields without turning them into inferred public impacts. Current and forecast
entries have distinct identity and safety flags. A missing current period fails clearly;
incomplete period or category entries skip. The local fixture scan makes no HTTP request.

On 2026-10-15, a read-only HEAD request to the exact NOAA endpoint returned HTTP 200,
`application/json`, about 1.1 KB, `ETag`, and `Last-Modified`. A same-day JSON read showed period
`0` stamped at the current update time and periods `1` through `3` at current/future forecast
dates. This supports the parser's current-versus-forecast distinction, though it remains a
layout-derived interpretation rather than a separate product-schema guarantee.

The exact endpoint is now in the live HTTP allowlist. Its registry default remains disabled and
unverified for local configuration. An opt-in live scan requires `orbital.enabled`,
`news.enabled`, `news.scopes.ORBITAL.enabled`, `news.fetch_policy.allow_official_http`, and this
source's `enabled` and `verification_status: verified`, with exact URL/parser/kind and no auth.
The scanner retains current scale rows only when their source timestamp is within six hours and
forecast rows within one hour past through 96 hours ahead. Zero and null scales remain omitted.
Mocked-transport tests cover exact admission, 200/304 handling, period provenance, and freshness;
no live app scan was run.
