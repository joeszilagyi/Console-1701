# REGIONAL NWCC Large-Fire Public View Fixture Verification

Observed 2026-10-15. This verifies an offline fixture and incident-identity contract. It does
not authorize live ingest or claim that a listed fire is actively burning now.

- The [NWCC fire map](https://gacc.nifc.gov/nwcc/firemap.php) describes the Northwest large-fire
  map as a daily source with possible reporting gaps. The [public ArcGIS item](https://www.arcgis.com/home/item.html?id=d2408259cd05480f876acc7a51840ff4)
  is owned by `nwcc.gis_nifc` in NIFC's ArcGIS organization. Its description says the point view
  follows the NWCC daily briefing, may lag during heavy fire activity, and local managing units
  have the most current information. The item also disclaims navigation, legal-boundary and
  access-restriction use.
- A bounded GET of the public view's FeatureServer layer 0 returned HTTP 200, JSON, 30,153 bytes,
  four features, and no transfer-limit flag. The query used `UNIT_ID LIKE 'WA%'`, nine named
  output fields, `EditDate DESC`, `resultRecordCount=100`, and `returnGeometry=false`. The exact
  URL is the disabled `nwcc_large_fire_wa` registry URL. Sisi (`WAOWF`, `260664`) and Little Giant
  (`WAOWF`, `260406`) had 2026-10-15 edit times and the same acreage as NIFC's current IMSR
  records. Sinlahekin and Luna had older 2026-10-07 and 2026-10-04 edit times respectively.
- The fixture-only parser requires the exact query URL and ArcGIS response metadata, caps input
  at 64 KiB and 100 rows, and rejects error/truncated responses. It validates WA managing unit,
  fire number, start date, edit time, acres, containment percentage, GlobalID and official
  InciWeb link. It retains bounded metadata and a local canonical key, with no article text,
  status prose, contact information, map geometry, or private location fields.
- WA in `UNIT_ID` identifies a managing unit, not a verified fire point or affected jurisdiction.
  `EditDate` is a source-record edit time, not a promise of current incident activity. The view
  exposes percent contained but no explicit active-status field in this bounded query. No active
  fire, evacuation or public-impact claim is made from it. Older records remain visibly dated
  and receive the shared recency treatment.
- Start year, unit and fire number normalize to the same fire key as NIFC's unique identifier
  for Sisi and Little Giant. The offline two-source scan stores each pair as one incident cluster.
  Both views are interagency/NIFC data and share one `wildfire_federal` family, so these pairs
  do not count as independent corroboration.
- Direct HTTP remains blocked even with the shared official-HTTP switch enabled. A live release
  needs exact URL, cadence, response-size, source policy and freshness review, including how
  old records in a daily layer should be shown or filtered. The separate WA DNR active-incident
  field gap remains open.
