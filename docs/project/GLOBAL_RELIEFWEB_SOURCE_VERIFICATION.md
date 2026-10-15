# ReliefWeb API verification boundary

Checked 2026-10-15 against the official [API overview](https://apidoc.reliefweb.int/),
[request parameters](https://apidoc.reliefweb.int/parameters),
[result structure](https://apidoc.reliefweb.int/result-structure), and
[field tables](https://apidoc.reliefweb.int/fields-tables).

The documented v2 result contains a `data` list of records with `id` and `fields`.
Disaster fields include `name`, `status`, countries, types, `date.event`, `date.created`,
`date.changed`, and canonical `url`. The parser only retains bounded disaster metadata;
it does not ingest report bodies. A reports count is retained only if the source actually
provides an integer `reports_count` field.

ReliefWeb states that, since 2025-11-01, API use requires a pre-approved `appname`. An
unapproved sample request on 2026-10-15 returned HTTP 403. The fixture is therefore based
on the documented field schema, not a sampled live response. Registered ReliefWeb disaster
and update sources are credential-gated, disabled by default, and have no HTTP allowlist.
The tests read a local JSON fixture and block network access.
