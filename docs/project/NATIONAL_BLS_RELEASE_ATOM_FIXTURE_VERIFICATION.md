# NATIONAL BLS Release Atom Fixture Verification

Verified 2026-10-15 for the first-pass NATIONAL fixture pack.

BLS lists separate Employment Situation and Consumer Price Index news-release feeds at
<https://www.bls.gov/feed/>. Their exact URLs are
`https://www.bls.gov/feed/empsit.rss` and `https://www.bls.gov/feed/cpi.rss`.
Despite the `.rss` suffix and `application/rss+xml` response type, bounded GETs returned
Atom 1.0 XML. Both returned HTTP 200 and 12 entries in this check, about 8.5 KiB each.
The channels identify themselves as `bls.gov:feed:empsit` / `Employment Situation` and
`bls.gov:feed:cpi` / `Consumer Price Index`. Entries contain a title, BLS archive link,
series/date/time ID, `published`, `updated`, `News Release` category, and `content`.
The current first entries parsed as `empsit-2026_10_02__07_51_08` and
`cpi-2026_10_14__07_50_31`. The timestamp includes an offset in the source feed.

The `bls_release_atom` parser is restricted to two exact NATIONAL source keys and feed
URLs. It checks channel identity, official archive URL shape, release ID, category,
publication/update timestamps, duplicate IDs, a 256 KiB payload cap, and a 30-entry cap.
It rejects DTD/entity declarations. It stores release title, URL, times, series and
entry identity. It does not store `content` or article body, ingest series data, or infer
an economic shock from headline wording. Configured title terms determine whether a
release appears in NATIONAL attention; the feed series itself is an explicit source
allowlist. Both registry entries are disabled by default. Live BLS fetch remains outside
the app's exact official HTTP allowlist; this verification supports fixture ingest only.

The synthetic fixtures match the observed field names and namespaces and include body
text that tests prove is discarded. Offline scans verify both series, economic title
allowlists, stored identity and no HTTP. Further live admission needs a separate
source-specific fetch review, cadence and stale-feed behavior, and explicit user opt-in.
