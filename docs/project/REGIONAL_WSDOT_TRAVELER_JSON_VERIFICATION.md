# REGIONAL WSDOT Traveler Highway Alerts JSON Review

Reviewed 2026-10-15. Decision: **documented fixture parser; no live JSON ingest**.

## Ownership and access

WSDOT's [Traveler Information API](https://www.wsdot.wa.gov/traffic/api/) lists Highway Alerts
REST and states that an access code must be assigned for service use. The official
[GetAlertsAsJson operation](https://www.wsdot.wa.gov/traffic/api/HighwayAlerts/HighwayAlertsREST.svc/help/operations/GetAlertsAsJson)
describes a GET returning current alerts in JSON; its URL requires `AccessCode`. No code was
requested, stored, or used in this review. The operation documentation shows an HTTP example URL,
so HTTPS behavior, authentication response, actual media type, rate limits, and live data are not
verified. Keep `wsdot_traveler_api` disabled and outside the exact live HTTP allowlist. The
[separate public Highway Alerts RSS](WSDOT_REGIONAL_HIGHWAY_ALERTS_RSS_VERIFICATION.md) is the
current live-capable WSDOT source.

## Documented parser shape

WSDOT's [Alert class](https://www.wsdot.wa.gov/traffic/api/Documentation/class_alert.html) and
[RoadwayLocation class](https://wsdot.wa.gov/Traffic/api/Documentation/class_roadway_location.html)
document `AlertID`, county, region, category, status, headline/extended descriptions, priority,
start/end/update times, and start/end roadway location with road, direction, description, and
milepost. The REST example uses Microsoft's `/Date(milliseconds-offset)/` JSON time form. The
fixture `tests/fixtures/news/regional_wsdot_traveler_alerts.json` follows that documented shape;
it is synthetic and is **not** an observed API response.

The parser stores bounded text, numeric alert identity, official county/region, route and facility
tokens, status/category, UTC times, roadway direction/milepost, and transport ranking evidence.
Closed alerts get zero public-impact score. It does not store raw response bodies, access codes,
or precise roadway coordinates. The documented JSON record supplies no per-alert URL. For item
identity and audit linkage, the parser constructs the official RSS `refnum` link using `AlertID`
and marks `source_url_basis=official_rss_refnum_link`; that legacy link may redirect to WSDOT's
general alert page, as recorded in the RSS review.

## Filter, retention, and release gate

REGIONAL fixture scanning accepts statewide rows; route, county, facility, pass, and border
evidence support later ranking and relevance rules. Items use the shared default seven-day
retention, with fourteen-day fetch-run and thirty-day source-health history. A production JSON
adapter would first need a legitimate access code, exact HTTPS endpoint and response verification,
documented credential handling and interval policy, fixture/live error tests, and an explicit
allowlist decision. No page load, host scan, or test may request the service.
