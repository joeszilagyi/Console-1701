# SYSTEM Solar System and Beyond Source Verification Workflow

Reference design:

- `docs/project/SYSTEM_SOLAR_SYSTEM_BEYOND_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md`

Use this checklist before any Solar System and Beyond source is enabled beyond disabled metadata.

## Checklist

1. Confirm endpoint ownership.
1. Confirm the access method is lawful and machine-readable.
1. Confirm source terms, robots notes, and policy-sensitive constraints.
1. Confirm the parser shape and the exact fields that will be stored.
1. Confirm auth or key requirements, if any.
1. Confirm rate limits and refresh expectations.
1. Confirm retention sensitivity and how quickly stored rows should expire.
1. Confirm privacy risk and whether exact locations, article bodies, or other sensitive fields are
   prohibited.
1. Confirm object, mission, science, and scope filters for planets, moons, small bodies,
   exoplanets, missions, observatories, alerts, archives, and broad sky-science sources.
1. Confirm the verification status that should be recorded in the registry.
1. Confirm the source-health behavior for the source before live ingest is enabled.

## Required Registry Fields

Record these fields before enabling any Solar System and Beyond ingest:

- `source_key`
- `source_family`
- `source_class`
- `adapter`
- `scope`
- `official_status`
- `expected_access_kind`
- `verification_status`
- `policy_risk`
- `parser_risk`
- `privacy_risk`
- `retention_sensitivity`
- `future_phase`

## Source Health States

Keep the status honest:

- `disabled`
- `not_configured`
- `configured_never_run`
- `healthy`
- `stale`
- `failing`
- `parser_failed`
- `policy_blocked`
- `robots_blocked`
- `auth_required`
- `rate_limited`
- `unsupported`
- `manual_review_only`

## Notes

- Keep Solar System and Beyond sources disabled by default until the checklist is complete.
- Prefer fixture-backed validation before any live ingest.
- Do not add page-load fetching while a source is still under verification.

## Per-source signoff record

Use one record per exact URL and query, including a bounded query against an archive. `unknown`
means the field has not been verified; unknown access, policy or schema blocks live admission.

| Field | Record |
| --- | --- |
| Source identity | Registry key, family/class, official status, scope and distinct-publisher rule |
| Exact access | Owner documentation, HTTPS URL, method, format, query bounds, auth/key and redirects |
| Observed shape | Date, status, content type, byte/row count, validators, channel/schema/version, fixture |
| Terms and load | Terms, robots, attribution, published rate limit, retry/backoff and refresh interval |
| Stored metadata | Title/URL, source time, object/mission/transient ID, status, bounded description, no article body or science product |
| Scope filter | Why the record belongs to planetary, exoplanet, telescope, transient, or mission science rather than ORBITAL or GLOBAL |
| Safety and value | Hype/alien-life/UFO suppression, preliminary/retraction handling, archive-firehose cap, public-value evidence |
| Retention and health | Expiry, source stale/failing/rate/auth/policy states, response cap and purge evidence |
| Decision | `reference_only`, `fixture_only`, or `live_opt_in`; blocker, reviewer and check date |

Before `live_opt_in`, require a settled internal scope and UI label, an exact allowlisted URL/query,
source and parent opt-ins, `verification_status: verified`, bounded time/row/byte limits, a
fixture parser, mocked transport/gate tests, and no GET or host-scan fetch. Archives must return
tiny metadata rows only; image, paper, sky-map and data-product downloads remain outside this
Recent Signal layer. A successful ORBITAL feed parser does not automatically route all of its
items into science.

## Endpoint walkthroughs

| Candidate | Observed evidence and current decision |
| --- | --- |
| [NASA Science News blog](https://science.nasa.gov/blogs/science-news/) | The exact `/feed/` URL returned `application/rss+xml` on 2026-10-15, but a bounded read failed strict XML parsing because the root namespace attributes were malformed. `reference_only` until the publisher fixes the feed or an official alternative is verified; do not silently repair live XML. |
| [JPL RSS directory](https://www.jpl.nasa.gov/rss/) | JPL lists `/feeds/news/`, but a direct bounded request returned HTTP 403 on 2026-10-15. `reference_only`; no bypass or copied third-party feed. [NASA's JPL center feed](https://www.nasa.gov/centers-and-facilities/jpl/feed/) returned parseable RSS but mixes Earth and mission science, so it needs a separate scope-specific fixture/parser and is not a substitute approval. |
| [ESA RSS directory](https://www.esa.int/Services/RSS_Feeds) | Top News and Human Spaceflight exact feeds are parseable for ORBITAL, as recorded in [ESA source verification](ORBITAL_ESA_RSS_SOURCE_VERIFICATION.md). `fixture_only` for science until a separate science/mission filter is tested; routine images and broad agency news cannot become science events by default. |
| [NASA Science Photojournal feeds](https://science.nasa.gov/photojournal/rss-feeds/) | The official directory lists topic-specific image feeds. `reference_only` for Recent Signal; an image release is not automatically a major science finding and image files must not be downloaded. |

The signoff status is endpoint-specific. Record parser failure and HTTP 403 as source-health
evidence, then move to an independent candidate while access remains unresolved. Any future
exoplanet, MAST, PDS, HEASARC, GCN, TNS or literature source needs its own record with row caps,
terms, and domain-specific relevance tests.

The NASA-hosted JPL center feed now has a fixture-only science parser and a disabled registry
candidate. A 2026-10-15 bounded read returned HTTP 200, `application/rss+xml`, a parseable
`Jet Propulsion Laboratory – NASA` channel, and ten mixed-topic entries. The parser keeps
science-category headlines and rejects Earth-only and operational launch/testing headlines; it
does not authorize live science ingest or the inaccessible direct JPL feed.
