# ORBITAL JPL CNEOS Fireball Source Verification

Checked 2026-10-15 against NASA/JPL's [Fireball Data API documentation](https://ssd-api.jpl.nasa.gov/doc/fireball.html), [CNEOS fireball page](https://cneos.jpl.nasa.gov/fireballs/), and [SSD API fair-use policy](https://ssd-api.jpl.nasa.gov/doc/index.php).

The documented `fireball.api` response has a `signature.version` (1.2), `fields`, and field-array
`data` rows. Peak-brightness `date`, radiated `energy` (units of 10^10 joules), and estimated
`impact-e` (kilotons) are guaranteed. Location direction, altitude, and entry velocity components
may be absent. The API calls `impact-e` an *estimated impact energy*; it does not establish
ground impact or damage. The fixture includes a located event with velocity components, a
low-energy event, and an unlocated event.

The first-pass parser requires version 1.2, bounds row count, keeps UTC peak-brightness time,
retains source units, derives a velocity magnitude only when all three source components exist,
and records location only when all direction fields are present. It defaults to at least 0.1 kt
estimated impact energy and at most 30 days of age, both configurable under `orbital:`. Small or
stale events do not enter attention. The local fixture scan makes no HTTP request.

The documented response has no stable row ID. The parser now links to a valid, exact JPL query
using UTC peak-brightness time plus both reported energy values, so same-second records with
different values remain distinct in SQLite. If two retained rows still have the same available
query identity, parsing fails visibly rather than silently overwriting one. ORBITAL correlation
uses time and reported coordinates when location is present; unlocated rows require time plus
both energy values. A time-only match is insufficient. Two same-second events with different
location or energy remain separate in direct parser and offline stored-cluster tests. An energy
revision at the same reported time and location can join as one JPL-family event, without an
independent-corroboration claim. This is a conservative derived identity, not an official event ID.

The registry source remains disabled and the API is not live allowlisted. Before live admission,
select a bounded date/energy/limit query, verify response size, update cadence and source delay,
and keep the no-damage-inference wording in the evidence and UI.
