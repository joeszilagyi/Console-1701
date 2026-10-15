# GLOBAL humanitarian item evidence contract

Implemented 2026-10-15 for RS-076. The persisted `evidence.humanitarian` object is attached to
GLOBAL ReliefWeb disaster and report items. It is derived only from source metadata already
accepted by the fixture parsers and the shared scan audit fields.

## Fields

- `contract_version`: currently 1.
- `source_id`, `source_family`, `official_status`, and `humanitarian_source`: provenance and
  source classification. `official_status` is the configured registry label, not a claim that
  every ReliefWeb-hosted report was authored by ReliefWeb.
- `affected_countries`: source-provided ReliefWeb country names; no country inferred from title.
- `disaster_ids`: the disaster record ID or the configured active disaster IDs matched by a
  report. This is a crisis identity, not a casualty count.
- `event_type`: source-provided disaster type when available, otherwise a conservative report or
  disaster label.
- `source_published_at`, `first_seen_at`, `last_seen_at`: separate publication and local
  observation times.
- `description`: at most 500 characters of already bounded source metadata. No article body.
- `report_url` for reports, plus `source_url` for both item types.
- `retention_expires_at` and `policy_notes`: the same scan decision and expiry used by storage.
- `people_at_risk`: explicit `not_provided_in_stored_metadata` with null value until a verified
  structured source field is added. Do not parse casualty or population estimates from prose.
- `body_stored`: false.

The item-detail API already returns stored JSON evidence; no page or host scan performs an
external request to fill these fields. Offline scan tests check disaster/report evidence,
source-provided geography, timestamps, retention and no body leakage. A source-health failure
must leave the last good item evidence under the existing retention policy.
