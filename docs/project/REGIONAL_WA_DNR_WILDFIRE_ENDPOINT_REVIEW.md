# REGIONAL WA DNR Wildfire Endpoint Review

Reviewed 2026-10-15 for the REGIONAL fixture pack. No active-incident
machine-readable source was signed off.

- The official [Current Wildfire Incident Information page](https://dnr.wa.gov/wildfire-resources/current-wildfire-incident-information)
  and [Wildfire Portal](https://dnr.wa.gov/wildfire-resources/current-wildfire-incident-information/wildfire-portal)
  are human-facing references to notable fire updates and the dashboard.
  The portal includes older contained fires; it is not a machine-readable active
  fire feed. The dashboard HTML is not an ingest source.
- The official `fireinfo.dnr.wa.gov` link redirects to DNR's public ArcGIS
  [Wildfire Intel Dashboard](https://experience.arcgis.com/experience/6cdda73cf6154949a1fae76ccb2900a0).
  A bounded read of its public item configuration on 2026-10-15 referenced the DNR
  fire-statistics layers and three Survey123 stakeholder report services (overview,
  aviation, and region intel). It did not identify a separate current-incident
  feature layer with a positive active-state field; this is source research, not
  permission to scrape dashboard HTML or ingest those report services.
- WA DNR publishes an official [Current DNR Fire Statistics ArcGIS REST layer](https://gis.dnr.wa.gov/site3/rest/services/Public_Wildfire/WADNR_PUBLIC_WD_WildFire_Data/MapServer/1).
  Its fields include incident and fire-event IDs, name, county, acres, discovery,
  control and out dates, coordinates and class. It supports JSON/GeoJSON queries.
- A bounded GET on 2026-10-15 with `DSCVR_DT >= DATE '2026-10-01'`,
  `returnCountOnly=true`, and `f=json` returned HTTP 200 and count 24. A second
  GET selected thirteen fields, `returnGeometry=false`, three records ordered
  by discovery date, and returned HTTP 200, 2,463 bytes. Those three included
  a controlled fire and an out fire, both under the layer named “Current”.
- The sampled fields have no explicit active state or authoritative update
  timestamp. An empty control/out date is not proof of active status. The layer
  is useful for fire statistics, but cannot truthfully drive a current-incident
  alert parser or active-fire ranking from the observed shape.
- A follow-up bounded query on 2026-10-15 selected fires of at least 100 acres
  discovered since 2026-09-01 and returned four records. Three had no control
  or out date; the fourth had both. None supplied a positive active-status field
  or update time. Filtering by acreage and discovery date does not resolve the
  lifecycle ambiguity.
- The `wa_dnr_current_wildfire` registry entry therefore remains a disabled
  reference source. Even if a user marks it enabled with a file or HTTP URL,
  the scanner records unsupported and does not read or fetch it. Resume only
  after identifying a DNR-endorsed current-incident feature service or a
  source-backed active-status field with bounded geography and lifecycle data.

## Separate fire-statistics fixture

A follow-up bounded query on 2026-10-15 selected eleven fields, discovery dates
since 2026-09-01, at least 100 reported acres, and at most ten rows. The exact
official ArcGIS query returned HTTP 200, 2,585 bytes, and four records. Three
had no control or out date; Sutherland had both dates. The records supplied
fire-event and incident IDs, names, county labels, acreage, discovery dates,
class codes, and starting jurisdiction. Name searches for the existing Sisi
and Little Giant NIFC/NWCC fixture incidents returned no DNR matches; bounded
NIFC/NWCC name checks for the DNR examples also returned none. There is no
observed independent-family incident pair to claim.
A bounded follow-up of the parser's `FIREEVENT_ID=89929` record link returned
HTTP 200, 1,307 bytes and exactly that one event, so item URLs are official
record queries rather than fabricated deep links.

The separate `wa_dnr_fire_statistics` registry source and parser were first validated
against the four-row September sample and require an exact query contract. They preserve day-precision
discovery and reported control/out dates, official identity and county, and
explicitly mark active status, evacuation, and public impact unverified. The
source is disabled, fixture-only and not live allowlisted; a live opt-in is
policy-blocked. This does not change the `wa_dnr_current_wildfire` decision
above or establish a current-incident feed.

Expanded evidence on 2026-10-15: an exact DNR layer query for fires discovered
since 2026-07-01 with at least 1,000 reported acres returned 31 rows in 10,810
bytes, under a 40-row request cap. The saved large-fire response remains under
the parser's 16 KiB limit; the earlier four-row smaller-fire fixture is also
retained under its separate exact query contract. The larger response includes Sisi,
Little Giant, and Sinlahekin with the same fire names and discovery days as the
separately observed NWCC large-fire source start dates. An offline two-parser
scan now joins those three incident identities across the `wa_dnr` and
`wildfire_federal` families; a changed start date prevents a join. The NWCC edit
date and DNR discovery date need not be within 48 hours for that exact
source-backed identity match. Neither the DNR layer nor this correlation proves
that any fire is active now or that people are affected.
