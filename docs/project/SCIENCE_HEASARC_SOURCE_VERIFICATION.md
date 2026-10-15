# HEASARC Metadata Source Verification

Checked 2026-10-15 against HEASARC's official [API overview](https://heasarc.gsfc.nasa.gov/docs/archive/apis.html),
[Xamin API guide](https://heasarc.gsfc.nasa.gov/docs/xamin-api.html),
[VO/TAP service guide](https://heasarc.gsfc.nasa.gov/navo/summary/navo_services.html),
[data-use policy](https://heasarc.gsfc.nasa.gov/docs/heasarc/data_policy.html),
[regularly updated table index](https://heasarc.gsfc.nasa.gov/docs/heasarc/databases/databases_2025.html),
and [NuSTAR master-table notes](https://heasarc.gsfc.nasa.gov/W3Browse/nustar/numaster.html).

| Interface | Verified shape | First-pass decision |
| --- | --- | --- |
| Xamin query | `GET https://heasarc.gsfc.nasa.gov/xamin/query` supports `table`, `time`, `fields`, `resultmax`, and `format=votable`. | Candidate for a single named high-energy mission table with a short time window and explicit positive row cap. Keep disabled pending fixtures and signoff. |
| VO TAP | `https://heasarc.gsfc.nasa.gov/xamin/vo/tap/sync` accepts ADQL queries. | Heavy-archive blocked; do not accept arbitrary SQL/ADQL from the app or users. |
| Cone search | `https://heasarc.gsfc.nasa.gov/xamin/vo/cone` accepts a table and sky position. | Reference lookup only; no repeated sky survey. |
| Data products | Xamin and VO can link to observation products. | No FITS, spectra, images, event files, bulk exports, or product-link traversal. |

The official index lists `swiftmastr`, `xmmmaster`, `fermigtrig`, and other mission-specific
tables. Choose one table by exact allowlist, then verify its date field, public-release status,
and row semantics before using it. Observation metadata is not automatically a discovery or
alert. The NuSTAR notes explicitly distinguish planned, accepted, observed, validated, and
public data; a future parser must not announce accepted/scheduled targets as observations.

One bounded public Xamin probe on 2026-10-15 used `table=swiftmastr`,
`time=2026-10-01..2026-10-02`, `fields=standard`, `resultmax=2`, and `format=votable`.
It returned HTTP 200, XML VOTable 1.4, two rows, named `FIELD` metadata, and
`INFO name="QUERY_STATUS" value="OVERFLOW"`. The two rows were routine Swift observations,
so the probe establishes transport and parser shape only. `OVERFLOW` means results were
truncated; it must never be treated as a complete scan. Xamin documents that `ResultMax <= 0`
means **no limit**, and sorting a capped query can still require a full server-side sort.
Do not send zero/negative caps, unbounded time windows, broad joins, or unbounded sorts.

HEASARC's data-use page says its materials are freely available but notes mission-specific
conditions, including XMM-Newton's noncommercial wording and publication acknowledgement.
It does not establish a numeric public API rate allowance. A future reader should be serial,
infrequent, cached, and stop/back off on 429 or other source errors rather than assume a
throughput entitlement. Source health must distinguish access failure, malformed VOTable,
truncation/overflow, stale table, and a valid empty bounded result. Keep only an observation
ID, mission/table ID, selected public metadata fields, retrieval and observation times, and
the official source link under normal Recent Signal retention; do not persist raw table dumps.

Promotion requires an exact query contract, positive row and byte caps, timeouts, public-status
filtering, a checked source-use decision for the chosen mission, fixture tests for VOTable
namespaces and `QUERY_STATUS`, source-health tests, and an explicit local opt-in. HEASARC is
currently disabled and absent from the runtime HTTP allowlist.
