# NATIONAL Federal Register API fixture verification

Reviewed 2026-10-15 for RS-047. Decision: **published-document JSON shape verified and offline
filtered fixture parser implemented; live polling stays disabled**.

## Official API and bounded observation

The Federal Register [developer resources](https://www.federalregister.gov/reader-aids/developer-resources/rest-api)
describe public JSON/CSV REST endpoints, no API key, selectable fields, and pagination limited to
the first 2,000 results unless narrowed by date. The [interactive API documentation](https://www.federalregister.gov/developers/documentation/api/v1)
lists the supported endpoints. A bounded GET of
`https://www.federalregister.gov/api/v1/documents.json?per_page=2&order=newest` returned HTTP 200
`application/json` on 2026-10-15. The envelope had `description`, `count`, `total_pages`,
`next_page_url`, and `results`; document rows had `document_number`, `title`, `type`, `abstract`,
`html_url`, `publication_date`, `agencies`, and other fields. Each agency carried a stable `slug`.
`comment_end_date`, `effective_on`, and `action` were not present in the default list response;
the fixture tests their optional parsing, and any future live query must request and verify those
fields explicitly. The sampled result count was much larger than one page, so a live adapter must
use bounded date and agency filters before pagination. It must not turn the entire Register into
an attention stream.

The Federal Register site explains that its HTML/XML rendition is an **informational** version;
users needing legal authority should check the official PDF edition on govinfo.gov. The parser
records that distinction and links to the Federal Register document page. It does not claim the
HTML rendition itself is the official legal text or store full rule text.

## Offline filter contract

`federal_register_documents_json` requires configured `agency_slugs`, `document_types`, and
`impact_terms`. A row must match all three, with the impact phrase in the title. A fixed
low-public-value rule suppresses information collections, meeting notices, routine filings and
OMB review notices even if they contain a configured impact word. The parser caps the response at
100 rows, validates document number and official document URL, and preserves publication date,
optional comment deadline and effective date as calendar dates. It stores bounded abstract and
action text, matched filter evidence, agency slugs and a capped regulatory ranking factor.
NATIONAL facets index matched agencies and the regulatory sector. The synthetic fixture proves
two high-impact FAA documents pass, while a routine information collection, wrong agency and
unmatched title do not. An offline `news-scan` test verifies persistence without network access.

These terms are an explicit operator choice, not a general model of legal or economic impact.
A title match supports a candidate attention signal; it does not establish that the rule applies
to this host, that comments remain open, or that a deadline has legal effect for the user.

## Live release gate

Keep Federal Register candidates disabled. Before a live exact-URL `news-scan` adapter, verify
query parameter encoding for date/agency/type/field selection, page limits, redirects, rate and
conditional behavior, corrections/withdrawals, source retention, and duplicate identity across
pagination. The API's `next_page_url` must be treated as a candidate to validate against the
exact allowed host and query bounds, never followed blindly. Page loads, host scans and tests
remain offline.
