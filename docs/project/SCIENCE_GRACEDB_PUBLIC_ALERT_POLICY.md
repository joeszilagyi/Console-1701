# GraceDB and LVK Public Alert Policy for Solar System and Beyond

Checked 2026-10-15 against [GraceDB's REST documentation](https://gracedb.ligo.org/documentation/rest.html),
[superevent query guide](https://gracedb.ligo.org/documentation/queries.html),
the [LVK public-alert guide](https://emfollow.docs.ligo.org/userguide/content.html), and
[NASA GCN's LVK mission page](https://gcn.nasa.gov/missions/lvk).

GraceDB has a documented REST root at `https://gracedb.ligo.org/api/`, with public read access
without credentials only for data released publicly. The API exposes superevents and related
annotations/files. The query guide supports production/test distinction and `is_public` filtering;
querying by superevent ID or bounded time is preferable to sweeping event tables. A public
superevent ID is the durable identity. Internal or test/MDC events must not appear as Recent
Signal. GraceDB documents HTTP 429 behavior and retry guidance for creation/annotation requests;
this review did not establish a separate public read quota, so a future reader needs conservative
intervals, pagination/row caps, and backoff.

NASA GCN describes LVK `EARLYWARNING`, `PRELIMINARY`, `INITIAL`, `UPDATE`, and `RETRACTION`
notices. A retraction means the trigger is no longer a candidate of interest. As of the GCN
announcement checked here, LVK notices are distributed as JSON over authenticated Kafka, with
client credentials; no email fallback is available for that stream. The application will not add
a Kafka dependency or credential flow as part of first-pass fixture work. A narrow, public,
polling GraceDB reader is a separate future option after exact query and response testing.

**Decision:** disabled and policy-reviewed, with no live adapter yet. A fixture parser uses
public superevent metadata only: ID, public status, source/alert time, event time, alert type,
classification/significance only when source-provided, latest revision, source URL, and
preliminary/update/retraction state. Correlate all revisions by superevent ID. Retractions must
withdraw elevation and remain visible as retractions until expiry; a preliminary alert must not
be rendered as a confirmed gravitational wave. Distinguish the event time from notice/update
time, and do not infer an Earth impact or local visibility claim.

Bounded public reads on 2026-10-15 verified the v2 superevent record and its `links.voevents`
metadata list for two historical Production events. `S251017di` has an early-warning revision
followed by `RE`, and its public page marks it retracted. `S251013x` has preliminary, initial,
and update revisions without a retraction. The local fixture assembly stores only those record
and VOEvent metadata fields, rejects mismatched REST links, and treats any `RE` revision as a
withdrawal. The fixture scan stores the withdrawn event with a retraction penalty and preserves
the other candidate as an update. No live poll is enabled by this parser.

Sky-map URLs can be retained as official provenance links, but no FITS, HEALPix, image, or other
sky-map file is downloaded, parsed, cached, or shown as a precise location. The REST API's
`files/` subtree and broad logs/annotations are outside the default fetch contract. Any future
live reader must use an exact public endpoint/query with `is_public` and production filters,
bounded recent time, explicit page/row/byte caps, conditional request or interval control,
429 backoff, source-health states, retention and purge tests, and mocked preliminary/update/
retraction sequences. Do not use credentials for nonpublic GraceDB data.
