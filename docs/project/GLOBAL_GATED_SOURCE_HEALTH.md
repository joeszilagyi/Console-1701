# GLOBAL gated source health

GLOBAL source definitions can remain visible in config and the source-health UI when a social,
heavy open-data, or homepage gate is off. An enabled candidate is blocked before any local file
read or HTTP request and records a specific fetch/health state: `social_disabled`,
`heavy_open_data_disabled`, or `homepage_extract_disabled`. Registered manual-review sources
record `manual_review_only`; registry reference pages record `unsupported` if someone enables
them as ingest sources.

Credential-required sources still need the explicit GLOBAL auth allowance before config loads.
Without credential material they record `auth_required` before access. High policy-risk conflict
sources still require a recorded policy review before config loads. No GLOBAL endpoint is in the
live HTTP allowlist. The only way these fixtures can ingest is through explicit local file URLs
and their required gates; ordinary GET routes never perform ingest.

The GLOBAL page shows the specific states in source cards and adds heavy/homepage gate counts.
The checklist retains the broader UI/health matrix as open until the other state transitions and
SYSTEM presentation are verified.
