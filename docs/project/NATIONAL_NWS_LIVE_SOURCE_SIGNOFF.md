# NATIONAL NWS Severe Alert Live Source Signoff

Verified 2026-10-15 for the NATIONAL first-pass opt-in source.

## Exact source and bounded observation

The [NWS Alerts Web Service](https://www.weather.gov/documentation/services-web-alerts)
documents the active-alert endpoint and recommends no more than one request every 30
seconds. The current official `https://api.weather.gov/openapi.json` schema lists `status`
and `severity` as form-style, comma-separated array query filters for `/alerts/active`.
The exact admitted URL is:

`https://api.weather.gov/alerts/active?status=actual&severity=Extreme,Severe`

A bounded direct GET returned HTTP 200 `application/geo+json`, an ETag, 756,698 bytes and
136 GeoJSON features. All 136 were `Actual` and `Severe` in this observation; there were no
`Extreme` features at that time. The unfiltered endpoint returned 714 features and about
3.19 MB, so the narrow filter materially reduces work and avoids ingesting routine alerts.
The result is a snapshot, not a guarantee that later severe-alert responses fit the default
1 MiB cap. Oversize responses fail the scan without partial ingestion.

## Admission and data contract

Only scope `NATIONAL`, key `nws_active_alerts_api`, kind `api_json`, parser
`nws_alerts_json`, verification `verified`, and the exact URL above can use the transport.
The source, NATIONAL scope, shared news gate and `allow_official_http` all require explicit
opt-in, followed by a `news-scan`; the registry and standing config remain disabled.
The source interval must be at least five minutes. Transport refuses redirects and
nonallowlisted URLs and uses bounded HTTPS, timeout, byte cap, conditional ETag and backoff.

The parser enforces `Actual` plus `Severe` or `Extreme` for this live source even if the
server filter misbehaves, and rejects more than 1,000 features. Existing fixture sources
can still exercise nonsevere NATIONAL alert metadata. Stored items retain NWS event ID,
status, severity, urgency, certainty, UGC-derived state/territory, timing, official URL,
bounded instruction and source-backed ranking. A UGC state identifies alert coverage; it
does not prove national or multi-state impact. No raw response or full product body is stored.
A zero-feature response is healthy and does not prove safety.

## Verification and limits

An isolated scan using temporary config and SQLite state returned `complete`, HTTP 200,
`healthy`, and 136 stored NATIONAL items. Every item had `Severe` and a UGC-derived state.
The temporary opt-in and state were removed; standing config and timer were not changed.
Offline tests cover exact source rejection, parent/HTTP/interval gates, parser failure on
out-of-contract rows and oversized feature lists, conditional ETag refresh, and NATIONAL
page/API GETs without fetch. A live HTTP 304 was not observed; it is tested with a mock.
This feed is weather alerts only. Other NATIONAL source admissions retain separate gates.
