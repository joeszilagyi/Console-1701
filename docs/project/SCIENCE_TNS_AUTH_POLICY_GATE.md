# TNS transient access and first-pass gate

Reviewed 2026-10-15 for RS-144 against the official [TNS getting-started guide](https://www.wis-tns.org/content/tns-getting-started),
[FAQ](https://www.wis-tns.org/content/faq), [TNS 2.0 API manual](https://www.wis-tns.org/sites/default/files/api/tns2_manuals/TNS2.0_APIs_manual.pdf),
and [TNS Newsfeed](https://www.wis-tns.org/node/41146). TNS is the IAU naming mechanism for
astronomical transients. Public object metadata and proprietary group reports have different
access rules; Recent Signal may only ingest public records.

The Search and Get Object APIs use POST at `/api/get/search` and `/api/get/object`. They require a
bot API key and a bot `tns_marker` User-Agent. The Search API sample returns object name,
prefix and ID, but that short list does not itself supply a source publication or discovery
timestamp. Get Object supplies detail for a named object and can also return photometry/spectra;
those products must be disabled in a metadata-only request. The service uses a 60-second moving
rate window and returns HTTP 429 when a limit is exceeded. The response may carry proprietary
records visible to the bot's group, so an authenticated response is not automatically public.

TNS also stages a daily full public-object ZIP plus daily and hourly delta ZIPs. Its guide lists
`objid`, name/prefix, type, discovery date, received/creation/modified times and other columns.
The full catalog is a heavy archive; it is excluded by the first-pass firehose gate. Delta paths
change by day or hour, require a separate exact-request design and authenticated access, and
can include old objects modified recently. A delta timestamp is not a new discovery claim.

**Current decision:** keep every TNS source disabled with `auth_required` or manual-reference
health. No bot key exists in the repo; no TNS POST, ZIP download, page scraping, or API-shaped
fixture is enabled. The current official Search sample is insufficient to date an item, while
Get Object and delta transport require credentials and a new request contract. This does not
block ATel and GraceDB public opt-ins or the fixture-only GCN path.

Before a TNS adapter is admitted, define an explicit owner-approved account and credential
location outside the repo, exact POST or bounded delta request construction, public-only field
verification, response and row caps, 429 backoff, and a small observed response fixture. Store
only object ID/name/prefix, public classification, source dates, canonical object URL and bounded
status evidence for at most 14 days. Do not retain reporter names, internal group identifiers,
full reports, photometry, spectra, FITS files or raw responses. Tests must prove missing
credentials produce `auth_required` without a request, and page loads, host scans and pytest
never contact TNS. A live signoff must verify the exact response, terms, public visibility and
rate behavior before enabling any transport.
