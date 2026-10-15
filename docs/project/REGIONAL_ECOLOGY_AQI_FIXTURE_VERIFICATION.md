# REGIONAL WA Ecology AQI Fixture Verification

Observed 2026-10-15. This verifies a fixture shape, not live-ingest signoff.

- The official [Ecology hourly AQI ArcGIS layer](https://gis.ecology.wa.gov/serverext/rest/services/AQ/AirQualityMonitoringHourlyResults/MapServer/0)
  describes hourly telemetry and calculated AQI for Washington stations over
  the past 24 hours, updated hourly. It exposes `SiteId`, `SiteName`,
  `SiteLocation`, `DateTime_PST`, `HourPriorToLatest`, `AQIValue`,
  `AQICategory`, and pollutant-specific AQI/concentration fields.
- A bounded GET to `https://gis.ecology.wa.gov/serverext/rest/services/AQ/AirQualityMonitoringHourlyResults/MapServer/0/query?where=HourPriorToLatest%3D1+AND+SiteId+IN+%2842%2C46%2C76%29&outFields=%2A&returnGeometry=false&resultRecordCount=3&f=json`
  returned HTTP 200, JSON, 4,196 bytes, and three Seattle features. Site 46
  had AQI 53, Moderate, and PM2.5 AQI 53 at 2026-10-15T22:00:00Z. The
  query requested `outFields=*` because a narrower selected-field attempt
  returned an ArcGIS 400 error; the parser retains only an explicit field set.
- The response includes exact station street addresses in `SiteLocation`.
  The parser neither stores nor displays those addresses. It accepts only the
  observed SiteIds 42, 46 and 76 with matching names, the latest-hour marker,
  no more than three features, and a 64 KiB fixture cap. The sample time is
  converted from ArcGIS epoch milliseconds to UTC.
- [Ecology's AQI guidance](https://ecology.wa.gov/research-data/monitoring-assessment/air-quality-index)
  lists Good 0–50, Moderate 51–100, Unhealthy for Sensitive Groups 101–150,
  Unhealthy 151–200, Very Unhealthy 201–300 and Hazardous 301+. The parser
  checks category/value consistency and ranks only the source-provided AQI
  severity. Moderate receives no public-impact boost; no smoke source or health
  instruction is inferred from a station reading.
- Direct HTTP remains blocked by the app allowlist and the parser. Live
  promotion needs bounded transport, an interval and freshness policy for the
  hourly layer, source-health handling for unavailable stations, and separate
  signoff. AirNow requires an API key and is outside this fixture slice.
