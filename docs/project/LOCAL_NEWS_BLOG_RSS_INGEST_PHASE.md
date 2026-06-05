# LOCAL News and Blog RSS Ingest Phase

Use this note for local news and neighborhood blog ingest planning.

## Current state

- Fixture-only RSS/Atom parsers already exist for local news and neighborhood blog feeds.
- Neighborhood blogs remain gated behind `local.allow_neighborhood_blogs`.
- The ingest path still needs an explicit opt-in live command before any network fetching is added.

## Required behavior

- Store headline metadata only.
- Keep descriptions bounded.
- Avoid article-body fetching.
- Avoid paywall bypass.
- Prevent syndicated duplicates from inflating independent convergence.

## Remaining work

- Add a source-by-source live RSS/Atom ingest command.
- Define source verification rules for local news and neighborhood blog feeds.
- Add duplicate-syndication handling for enabled feeds.
