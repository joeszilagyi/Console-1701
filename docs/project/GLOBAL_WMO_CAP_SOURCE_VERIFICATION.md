# WMO Severe Weather CAP source verification

Verified 2026-10-15 for RS-069. This is source and parser planning, not CAP ingest. No WMO or
national-service URL is live-allowlisted in console-1701.

## Authority and source path

- [WMO Severe Weather Information Centre](https://severeweather.wmo.int/) (SWIC) displays
  warnings from National Meteorological and Hydrological Services (NMHSs) and specialized
  centres. WMO aggregates them; the issuing national agency remains the warning authority.
- The official [SWIC CAP source directory](https://severeweather.wmo.int/sources.html) loads
  `https://severeweather.wmo.int/json/sources.json`. Its entries name the issuing organization,
  language, RSS/Atom CAP feed URL, feed status, and WMO alerting-authority register link. The
  directory listed 155 entries at inspection; this count is a snapshot, not a coverage promise.
- [WMO's notes to users](https://severeweather.wmo.int/note.html) say the displayed information
  is based on warnings from NMHSs and specialized centres, and that reuse should attribute the
  issuing centre. They also warn that missing map warnings may reflect inaccessible or
  nonconforming CAP feeds. A blank map is not an all-clear.
- The [WMO Register of Alerting Authorities](https://alertingauthority.wmo.int/) provides a
  separate way to check the named issuer. A source entry and a live warning must be checked
  against the issuing authority before promotion.

## Exact feeds checked

| Issuer | Directory URL and observation | Disposition |
| --- | --- | --- |
| Australian Bureau of Meteorology | `https://severeweather.wmo.int/v2/cap-alerts/au-bom-en/rss.xml` returned RSS 2.0 with item links to WMO-hosted CAP XML on 2026-10-15. The directory links to the Bureau's WMO authority record. | Candidate for a future exact-feed fixture/parser review. Do not treat WMO as the issuer. |
| German Weather Service (DWD) | `https://www.dwd.de/DWD/warnungen/cap-feed/en/rss.xml` returned an official RSS channel with no items at inspection. | Availability/shape of active items still unverified. Keep disabled. |

A linked Australian warning was inspected as CAP 1.2 XML with the namespace
`urn:oasis:names:tc:emergency:cap:1.2`. It contained `identifier`, `sender`, `sent`, `status`,
`msgType`, `scope`, references, and an `info` block with language, event, urgency, severity,
certainty, effective/expiry times, sender name, headline, bounded description, and affected-area
text/geocodes. This is a parser-shape observation, not a decision to ingest or elevate every CAP
message. In the sample, `status=Actual`, `msgType=Update`, and `scope=Public`; cancellations and
tests must be handled separately before an adapter is enabled.

A bounded follow-up direct read on 2026-10-15 returned HTTP 200 for the exact Australian RSS URL,
287,988 bytes and 500 items. Its channel title and Atom self link identify the Bureau of
Meteorology feed. Each sampled item has a title, WMO-hosted CAP XML link, `AusBoM-` GUID and RSS
publication time. A linked 3,983-byte CAP document returned HTTP 200 and contained multiple
`info` blocks, including an area cancellation in an otherwise updated message. The checked-in
`global_wmo_bom.rss` fixture reduces three observed items. Its parser reads RSS metadata only,
marks CAP status/severity/expiry/area unverified, and keeps items at background attention. It
does not fetch or parse the linked CAP documents; direct WMO HTTP remains disabled in the app.

A follow-up bounded read of the exact linked CAP document returned HTTP 200 and 3,983 bytes.
Its `Actual`/`Update`/`Public` envelope contained two `info` blocks: a Moderate warning for one
New South Wales forecast district and a Minor cancellation for three other district codes. The
new fixture-only `wmo_bom_cap_xml` parser accepts a separately configured exact CAP URL; it does
not follow RSS links or add WMO to the live HTTP allowlist. The reduced fixture keeps the observed
envelope, fields and two-area-state structure, with paraphrased headlines and no narrative body.
It bounds XML and info/area counts, verifies the BoM sender and CAP namespace, preserves each
info block's severity, urgency, certainty, effective/expiry time and area descriptions, and
separates cancelled areas. A current `Actual`/`Public` Severe or Extreme info block contributes
alert/severity rank only when urgency and certainty are source-backed; Moderate/unknown, Test,
Cancel, and expired cases receive no alert boost; `Test` documents emit no item. No observed impact
or global reach is inferred.
The item expires at the earliest active-info expiry. The RSS GUID and CAP identifier may join as
one WMO-family event, without independent corroboration. This is fixture-only source validation,
not approval for linked-document or live-feed fetching.

## Local policy for future live promotion

The SWIC dashboard and source-directory registry entries are `source_health_probe_only` with a
24-hour review cadence. They are not CAP adapters and must not be scraped. A future CAP source
must be a separate, exact feed URL tied to its issuer, language, WMO register entry, source terms,
and explicit local configuration. A tentative 15-minute polling interval is appropriate only
after feed-specific rate and update behavior is checked; use a payload cap, timeout, backoff, and
conditional requests. Page loads and tests may never fetch it.

The fixture parser bounds item count and XML size, verifies the CAP namespace and issuer, and
retains metadata rather than full warning bodies. A future live adapter must preserve its
distinction between `Actual`/`Test`, `Alert`/`Update`/`Cancel`, public/restricted scope, expiry,
and source-provided urgency/severity/certainty. It should preserve area labels and codes without
claiming global impact from a local warning. Source health must expose disabled, never run, stale,
inaccessible,
parser failure, policy block, and successful states with the issuer and exact feed URL visible.
