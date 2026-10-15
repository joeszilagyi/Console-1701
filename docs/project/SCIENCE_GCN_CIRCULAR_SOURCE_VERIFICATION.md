# GCN Circular Source Verification for Solar System and Beyond

Checked 2026-10-15 against NASA GCN's [Circular overview](https://gcn.nasa.gov/docs/circulars),
[archive guide](https://gcn.nasa.gov/docs/circulars/archive),
[Circular schema](https://gcn.nasa.gov/docs/schema/v6.0.0/gcn/circulars.schema.json), and
[archive](https://gcn.nasa.gov/circulars). GCN Circulars are brief, citable, human-written
astronomy bulletins; they may report observations, follow-ups, near-term predictions, or planned
observations. They are not all confirmed discoveries or public-impact events.

The documented JSON schema has unique `circularId`, inferred `eventId`, `subject`, `body`,
`createdOn` in Unix milliseconds, `submitter`, and submission method/format. The event name is
inferred from subject text and moderators can associate aliases with one event group. That makes
`eventId` useful but not infallible as a correlation key. Circular bodies can include personal
email addresses and links to sky maps or other large products; first-pass storage should keep
only circular ID, event ID, subject, public URL, source time, and a bounded status/follow-up label.
Do not store submitter email, full body, attachment, sky map, or article text.

An official [Circular page](https://gcn.nasa.gov/circulars/33603) links a per-circular
`33603.json` response. A bounded direct read on 2026-10-15 returned HTTP 200 and a 1,325-byte
JSON object with `circularId`, `eventId`, `subject`, `createdOn`, `body`, `submitter`, and `email`.
The local test fixture uses that observed shape, with synthetic body/contact content to verify
those fields are excluded from stored news items. The fixture adapter is limited to one local
JSON object and never fetches the linked JSON or any body URL.

**Access decision:** fixture only. The public archive offers browser search
with date filters and a daily full JSON/text `.tar.gz` export of roughly 30 MB. A bounded,
documented public metadata API with rate guidance was not established in this review. The full
archive is a firehose and should not be downloaded for a recent-signal scan. NASA documents
email/Kafka subscriptions; Kafka client credentials and a streaming dependency would require a
separate explicit policy and architecture decision. No guessed private web API, archive scraping,
or full-archive download is permitted by this signoff.

Before any live adapter, verify a supported narrow discovery method, account and reuse terms,
rate and retention limits, pagination/time bounds, current schema version, and
correction/retraction semantics. Expand fixtures for aliases and multi-circular revisions.
Use a short retention window and low default priority. Deduplicate by circular ID; correlate
separate circulars by event name/aliases only with source-backed evidence. A follow-up or
proposed observation must not be rendered as a confirmed detection.
