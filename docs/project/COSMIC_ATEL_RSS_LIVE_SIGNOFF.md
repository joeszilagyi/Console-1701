# ATel RSS live source signoff

Checked 2026-10-15 for RS-131, RS-122, and RS-144.

## Endpoint and policy

- The publisher's [Feeds page](https://www.astronomerstelegram.org/?listxml) links the exact
  all-telegrams `https://www.astronomerstelegram.org/?rss` URL. It returns RSS 1.0 `text/xml`,
  not RSS 2.0. The observed snapshot contained ten items and 12,359 bytes, with no redirect.
- The site's `robots.txt` returned HTTP 200 and `User-Agent: * / Allow: /`. Its
  [editorial policy](https://www.astronomerstelegram.org/?inform=) says reports are posted
  instantly without editorial filtering and describes citation and redistribution terms.
  The feed is public and requires no account for reading. This app stores a short metadata
  summary and official source link, without author email, credential provenance, or full body.
- The observed RSS item includes an ATel number in title and `identifier`, an exact `?read=N`
  link, `dc:date`, creator, and description. The parser checks number agreement and retains
  explicit object tokens from the title. It does not infer confirmation or scientific meaning.

## Admission bounds

- Exact tuple: COSMIC / `astronomers_telegram_rss` / the URL above / `rss` / `atel_rss`.
- Disabled registry default and explicit `news.enabled`, COSMIC scope/source enablement, and
  `news.fetch_policy.allow_official_http` are required. Page and host scans do not fetch.
- 64 KiB response and parser caps, 20-item parser cap, minimum 30-minute interval, existing
  rate/error backoff, 14-day live freshness filter, and default seven-day item retention apply.
- The transport accepts only the observed `text/xml` media type for this tuple, uses an
  identifying user agent, and forbids redirects and environment proxies.
- A zero-item valid feed is healthy. A malformed/HTML/oversized response records a failed
  source run; no item is fabricated. ATel items remain labeled preliminary and unreviewed.

## Verification

- Fixture parser and offline scan tests cover exact identity, XML errors, DTD rejection,
  size bound, bounded metadata, no HTTP, and no full body storage.
- Mocked live tests cover exact tuple, opt-in, response cap, transport media type, and stored
  live evidence. Full pytest passed (645 tests); Ruff passed.
- An isolated explicit live `news-scan` returned HTTP 200, healthy source state, ten stored
  COSMIC items, and 12,359 response bytes. The temporary state directory was discarded.

The ATel feed is a preliminary research communication source. A telegram is not independent
confirmation of its own scientific claim; later official releases or other source families
must provide corroboration for higher-confidence events.
