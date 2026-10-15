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

The registry candidate remains disabled and the exact endpoint is not in the live HTTP
allowlist. Live admission still needs cadence, conditional request, freshness, period semantics,
and health verification under an explicit opt-in scan.
