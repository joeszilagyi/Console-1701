# COSMIC NASA Exoplanet Archive tiny TAP signoff

Verified 2026-10-15 for RS-143 against the archive's [TAP user
guide](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html),
[PS column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html),
and [acknowledgment guidance](https://exoplanetarchive.ipac.caltech.edu/docs/acknowledge.html).
The public synchronous service is `GET
https://exoplanetarchive.ipac.caltech.edu/TAP/sync` with JSON output. A
bounded seven-column, ten-row direct read returned HTTP 200,
`application/json`, and 1,803 bytes. An isolated explicit `news-scan` with
temporary config/state returned HTTP 200, parsed ten rows, and stored eight
distinct COSMIC items. The temporary opt-in and SQLite state were removed.

The app constructs the entire query. It selects only `pl_name`, `hostname`,
`discoverymethod`, `disc_year`, `rowupdate`, `soltype`, and `default_flag` from
`ps`, with `TOP 10`, `default_flag=1`, a UTC seven-calendar-day window on
`rowupdate`, and newest-first ordering. User-supplied live query contracts are
rejected. The exact base URL, source id, parser, kind, official URL, verification
status, query contract, and absence of auth are allowlisted. The response cap
is 64 KiB; transport also imposes a 30-second maximum timeout, no redirects
or inherited proxy, validators, and backoff. The minimum refresh interval is
24 hours. The parser rejects extra columns, rows above ten, dates outside the
window, and malformed metadata.

The source remains disabled in standing config. Live access requires explicit
`news.enabled`, `solar_system_beyond.enabled`, COSMIC scope/source enabled,
`news.fetch_policy.allow_official_http: true`, and a `news-scan` command. No
page load, host scan, or pytest fetches the service. Only bounded parameter
metadata and source provenance are stored. No full catalog, observation,
image, spectrum, or linked product is requested. `rowupdate` means an archive
parameter update; it is not a discovery date or a claim of a newly confirmed
planet. The item and event evidence keeps this distinction, and its default
retention is seven days. A successful zero-row response remains healthy.

The archive's acknowledgment page addresses publications. The UI attributes
each item to the NASA Exoplanet Archive and links its official system overview;
any publication or redistribution of these data must follow the archive's
published acknowledgment guidance. Additional TAP tables or queries require a
new source-specific signoff.
