# REGIONAL NIFC Current IMSR Fixture Verification

Observed 2026-10-15. This verifies an official response and its offline fixture shape; it does
not authorize live ingest.

- The [NIFC national incident map](https://www.nifc.gov/nicc/incident-information/national-incident-map)
  links NIFC Open Data's authoritative current IMSR incident layers. The linked
  [current IMSR incident locations view](https://data-nifc.opendata.arcgis.com/datasets/20c1f27e9db94bc2a2ae1b183e4620d6_0/explore)
  exposes an ArcGIS FeatureServer point layer.
- A bounded GET of that layer's `/query` endpoint returned HTTP 200, JSON, 5,573 bytes,
  two Washington features, and no transfer-limit flag. The query used
  `IsLatest='x' AND incident_id LIKE 'WA-%'`, eleven named output fields,
  `post_date_isoformat DESC`, `resultRecordCount=100`, and `returnGeometry=false`.
  The exact URL is the disabled `nifc_imsr_current_wa` registry URL. Both observed rows
  had report date `20261015`: `WA-OWF-260664` (Sisi, 4,615 acres) and
  `WA-OWF-260406` (Little Giant, 172,912 acres).
- The local fixture keeps the exact bounded response. The fixture-only parser requires the
  official query URL and ArcGIS response metadata, rejects an error or truncated result,
  caps input at 64 KiB and 100 rows, and validates each WA incident ID, unique fire identifier,
  latest marker, report day, acreage and Washington coordinate bounds. It stores only bounded
  incident metadata, not article text or map geometry. A local canonical incident key lets
  later IMSR report dates retain the same event identity.
- `IsLatest='x'` establishes presence in the current IMSR report view. It does not establish
  active burning, evacuation, smoke exposure or public impact. A blank `x100pct` is not an
  active-fire flag; `c` means 100 percent contained. Ranking adds only a bounded large-fire
  report-context factor, and adds none for a contained record. Neither a DNR active-incident
  claim nor Washington public impact is inferred from this federal report.
- Registry presence remains disabled by default. Direct HTTP is blocked even with the shared
  official-HTTP switch enabled. Live promotion still needs exact-URL allowlist review, source
  policy and cadence decisions, and a bounded response-size plan. The separate WA DNR
  active-incident endpoint gap remains open.
