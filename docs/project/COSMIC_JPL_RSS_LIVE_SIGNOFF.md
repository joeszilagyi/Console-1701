# COSMIC NASA-hosted JPL RSS live signoff

Checked 2026-10-15 against NASA's [JPL center RSS feed](https://www.nasa.gov/centers-and-facilities/jpl/feed/).
This is the exact endpoint already used by the fixture parser. With the scanner's identifying
user agent, a bounded read returned HTTP 200, `application/rss+xml`, a parseable RSS 2.0 channel
named `Jet Propulsion Laboratory – NASA`, and ten items in about 278 KiB. The feed mixes mission
operations, planetary science, astrophysics, and Earth stories; it is not a dedicated science
signal feed.

The `nasa_jpl_science_feed` COSMIC source is disabled by default. Live use requires the science
parent flag, news and COSMIC scope flags, an enabled exact source, `fixture_only: false`, the
matching official URL and parser, and the explicit official-HTTP switch on a `news-scan` command.
The transport rejects changed URLs, parsers, auth, redirects, unexpected content type, and
responses above 1 MiB. Config requires at least a 60-minute cadence. Live science items must
carry source publication times within 14 days and are retained at most seven days.

The parser requires a science category supplied by the RSS item and excludes operational titles,
non-NASA links, malformed XML, and oversized payloads. It stores bounded headline metadata,
categories, source and mission-path evidence, and explicit no-body/no-product markers. An
isolated explicit `news-scan` using a temporary SQLite state returned HTTP 200 and healthy source
state, storing two COSMIC items: a SPHEREx brown-dwarf release and a Curiosity Mars image story.
The older far-infrared telescope item and current ORBITAL launch item were not stored. Mocked
tests cover the exact allowlist, HTTP opt-in, freshness, source identity, and offline fixture
behavior; the full suite passes.

The separately hosted JPL feed returns HTTP 403 to the identifying scanner agent and has no app
allowlist entry. No page load performs a fetch.
