# Minor Planet Center Science-Context Source Verification

Checked 2026-10-15 against the official [MPC API directory](https://docs.minorplanetcenter.net/mpc-ops-docs/apis/),
[MPECs API](https://docs.minorplanetcenter.net/mpc-ops-docs/apis/mpecs/),
[Orbits API tutorial](https://docs.minorplanetcenter.net/tutorials/notebooks/mpc_tutorial_api_orbits/),
[Observations API](https://docs.minorplanetcenter.net/mpc-ops-docs/apis/get-obs/),
[List API](https://docs.minorplanetcenter.net/mpc-ops-docs/apis/list/), and
[MPC usage FAQ](https://docs.minorplanetcenter.net/mpc-ops-docs/faqs/).

| Candidate | Documented shape | First-pass decision |
| --- | --- | --- |
| MPECs | `GET https://data.minorplanetcenter.net/api/mpecs` with JSON request specifying `terms` and optional `issued_after`/`issued_before`; response records include `fullname`, `title`, `pubdate`, and official `link`. | Best metadata-only science-context candidate after a single named object/mission term and recent date window are tested. No broad wildcard search. |
| Orbits | `GET /api/get-orb` with one `desig`; returns detailed `mpc_orb` JSON, including elements and uncertainties. | Reference/fixture candidate for a known object, not a recurring event feed. Do not render precise orbital tracking. |
| Observations and NEOCP observations | Official APIs return detailed astrometric rows or complete observation history. | Heavy data/reference only; no full observation download for Recent Signal. |
| Object lists | Official `GET /api/list` can return as many as 50,000 rows by default and has `limit`/`offset`. | Archive firehose blocked; not a discovery feed. |

MPC warns that more than five API requests per second can cause HTTP 429 or IP blocking. A future
reader should be far slower, serial, cached, and back off on 429. The docs establish request and
response shapes, but this pass did not run the service or verify a production response envelope,
terms for automated redisplay, conditional validators, or a safe refresh interval. All live
access stays disabled and outside the exact HTTP allowlist until fixture and signoff work exists.

For a future MPEC fixture, store MPEC `fullname` as the item ID, title, official link, UTC
publication time, explicit designation, bounded category/status evidence, and the exact query
bounds. Do not store circular bodies, observation rows, full orbit vectors or covariance arrays.
Deduplicate aliases of the same object and separate publication time from the underlying
observation epoch. MPC science context can corroborate named-object discoveries or mission
follow-up; close-approach/hazard operations remain canonical in ORBITAL's JPL CNEOS path. An
MPEC alone must not become an impact prediction or local alert.
