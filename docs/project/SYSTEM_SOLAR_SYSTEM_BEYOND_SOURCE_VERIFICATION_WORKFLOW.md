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
| [NASA Science News blog](https://science.nasa.gov/blogs/science-news/) | The exact `/feed/` URL returned `application/rss+xml` on 2026-10-15, but a bounded read failed strict XML parsing because the root namespace attributes were malformed. A local-only fixture parser repairs the exact single separator and keeps selected space-science headlines; live access remains `reference_only` until the publisher fixes the feed or an official alternative is verified. Do not silently repair live XML. |
| [JPL RSS directory](https://www.jpl.nasa.gov/rss/) | JPL lists `/feeds/news/`, but the identifying scanner agent received HTTP 403 on 2026-10-15. `reference_only` for that endpoint. [NASA's JPL center feed](https://www.nasa.gov/centers-and-facilities/jpl/feed/) has a separate exact COSMIC science parser and [live signoff](COSMIC_JPL_RSS_LIVE_SIGNOFF.md). |
| [ESA RSS directory](https://www.esa.int/Services/RSS_Feeds) | Top News and Human Spaceflight exact feeds are parseable for ORBITAL, as recorded in [ESA source verification](ORBITAL_ESA_RSS_SOURCE_VERIFICATION.md). The dedicated Space Science feed is verified separately for one opt-in COSMIC live path; routine images and broad agency news cannot become science events by default. |
| [NASA Science Photojournal feeds](https://science.nasa.gov/photojournal/rss-feeds/) | The official directory lists topic-specific image feeds. `reference_only` for Recent Signal; an image release is not automatically a major science finding and image files must not be downloaded. |
| [ATel Feeds page](https://www.astronomerstelegram.org/?listxml) | The exact `?rss` all-telegrams RSS 1.0 feed has a bounded metadata parser and [live signoff](COSMIC_ATEL_RSS_LIVE_SIGNOFF.md). Reports remain preliminary because the publisher does not edit them. |

The signoff status is endpoint-specific. Record parser failure and HTTP 403 as source-health
evidence, then move to an independent candidate while access remains unresolved. Any future
exoplanet, MAST, PDS, HEASARC, GCN, TNS or literature source needs its own record with row caps,
terms, and domain-specific relevance tests.

The NASA-hosted JPL center feed has an exact disabled-by-default COSMIC live opt-in. A
2026-10-15 isolated live scan returned HTTP 200 and two science items. Its parser keeps
science-category headlines and rejects Earth-only and operational launch/testing headlines;
the inaccessible JPL-hosted feed remains a separate blocked endpoint.

ESA's [official RSS directory](https://www.esa.int/Services/RSS_Feeds) links a dedicated
[Space Science feed](https://www.esa.int/rssfeed/Our_Activities/Space_Science). A bounded
2026-10-15 read returned HTTP 200, `application/rss+xml`, the `ESA Space Science` channel, and
15 mixed science, launch, and multimedia entries. Its fixture parser keeps only Space Science
article paths and excludes launch and image-only links. On 2026-10-15, a second bounded direct
read of the exact URL
returned HTTP 200, `application/rss+xml; charset=utf-8`, 40,550 bytes, a parseable
`ESA Space Science` channel, 15 items, and no redirect. The fixture parser and mocked transport
tests now verify exact identity, scope filtering, 14-day freshness, a one-hour minimum scan
interval, 1 MiB response cap, seven-day metadata retention, no page-load fetch, and no product
download. Decision: `live_opt_in` for this exact ESA feed only; all flags remain off by default.

ESA/Hubble and ESA/Webb publisher news pages link FeedBurner RSS. Bounded reads on
2026-10-15 returned parseable `ESAHubble News` and `ESAWebb News` channels, each with ten
entries; science releases carry `heic`/`weic` IDs, official story URLs, and dates, while
photo releases are interleaved. The ESA/Webb page also advertises a direct `webb.org` RSS
URL that returned 404; its `esawebb.org/rss/feed.xml` variant redirected to Hubble's feed.
The fixture parser uses the publisher-linked channels and official story hosts, but both
FeedBurner endpoints remain live-policy blocked pending third-party hosting review.

The [NASA Exoplanet Archive TAP guide](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html)
documents the current `ps` table and JSON output; its
[column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html)
separate `rowupdate` from discovery year and status. A two-row, date-bounded TAP read on
2026-10-15 returned HTTP 200 JSON with the seven fixture columns. The fixture parser blocks
broader table/column/window/row shapes. A `rowupdate` is a parameter update, not proof that
the planet was discovered on that date. The [exact tiny TAP live
signoff](COSMIC_EXOPLANET_TAP_LIVE_SIGNOFF.md) now admits only an app-built,
seven-day, ten-row, seven-column `ps` metadata query as an explicit opt-in.
The broad TAP source and other archive queries remain disabled.

The [MAST API guide](https://mast.stsci.edu/api/v0/) documents `invoke` and request envelopes;
the [services guide](https://mast.stsci.edu/api/v0/_services.html) documents
`Mast.Caom.Filtered` versus `Mast.Caom.Products`, and the
[JSON format](https://mast.stsci.edu/api/v0/md_result_formats.html) includes paging. A
one-day JWST/TRAPPIST-1 observation query returned HTTP 200 and three matching rows with six
selected metadata columns. The fixture parser requires a complete bounded page, stores the
observation start as such, and rejects product fields. Live MAST remains disabled pending
source-use and heavy-archive signoff; it must never call product/download services by default.

PDS's [official Search API guide](https://nasa-pds.github.io/pds-api/guides/search/endpoints.html)
documents exact product-identifier resolution and warns that its federation may return 404
for unpopulated data sets. A bounded lookup of one known collection LID on 2026-10-15 returned
HTTP 200 JSON after redirect to another NASA PDS host. The fixture parser keeps collection
identity, mission, target, version, and registry harvest time only; it neither traverses
`/members` nor treats the harvest timestamp as a release date. Live access remains blocked
pending exact URL/redirect, source-use, and heavy-archive signoff.

GCN's [unified notice guide](https://gcn.nasa.gov/docs/notices/schema) and official
[Alert](https://gcn.nasa.gov/docs/schema/v7.1.0/gcn/notices/core/Alert.schema.json),
[Event](https://gcn.nasa.gov/docs/schema/v7.1.0/gcn/notices/core/Event.schema.json),
and [Localization](https://gcn.nasa.gov/docs/schema/v7.1.0/gcn/notices/core/Localization.schema.json)
definitions support a local metadata fixture parser. It preserves source-provided alert type,
event/trigger ID, times, mission/instrument and coordinates while dropping sky-map content.
The [notice transport guide](https://gcn.nasa.gov/docs/notices) lists Kafka/email subscription
paths, so this parser is fixture-only and has no live transport or verified notice permalink.
