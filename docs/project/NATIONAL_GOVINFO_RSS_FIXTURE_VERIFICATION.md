# NATIONAL GovInfo RSS fixture verification

Reviewed 2026-10-15 for RS-048. Decision: **selected collection RSS shapes verified and an
offline filtered fixture parser implemented; live feeds remain disabled**.

## Official feed discovery and shape

GovInfo's [feeds directory](https://www.govinfo.gov/feeds) lists collection RSS feeds and says
they generally contain the 100 most recent published documents. It also offers custom
search-based feeds, whose update behavior differs from the standard collection feeds. The exact
official [Federal Register](https://www.govinfo.gov/rss/fr.xml),
[enrolled bills](https://www.govinfo.gov/rss/bills-enr.xml), and
[public/private laws](https://www.govinfo.gov/rss/plaw.xml) RSS URLs returned HTTP 200
`text/xml` in bounded reads on 2026-10-15. They contained respectively 99, 100, and 100 items;
the sampled responses did not expose `ETag` or `Last-Modified`. Standard item fields were `guid`,
`title`, `pubDate`, `category`, `link`, and an HTML-formatted `description` listing content files.
Item links pointed to `https://www.govinfo.gov/app/details/{guid}`. The descriptions were file
lists, not policy summaries or full publication bodies.

The sampled Federal Register feed's first item was a 2025 issue with a 2026 RSS `pubDate`.
An RSS publication time therefore must not be called the document's legal effective date or even
assumed to equal its original issue date. The parser records its meaning explicitly. A GovInfo
enrolled-bill listing signals the availability of that bill's publication, not that it became law.
Legal effect, contents and applicability require separate document review.

## Offline parser and filters

`govinfo_collection_rss` accepts only the verified `BILLS`, `PLAW`, and `FR` collection
channels and requires configured title `impact_terms`. It validates GUID prefix, official
details URL, publication time and duplicate identity, strips HTML from bounded description
metadata, and records collection, document ID, stage and matched terms. A capped NATIONAL
publication ranking factor and GPO/publication facets support the item drawer. The synthetic
enrolled-bills fixture includes one matching and one routine bill; an offline `news-scan` test
verifies that only the matching item persists. No bill or law text is stored.

## Live release gate

Keep `govinfo_feeds` disabled. Before an exact-URL opt-in scan, verify one chosen collection's
policy, feed cadence, 100-item rollover risk, stale-item handling, retention, redirects,
conditional behavior, and whether title-only impact terms are sufficient for the intended use.
Do not enable every collection or follow content-file links to download PDFs. Page loads, host
scans and tests remain offline.
