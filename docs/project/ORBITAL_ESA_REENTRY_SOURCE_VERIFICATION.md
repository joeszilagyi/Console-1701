# ORBITAL ESA Reentry Source Verification

Checked 2026-10-15 against ESA's [Re-entry Prediction Front-end User Guide](https://reentry.esoc.esa.int/files/public/GEN-REN-MAN-00232-OPS-GR%20ESA%20Re-entry%20Prediction%20Front-end%20User%20Guide.pdf),
[ESA press explanation](https://www.esa.int/Newsroom/Press_Releases/Media_invitation_Satellite_reentries_explained),
and the [public background pages](https://reentry.esoc.esa.int/home/recovereddebris).
The guide states that actual predictions require a login. ESA's press page describes free
registration for the prediction area. The public area contains background, history, observations,
and recovered-debris context. Predictions are updated as new data arrive and have substantial
uncertainty; the user guide warns that hosted predictions can contain errors.

**Decision:** `esa_reentry` is an official, auth-required source and remains disabled. Its public
home page is reference context only. The registry now records `restricted_auth_required` and an
empty local credential slot, which produces `auth_required` source health with no attempted
access. There is no verified public machine-readable prediction endpoint, parser shape, rate
limit, or retention permission. No login automation, HTML scraping, map extraction, or live
allowlist entry is authorized by this verification.

If ESA later documents a permitted API or feed, verify the exact endpoint, account terms, rate
limit, publication and prediction timestamps, uncertainty fields, update/cancellation semantics,
object identity, and response size before a fixture parser. Any eventual display must keep the
uncertainty visible, avoid exact ground-track or tactical output, avoid unsupported local-risk
claims, and expire quickly. Public blog or recovered-debris pages must not be treated as current
prediction data.
