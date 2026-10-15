# King County Emergency News RSS Review

Reviewed 2026-10-15. Decision: **verified official fixture source; live HTTP remains disabled**.

## Ownership and endpoint

[King County Emergency Management's ALERT page](https://kingcounty.gov/en/dept/executive-services/health-safety/safety-injury-prevention/emergency-preparedness/alert-king-county)
links to King County Emergency News. The blog's [About page](https://kcemergency.com/about/)
states that King County Emergency Management maintains it and activates it for widespread
disasters or other significant events. This confirms the blog's official relationship while
distinguishing it from the separate Everbridge registration service. The exact feed is
`https://kcemergency.com/feed/`.

A bounded read on 2026-10-15 returned HTTP 200, `application/rss+xml`, RSS channel title
`King County Emergency News`, and an item with title, official HTTPS link/GUID, RFC 822 `pubDate`,
category, and description. `robots.txt` disallowed `/wp-admin/` but had no feed disallow rule.
No published feed rate limit was identified; a 30-minute interval is a conservative proposal, not
a publisher guarantee. The feed's first item was an ALERT King County semiannual **test**, which
must not be presented as an active emergency.

## Parser, storage, and ranking

`king_county_emergency_rss` requires the official RSS channel and `kcemergency.com` HTTPS item
links. It stores bounded title, link, publication time, categories, a plain-text description of at
most 500 characters, and source/fixture evidence. It does not read or store article bodies. The
publisher jurisdiction is recorded as King County; that alone does not prove the impact is
countywide. Deterministic title/category rules classify `emergency_alert`, `recovery`, `test`, or
`county_notice`. Tests and drills get no emergency public-impact score; recovery receives a small
score; an explicit warning/evacuation/shelter alert receives the higher county-emergency score.
No inference from a generic `Other` category creates an alert.

The synthetic fixture `tests/fixtures/news/regional_king_county_emergency.rss` includes a warning,
a recovery post, and the observed style of a semiannual system test. It is **not** a downloaded
feed snapshot. Offline parser and configured-scan tests verify identity, body exclusion, bounded
description, category classification, ranking, and zero network requests.

## Release gate

The REGIONAL registry points to the exact feed and remains disabled. Live ingest would require a
separate exact-URL allowlist and controlled `news-scan` opt-in, plus response/failure and retention
tests. The existing seven-day item, fourteen-day fetch-run, and thirty-day health retention
defaults apply. A zero-item feed or stale publication time must be represented honestly; this
source is activated mainly during significant events, so routine silence is not proof of safety.
