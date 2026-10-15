# NATIONAL NHTSA recall API fixture verification

Reviewed 2026-10-15 for RS-043. Decision: **fixture parser implemented; live polling remains
disabled**.

## Official API and identity

NHTSA's [datasets and APIs page](https://www.nhtsa.gov/nhtsa-datasets-and-apis) documents recall
lookup by campaign number and by vehicle model year, make, and model. A bounded response from
`https://api.nhtsa.gov/recalls/campaignNumber?campaignNumber=12V176000` had top-level `Count`,
`Message`, and `results`. Rows included `NHTSACampaignNumber`, `Manufacturer`,
`ReportReceivedDate`, `Component`, `ModelYear`, `Make`, `Model`, `Summary`, `Consequence`, `Remedy`,
`parkIt`, `parkOutSide`, and sometimes `PotentialNumberofUnitsAffected`. A bounded vehicle lookup
returned multiple rows with optional fields differing between rows. The documented API is a
**lookup**, not a general recent-recalls feed; a future live integration needs a verified discovery
path and update cadence before it can poll current recalls. The [API use policy](https://api.nhtsa.gov/)
also governs any future access.

The parser takes a local copy of that envelope. It validates the count, campaign identity, report
date and core fields, groups model rows by campaign number, and rejects contradictory campaign
rows. The official campaign query URL is the item identity and source URL. The
[NHTSA recalls page](https://www.nhtsa.gov/recalls) is retained as a consumer VIN lookup and
instruction page, not claimed to be a campaign-specific notice. A reported date has day precision;
midnight UTC is a storage representation, not an NHTSA issue time.

## Evidence and ranking

The synthetic fixture covers two campaigns and a multi-model campaign. Stored evidence includes
manufacturer, component, bounded model list, affected-unit estimate when supplied, bounded
summary/consequence/remedy, `parkIt`, `parkOutSide`, and an explicit safety ranking contribution.
It does not store a full notice body or private VIN. The ranking gives capped weight only to
source-supplied park instructions or a large affected-unit estimate; the recall's existence alone
does not imply a severe hazard. NATIONAL agency and transportation facets are indexed. Offline
parser and `news-scan` tests verify normalization, campaign grouping, ranking and fixture-only
provenance.

## Live release gate

Keep the existing registry candidate disabled. Before adding an exact HTTPS allowlist entry,
verify a current-recall discovery endpoint or official feed, conditional response/rate behavior,
revision/withdrawal semantics, count and pagination limits, fresh-data cadence, and item URL
behavior. A vehicle or campaign lookup alone cannot honestly be described as a complete recent
recall stream. Page loads, host scans and tests must remain offline.

## Neighboring recall-source blockers

FSIS [announces a public recall and public-health-alert API](https://www.fsis.usda.gov/news-events/news-press-releases/fsis-launches-new-data-tool-recall-and-public-health-alert-api)
and lists it in [developer resources](https://www.fsis.usda.gov/science-data/developer-resources).
The linked documentation PDF and candidate API path returned HTTP 403 during bounded checks on
2026-10-15, so the response contract cannot be verified yet. RS-041 stays open.

CPSC's [official API information](https://www.cpsc.gov/Recalls/CPSC-Recalls-Application-Program-Interface-API-Information)
and [programmer guide](https://www.cpsc.gov/s3fs-public/RecallRetrievalWebServicesProgrammersGuide20180917.pdf)
document the Recall REST service and JSON/date parameters. A bounded recent-date GET and HEAD
against the service timed out with no response body on 2026-10-15. The guide can inform a future
fixture, but live service behavior still needs direct confirmation. RS-042 stays open.
