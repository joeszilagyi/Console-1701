# LOCAL Social Source Policy

Use this note when reviewing community or social sources for the LOCAL scope.

## Current enforced rules

- Social candidates stay disabled by default.
- `local.allow_social_sources` must be explicitly enabled before social sources can be configured.
- Social candidates may remain `manual_review_only` when the source is only being reviewed rather
  than live ingested.
- Never scrape HTML to bypass platform restrictions, API rules, or rate limits.
- Keep retention short if any compliant social source is ever enabled.

## Source classes covered

- Bluesky AT Protocol
- Reddit official API or permitted feed access
- X official API access when compliant and explicitly configured

## Remaining work

- Define a live adapter path for one compliant source at a time.
- Add source-specific retention and evidence rules for any enabled social feed.
- Keep social signals secondary to official and local operational sources.
