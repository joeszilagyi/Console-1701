# CISA advisory machine-readable endpoint blocker

Checked 2026-10-15 for RS-045. CISA's official
[Cybersecurity Alerts & Advisories page](https://www.cisa.gov/news-events/cybersecurity-advisories)
describes advisory categories, including alerts, cybersecurity advisories, ICS advisories and
analysis reports. A bounded direct request to the candidate
`https://www.cisa.gov/news-events/cybersecurity-advisories?feed=rss` returned HTTP 403. The
guessed `.xml` sibling returned HTTP 404. Neither establishes a usable machine-readable feed
contract. Search-engine views of advisory pages are insufficient to define an ingest schema.

RS-045 remains open. Before a fixture parser or live source can claim support for advisories,
find a CISA-published RSS/API endpoint or another official machine-readable contract, verify
its fields and update behavior, then define identity, CVE/vendor/severity/mitigation extraction
from source-provided fields. Do not invent those fields from a headline or fetch arbitrary
advisory pages during scan. Existing KEV research and its offline parser are separate from
CISA advisories. No CISA advisory source was enabled.
