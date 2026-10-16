# GLOBAL IAEA RSS source verification

Checked 2026-10-15 for RS-075. The official [IAEA RSS directory](https://www.iaea.org/feeds)
links to [Top News](https://www.iaea.org/feeds/topnews) and
[Media Advisories](https://www.iaea.org/feeds/pressalerts). Bounded reads returned HTTP 200
`application/rss+xml; charset=utf-8`. Top News was 10,619 bytes with 15 items, `ETag` and
`Last-Modified`; Media Advisories was 69,429 bytes with 15 items. Only Top News is used by this
fixture parser. Its channel title is `IAEA Top News`; sampled items provided title, description,
`http://www.iaea.org/...` link, numeric GUID, and a `YY-MM-DD HH:MM` `pubDate` with no timezone.
No category appeared in the sampled Top News items. The feed included a Ukraine situation update,
training and science articles, a safety review, and Fukushima monitoring stories. Those examples
show why a broad nuclear-keyword rule would make ordinary IAEA work look urgent.

`iaea_rss` is an offline GLOBAL fixture parser. It validates the official article host/path,
canonicalizes HTTP links to HTTPS, keeps categories if supplied, and stores only bounded plain-text
description. It accepts a narrow nuclear or radiological emergency phrase in the title, or a
Director General situation update with a configured active-crisis term. Routine training, science,
meeting and institutional titles are excluded. The raw feed time is retained as evidence, while
`source_published_at` uses the calendar day at UTC midnight solely for day-level recency. The
original timezone and exact instant are unknown. Title matching does not establish severity,
facility condition, geographic impact, or public action guidance. A synthetic fixture covers
retained and filtered items, and an offline scan test verifies persistence without HTTP access.
GLOBAL event ranking now assigns only an eight-point nuclear-safety context factor to an urgent
title retained from this exact official source. The routine situation update gets no such factor.
The factor is neither severity nor public-impact evidence, and it does not set active-alert state.
Stored-cluster and direct tests verify those limits; nonofficial IAEA-like metadata gets no factor.

Keep the registry feed candidate disabled. Before live admission, verify feed cadence, conditional
responses, corrections, timezone semantics, HTTPS article redirects, robots/terms, retention, and
whether title filters miss safety events. Linked articles are not fetched by page load, host scan,
fixture test or this parser.
