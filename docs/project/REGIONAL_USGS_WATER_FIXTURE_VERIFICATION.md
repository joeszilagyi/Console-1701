# REGIONAL USGS Water Fixture Verification

Observed 2026-10-15. This is fixture-shape verification, not live-ingest signoff.

- Official source: [USGS Water Data APIs](https://api.waterdata.usgs.gov/) and
  [OGC API documentation](https://api.waterdata.usgs.gov/docs/ogcapi/).
- Exact observation query: `https://api.waterdata.usgs.gov/ogcapi/v1/collections/latest-continuous/items?f=json&monitoring_location_id=USGS-12119000&parameter_code=00060,00065&limit=5`.
  A bounded GET returned HTTP 200, JSON, 2,847 bytes, and two features.
- Exact station query: `https://api.waterdata.usgs.gov/ogcapi/v1/collections/monitoring-locations/items/USGS-12119000?f=json`.
  A bounded GET returned HTTP 200, JSON, 3,757 bytes, and one station feature.
- Gauge and geography: `USGS-12119000`, Cedar River at Renton, King County,
  Washington; HUC12 `171100120107`, narrowed to HUC8 `17110012`; point
  `[-122.20345473813, 47.4825999269035]`. The parser accepts only this
  verified gauge, HUC8, and matching observation/station point.
- Observed fields: `00060` streamflow `315 ft^3/s` and `00065` gage height
  `8.56 ft`, both at 2026-10-15T22:15:00Z, provisional. The sample contains
  `time`, `value`, `unit_of_measure`, `approval_status`, `qualifier`, and
  `last_modified` per time series. The fixture copies only the bounded fields
  needed for parsing; the station's free-text revision note is not stored.
- Semantics: the `latest-continuous` collection contains the latest observation
  per time series, which can lag the response timestamp. The parser records age
  against `timeStamp` and marks observations older than two hours stale. The
  two returned shapes provide no flood-stage threshold or flood category.
  A raw stage of 8.56 ft therefore yields `unknown_no_threshold` and zero
  flood-severity score. No public-impact inference is made from this reading.
- Runtime: the parser accepts only an explicit local fixture tied to the exact
  observation URL. It rejects direct HTTP parsing; `official_http` has no
  allowlist entry for this source. A future live adapter must fetch and validate
  both endpoints with bounded size, cadence, and station identity before enabling.
  The legacy [WaterServices retirement notice](https://waterdata.usgs.gov/blog/api-waterservices-decom/)
  is why this slice uses the modern OGC API.
