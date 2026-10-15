# REGIONAL WA DNR Wildfire Endpoint Review

Reviewed 2026-10-15 for the REGIONAL fixture pack. No active-incident
machine-readable source was signed off.

- The official [Current Wildfire Incident Information page](https://dnr.wa.gov/wildfire-resources/current-wildfire-incident-information)
  and [Wildfire Portal](https://dnr.wa.gov/wildfire-resources/current-wildfire-incident-information/wildfire-portal)
  are human-facing references to notable fire updates and the dashboard.
  The portal includes older contained fires; it is not a machine-readable active
  fire feed. The dashboard HTML is not an ingest source.
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
- The `wa_dnr_current_wildfire` registry entry therefore remains a disabled
  reference source. Even if a user marks it enabled with a file or HTTP URL,
  the scanner records unsupported and does not read or fetch it. Resume only
  after identifying a DNR-endorsed current-incident feature service or a
  source-backed active-status field with bounded geography and lifecycle data.
