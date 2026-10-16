# ORBITAL ESA RSS Source Verification

Checked 2026-10-15 against ESA's [RSS feed directory](https://www.esa.int/Services/RSS_Feeds),
[Top News feed](https://www.esa.int/rssfeed/Our_Activities/Space_News), and
[Human Spaceflight feed](https://www.esa.int/rssfeed/Our_Activities/Human_Spaceflight).
Both exact HTTPS feeds returned HTTP 200 with parseable RSS. Their observed channel titles were
`ESA Top News` and `ESA Human and Robotic Exploration`.

Items have title, official `esa.int` article link, opaque GUID, `pubDate` with a timezone, and
HTML description. The observed Top News feed mixed crew return, images, videos, and Earth
content; the Human Spaceflight feed also carried routine facts pages. The fixture pack mirrors
these shapes. The dedicated parser keeps official article metadata, bounded plain-text
description, source URL, time, and explicit ISS/Artemis mission labels when present in title or
path. It filters routine media and unrelated titles. Reentry and debris headlines are held out
of this parser pending their own source and policy review; no safety classification is inferred
from a generic ESA RSS item.

For ORBITAL correlation, an ESA article is typed as `iss_update` only when its own title
or official article path identifies ISS; the Human Spaceflight feed name alone does not
establish that identity. NASA station articles and these ESA ISS articles share that event
type and a normalized `ISS` mission label. The parsers also retain a narrow action from
each article title (for example, docking or launch). Cross-agency title/context matching
requires the same nonempty action, a 96-hour publication window, shared title tokens,
and independent NASA/ESA families. Generic station updates without an action stay
separate. A parser-backed two-feed offline scan verifies a docking match and a
same-mission launch mismatch; it does not imply that the two fixture headlines were
observed together in live feeds.

Both registry candidates remain disabled by default. The two exact feeds are now in the live
HTTP allowlist, subject to an explicit source opt-in, `verification_status: verified`, and the
parent `allow_official_http` gate. Live items must be published within seven days (with one hour
of future clock tolerance). The shared official HTTP transport handles validators and response
bounds. Mocked scans cover article filtering, provenance, stale items, and closed gates; no
application live scan was run.
