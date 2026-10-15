# GLOBAL UN Press RSS source verification

Checked 2026-10-15 for RS-074. The exact official
[UN Press RSS feed](https://press.un.org/en/rss.xml) returned HTTP 200
`application/rss+xml`, 7,104 bytes, ten items, `ETag`, and `Last-Modified` in a bounded read.
Its channel title was `UN Meetings Coverage and Press Releases`. Sampled items supplied title,
link, description, `pubDate`, Dublin Core creator and GUID. Links/GUIDs used official
`https://press.un.org/en/...` pages. The sampled first items included a Secretary-General
message, Security Council meeting coverage, and a routine commission session announcement.
These are press-office metadata, not a structured record of decisions or crisis severity.

`un_press_rss` is an offline GLOBAL fixture parser for this channel. It requires configured
`active_crisis_terms` and retains only a Security Council, General Assembly, humanitarian or
peacekeeping title that also has a configured crisis term or a narrow action term. Routine
messages, remarks, meeting announcements and schedules are suppressed. The parser stores a
bounded plain-text description, publication time, official URL/GUID, feed creator, matched
terms, and United Nations institution identity. Organ labels inferred from titles are marked
`title_only_unverified`; no resolution outcome is inferred. A synthetic fixture includes two
retained items and two low-value items, and an offline scan test verifies persistence without
HTTP access.

Keep the registry RSS candidate disabled. Before live admission, verify feed cadence,
conditional response behavior, item corrections, organ/category data, robots/terms, retention
and whether title filters miss important events. The press-release page and linked documents
are not fetched by page load, host scan, fixture test or this parser.
