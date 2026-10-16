# GLOBAL conflict and humanitarian sensitivity rules

Implemented 2026-10-15 for RS-077. GLOBAL sources can declare a validated
`conflict_sensitive` boolean and explicit `sensitivity_flags`. The
`official_conflict_humanitarian` source class defaults to conflict-sensitive. These controls
are metadata policy decisions, not headline keyword guesses. The existing source policy review
gate still applies to high-risk enabled conflict sources.
The separate pre-storage GLOBAL attention classifier also recognizes explicit doxxing and
named/private-person tracking phrases in bounded titles and descriptions. It sets the same hard
flags before persistence; generic tracking of storms or other events does not trigger this rule.

## Supported flags and behavior

- `conflict_adjacent` or `conflict_sensitive`: a lone, nonofficial report is capped at score 20
  and labeled `unconfirmed_conflict_or_rumor`. Elevation requires an official source or a
  correlated event with at least two independent source families. This preserves the event as
  cautious context without making an unverified report a lead signal.
- `war_ticker`, `graphic_violence`, `casualty_speculation`, `targeted_person_tracking`,
  `private_distress`, `doxxing`, and `source_laundering`: hard suppression. The GLOBAL event score
  becomes zero, and the event is omitted from the GLOBAL cluster attention list. Stored item
  evidence records the flags and suppression reason.
- `graphic_violence`, `casualty_speculation`, `targeted_person_tracking`, `private_distress`, and
  `doxxing`: item title is replaced with `Sensitive humanitarian report` and description is
  dropped **before storage**. The original item URL remains for provenance. An explicit
  `redacted_before_storage` flag records the action.
- Existing `global_identity.rumor` penalties remain, and a rumor without official or independent
  confirmation is also capped. Repeated reports from one source family do not count as
  independent confirmation.

The event ranking JSON stores the score before and after the sensitivity penalty, explicit
flags, whether official or independent confirmation was present, and a plain-language label.
It does not infer casualty figures, local impact, or source independence from prose. A publisher
being official does not make a flagged graphic/private item suitable for the attention list.

Tests cover a lone conflict-sensitive report, official confirmation, independent-family
corroboration, hard suppression, pre-storage redaction, and an offline fixture scan that leaves
no sensitive headline or cluster row. Future conflict parsers must set item-level flags from
verified structured evidence; these rules do not scan arbitrary article bodies or social posts.
