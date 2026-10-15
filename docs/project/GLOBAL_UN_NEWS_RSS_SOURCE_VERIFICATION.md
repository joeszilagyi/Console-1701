# GLOBAL UN News RSS verification

Checked 2026-10-15 for RS-073 against the UN News public RSS endpoint
`https://news.un.org/feed/subscribe/en/news/all/rss.xml`. The feed returned RSS 2.0 with a
channel title beginning `UN News`, 30 items in the bounded inspection, and item `title`, `link`,
`description`, `guid`, `pubDate`, and `source` fields. The inspected items had no categories;
category is optional. The exact official endpoint supersedes the unverified `en/rss.xml` URL in
the design seed. The general UN News website is a reference-only registry entry.

The feed link uses `/feed/view/en/story/...`; the GUID uses `/en/story/...`. The fixture parser
stores the GUID as the canonical official story URL and retains the feed link as evidence.
Descriptions are converted to bounded plain text, not retained as article bodies. Publication
time and source label are preserved. It applies narrow, explicit exclusions to roundup,
interview, podcast, photo-story, and routine-remarks formats, and to matching category labels
when present. No country, humanitarian impact, or diplomacy outcome is inferred from a title.

The RSS metadata is an institutional news signal, with ranking based on official source family
and configured priority; event impact needs separate source facts or corroboration. The feed
remains disabled for live HTTP ingestion. Any future opt-in scan needs an exact URL allowlist,
payload limit, timeout, retention, and a no-page-load fetch regression. Fixture tests use only
local files and verify the source-health state.
