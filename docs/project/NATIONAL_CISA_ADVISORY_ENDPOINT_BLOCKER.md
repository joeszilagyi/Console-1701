# CISA advisory machine-readable endpoint verification

Checked 2026-10-15 for RS-045. CISA's official
[Cybersecurity Alerts & Advisories page](https://www.cisa.gov/news-events/cybersecurity-advisories)
describes advisory categories, including alerts, cybersecurity advisories, ICS advisories and
analysis reports. A bounded direct request to the candidate
`https://www.cisa.gov/news-events/cybersecurity-advisories?feed=rss` returned HTTP 403. The
guessed `.xml` sibling returned HTTP 404. Neither establishes a usable machine-readable feed
contract. Search-engine views of advisory pages are insufficient to define an ingest schema.

This initial blocker was resolved on 2026-10-15 by an exact CISA-hosted feed:
`https://www.cisa.gov/cybersecurity-advisories/all.xml`. A bounded direct GET with the
scanner's identifying user agent returned HTTP 200, `application/rss+xml`, 1,237,845 bytes,
and 30 items in `All CISA Advisories`. The snapshot mixed cybersecurity advisories, ICS and
ICS medical advisories, alerts, and routine KEV catalog notices. Items carried a CISA HTTPS
link, `/node/<id>` GUID, publication date, CISA creator, and HTML description. No ETag or
Last-Modified validator was returned. The largest description was about 468 KiB; the body is
needed transiently to find source-provided CVEs, CVSS values, sectors, and mitigation sections.

RS-045 now has a fixture parser and offline scan. It stores bounded metadata only: source
identity, advisory class, title, publication time, up to 20 CVE IDs, source-provided CVSS
severity when present, one sector, and a mitigation-page link when a section is present. It
never stores the HTML body and skips routine KEV catalog announcements. No update timestamp
was present in the observed item shape, so `updated_at` stays null. Vendor/product is retained
only as the ICS title; the parser does not infer structured product data. Emergency directives
are represented in the fixture as a parser contract; none appeared in the 30-item live snapshot.

Live ingest remains disabled. The observed 1.24 MB response exceeds the shared 1 MiB default
fetch cap; a source-specific 2 MiB admission and current-item/body-size guard need a separate
review. A live signoff must also verify source terms, cadence, retention, source health, and an
isolated explicit `news-scan` before this registry entry can be marked `verified` or allowlisted.
