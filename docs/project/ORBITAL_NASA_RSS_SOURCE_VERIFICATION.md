# ORBITAL NASA RSS Source Verification

Checked 2026-10-15 against NASA's [RSS feeds directory](https://www.nasa.gov/rss-feeds/) and its
linked [news releases RSS feed](https://www.nasa.gov/news-release/feed/). The directory is an
HTML index, so the disabled `nasa_rss_feeds` registry candidate now points to the exact feed
and retains the directory as its homepage reference.

The observed RSS 2.0 channel is titled `NASA`. Items have title, canonical `link`, GUID,
`pubDate`, optional categories, and a short description. A bounded read on 2026-10-15 found
station and crew stories mixed with Earth science, education, and general agency news. The
fixture preserves that mixture. The dedicated parser accepts only official NASA article links
with an ORBITAL path and title action, then stores URL, GUID, date, categories, source URL, and
bounded plain-text description. Routine or unrelated stories are skipped. It does not store
article bodies or treat NASA science news as operational ORBITAL events by default.

On 2026-10-15, read-only HEAD checks of the news-release feed and the five dedicated feeds
returned HTTP 200, `application/rss+xml`, `ETag`, and `Last-Modified`. The exact six URL/parser
pairs are now in the live allowlist, while registry/config defaults remain disabled. A live scan
requires the explicit news/ORBITAL/source/HTTP switches and `verification_status: verified`.
Articles older than seven days or more than one hour in the future are dropped before storage.
Mocked-transport tests exercise the six original feed parsers, exact URLs, channel/path filters,
disabled gates, and the old Kennedy-feed case. NASA news, station, blog, and JPL
family variants count as one NASA provenance family for independent-source corroboration, while
their original channel family remains in source evidence.

Five dedicated NASA feeds were also checked with HTTP 200 and RSS 2.0 parse on 2026-10-15:
the [Station mission feed](https://www.nasa.gov/missions/station/feed/),
[Artemis mission feed](https://www.nasa.gov/missions/artemis/feed/),
[Space Station blog feed](https://www.nasa.gov/blogs/spacestation/feed/),
[Artemis blog feed](https://www.nasa.gov/blogs/artemis/feed/), and
[Kennedy blog feed](https://www.nasa.gov/blogs/kennedy/feed/). Their channel titles and canonical
NASA article links were observed. The older `blogs.nasa.gov` pages redirect to `www.nasa.gov`.
The registry now points to the exact feeds and the parser applies each feed's channel and path
boundary. Kennedy's sample feed contained old material, which the seven-day live freshness gate
now drops.

JPL's [RSS directory](https://www.jpl.nasa.gov/rss/) links a news feed. That endpoint returned
HTTP 403 to the scanner's identifying user agent, so it is not allowlisted. NASA's
[NASA-hosted JPL feed](https://www.nasa.gov/centers-and-facilities/jpl/feed/) returned HTTP 200,
`application/rss+xml`, and a parseable `Jet Propulsion Laboratory – NASA` channel with ten
items in a bounded 278 KiB read on 2026-10-15. The channel mixed mission actions and science
features. `jpl_rss` now points to this exact NASA-hosted feed; its parser requires a NASA
article URL, mission or news-release path, and an action title. A checked-in fixture covers a
mission test and launch, and excludes science-only, student, and non-NASA links.

The exact JPL URL/parser pair is in the opt-in HTTP allowlist, disabled by default. An isolated
explicit `news-scan` with an empty temporary SQLite state returned HTTP 200, healthy source
state, and two ORBITAL items: a JPL lunar-lander test and NASA Roman telescope launch. The
scanner used its identifying default user agent; no browser-agent substitution was needed.
The `science.nasa.gov/feed/` candidate still does not provide a verified, accessible RSS path,
so RS-098 remains partial.
