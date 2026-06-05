# REGIONAL Source Registry And Config

This note captures the current REGIONAL source registry and config groundwork.

## Current state

- `console1701/news/regional_registry.py` seeds disabled REGIONAL metadata for the first
  Washington / PNW candidates.
- `console1701/config.py` now normalizes a top-level `regional` config tree with geography,
  social, and homepage-extraction flags.
- REGIONAL source metadata is validated before a source can be enabled.

## Regional config defaults

- `enabled: false`
- `label: Washington / PNW`
- `primary_region: Washington`
- `secondary_regions: [Puget Sound, Pacific Northwest, Cascadia]`
- `include_oregon_when_relevant: true`
- `include_bc_when_relevant: true`
- `include_transport_corridors: true`
- `include_wildfire_smoke: true`
- `include_seismic_volcano: true`
- `include_public_health: true`
- `include_state_government: true`
- `include_regional_news: true`
- `allow_social_sources: false`
- `allow_homepage_extractors: false`

## Remaining work

- Add REGIONAL event, ranking, and live-ingest plumbing.
- Expand the registry as more verified regional sources become available.
- Keep the regional scope disabled by default until explicit configuration exists.
