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

The source remains disabled and the exact feed is not live allowlisted. Before live admission,
check current feed size, conditional requests, cadence, title/path filter recall, and source
health under an explicit opt-in scan.

Five dedicated NASA feeds were also checked with HTTP 200 and RSS 2.0 parse on 2026-10-15:
the [Station mission feed](https://www.nasa.gov/missions/station/feed/),
[Artemis mission feed](https://www.nasa.gov/missions/artemis/feed/),
[Space Station blog feed](https://www.nasa.gov/blogs/spacestation/feed/),
[Artemis blog feed](https://www.nasa.gov/blogs/artemis/feed/), and
[Kennedy blog feed](https://www.nasa.gov/blogs/kennedy/feed/). Their channel titles and canonical
NASA article links were observed. The older `blogs.nasa.gov` pages redirect to `www.nasa.gov`.
The registry now points to the exact feeds and the parser applies each feed's channel and path
boundary. Kennedy's sample feed contained old material, so a future live admission needs a
content-date freshness gate.

JPL's [RSS directory](https://www.jpl.nasa.gov/rss/) links a news feed, but a direct bounded read
of that endpoint returned HTTP 403 in this environment. The `science.nasa.gov/feed/` candidate
did not return parseable RSS. Their registry candidates remain unparsed and disabled until an
exact, accessible feed can be verified. RS-098 therefore remains partial.
