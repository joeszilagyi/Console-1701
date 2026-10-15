# GLOBAL storage facets

The first-pass GLOBAL storage contract uses the existing scoped source, fetch-run, item,
cluster, health, and retention tables. The `news_item_facets` table adds indexed lookups for
country, verified region, event type, source family, impact tag, and explicit crisis
sensitivity flags. The stored item evidence remains the detailed source of truth.

Facet rows are derived when a GLOBAL item is inserted or refreshed. `init_db` backfills
existing GLOBAL items that have no facet rows, including databases created before the table
existed. The foreign key cascades when expired items are purged. A query helper returns only
active, unexpired GLOBAL items and validates facet kind and result limit.

Country and event type values come from structured GDACS or ReliefWeb parser evidence.
Title-derived WHO geography is deliberately excluded because it is not verified geography.
Regions and sensitivity flags are indexed only when evidence explicitly marks them as
verified or enabled. Broader correlation and crisis classification remain separate work.
