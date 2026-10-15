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

## Local policy for the future parser

The SWIC dashboard and source-directory registry entries are `source_health_probe_only` with a
24-hour review cadence. They are not CAP adapters and must not be scraped. A future CAP source
must be a separate, exact feed URL tied to its issuer, language, WMO register entry, source terms,
and explicit local configuration. A tentative 15-minute polling interval is appropriate only
after feed-specific rate and update behavior is checked; use a payload cap, timeout, backoff, and
conditional requests. Page loads and tests may never fetch it.

The parser should first bound item count and XML size, verify the CAP namespace and issuer,
retain metadata rather than full warning bodies, and distinguish `Actual`/`Test`,
`Alert`/`Update`/`Cancel`, `Public`/restricted scope, expiry, and the source-provided
urgency/severity/certainty. It should preserve area labels and codes without claiming global
impact from a local warning. Source health must expose disabled, never run, stale, inaccessible,
parser failure, policy block, and successful states with the issuer and exact feed URL visible.
