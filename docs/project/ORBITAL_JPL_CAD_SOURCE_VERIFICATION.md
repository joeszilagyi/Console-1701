# ORBITAL JPL CNEOS Close Approach Source Verification

Checked 2026-10-15 against NASA/JPL's [SBDB Close-Approach Data API documentation](https://ssd-api.jpl.nasa.gov/doc/cad.html), [CNEOS close-approach table](https://cneos.jpl.nasa.gov/ca/), and [SSD API fair-use policy](https://ssd-api.jpl.nasa.gov/doc/index.php).

The documented `cad.api` response has a `signature.version` (1.5), a `fields` array, and `data`
rows ordered by those field names. The API defaults to Earth NEO approaches under 0.05 au over
the next 60 days. Fields include designation, orbit ID, close-approach calendar time in TDB,
nominal and uncertainty-bound distances in au, relative velocity in km/s, and optional H and
known diameter. The fixture follows this field-array shape and includes close, distant,
small-diameter, and unknown-diameter cases.

The first-pass parser requires version 1.5 and bounds the row count. It preserves TDB explicitly;
it does not relabel an approach time as UTC. It derives lunar-distance display from the official
au distance, keeps the nominal and uncertainty bounds separate, and never describes a close
approach as an impact prediction. By default, it retains objects within five lunar distances,
requires known diameter of at least 0.05 km beyond one lunar distance, and permits an unknown
diameter only within one lunar distance. Those thresholds are configurable under `orbital:`.

The registry source is disabled and the API is not live allowlisted. Before live admission,
choose an exact bounded query URL with `date-min`, `date-max`, `dist-max`, `diameter=true`, and
`fullname=true`, check rate limits and signature behavior, and verify freshness and public risk
wording in an explicit opt-in scan.
