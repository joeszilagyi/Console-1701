Use this as `build_order/003_national.md`.

I kept it in the same design-only lane as your first queue prompt: architecture/source-target inventory, no collectors, no live fetches, no dependencies, no runtime changes, BACKLOG law, and proof at the end.

I anchored the national source set around official machine-readable or source-identifiable targets where possible: NWS API and alerts, USGS earthquake GeoJSON feeds, CISA advisories and KEV, FDA recalls, FSIS Recall API, CPSC recalls API/RSS, NHTSA datasets/APIs, FAA NAS Status, Federal Register API, Congress.gov API, FEMA/DHS public alert/news pages, BLS/BEA/FRED economic APIs, and Recalls.gov. ([National Weather Service][1])

```text
You are working in the console-1706 repository.

This task assumes the prior scoped recent-signal architecture prompt, LOCAL Seattle design prompt, and REGIONAL Pacific Northwest design prompt have either already been run, or will be pasted above this prompt.

This is a NATIONAL scope architecture, source-target inventory, and ranking design task only.

Do not implement collectors.
Do not add live network fetches.
Do not scrape live websites.
Do not call APIs.
Do not add dependencies.
Do not add API keys.
Do not change runtime behavior.
Do not change page templates or CSS.
Do not create UI panels yet.
Do not commit.
Do not push.

Your job is to design the NATIONAL recent-signal layer in enough detail that later Codex passes can implement it safely, source by source, without guessing.

Before doing anything, inspect the current repo state and previous design outputs.

Required first checks:

pwd
git status --short
find docs/project -maxdepth 1 -type f -print | sort || true
grep -n "Recent Signal\|News Ingestion\|LOCAL\|REGIONAL\|NATIONAL" BACKLOG.md || true

If previous docs exist, read them first and extend them cleanly:

- docs/project/NEWS_SCOPE_INGESTION_ARCHITECTURE_DESIGN.md
- docs/project/LOCAL_SEATTLE_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md
- docs/project/REGIONAL_PNW_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md

Do not duplicate BACKLOG sections already added by previous tasks. Extend the relevant section cleanly or add a new NATIONAL subsection.

The user intent:

console-1706 is a local-only home dashboard running at http://127.0.0.1:1706/.

The NATIONAL tab should eventually answer:

"What is happening across the United States that may matter right now?"

The NATIONAL scope should eventually combine recent signals from:

- National official alerts.
- Federal emergency, disaster, weather, public health, recall, aviation, transportation, cyber, economic, regulatory, and government sources.
- National hazards: severe weather, hurricane, wildfire, earthquake, tsunami, volcano, flood, air quality, drought, and major disaster signals.
- National infrastructure: aviation, highways, rail, ports, energy, telecom, cyber, and major supply-chain disruptions where public and official.
- National public health and safety alerts: CDC, FDA, USDA FSIS, CPSC, NHTSA, EPA, OSHA, and similar official sources.
- Federal government actions with immediate public-impact value: Federal Register public inspection, executive actions, agency rules, congressional activity, Supreme Court/court system activity, and agency press releases only when relevant.
- National economic releases and market/economic condition signals from official sources, not stock-picking.
- National news outlets, public media, wire services, nonprofit journalism, and large broadcasters.
- Community/social national signals only when accessible through compliant, explicitly configured methods.
- Source health and freshness data.

The daily runtime goal is no LLM usage.

LLMs may be used during development to design adapters, inspect fixtures, write tests, or analyze source options. The application itself must not require LLM calls for normal operation.

Hard project constraints:

- Local-first.
- Boring.
- Stable.
- Lowest upkeep cost.
- No hidden cloud behavior.
- No hidden LLM calls.
- No telemetry.
- No fake demo data.
- No hidden page-load network fetches.
- No external fetch unless explicitly configured and enabled in a future phase.
- No scraping behind login.
- No bypassing paywalls, API restrictions, bot controls, or auth.
- No browser automation.
- No Selenium.
- No Playwright.
- No headless browser.
- No aggressive polling.
- No recursive crawling.
- No raw article body archive.
- No long-term social media archive.
- No storing secrets in the repo.
- No sudo.
- No package installation.
- No destructive commands.
- Preserve FastAPI, Jinja2, SQLite, vanilla CSS, vanilla JS, pytest.
- Bind only to 127.0.0.1 on port 1706.
- Treat AGENTS.md as binding project law.
- If anything is not completed or remains uncertain, update BACKLOG.md.

Current known test baseline from the user:

- pytest currently reports 37 passed and 1 failed.
- Known failure:
  tests/test_evidence.py::test_system_summary_formats_last_scan_without_timezone_suffix
- Expected:
  2026-04-28 06:55:01
- Actual:
  2026-04-28 13:55:01
- This task should not touch timestamp formatting or evidence code unless you explicitly document why.
- Do not leave the suite worse than baseline.

Inspect these files first:

- AGENTS.md
- README.md
- BACKLOG.md
- config.example.yml
- console-1706-codex-plan-01.md
- docs/project/NEWS_SCOPE_INGESTION_ARCHITECTURE_DESIGN.md, if it exists
- docs/project/LOCAL_SEATTLE_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md, if it exists
- docs/project/REGIONAL_PNW_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md, if it exists
- console1706/schema.sql
- console1706/config.py
- console1706/db.py
- console1706/scanner.py
- console1706/api.py
- console1706/templates/index.html
- console1706/static/app.css
- console1706/static/app.js
- console1706/evidence.py
- console1706/system_probe.py
- tests/

Deliverables:

1. Create this document:

   docs/project/NATIONAL_US_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md

   Create docs/project if it does not exist.

2. Update BACKLOG.md with concrete future implementation tasks flowing from this NATIONAL design.

3. Do not touch application code unless absolutely necessary. This should normally be docs plus BACKLOG only.

4. Do not perform live source verification. The source links below are seed targets. Classify them as candidate links and design how they should be verified in a later phase.

5. The final response must prove what changed and what did not change.

The design document must include the following sections.

SECTION 1: Purpose

Explain the NATIONAL scope in plain engineering language.

The NATIONAL scope is the United States recent-signal layer. It should tell the user what is happening at national scale, with source provenance, observed time, source kind, ranking reason, and evidence.

It is not:

- A general web crawler.
- A national news archive.
- A political doom feed.
- A stock market trading dashboard.
- A social media monitoring system.
- A permanent incident database.
- A law enforcement scanner.
- A hidden LLM summarizer.
- A cloud service.
- A replacement for LOCAL Seattle.
- A replacement for REGIONAL Washington / PNW.
- A replacement for GLOBAL world signals.

It is:

- A local, short-retention metadata dashboard.
- A deterministic cross-source event detector for U.S. public-impact signals.
- A source-health aware recent-signal system.
- A NATIONAL tab in console-1706 that can surface federal alerts, major hazards, transportation disruption, aviation disruption, recalls, public-health warnings, cybersecurity advisories, national emergency declarations, national news, economic releases, and compliant community echoes.
- A way to rank items by independent source convergence, official severity, public impact, freshness, user-configured source priority, and national relevance.

Make clear that "national" means useful public, configured, lawful, recent signals that the user chooses to enable. It does not mean unbounded crawling, political addiction, private data collection, or mass social monitoring.

SECTION 2: National scope boundaries

Define NATIONAL geography and relevance.

Default NATIONAL scope:

- United States national scope.
- U.S. federal agencies.
- All U.S. states and territories only when the event has national public-impact value.
- Major national corridors, airports, ports, energy grids, cyber infrastructure, public-health systems, federal recalls, federal emergency declarations, national weather/hazard systems, and national government operations.
- U.S.-wide weather, disaster, wildfire, hurricane, earthquake, air-quality, aviation, transportation, cyber, recall, health, regulatory, court, congressional, and official economic signals.
- National news outlets and public media when they cover U.S. events with broad importance.
- State or regional events only when the event affects national systems or is receiving independent national coverage.

Out of NATIONAL by default:

- Routine Seattle items. Those belong in LOCAL.
- Routine Washington / PNW items. Those belong in REGIONAL.
- Ordinary state politics unless it has national impact.
- Routine agency press releases with no immediate public effect.
- Generic op-eds and punditry.
- Political personality chatter.
- Stock tips, financial advice, or market speculation.
- Crime blotter noise.
- Single-source social chatter.
- Private medical or residential distress.
- Sources requiring login, payment, scraping around controls, or tokens not explicitly configured by the user.

Design a later config escape hatch:

national:
  enabled: false
  default_place_label: "United States"
  include_federal_alerts: true
  include_weather_hazards: true
  include_disasters: true
  include_public_health: true
  include_recalls: true
  include_transportation: true
  include_aviation: true
  include_cybersecurity: true
  include_energy_grid: true
  include_economic_releases: true
  include_federal_register: true
  include_congress: false
  include_courts: false
  include_national_news: true
  include_social_sources: false
  include_state_events_when_national_impact: true
  earthquake_min_magnitude: 5.0
  hurricane_attention_minimum: "watch"
  severe_weather_attention_minimum: "warning"
  wildfire_national_attention_min_acres: 1000
  recall_attention_classes:
    - "Class I"
    - "high_public_impact"
  cyber_attention_minimum:
    - "known_exploited"
    - "emergency_directive"
    - "high_impact_advisory"

SECTION 3: Relationship to LOCAL, REGIONAL, GLOBAL, and OVERVIEW

Explain how NATIONAL interacts with other scopes.

Rules:

- NATIONAL should not duplicate LOCAL Seattle unless the Seattle item has national impact.
- NATIONAL should not duplicate REGIONAL PNW unless the regional item has U.S.-wide impact or independent national coverage.
- NATIONAL should not duplicate GLOBAL unless the event is U.S.-specific or has direct U.S. national impact.
- GLOBAL owns non-U.S. world events unless U.S. national systems are directly involved.
- OVERVIEW should select the highest-priority items from LOCAL, REGIONAL, NATIONAL, GLOBAL, ORBITAL, and SYSTEM without burying urgent local/system issues.
- If a NATIONAL item directly affects Seattle or Washington, it can be tagged LOCAL_IMPACT or REGIONAL_IMPACT while canonical scope remains NATIONAL.
- If a LOCAL or REGIONAL item becomes nationally significant, it can be promoted or cross-listed into NATIONAL with evidence.

Examples:

- Routine SFD call in Seattle: LOCAL only or ignored.
- Major Seattle port shutdown affecting national freight: LOCAL, REGIONAL, NATIONAL.
- Snoqualmie Pass closure: REGIONAL unless national supply-chain impact exists.
- National FAA ground stop: NATIONAL and possibly LOCAL_IMPACT if SEA affected.
- FDA Class I food recall distributed nationwide: NATIONAL.
- CDC Health Alert Network warning: NATIONAL.
- U.S. severe weather outbreak across several states: NATIONAL.
- Major hurricane landfall warning: NATIONAL.
- Federal Register routine notice: NATIONAL source pool but low priority unless public impact is high.
- Supreme Court decision with immediate national policy effect: NATIONAL, if court sources are enabled.
- Global earthquake outside U.S. with no U.S. impact: GLOBAL.
- U.S. embassy warning abroad affecting U.S. travelers: NATIONAL and possibly GLOBAL depending on later GLOBAL design.

SECTION 4: Seed source target inventory

Create a source inventory table in the design document.

Use the source links below as seed targets.

Every row must include:

- source_key
- source_name
- source_family
- source_class
- scope
- raw_url
- expected_access_kind
- likely_adapter_type
- likely_refresh_interval
- initial_priority
- official_status
- privacy_risk
- policy_risk
- parser_risk
- retention_sensitivity
- verification_status
- why_it_matters
- future_phase

Use these source classes:

- official_alert
- official_emergency
- official_disaster
- official_weather_hazard
- official_hurricane
- official_wildfire
- official_air_quality
- official_water_flood
- official_seismic_volcano
- official_public_health
- official_recall
- official_food_safety
- official_transport
- official_aviation
- official_rail
- official_energy
- official_cybersecurity
- official_federal_civic
- official_regulatory
- official_economic
- official_court_legal
- national_news
- wire_service
- public_media
- local_tv_radio_national
- nonprofit_news
- social_candidate
- unofficial_aggregator
- source_health_only
- manual_review_only

Use these adapter types:

- rss_atom
- static_html_headline_candidate
- official_api_json
- cap_alerts
- geojson_feed
- hydrology_api_json
- recall_api_json
- federal_register_api
- congress_api_candidate
- govinfo_rss
- economic_api_json
- aviation_status_json_or_xml
- csv_download_candidate
- data_gov_catalog_candidate
- arcgis_feature_service_candidate
- source_health_probe_only
- local_file_fixture
- manual_review_only

Use these verification_status values:

- user_seeded
- assistant_seeded
- official_page_seen
- candidate_needs_verification
- candidate_policy_sensitive
- unofficial_secondary
- reject_for_now

Do not overstate verification. If a URL is only a likely feed endpoint, mark it candidate_needs_verification.

Seed source targets:

National emergency, disaster, homeland-security, and federal alert sources:

https://www.fema.gov/
https://www.fema.gov/about/newsroom
https://www.fema.gov/about/news-multimedia/press-releases
https://www.fema.gov/openfema-data-page/disaster-declarations-summaries-v2
https://www.fema.gov/about/openfema/other-data-sources
https://www.disasterassistance.gov/
https://www.dhs.gov/national-terrorism-advisory-system
https://www.dhs.gov/ntas/advisories
https://www.dhs.gov/news
https://www.dhs.gov/news-releases/press-releases
https://www.dhs.gov/subscribe-updates-dhs
https://www.ready.gov/alerts
https://www.ready.gov/
https://www.weather.gov/alerts
https://api.weather.gov/alerts/active
https://www.weather.gov/documentation/services-web-api
https://www.weather.gov/documentation/services-web-alerts

Weather, hurricanes, storms, fire weather, drought, flood, and climate hazards:

https://www.weather.gov/
https://www.weather.gov/alerts
https://api.weather.gov/alerts/active
https://www.weather.gov/documentation/services-web-api
https://www.spc.noaa.gov/
https://www.spc.noaa.gov/products/
https://www.spc.noaa.gov/products/outlook/
https://www.spc.noaa.gov/products/watch/
https://www.spc.noaa.gov/products/fire_wx/
https://www.wpc.ncep.noaa.gov/
https://www.wpc.ncep.noaa.gov/qpf/qpf2.shtml
https://www.wpc.ncep.noaa.gov/discussions/hpcdiscussions.php?disc=pmdspd
https://www.nhc.noaa.gov/
https://www.nhc.noaa.gov/gtwo.php
https://www.nhc.noaa.gov/aboutrss.shtml
https://www.nhc.noaa.gov/gis/
https://www.nhc.noaa.gov/data/
https://www.ncei.noaa.gov/access/monitoring/us-drought-monitor/
https://droughtmonitor.unl.edu/
https://www.drought.gov/
https://www.weather.gov/fire/
https://www.nwrfc.noaa.gov/
https://water.noaa.gov/
https://water.noaa.gov/about/nwm
https://waterservices.usgs.gov/
https://api.waterdata.usgs.gov/
https://www.usgs.gov/mission-areas/water-resources

Wildfire, smoke, national fire coordination, and air quality:

https://www.nifc.gov/
https://www.nifc.gov/fire-information/nfn
https://www.nifc.gov/fire-information/statistics
https://inciweb.wildfire.gov/
https://www.fireweatheravalanche.org/fire/
https://www.airnow.gov/
https://docs.airnowapi.org/
https://fire.airnow.gov/
https://www.epa.gov/outdoor-air-quality-data
https://www.epa.gov/air-research/air-quality-models

Earthquake, tsunami, volcano:

https://earthquake.usgs.gov/
https://earthquake.usgs.gov/earthquakes/feed/
https://earthquake.usgs.gov/earthquakes/feed/v1.0/
https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php
https://earthquake.usgs.gov/fdsnws/event/1/
https://www.usgs.gov/programs/VHP
https://volcanoes.usgs.gov/
https://www.usgs.gov/observatories
https://www.usgs.gov/observatories/hvo
https://www.usgs.gov/observatories/cvo
https://www.usgs.gov/observatories/calvo
https://www.usgs.gov/observatories/yvo
https://www.tsunami.gov/
https://www.weather.gov/tsunami/

Public health, disease, food safety, recalls, and consumer safety:

https://www.cdc.gov/
https://www.cdc.gov/han/
https://www.cdc.gov/han/php/about/index.html
https://www.cdc.gov/han/php/notices/index.html
https://www.cdc.gov/outbreaks/
https://www.cdc.gov/media/
https://www.cdc.gov/media/releases.html
https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts
https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts/major-product-recalls
https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts/enforcement-reports
https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds
https://www.fsis.usda.gov/recalls
https://www.fsis.usda.gov/science-data/developer-resources
https://www.fsis.usda.gov/science-data/developer-resources/recall-api
https://www.cpsc.gov/Recalls
https://www.cpsc.gov/Recalls/CPSC-Recalls-Application-Program-Interface-API-Information
https://www.cpsc.gov/Newsroom/CPSC-RSS-Feed
https://www.recalls.gov/
https://www.nhtsa.gov/recalls
https://www.nhtsa.gov/data
https://www.nhtsa.gov/nhtsa-datasets-and-apis
https://www.osha.gov/news/newsreleases
https://www.epa.gov/newsreleases
https://www.epa.gov/rss-news-feeds

Transportation, aviation, rail, freight, ports, and national travel:

https://www.transportation.gov/
https://www.transportation.gov/newsroom
https://www.faa.gov/
https://www.faa.gov/newsroom
https://www.faa.gov/newsroom/statements/general-statements
https://nasstatus.faa.gov/
https://nasstatus.faa.gov/list
https://nasstatus.faa.gov/api/airport-status-information
https://www.faa.gov/airport-status
https://www.fly.faa.gov/ois/?legacy=true
https://api.faa.gov/s/
https://github.com/Federal-Aviation-Administration/ASWS
https://www.fra.dot.gov/
https://railroads.dot.gov/newsroom
https://railroads.dot.gov/accident-and-incident-reporting
https://www.amtrak.com/alert
https://www.amtrak.com/service-alerts-and-notices
https://www.maritime.dot.gov/newsroom
https://www.maritime.dot.gov/outreach/newsroom/press-releases
https://ops.fhwa.dot.gov/511/
https://www.nhtsa.gov/press-releases

Cybersecurity, infrastructure, and technology risk:

https://www.cisa.gov/
https://www.cisa.gov/news-events/cybersecurity-advisories
https://www.cisa.gov/news-events/alerts
https://www.cisa.gov/news-events/ics-advisories
https://www.cisa.gov/news-events/bulletins
https://www.cisa.gov/known-exploited-vulnerabilities-catalog
https://www.cisa.gov/about/contact-us/subscribe-updates-cisa
https://www.cisa.gov/news-events/news
https://www.cisa.gov/news-events/emergency-directives
https://www.fbi.gov/news
https://www.ic3.gov/Media/Y2026/PSA
https://www.nist.gov/news-events/news
https://nvd.nist.gov/
https://nvd.nist.gov/developers/start-here

Energy, grid, fuels, and infrastructure:

https://www.energy.gov/
https://www.energy.gov/newsroom
https://www.oe.netl.doe.gov/OE417_annual_summary.aspx
https://www.eia.gov/
https://www.eia.gov/opendata/
https://www.eia.gov/todayinenergy/
https://www.ferc.gov/news-events/news
https://www.nerc.com/news/Pages/default.aspx
https://www.bpa.gov/

Federal government, regulation, courts, Congress, executive actions:

https://www.whitehouse.gov/news/
https://www.whitehouse.gov/briefings-statements/
https://www.whitehouse.gov/presidential-actions/
https://www.federalregister.gov/
https://www.federalregister.gov/public-inspection/current
https://www.federalregister.gov/developers/documentation/api/v1
https://www.federalregister.gov/reader-aids/developer-resources/rest-api
https://www.govinfo.gov/
https://www.govinfo.gov/feeds
https://www.congress.gov/
https://api.congress.gov/
https://github.com/LibraryOfCongress/api.congress.gov/
https://www.loc.gov/apis/additional-apis/congress-dot-gov-api/
https://www.supremecourt.gov/
https://www.supremecourt.gov/opinions/slipopinion/25
https://www.uscourts.gov/
https://www.uscourts.gov/rss-feeds
https://www.justice.gov/news

Economic releases and national indicators:

https://www.bls.gov/
https://www.bls.gov/bls/newsrels.htm
https://www.bls.gov/bls/api_features.htm
https://www.bls.gov/developers/home.htm
https://www.bea.gov/
https://www.bea.gov/news
https://www.bea.gov/resources/for-developers
https://apps.bea.gov/API/signup/
https://fred.stlouisfed.org/
https://fred.stlouisfed.org/docs/api/fred/
https://www.federalreserve.gov/newsevents.htm
https://www.federalreserve.gov/data.htm
https://www.federalreserve.gov/data/data-download-fred-information.htm
https://home.treasury.gov/news/press-releases
https://home.treasury.gov/policy-issues/financial-sanctions/recent-actions
https://fiscaldata.treasury.gov/
https://fiscaldata.treasury.gov/api-documentation/
https://www.census.gov/data/developers.html
https://www.census.gov/newsroom.html

National news, public media, wires, nonprofit journalism:

https://apnews.com/
https://apnews.com/hub/us-news
https://www.reuters.com/world/us/
https://www.npr.org/
https://www.npr.org/rss/
https://www.pbs.org/newshour/
https://www.pbs.org/newshour/feeds/rss/headlines
https://www.cbsnews.com/latest/rss/main
https://abcnews.go.com/US
https://abcnews.go.com/abcnews/usheadlines
https://www.nbcnews.com/
https://feeds.nbcnews.com/nbcnews/public/news
https://www.cnn.com/
https://www.cnn.com/services/rss/
https://www.foxnews.com/
https://moxie.foxnews.com/google-publisher/latest.xml
https://www.usatoday.com/news/
https://rssfeeds.usatoday.com/usatoday-NewsTopStories
https://www.propublica.org/
https://www.propublica.org/feeds
https://www.theguardian.com/us-news
https://www.theguardian.com/us-news/rss
https://www.bbc.com/news/world/us_and_canada
https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml

National social/community candidates, policy-sensitive:

https://www.reddit.com/r/news/
https://www.reddit.com/r/politics/
https://www.reddit.com/r/weather/
https://www.reddit.com/r/TropicalWeather/
https://www.reddit.com/r/aviation/
https://www.reddit.com/r/sysadmin/
https://www.reddit.com/r/cybersecurity/
https://www.reddit.com/r/economics/
https://x.com/NWS
https://x.com/NHC_Atlantic
https://x.com/fema
https://x.com/CDCgov
https://x.com/US_FDA
https://x.com/USCPSC
https://x.com/NHTSAgov
https://x.com/CISAgov
https://x.com/FAANews
https://x.com/USGS_Quakes
https://x.com/WhiteHouse
https://x.com/FederalRegister
https://bsky.app/search?q=United%20States%20breaking%20news
https://bsky.app/search?q=NWS%20warning
https://bsky.app/search?q=FAA%20ground%20stop
https://bsky.app/search?q=FDA%20recall
https://bsky.app/search?q=CISA%20advisory
https://bsky.app/search?q=USGS%20earthquake

Source policy references:

https://www.rfc-editor.org/rfc/rfc9309.html
https://www.rssboard.org/rss-specification
https://www.sitemaps.org/protocol.html
https://schema.org/NewsArticle
https://redditinc.com/policies/developer-terms
https://redditinc.com/policies/data-api-terms
https://docs.x.com/x-api/introduction
https://docs.bsky.app/docs/api/at-protocol-xrpc-api

SECTION 5: Source admission tiers

Design source tiers.

Tier 0:
- Local fixtures only.
- No network.
- Used for tests.

Tier 1:
- Official APIs, official open data, RSS/Atom, CAP feeds, GeoJSON feeds, hydrology APIs, recall APIs, federal register APIs, official agency JSON endpoints, and official government RSS.
- Best first live candidates.

Tier 2:
- Official pages with stable public operational data but no obvious feed/API.
- Candidate only after source-policy review.
- Prefer source-health checks and manual review before parser implementation.

Tier 3:
- National news RSS or publisher-provided feeds.
- Store headline metadata only.
- No article-body archive.
- No paywall bypass.

Tier 4:
- Public media, nonprofit outlets, and specialist topic outlets.
- Prefer RSS/Atom.
- Store headline metadata only.
- Respect robots and terms.

Tier 5:
- Social/community signals.
- Policy-sensitive.
- Disabled by default.
- Reddit only through compliant official API or permitted feed access.
- X/Twitter only through official API access if explicitly configured.
- Bluesky may be explored through official AT Protocol later.
- No HTML scraping to bypass platform restrictions.

Tier 6:
- Unofficial aggregators and dashboards.
- Useful as human comparison or source-health reference.
- Do not treat as primary authority over official sources.
- Do not clone their work or scrape aggressively.
- If used later, source-health-only or manual-review-only unless policy review supports more.

SECTION 6: NATIONAL event model

Design a NATIONAL event model that sits above raw items.

The system should not only store "news items." It should infer that multiple recent items refer to the same national event.

Propose a future national_events table or explain how news_clusters should be extended.

A NATIONAL event should have:

- national_event_id
- scope
- event_key
- event_type
- title
- representative_item_id
- severity
- public_impact_score
- source_diversity_score
- official_confirmation_score
- social_echo_score
- news_echo_score
- emergency_score
- weather_hazard_score
- disaster_score
- public_health_score
- recall_score
- transport_impact_score
- aviation_impact_score
- cyber_impact_score
- economic_impact_score
- regulatory_impact_score
- federal_civic_score
- first_seen_at
- last_seen_at
- last_elevated_at
- expires_at
- geography_json
- states_json
- agencies_json
- corridors_json
- source_ids_json
- item_ids_json
- evidence_json
- ranking_explanation_json
- status

Event types should include at least:

- national_emergency_alert
- federal_disaster_declaration
- severe_weather_outbreak
- hurricane_watch_warning
- tornado_outbreak
- wildfire_national
- smoke_air_quality_national
- flood_national
- drought_national
- earthquake_national
- tsunami_national
- volcano_unrest
- public_health_alert
- disease_outbreak
- food_recall
- drug_device_recall
- consumer_product_recall
- vehicle_recall
- aviation_ground_stop
- airport_national_disruption
- rail_disruption
- major_transport_disruption
- cyber_advisory
- known_exploited_vulnerability
- emergency_directive
- energy_grid_disruption
- federal_regulatory_action
- executive_action
- congressional_action
- court_decision
- economic_release
- sanctions_action
- major_national_news
- community_signal
- source_health_problem

Make clear that routine low-impact national news should not automatically become elevated NATIONAL events.

SECTION 7: Cross-source convergence ranking

Design deterministic ranking around this idea:

If something appears in official sources, national news, agency feeds, transport feeds, public-health feeds, cyber feeds, recall sources, and community/social signals within a short window, it is probably important or interesting.

Implement this as design only.

Do not design an LLM summarizer.

The scoring model must be explainable.

Required scoring factors:

1. Official severity

Examples:

- NWS warning or severe weather outbreak.
- National Hurricane Center watch or warning.
- FEMA disaster declaration or major response update.
- DHS NTAS bulletin or official homeland-security alert.
- CDC HAN health alert.
- FDA major recall or Class I recall.
- FSIS public health alert or recall.
- CPSC consumer recall with injury/death risk.
- NHTSA vehicle safety recall with broad impact.
- CISA Known Exploited Vulnerability addition.
- CISA emergency directive or high-impact advisory.
- FAA ground stop, ground delay, airport closure, or nationwide NAS issue.
- USGS earthquake above configured magnitude or felt across multiple states.
- NIFC or InciWeb large wildfire with evacuation or smoke impact.
- Federal Register rule/action from a high-impact agency.
- BLS/BEA/Fed/Treasury economic release that is scheduled and high-salience.

2. Source diversity

Independent source families count more than repeated mentions from the same family.

Example families:

- fema
- dhs
- nws
- noaa_spc
- noaa_nhc
- noaa_wpc
- noaa_nwm
- usgs
- cdc
- fda
- fsis
- cpsc
- nhtsa
- faa
- dot
- cisa
- nist
- fbi
- doe
- eia
- ferc
- treasury
- federal_reserve
- bls
- bea
- census
- federal_register
- congress
- govinfo
- supreme_court
- national_wire
- public_media
- national_tv
- nonprofit_news
- reddit
- bluesky
- x_api
- source_health

3. Temporal proximity

Items closer in time are more likely to be the same event.

Propose matching windows:

- Breaking national news: 0 to 24 hours.
- Weather outbreak: active alert duration or 0 to 48 hours.
- Hurricane: active advisory cycle or 0 to 7 days.
- Wildfire/smoke: 0 to 72 hours, longer only if active.
- Earthquake/tsunami: 0 to 24 hours, with aftershock clustering.
- Public health alert: 0 to 14 days.
- Recall: 0 to 30 days, but attention should decay unless high severity or newly updated.
- Cyber advisory/KEV: 0 to 14 days, with high-severity items staying visible while active.
- FAA/transport disruption: 0 to 12 hours, active event duration, or 0 to 24 hours.
- Economic release: release day plus 24 hours unless follow-up coverage converges.
- Federal regulatory/civic action: 0 to 72 hours unless active public comment or immediate public impact exists.

4. Geographic proximity and reach

Match by:

- United States national flag
- state
- territory
- region
- FEMA region
- NWS region
- storm basin
- affected airports
- affected states
- affected product distribution area
- affected industry
- affected federal agency
- affected infrastructure sector
- affected population group
- court/federal jurisdiction
- national or multi-state label

5. Public impact

Boost:

- official emergency alerts
- disaster declarations
- hurricane/tornado/severe weather warnings
- nationwide or multi-state aviation disruption
- high-risk recalls
- public health warnings
- widespread cyber threats
- energy/grid disruptions
- major transport closures
- federal rules with immediate public effect
- Supreme Court/court decisions with immediate national effect
- economic releases with broad public salience
- sanctions or foreign policy actions with direct domestic impact
- national security advisories
- multi-source national news convergence

6. Recency

Recent items matter more, but older active hazards can stay elevated while still active.

7. User-configured priority

Allow future config to boost:

- weather
- hurricane
- aviation
- cyber
- recalls
- public health
- FDA
- CDC
- CISA
- NWS
- FAA
- transportation
- energy
- economy
- courts
- Congress
- federal regulations
- Pacific Northwest impact
- Seattle impact
- Washington impact

8. Low-public-value penalty

De-emphasize:

- routine agency press releases
- generic political messaging
- minor personnel announcements
- single-source punditry
- duplicate syndicated stories
- local stories with no national impact
- vague social-only reports
- economic data releases not on the configured attention list
- routine court filings with no public impact
- press releases that only announce grants unless tied to emergency/disaster response

The design must include a sample scoring formula.

Example:

score =
  recency_score
  + official_severity_score
  + source_diversity_score
  + public_impact_score
  + geographic_reach_score
  + active_alert_score
  + source_priority_score
  + cluster_size_score
  + local_or_regional_impact_score
  - duplicate_family_penalty
  - stale_source_penalty
  - low_confidence_penalty
  - low_public_value_penalty
  - out_of_scope_penalty

The design must explain that "frequency of appearance" means independent cross-source convergence, not raw duplicate counts.

Bad ranking:

- 30 syndicated versions of the same political article dominate.

Good ranking:

- FAA national ground stop.
- FAA/NAS official status confirms.
- Major airports show active events.
- National news and local airport feeds converge.
- Social chatter appears only as a low-weight echo if compliant.
- All within a plausible time window.

SECTION 8: NATIONAL source category design

Design source categories.

Each category must have:

- why it exists
- first safe sources
- parser/adaptor class
- likely refresh interval
- privacy risk
- policy risk
- source-health signals
- sample item fields
- how it contributes to ranking
- later implementation phase

Categories:

1. National emergency and disaster.

2. Weather, hurricane, flood, fire weather, and drought.

3. Wildfire, smoke, and national air quality.

4. Earthquake, tsunami, and volcano.

5. Public health, disease, food safety, recalls, and consumer safety.

6. Transportation, aviation, rail, ports, and national travel.

7. Cybersecurity and critical infrastructure.

8. Energy, grid, fuels, and infrastructure.

9. Federal government, regulatory, courts, Congress, and executive actions.

10. Economic releases and national indicators.

11. National news, public media, wires, and nonprofit journalism.

12. Social/community echoes.

13. Source health and disabled states.

SECTION 9: NATIONAL public-safety and privacy posture

Design this carefully.

Rules:

- Store source-provided public metadata only.
- Do not store full narratives beyond bounded descriptions.
- Do not archive social posts long term.
- Do not surface private individual data.
- Preserve source links in evidence so the user can click official sources.
- For major incidents, show public operational facts:
  event type, source, source family, affected states/agencies/sectors, public impact, observed time, source link.
- Treat early official reports as preliminary where applicable.
- Do not turn NATIONAL into a fear dashboard.
- Do not turn NATIONAL into a partisan outrage dashboard.
- Low-public-value political churn should be background pulse or ignored unless it has official, legal, emergency, economic, or public-impact significance.
- Social-only national claims should never outrank official alerts.

SECTION 10: NATIONAL source freshness and retention

Design short retention.

Default candidate retention:

- Raw fetch diagnostics: 7 days or less.
- Raw payload debug: disabled by default. If ever enabled, 6 hours max by default.
- Official alert metadata: expiration plus 24 hours.
- Weather/hazard metadata: expiration plus 24 to 48 hours.
- Hurricane/advisory metadata: active storm plus 7 days.
- Wildfire/smoke metadata: 7 to 14 days while active, then expire.
- Earthquake metadata: 7 days for significant U.S. events, 14 days for major events.
- Volcano unrest metadata: 14 days while active, official-only.
- Recall metadata: 14 to 30 days, with high-severity recalls allowed to remain visible as active if source says active.
- Public health alert metadata: 14 to 30 days depending on source expiration and severity.
- Cyber advisory metadata: 14 to 30 days, with KEV items visible according to due date or configured active window.
- FAA/transport disruption metadata: 3 to 7 days.
- Economic release metadata: 3 to 7 days.
- Federal Register/civic metadata: 7 days unless active public-comment/action window is explicitly tracked.
- News headline metadata: 7 days.
- National event clusters: 7 to 14 days.
- Source health: 30 days.
- Ranking explanations: same as event/item retention.
- Social metadata, if ever enabled: 24 to 72 hours unless source terms require shorter or prohibit storage.

Every ingest run in later phases must purge expired data.

No article body archive.

No permanent national incident archive.

No permanent social archive.

SECTION 11: Adapter design for NATIONAL

Design future adapter families.

Do not implement now.

Required adapter families:

rss_atom:
- Federal agency RSS feeds.
- National news/public media feeds.
- CPSC RSS.
- FDA RSS if verified.
- GovInfo feeds.
- Court or agency feeds where available.
- Must parse title, URL, published timestamp, description, categories.
- Must bound description length.
- Must not fetch article bodies.

official_api_json:
- NWS active alerts.
- FDA, CISA, FAA, EIA, NHTSA, FEMA/OpenFEMA, and other official JSON endpoints where verified.
- Must support timeouts, response size caps, source-specific rate limits, and conditional requests when available.

cap_alerts:
- NWS CAP/API alert records if useful.
- Must preserve severity, urgency, certainty, effective time, expiration, area, and instruction URL.

geojson_feed:
- USGS earthquake GeoJSON.
- Possible wildfire or federal geospatial feeds if verified.
- Must support region filters, magnitude filters, hazard filters, and source provenance.

hydrology_api_json:
- USGS water services and NOAA water candidates if verified.
- Must support gauge allowlists and national/regional filters.

recall_api_json:
- FSIS Recall API.
- CPSC Recalls API.
- NHTSA recalls APIs.
- FDA recall data only after endpoint verification.
- Must preserve recall class, product, firm, hazard, distribution scope, date, and official URL.

federal_register_api:
- Federal Register API.
- Public inspection current documents.
- Must support agency allowlist, document type allowlist, and high-impact filters.
- Must not flood dashboard with routine notices.

congress_api_candidate:
- Congress.gov API requires an API key.
- Disabled by default.
- Must treat auth/key handling carefully.
- Must support bill/action filters and avoid becoming a general legislative firehose.

govinfo_rss:
- GovInfo RSS feeds for collections.
- Must be allowlisted and filtered.

economic_api_json:
- BLS API.
- BEA API.
- FRED/Federal Reserve candidates.
- Treasury Fiscal Data API.
- Must support scheduled-release awareness and configured series allowlists.
- Must not provide investment advice.

aviation_status_json_or_xml:
- FAA NAS Status and airport status candidates.
- Must preserve active event type, airport, delay, ground stop/ground delay/closure, and observed time.

csv_download_candidate:
- Only for official CSV data with stable schema.
- Disabled by default until fixture tests exist.
- Must cap rows and support updated-since or short retention.

data_gov_catalog_candidate:
- Data.gov and agency catalogs only for discovery, not live dashboard ingestion.
- Manual review only unless a specific dataset is promoted.

arcgis_feature_service_candidate:
- Only if official federal/state feature services are discovered.
- Do not screen scrape dashboards.

static_html_headline_candidate:
- Only for official pages or national news pages with no RSS/API.
- Disabled unless homepage extractor support is explicitly allowed.
- Must use per-source selectors.
- No recursive crawling.
- No article-body fetch.
- Robots/policy review required.

source_health_probe_only:
- For dashboards and portals useful as human status references but not suitable for ingestion.

manual_review_only:
- For policy-sensitive, parser-risky, login-required, auth-required, or unclear targets.

SECTION 12: Candidate national source registry example

Include a YAML-like example in the design document.

Do not edit config.example.yml yet unless prior architecture already requires disabled examples.

The example must be disabled by default.

Example shape:

national_sources:
  enabled: false
  label: "United States"
  retention:
    official_alert_days: 7
    weather_hazard_days: 7
    hurricane_days: 14
    public_health_days: 30
    recall_days: 30
    cyber_days: 30
    transport_days: 7
    economic_release_days: 7
    headline_days: 7
    event_cluster_days: 14
    source_health_days: 30
    raw_payload_debug_enabled: false
    raw_payload_debug_ttl_hours: 6
  ranking:
    source_diversity_weight: 3.0
    official_severity_weight: 3.25
    public_impact_weight: 3.0
    geographic_reach_weight: 2.5
    recency_weight: 2.0
    social_echo_weight: 0.4
    low_public_value_penalty_weight: 3.0
    out_of_scope_penalty_weight: 3.0
  privacy:
    suppress_private_individual_details: true
    social_retention_hours: 48
    social_sources_disabled_by_default: true
  relevance:
    include_state_events_when_national_impact: true
    local_impact_tags:
      - "Seattle"
      - "Washington"
      - "Pacific Northwest"
  sources:
    - id: nws_active_alerts_us
      enabled: false
      source_family: nws
      source_class: official_weather_hazard
      adapter: official_api_json
      url: "https://api.weather.gov/alerts/active"
      priority: 100
      interval_minutes: 10
      verification_status: official_page_seen
      evidence_notes: "Use NWS API metadata and alert expiration."

    - id: nhc_atlantic_rss
      enabled: false
      source_family: noaa_nhc
      source_class: official_hurricane
      adapter: rss_atom
      homepage_url: "https://www.nhc.noaa.gov/"
      url: "https://www.nhc.noaa.gov/aboutrss.shtml"
      priority: 95
      interval_minutes: 10
      verification_status: candidate_needs_verification
      notes: "Verify actual feed endpoints before ingest."

    - id: usgs_eq_geojson_us
      enabled: false
      source_family: usgs
      source_class: official_seismic_volcano
      adapter: geojson_feed
      url: "https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php"
      priority: 90
      interval_minutes: 5
      verification_status: official_page_seen
      filters:
        min_magnitude: 5.0
        region_hint: "United States"

    - id: cisa_kev
      enabled: false
      source_family: cisa
      source_class: official_cybersecurity
      adapter: official_api_json
      homepage_url: "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
      priority: 95
      interval_minutes: 60
      verification_status: official_page_seen
      notes: "Later phase must verify machine-readable endpoint or CSV/JSON source."

    - id: fda_recalls
      enabled: false
      source_family: fda
      source_class: official_recall
      adapter: rss_atom
      homepage_url: "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts"
      priority: 90
      interval_minutes: 60
      verification_status: official_page_seen
      notes: "Verify RSS/API path before implementation. Store metadata only."

    - id: fsis_recall_api
      enabled: false
      source_family: fsis
      source_class: official_food_safety
      adapter: recall_api_json
      homepage_url: "https://www.fsis.usda.gov/science-data/developer-resources/recall-api"
      priority: 90
      interval_minutes: 60
      verification_status: official_page_seen

    - id: faa_nas_status
      enabled: false
      source_family: faa
      source_class: official_aviation
      adapter: aviation_status_json_or_xml
      homepage_url: "https://nasstatus.faa.gov/"
      url: "https://nasstatus.faa.gov/api/airport-status-information"
      priority: 95
      interval_minutes: 5
      verification_status: official_page_seen

    - id: federal_register_public_inspection
      enabled: false
      source_family: federal_register
      source_class: official_regulatory
      adapter: federal_register_api
      homepage_url: "https://www.federalregister.gov/public-inspection/current"
      url: "https://www.federalregister.gov/developers/documentation/api/v1"
      priority: 65
      interval_minutes: 120
      verification_status: official_page_seen
      filters:
        document_types:
          - "Rule"
          - "Proposed Rule"
          - "Presidential Document"
        agency_allowlist: []
      notes: "Low default priority unless high-impact agency/action filter matches."

SECTION 13: NATIONAL UI architecture

Design the eventual NATIONAL page.

Do not implement it.

The NATIONAL page should use the same console style.

Propose four bays.

Bay 1:
- "National attention now"
- Highest-ranking NATIONAL events.
- Must show why each item is ranked.
- Must show source-family badges.
- Must show official vs news vs community convergence.
- Must show observed time and last seen.
- Must not dump low-impact political churn.

Bay 2:
- "Official alerts and hazards"
- FEMA, DHS, NWS, NOAA, NHC, SPC, USGS, CDC, FDA, FSIS, CPSC, NHTSA, CISA, FAA, and similar.
- Show active official alerts first.
- Show source freshness.
- Show active severe weather, hurricane, recall, cyber, public-health, aviation, and emergency alerts.

Bay 3:
- "Systems and infrastructure"
- Aviation, cyber, transportation, energy, economic releases, Federal Register, Congress/courts if enabled.
- Useful for "will this affect national systems, travel, services, software/security, markets, or government operations?"

Bay 4:
- "National press and civic pulse"
- AP, Reuters, NPR, PBS, major national broadcasters, nonprofit journalism, and future configured sources.
- Social/community signals only if configured and compliant.
- No fake headlines.
- If disabled, show "NATIONAL news sources not configured."

Each row should show:

- title
- event type
- source or representative source
- source-family badges
- confidence/convergence count
- observed time
- last seen
- ranking reason
- evidence affordance
- geographic label, such as national, state, multi-state, affected airport, agency, sector, or region

Empty states:

- NATIONAL recent-signal layer disabled.
- NATIONAL sources not configured.
- NATIONAL sources configured but disabled.
- NATIONAL sources configured but never scanned.
- NATIONAL sources stale.
- NATIONAL source policy blocked.
- NATIONAL parser failed.
- NATIONAL social sources disabled by policy.
- NATIONAL homepage extraction disabled by policy.
- NATIONAL official API requires token and is not configured.

SECTION 14: Evidence model for NATIONAL

Every item/event must trace back to source evidence.

For a NATIONAL event, evidence should include:

- source ids
- source names
- source families
- source classes
- item URLs
- canonical URLs
- official source flags
- first seen
- last seen
- source published times
- fetch run ids
- parser names
- source health state
- ranking features
- geographic reach basis
- public impact basis
- source diversity basis
- retention expiration
- matching tokens
- event type
- event confidence
- policy notes
- low-public-value penalty if applied
- out-of-scope penalty if applied

For hazard events, evidence must also include, where available:

- alert severity
- urgency
- certainty
- effective time
- expiration time
- affected zones
- affected states
- storm name
- hurricane advisory number
- tornado/severe weather watch number
- wildfire name
- fire size
- containment
- evacuation level
- AQI station or region
- drought category
- earthquake magnitude
- earthquake depth
- tsunami status
- volcano alert level
- source instructions URL

For public health and recall events, evidence must include, where available:

- alert type
- issuing agency
- product
- firm
- recall class
- hazard
- affected distribution geography
- public instruction URL
- outbreak name or pathogen if source provides it
- effective/update date
- expiration or active status
- whether the source says the information is preliminary

For cyber events, evidence must include, where available:

- advisory id
- CVE ids
- product/vendor
- KEV due date if applicable
- severity if provided
- exploited-in-the-wild flag if provided
- mitigation URL
- emergency directive flag if applicable

For transport/aviation events, evidence must include, where available:

- airport
- route
- system
- event type
- delay estimate
- closure status
- ground stop or ground delay status
- start time
- end time
- source update time

SECTION 15: Source health for NATIONAL

Design source health states.

Required states:

- disabled
- not_configured
- configured_never_run
- healthy
- stale
- failing
- parser_failed
- policy_blocked
- robots_blocked
- auth_required
- rate_limited
- unsupported
- manual_review_only

Source health must be visible in SYSTEM later and summarized in NATIONAL Bay 4 or a footer strip.

Each source health row should have:

- source_id
- state
- last_attempt_at
- last_success_at
- last_failure_at
- next_eligible_fetch_at
- consecutive_failures
- last_http_status
- item_count_last_success
- stale_after_minutes
- message
- evidence_json

SECTION 16: First implementation sequence for NATIONAL

Design future phases.

Phase U0: this design
- Create design doc.
- Update BACKLOG.
- No runtime behavior change.

Phase U1: source registry scaffolding
- Add disabled NATIONAL source config.
- Add source registry schema or tables if not already done by global architecture.
- Add tests proving NATIONAL disabled by default.
- No network.

Phase U2: local fixtures only
- Create fixture files for:
  NWS active alert JSON.
  NHC RSS or advisory fixture.
  USGS earthquake GeoJSON fixture.
  CDC HAN fixture.
  FDA recall fixture.
  FSIS Recall API fixture.
  CPSC recall API fixture.
  NHTSA recall fixture.
  CISA advisory fixture.
  CISA KEV fixture.
  FAA NAS status fixture.
  Federal Register API fixture.
  BLS release fixture.
  AP/NPR/PBS RSS fixture.
- Parse fixtures only.
- Store normalized metadata.
- No live fetch.

Phase U3: NATIONAL event correlation
- Deterministic token/location/time/source-family matching.
- No LLM.
- Tests for convergence.
- Tests for duplicate suppression.
- Tests for source-family diversity.
- Tests for national vs regional vs local scope routing.

Phase U4: NATIONAL ranking
- Implement scoring model.
- Explain ranking in JSON.
- Tests for official severity, source diversity, recency, public impact, low-public-value penalty, stale-source penalty, and out-of-scope penalty.

Phase U5: NATIONAL UI disabled and fixture-backed states
- Replace NATIONAL placeholders with honest states.
- Fixture-backed in tests only.
- No live fetch.
- No fake headlines.

Phase U6: official API/RSS live fetch, opt-in only
- Start with one safe official source.
- Suggested first candidates:
  NWS active alerts.
  USGS earthquake GeoJSON.
  CISA advisories or KEV if machine-readable endpoint verified.
  FSIS Recall API.
  FAA NAS status if endpoint behavior is verified.
- Must be disabled by default.
- Must use explicit command.
- No page-load fetch.

Phase U7: additional official sources
- FDA recall feed/API after endpoint verification.
- CPSC recalls API.
- NHTSA recalls API.
- FEMA/OpenFEMA disaster declarations.
- Federal Register API with filters.
- BLS/BEA/FRED only after indicator allowlists are designed.

Phase U8: national news RSS
- Publisher feeds only.
- Store metadata only.
- No article bodies.
- No paywall bypass.

Phase U9: official dashboards and HTML research
- DHS/NTAS, FEMA, NIFC, FAA, and other official pages only through official feeds/APIs if found.
- Homepage extraction only after explicit policy review.
- No broad page scraping.

Phase U10: social/community
- Bluesky AT Protocol candidate.
- Reddit official API candidate.
- X official API only if explicitly configured.
- No HTML scraping.
- Short retention.
- Disabled by default.

SECTION 17: Testing strategy

Design tests.

Required tests:

Config:
- NATIONAL disabled by default.
- Source disabled by default.
- Invalid source class rejected.
- Invalid adapter rejected.
- Social source rejected unless allow_social_sources true.
- Homepage extraction rejected unless allow_homepage_extractors true.
- Congress.gov API source marked auth_required unless key source configured.
- BEA/FRED keyed sources marked auth_required unless key source configured.
- Source without URL rejected unless adapter supports no URL.
- Secrets not allowed in config.example.yml.

Registry:
- Source keys unique.
- Source family valid.
- Source class valid.
- Verification status valid.
- Retention settings valid.
- Geography filters valid.
- Agency filters valid.
- Sector filters valid.

Parser fixture tests:
- NWS alert JSON fixture parses.
- NHC advisory fixture parses.
- USGS earthquake GeoJSON fixture parses.
- CDC HAN fixture parses.
- FDA recall fixture parses.
- FSIS Recall API fixture parses.
- CPSC recall API fixture parses.
- NHTSA recall fixture parses.
- CISA advisory fixture parses.
- CISA KEV fixture parses.
- FAA NAS status fixture parses.
- Federal Register API fixture parses.
- Economic release fixture parses.
- National news RSS fixture parses.
- Malformed feed fails soft.
- Oversized payload blocked or truncated.

Privacy and low-public-value tests:
- Routine agency press release does not elevate to NATIONAL attention.
- Social-only vague report does not outrank official alert.
- Routine political messaging gets low-public-value penalty.
- Public-health alert shows official source and action URL, not invented advice.
- Economic data release does not become advice.
- Court/congress item does not elevate unless configured and public-impact threshold is met.

Correlation tests:
- FAA NAS event plus national news plus airport local impact becomes one event.
- NWS severe weather outbreak plus FEMA/disaster news plus national news becomes one event.
- FDA recall plus FSIS/CPSC/NHTSA source family distinctions do not merge unrelated recalls.
- CISA KEV plus advisory plus national news becomes one cyber event.
- Same event from multiple news outlets counts as news-family convergence but not endless duplicate inflation.
- Same source repeated does not inflate source diversity.
- Different source families increase diversity.
- Local/regional item without national impact does not appear in NATIONAL.
- Global item without U.S. impact does not appear in NATIONAL.

Ranking tests:
- Official severe weather warning outranks generic news.
- Major FAA ground stop outranks generic airport article.
- CDC HAN alert outranks generic health article.
- FDA/FSIS/CPSC high-risk recall outranks routine agency press release.
- CISA KEV addition outranks generic tech headline.
- Major federal disaster declaration outranks routine FEMA grant press release.
- Stale source lowers confidence.
- Source policy blocked item never displays as live.

API design tests for later:
- GET routes read SQLite only.
- GET routes do not fetch network.
- Disabled/not configured/stale/failing/auth_required states distinct.

UI tests for later:
- No fake headlines.
- Empty states clear.
- Evidence visible.
- Ranking reason visible.
- Source health visible.
- National/state/agency/sector label visible.

Safety tests:
- No page-load external fetches.
- No hidden LLM calls.
- No telemetry.
- No package install.
- No sudo.
- No social fetch unless explicitly configured.
- No API-key source runs without key configuration.

SECTION 18: Backlog update requirements

Update BACKLOG.md.

Add a section named:

NATIONAL United States Recent Signal Layer

Add concrete backlog items with Status: not implemented.

Include at least:

- NATIONAL source registry design implemented from document.
- Disabled-by-default NATIONAL config.
- NATIONAL SQLite schema or extension.
- NATIONAL fixture pack.
- NWS active alert parser.
- NHC advisory/feed verification.
- USGS earthquake GeoJSON parser.
- FEMA/OpenFEMA disaster declarations research.
- CDC HAN parser.
- FDA recall endpoint/feed verification.
- FSIS Recall API parser.
- CPSC Recalls API parser.
- NHTSA Recalls API parser.
- FAA NAS status fixture parser.
- CISA advisory parser.
- CISA KEV endpoint research.
- Federal Register API parser with filters.
- GovInfo RSS parser.
- Congress.gov API design, disabled and auth-required.
- BLS/BEA/FRED/Treasury economic source allowlist design.
- National news RSS parser.
- NATIONAL deterministic event correlation.
- NATIONAL deterministic ranking.
- NATIONAL low-public-value and public-impact rules.
- NATIONAL UI disabled states.
- NATIONAL source health states.
- NATIONAL evidence drawer contract.
- NATIONAL official-source live ingest phase, disabled by default.
- NATIONAL news RSS ingest phase, disabled by default.
- NATIONAL social source policy review, disabled by default.
- Documentation for source verification.
- Tests for no page-load external fetches.
- Tests for no API-key source running without config.

SECTION 19: Non-goals

List non-goals.

Required:

- No live fetch in this task.
- No collector implementation in this task.
- No UI implementation in this task.
- No general crawler.
- No page-load fetch.
- No hidden LLM summarization.
- No full article archive.
- No permanent incident archive.
- No private data collection.
- No stock trading advice.
- No investment advice.
- No medical advice.
- No legal advice.
- No political outrage feed.
- No scraping behind login.
- No bypassing Reddit/X/API restrictions.
- No claiming social chatter is verified fact.
- No treating unofficial aggregators as official.
- No treating duplicate articles as independent confirmation.
- No burying LOCAL or SYSTEM urgent items under NATIONAL headlines.
- No importing GLOBAL content unless U.S. national relevance rules allow it.
- No automatic API key discovery or secret storage.

SECTION 20: Final response requirements

Before final response, run:

pwd
git status --short
git diff --name-only
git diff --check
pytest -q

Expected pytest may still be:

37 passed, 1 failed

If the known timestamp test is still the only failure, say so exactly.

If any other test fails, stop and explain.

The final response must include:

1. Files changed.
2. Confirmation that no application code was changed, unless it was.
3. Confirmation that no external network fetches were added.
4. Confirmation that no dependencies were added.
5. Confirmation that no collectors were implemented.
6. Confirmation that NATIONAL remains disabled by default.
7. Test commands run and exact results.
8. git diff --check result.
9. git status --short.
10. BACKLOG entries added.
11. Uncertainties and source targets needing later verification.

Do not commit.

Do not push.

Do not install packages.

Do not run sudo.

Do not fetch live external sites.

Do not run curl against source targets for this task.
```

This one is intentionally broader than LOCAL and REGIONAL because NATIONAL needs hard filters against becoming a politics/news sludge pump. The strongest design guardrail is the low-public-value penalty: official alerts, recalls, cyber, FAA/NWS/FEMA/CDC/FDA/CISA type signals rise; duplicate punditry and ordinary press churn sink.

[1]: https://www.weather.gov/documentation/services-web-api?utm_source=chatgpt.com "API Web Service"
