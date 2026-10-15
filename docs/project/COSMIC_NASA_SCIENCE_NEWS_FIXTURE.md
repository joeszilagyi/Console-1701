# NASA Science News COSMIC fixture

Checked 2026-10-15 against the official [NASA Science News blog](https://science.nasa.gov/blogs/science-news/)
and its [RSS feed](https://science.nasa.gov/blogs/science-news/feed/). A bounded direct GET of
the exact feed returned HTTP 200, `application/rss+xml`, 79,465 bytes, and ten items. Its root
still has the observed missing separator between the `apod` and `media` namespace declarations.
After fixing that one separator locally for inspection, the newest item was dated 2026-08-24.
The feed therefore does not establish current-event coverage.

The local COSMIC fixture preserves that observed channel and defect. It includes NASA-hosted
Pluto and quasar headlines with explicit planetary/astrophysics categories, an Earth-only item,
a mission-action item, and a nonofficial link. The parser requires the exact `SYSTEM_SOLAR` source
identity, official feed URL, `file://` input, `fixture_only: true`, a 128 KiB cap, the official
channel and article host/path, publication time, a recognized source category, and a
nonoperational title. The only XML repair is the single known separator; other malformed XML
fails. It stores bounded headline metadata and category evidence, omits descriptions and article
bodies, and records the repair and no-download decisions. The offline scanner runs with HTTP
trapped. Direct live configuration is rejected.

The source remains disabled by default. Before any live admission, NASA must serve parseable XML
or an official alternative feed, fresh articles, and a separately reviewed exact URL, cadence,
retention, and scope policy. Neither the COSMIC page nor tests fetch this feed.
