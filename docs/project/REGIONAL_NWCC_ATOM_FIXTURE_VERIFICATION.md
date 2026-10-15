# REGIONAL NWCC Atom Fixture Verification

Observed 2026-10-15. This is fixture-shape verification, not live-ingest signoff.

- The [NWCC About Us page](https://nwccinfo.blogspot.com/p/who-we-are.html)
  says the Northwest Interagency Coordination Center posts official fire
  information with public information officers from federal, state and local
  agencies. It links the public Atom feed at
  `https://nwccinfo.blogspot.com/feeds/posts/default`.
- A bounded GET of that exact URL returned HTTP 200, `application/atom+xml`,
  43,548 bytes and 25 entries. Observed entries had Blogger post IDs, titles,
  `published`/`updated` timestamps, an `alternate` article link, and content.
  The curated fixture copies four observed entries with ID/title/time/link only;
  it does not include or store content, images, iframes or attachments.
- The parser accepts only the exact local fixture tied to the linked Atom URL.
  It validates Blogger identity and official blog article links, caps response
  size at 64 KiB and entries at 50, and retains named fire updates. It excludes
  general fire-year notices, lightning maps and other routine posts. A final
  update is labeled as final. Neither a PNW title nor a Blogger post proves
  Washington impact, acreage, active fire status or severity.
- The source stays disabled for direct HTTP. A live promotion needs an exact
  allowlist/signoff, cadence and source terms review, plus a response-size
  policy for any larger seasonal feed. No page or article scraping is used.
