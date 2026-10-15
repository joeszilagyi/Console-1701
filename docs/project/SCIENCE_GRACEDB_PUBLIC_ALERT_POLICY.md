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
intervals, row caps, and backoff.

NASA GCN describes LVK `EARLYWARNING`, `PRELIMINARY`, `INITIAL`, `UPDATE`, and `RETRACTION`
notices. A retraction means the trigger is no longer a candidate of interest. As of the GCN
announcement checked here, LVK notices are distributed as JSON over authenticated Kafka, with
client credentials; no email fallback is available for that stream. The application will not add
a Kafka dependency or credential flow as part of first-pass fixture work. A narrow, public,
polling GraceDB reader is available behind explicit local opt-in.

**Decision:** disabled by default and policy-reviewed. A fixture and live parser use
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
the other candidate as an update.

The live adapter only runs from an explicitly enabled `news-scan` source with the exact
`https://gracedb.ligo.org/api/v2/superevents/` URL and verified parser. It builds its own
UTC `created` query for the last 48 hours with `category: Production is_public: True`,
`count=10`, and a minimum 60-minute interval. The list's `numRows` must fit the cap and equal
the returned row count; an overflow fails the whole fetch, so no partial result is stored.
Each row must contain the matching public superevent and VOEvent REST links before any
follow-up GET. The adapter fetches only those VOEvent metadata URLs, never files or logs,
with no redirects or proxy use. The aggregate response and assembled parser input each have
a 64 KiB cap; HTTP 429 enters the scanner's rate-limited state. No conditional request is
available for this time-varying query, so the interval gate controls repeat reads.

An isolated live opt-in `news-scan` on 2026-10-15 returned HTTP 200, healthy source state,
623 response bytes, and zero items because the recent query contained no public Production
events. Mocked transport and scan tests cover a preliminary candidate followed by a
retraction, stable superevent identity, zero retraction score, overflow, nonproduction rows,
and foreign links. A later empty rolling query keeps the retracted item visible until its
seven-day expiry; the retention purge removes both the item and science event. The full
suite passed (695 tests) and Ruff passed. Empty-window live
reads do not prove live revision behavior; that remains covered by the mocked sequence.

Sky-map URLs can be retained as official provenance links, but no FITS, HEALPix, image, or other
sky-map file is downloaded, parsed, cached, or shown as a precise location. The REST API's
`files/` subtree and broad logs/annotations are outside the fetch contract. Cross-source
retention and purge are now covered for a fixture-only GCN notice plus Circular retraction.
An exact GCN or GraceDB event identifier retains a withdrawal marker for 21 days after the
last observed retraction. The marker keeps a refreshed initial report withdrawn when the
retraction item expires first; it is pruned by the normal retention command and stores no
sky map, report body, or private metadata. The GCN sequence is verified offline; a live
GraceDB retraction-to-expiry observation is not claimed. Do not use credentials for
nonpublic GraceDB data.
