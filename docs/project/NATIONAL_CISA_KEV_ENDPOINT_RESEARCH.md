# CISA KEV machine-readable endpoint research

Reviewed 2026-10-15 for RS-046. Decision: **JSON catalog and schema verified; an offline fixture
parser is implemented, while live KEV ingest stays disabled pending a separate signoff**.

## Ownership and access

CISA's [Known Exploited Vulnerabilities Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
links machine-readable JSON, CSV, and JSON Schema, and describes the catalog as an input to
vulnerability management prioritization. A bounded direct GET of the exact official
[JSON feed](https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json)
returned HTTP 200 `application/json` on 2026-10-15, 1,789,360 bytes, with `ETag` and
`Last-Modified`. The official [JSON Schema](https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities_schema.json)
also returned HTTP 200 `application/json`, 3,623 bytes. Neither needed authentication in this
check. A guessed CSV sibling path returned HTTP 404; the website advertises CSV, but its exact
current URL is **unverified**. Do not configure that guessed path.

## Observed schema and update semantics

The JSON envelope had `title`, `catalogVersion`, `dateReleased`, `count`, and `vulnerabilities`.
At observation the version was `2026.10.15`, `dateReleased` was
`2026-10-15T17:00:11.2795Z`, and `count` matched 1,746 unique CVE rows. The first row's
`dateAdded` was `2026-10-15`; the last was `2021-11-03`. This is a full catalog snapshot, so a
future scanner should compare CVE IDs and row contents against its prior good snapshot, not emit
1,746 fresh alerts on each poll. A changed catalog version or HTTP entity tag alone does not
identify which CVE changed. `dateAdded` identifies catalog admission, not last modification.
No per-row update timestamp was observed.

The schema requires `cveID`, `vendorProject`, `product`, `vulnerabilityName`, `dateAdded`,
`shortDescription`, `requiredAction`, and `dueDate` per row. Observed optional fields include
`knownRansomwareCampaignUse` (`Known` or `Unknown`), `forensicTriage`, `notes`, and `cwes`. The
schema says `Unknown` means CISA lacks confirmation of ransomware campaign use; it must not be
rendered as a negative finding. Preserve `dateAdded` and `dueDate` as calendar dates, without
inventing a time of day or an expiry at midnight. Bound all text fields and keep CVE as identity.

CISA's [BOD 22-01 explanation](https://www.cisa.gov/news-events/alerts/2022/02/10/cisa-adds-15-known-exploited-vulnerabilities-catalog)
states that federal civilian executive branch agencies must remediate catalog entries by the due
date. For other organizations the due date is useful context, not a universal legal deadline.
KEV membership says exploitation has been observed; it does not prove that this host has the
affected product or is exposed. Host applicability would require separate local inventory evidence.

## Proposed local policy and health

The feed is a public official JSON snapshot, with no auth seen and no personal data expected.
Keep the NATIONAL `cisa_kev` registry row disabled by default. A proposed refresh is every 6
hours with conditional `ETag`/`Last-Modified` requests, a byte cap above the observed 1.79 MB,
and backoff on rate limits or transport errors. This is a local polling choice, not a CISA
publication guarantee. The next live signoff must verify redirects, current terms and license,
robots guidance, response-size growth, conditional 304 behavior, allowed cadence, and exact URL
allowlisting.

For future live ingest, a 304 should mean a healthy unchanged catalog, while malformed JSON, schema
failure, duplicate CVE or count mismatch should be `parser_failed` and retain the last good
snapshot under retention. Network failure should be `failing` or `stale`; 429 should be
`rate_limited`; an auth response should be `auth_required`. An unexpectedly empty catalog should
not wipe prior rows. Show catalog admission separately from remediation due date and use
source-provided fields for cyber ranking. A KEV entry without local applicability evidence belongs
in NATIONAL context, not a claim of host compromise.

## Offline fixture adapter

`cisa_kev_json` now validates the nonempty snapshot envelope, count, unique CVE IDs and calendar
dates. It preserves bounded title/description/action fields, `Known` versus `Unknown` ransomware
evidence, forensic-triage flag, CWE list, catalog version and release time. Each CVE gets a CISA
catalog search URL for a distinct item identity; this is a search link, not a guaranteed per-row
permalink. The shared NATIONAL ranking adds a capped cyber factor, and indexed facets label CISA
and cybersecurity. The synthetic fixture covers two records and an offline `news-scan`; tests
confirm that an empty or inconsistent snapshot fails rather than deleting prior entries. The
parser records `local_applicability: unknown` and labels the due date as a federal civilian
executive branch deadline. It does not fetch the live catalog.
