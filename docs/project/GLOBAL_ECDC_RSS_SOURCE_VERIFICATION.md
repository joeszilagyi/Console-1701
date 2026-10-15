# ECDC news RSS fixture contract

Verified on 2026-10-15 against the official [ECDC RSS index](https://www.ecdc.europa.eu/en/rss-feeds)
and its [News/press releases feed](https://www.ecdc.europa.eu/en/taxonomy/term/1307/feed).
This verification covers a fixture parser. The app has no live ECDC HTTP allowlist entry.

The observed feed is RSS 2.0 with a `channel` titled `News`. Items include `title`, official
article `link`, HTML-encoded `description`, `pubDate`, `dc:creator`, and `guid`. The sampled live
items did not have a `category`; the parser preserves one when provided and stores an empty list
otherwise. It requires an official HTTPS article URL and valid publication time. Descriptions
become bounded plain text; no article body, case count, risk level, or country is inferred.

The checked-in `tests/fixtures/news/global_ecdc_news.rss` is synthetic and mirrors that XML
shape. It includes one optional category to test the documented RSS field. The parser labels
items as official ECDC public-health **context** for Europe and GLOBAL. Those labels are not
assertions that an individual article has Europe-wide or global impact. ECDC's disabled registry
priority is 50, below the WHO DON priority of 100; single ECDC feed items receive no automatic
official-severity boost. Independent convergence or later structured severity evidence may
elevate an event.

An explicit `news-scan` against a local fixture is the only implemented ingest path. Live use
requires a separate exact-URL allowlist, operational policy review, and disabled-by-default
configuration in the official-source phase.
