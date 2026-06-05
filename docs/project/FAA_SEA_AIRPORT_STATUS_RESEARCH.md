# FAA / SEA Airport Status Research

This note captures the current verified status for SEA airport status research.

## Verified official surfaces

- FAA airport status page for SEA: `https://www.faa.gov/airport-status/SEA`
- FAA NAS Status home: `https://nasstatus.faa.gov/`
- FAA NAS Status user guide: `https://nasstatus.faa.gov/static/media/NASStatusUserGuide.cccc6d48.pdf`

## Research result

- The FAA airport status page is an official public status surface for SEA.
- The NAS Status user guide documents a machine-readable XML view for active airport and en route
  events.
- The LOCAL registry entry for `faa_airport_status_sea` is now marked `source_health_probe_only`
  with an access note that points at the airport-status page and NAS Status XML path.

## Remaining work

- Add a live adapter only after policy review, timeout handling, and the parser contract are
  finalized.
- Keep the source disabled by default until the live ingest path is intentionally enabled.
