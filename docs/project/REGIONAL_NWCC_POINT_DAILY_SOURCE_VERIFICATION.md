# NWCC Daily Fire Point Fixture Verification

Observed 2026-10-15 (Pacific time). This is an offline evidence contract, not live admission.

The official [NWCC operational layer](https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/NWCC_Operational_Layers_view/FeatureServer/11)
identifies layer 11 as `NWCC_Point_Daily`. A separate [NWCC ArcGIS service description](https://services3.arcgis.com/T4QMspbfLg3qTGWY/ArcGIS/rest/services/PSA_ORWA_popups/FeatureServer)
describes this point layer as current active fires tracked by NWCC and updated daily or when status
changes. The layer's `editingInfo.dataLastEditDate` was `1791380896887`, or
2026-10-07 13:48:16.887 UTC. That eight-day lag prevents an active-now assertion on the
2026-10-15 collection day, even when a record's `STATUS` is `Active`.

The exact disabled registry query requests 10 points, selected fields, WGS84 geometry, and
`START_DATE DESC` from the layer's `/query` endpoint. The bounded count query returned six
records. The selected query returned those six: Sisi, Sinlahekin, Little Giant, and Luna with WA
management units, and Austin and Grasshopper with OR units. All six carried `Active` in `STATUS`.
The observed response and separate layer edit timestamp are paired in
`tests/fixtures/news/regional_nwcc_point_daily_wa.json`. The two Oregon records remain in the
fixture as filter evidence and do not become REGIONAL items.

The parser requires the exact official query, fixture URI, layer provenance, bounded response,
WA unit plus point bounds, stable unit/fire number and official IDs, valid InciWeb links, and a
source edit time after fire start. It stores `status_at_source_snapshot`,
`source_data_last_edit_at`, acres, point, and fire identity. It sets `active_now_verified`,
`evacuation_claimed`, and `public_impact_inferred` to false. Four matched NWCC large-fire records
share normalized unit/fire number/start-year identity and the same `wildfire_federal` family;
their overlap does not create independent corroboration.

Live access remains blocked. Before enabling it, verify update cadence and row-level freshness,
bound a query that can handle growth beyond ten rows without silent truncation, review exact
allowlist/policy, and define how stale source labels render. This layer does not supply a WA DNR
active-incident record or confirmed local public impact.
