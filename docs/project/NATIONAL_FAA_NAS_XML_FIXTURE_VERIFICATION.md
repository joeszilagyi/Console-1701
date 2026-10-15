# NATIONAL FAA NAS XML fixture verification

Reviewed 2026-10-15 for RS-044. Decision: **official XML shape verified and offline fixture
parser implemented; live ingest stays disabled**.

## Source shape

The FAA [NAS Status user guide](https://nasstatus.faa.gov/static/media/NASStatusUserGuide.cccc6d48.pdf)
documents active airport and en-route status. A bounded GET of the exact
[airport-status XML](https://nasstatus.faa.gov/api/airport-status-information) returned HTTP 200
`application/xml`, 2,179 bytes on 2026-10-15. It had root `AIRPORT_STATUS_INFORMATION`,
`Update_Time` (`Thu Oct 15 19:16:39 2026 GMT`), `Dtd_File`, and active `Delay_type` groups. The
observed groups included `Ground_Delay_List` with `ARPT`, `Reason`, `Avg`, and `Max`;
`Arrival_Departure_Delay_List` with `ARPT`, `Reason`, direction, `Min`, `Max`, and `Trend`; and
`Airport_Closure_List` with `ARPT`, `Reason`, `Start`, and `Reopen`. The guide describes ground
stops; the synthetic fixture includes a ground-stop group, but this bounded live response did not.
The observed response had no SEA event, which means only that SEA was absent from that active
snapshot. It does not prove SEA was on time.

The XML includes a `Dtd_File` value pointing to a legacy URL, but the parser never fetches that
URL and rejects actual DTD/entity declarations. The sampled response did not provide `ETag` or
`Last-Modified` headers. A future live adapter must account for full snapshots and retire airport
items missing from a subsequent successful HTTP 200 response. Invalid XML or an unsupported
active list must preserve the last good snapshot.

## Fixture and evidence contract

`faa_nas_status_xml` groups multiple active events for one airport into one item linked to the
official FAA airport-status page. It stores each event's type, reason, direction, bounded delay
fields, source start/reopen text, source update time, XML source URL, and a capped aviation ranking
factor. Closure start/reopen text lacks a year in the observed XML; the parser retains it as raw
source text with explicit precision instead of inventing a year. A closure notice may concern only
one runway or class of aircraft; the parser does not call the whole airport closed. The XML's
`ARPT` code alone does not prove U.S. country geography. A NATIONAL fixture source therefore
requires an explicit verified `airport_codes` allowlist; the synthetic fixture includes an
out-of-scope YUL row to verify filtering.

The fixture also covers SFO delay plus departure delay, SEA ground stop, and SAN closure notice.
Parser and offline `news-scan` tests verify grouping, bounded evidence, ranking, NATIONAL
FAA/aviation facets, and fixture-only provenance. A valid empty active-event snapshot returns
zero items. No article body or passenger data is stored.

## Live release gate

Keep `faa_nasstatus_api` disabled. Before an exact-URL opt-in `news-scan` adapter, confirm policy
and cadence, byte cap, all active event-list shapes, stop duration/expiry semantics, country and
airport coverage, closure scope, and last-good retention. The [LOCAL FAA/SEA research](FAA_SEA_AIRPORT_STATUS_RESEARCH.md)
proposed ten minutes as a conservative interval; it was not an FAA-published rate limit. Page
loads, host scans and tests remain offline.
