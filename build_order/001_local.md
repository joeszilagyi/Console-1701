You are working in the console-1706 repository.

This task assumes the previous architecture prompt for scoped recent-signal/news ingestion has either already been run or will be pasted above this prompt. Treat that architecture as context, but do not assume it is already implemented.

This is a LOCAL scope architecture, source-target inventory, and ranking design task only.

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

Your job is to design the LOCAL Seattle recent-signal layer in enough detail that later Codex passes can implement it safely, source by source, without guessing.

The user’s intent:

The root page at http://127.0.0.1:1706/ will eventually become a local command surface. The LOCAL scope should answer, at a glance, what is happening in Seattle and the immediate area right now.

The LOCAL scope should eventually combine recent signals from:

- Seattle Fire Department public 911 data.
- Seattle Police Department public call data and significant incident reports.
- AlertSeattle and emergency management.
- SDOT, WSDOT, traffic, roads, bridges, ferries, and transit sources.
- Seattle City Light outages and utility disruptions.
- SEA Airport and Port of Seattle operational notices.
- Weather, air quality, smoke, earthquake, flood, and hazard feeds.
- Seattle Open Data and official city datasets.
- Local neighborhood blogs and local news outlets.
- Community/social signals only when accessible through compliant, explicitly configured methods.
- Source health and freshness data.

The goal is not to mirror every source forever. The goal is a short-retention, local, evidence-backed, deterministic "what is going on" dashboard.

The daily runtime goal is no LLM usage. LLMs may be used at development time to design adapters, inspect fixture structure, write tests, or analyze source options, but the application itself must not require LLM calls for normal operation.

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

   docs/project/LOCAL_SEATTLE_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md

   Create docs/project if it does not exist.

2. Update BACKLOG.md with concrete future implementation tasks flowing from this LOCAL design.

3. Do not touch application code unless absolutely necessary. This should normally be docs plus BACKLOG only.

4. Do not perform live source verification. The source links below are seed targets. Classify them as candidate links and design how they should be verified in a later phase.

5. The final response must prove what changed and what did not change.

The design document must include the following sections.

SECTION 1: Purpose

Explain the LOCAL scope in plain engineering language.

The LOCAL scope is the Seattle recent-signal layer. It should tell the user what is happening locally, with source provenance, observed time, source kind, ranking reason, and evidence.

It is not:

- A police scanner clone.
- A fire scanner clone.
- A local news scraper.
- A permanent archive.
- A general Seattle search engine.
- A social media monitoring system.
- A crime dashboard.
- A system for amplifying every medical aid call.
- A source of emergency instructions beyond linking to official sources.
- A hidden LLM summarizer.
- A cloud service.

It is:

- A local, short-retention metadata dashboard.
- A deterministic cross-source event detector.
- A source-health aware recent-signal system.
- A LOCAL tab in console-1706 that can surface official alerts, incidents, travel disruptions, outages, hazards, airport/port operations, local news, and compliant community signals.
- A way to rank items by independent source convergence, official severity, local impact, freshness, and user-configured source priority.

Make clear that "all there is to know about Seattle" means all useful public, configured, lawful, recent signals that the user chooses to enable. It does not mean unbounded crawling or private data collection.

SECTION 2: Local scope boundaries

Define LOCAL geography.

Default LOCAL scope:

- Seattle city proper.
- SEA Airport because it is regionally critical and operationally tied to Seattle life.
- Port of Seattle because port/airport/maritime disruptions matter locally.
- King County Metro and Sound Transit only as they affect Seattle service.
- WSDOT and Washington State Ferries only as they affect Seattle corridors, ferries, bridges, passes, routes, or regional access.
- Weather/hazard feeds only for Seattle, King County, Puget Sound, and immediate surrounding hazard zones.
- Air quality and smoke for Seattle, King County, Puget Sound, and nearby relevant stations.
- Earthquakes only when within configured radius or above configured magnitude/severity.
- Local blogs and news outlets only when they meaningfully cover Seattle or Seattle neighborhoods.

Out of LOCAL by default:

- General Washington politics unless it has direct Seattle impact.
- Generic national stories.
- Generic global stories.
- Random social chatter not linked to Seattle.
- Full crime tracking beyond public official data.
- Personal emergencies with no broader public impact.
- Exact private-location amplification when it adds no public value.
- Sources requiring login, payment, scraping around controls, or access tokens not explicitly configured by the user.

Design a later config escape hatch:

local:
  enabled: false
  default_place_label: "Seattle"
  include_airport: true
  include_port: true
  include_king_county_transit: true
  include_wsdot_seattle_corridors: true
  include_ferries: true
  hazard_radius_miles: 75
  earthquake_min_magnitude: 3.0
  allow_neighborhood_blogs: false
  allow_social_sources: false

SECTION 3: Seed source target inventory

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
- official_incident
- official_open_data
- official_transport
- official_utility
- official_airport_port
- official_weather_hazard
- official_air_quality
- official_school_civic
- local_news
- neighborhood_blog
- social_candidate
- unofficial_aggregator
- source_health_only

Use these adapter types:

- socrata_json
- arcgis_dashboard_research
- arcgis_feature_service_candidate
- rss_atom
- wordpress_feed_candidate
- static_html_headline_candidate
- official_api_json
- gtfs_realtime_alerts
- airport_status_json_or_xml
- local_file_fixture
- source_health_probe_only
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

Official emergency and public safety:

https://alert.seattle.gov/
https://www.seattle.gov/emergency-management/prepare/alert-seattle
https://alert.seattle.gov/feed/
https://web.seattle.gov/sfd/realtime911/
https://web.seattle.gov/sfd/realtime911/getRecsForDatePub.asp?action=Today&incDate=&rad1=des
https://data.seattle.gov/Public-Safety/Seattle-Real-Time-Fire-911-Calls/kzjm-xkqj
https://dev.socrata.com/foundry/data.seattle.gov/kzjm-xkqj
https://sfdlive.com/
https://www.seattle.gov/police/information-and-data/data/online-crime-maps
https://www.arcgis.com/apps/dashboards/3556b79ef2494b8c9bd7eeddaabea68f
https://data.seattle.gov/Public-Safety/Call-Data/33kz-ixgy
https://dev.socrata.com/foundry/data.seattle.gov/33kz-ixgy
https://spdblotter.seattle.gov/
https://spdblotter.seattle.gov/significant-incident-reports/
https://spdblotter.seattle.gov/category/incident-reports/
https://spdblotter.seattle.gov/category/statements-and-news-releases/news-releases/
https://spdblotter.seattle.gov/feed/

Seattle Open Data and platform docs:

https://data.seattle.gov/
https://data.seattle.gov/stories/s/Getting-Started-on-the-Open-Data-Portal/feq8-x3ti/
https://dev.socrata.com/
https://dev.socrata.com/docs/endpoints.html

Transportation, roads, cameras, bridges, WSDOT, ferries:

https://web.seattle.gov/travelers/
https://www.seattle.gov/transportation/permits-and-services/interactive-maps
https://sdotblog.seattle.gov/
https://sdotblog.seattle.gov/feed/
https://data.seattle.gov/Transportation/SDOT-GIS-Datasets/jyjy-n3ap
https://data.seattle.gov/dataset/Traffic-Cameras/mvth-ptq3
https://data-seattlecitygis.opendata.arcgis.com/datasets/traffic-cameras/api
https://wsdot.wa.gov/traffic/api/
https://wsdot.com/travel/real-time/
https://wsdot.com/travel/real-time/map/
https://wsdot.wa.gov/travel
https://wsdot.com/ferries/schedule/bulletin.aspx
https://wsdot.wa.gov/travel/washington-state-ferries
https://wsdot.wa.gov/travel/sign-wsdot-travel-alerts

Transit:

https://kingcounty.gov/en/dept/metro/rider-tools/service-advisories
https://kingcounty.gov/en/dept/metro/rider-tools/service-advisories/rss
https://kingcountymetro.blog/
https://kingcountymetro.blog/feed/
https://www.soundtransit.org/ride-with-us/service-alerts
https://www.soundtransit.org/help-contacts/business-information/open-transit-data-otd/otd-downloads

Utilities and outages:

https://www.seattle.gov/city-light/outages
https://scl.datacapable.com/map/
https://experience.arcgis.com/experience/66636c38766c4fb4aca16976d79b0527/page/Energy-Page---Seattle-Light-Outage-Map
https://www.seattle.gov/city-light/outages/outage-alerts
https://alert.seattle.gov/poweroutage/
https://www.seattle.gov/utilities
https://www.seattle.gov/utilities/construction-resources/records-vault/data-resources

Airport and port:

https://www.portseattle.org/
https://www.portseattle.org/news
https://www.portseattle.org/newsroom
https://www.portseattle.org/sea
https://www.portseattle.org/sea/flight-status
https://www.portseattle.org/actions/airport-traveler-updates
https://www.portseattle.org/page/traveler-updates-and-tips
https://www.portseattle.org/page/live-estimated-checkpoint-wait-times
https://www.portseattle.org/ThisWeekatSEA
https://www.fly.faa.gov/fly/flyfaa/flyfaaindex?ARPT=SEA&p=1
https://nasstatus.faa.gov/
https://nasstatus.faa.gov/api/airport-status-information
https://www.faa.gov/airport-status/SEA
https://github.com/Federal-Aviation-Administration/ASWS

Weather, hazards, air quality, earthquakes:

https://www.weather.gov/sew/
https://www.weather.gov/documentation/services-web-api
https://www.weather.gov/documentation/services-web-alerts
https://api.weather.gov/alerts/active
https://www.weather.gov/alerts
https://www.airnow.gov/
https://docs.airnowapi.org/
https://pscleanair.gov/27/Air-Quality
https://pscleanair.gov/rss.aspx
https://pscleanair.gov/sensormap
https://www.seattle.gov/wildfire-smoke-safety
https://wasmoke.blogspot.com/
https://earthquake.usgs.gov/
https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php

Schools, civic status, events:

https://www.seattleschools.org/alerts/
https://www.seattleschools.org/departments/transportation/inclement-weather-transportation-plan/
https://www.seattleschools.org/departments/safety-security/faq/
https://www.seattlecenter.com/events
https://www.seattlecenter.com/events/event-calendar
https://www.seattlecenter.com/events/featured-events
https://parkways.seattle.gov/
https://parkways.seattle.gov/feed/

Local news, radio, TV, local journalism, neighborhood blogs:

https://westseattleblog.com/
https://westseattleblog.com/feed/
https://westseattleblog.com/rss-2/
https://www.capitolhillseattle.com/
https://www.capitolhillseattle.com/feed/
https://www.capitolhillseattle.com/about-chs/
https://www.kuow.org/
https://www.kuow.org/podcasts/seattlenow
https://www.king5.com/rss
https://www.kiro7.com/homepage
https://www.kiro7.com/rss-snd/
https://komonews.com/
https://komonews.com/news/local
https://www.fox13seattle.com/
https://www.cascadepbs.org/news/
https://www.theurbanist.org/
https://www.seattlebikeblog.com/

Community/social candidates, policy-sensitive:

https://www.reddit.com/r/Seattle/
https://www.reddit.com/r/SeattleWA/
https://www.reddit.com/r/AskSeattle/
https://x.com/seattledot
https://x.com/SeattlePD
https://x.com/AlertSeattle
https://x.com/flySEA
https://x.com/kcmetroalerts
https://x.com/wsferries
https://bsky.app/search?q=Seattle

Source policy references:

https://www.rfc-editor.org/rfc/rfc9309.html
https://www.rssboard.org/rss-specification
https://www.sitemaps.org/protocol.html
https://schema.org/NewsArticle
https://redditinc.com/policies/developer-terms
https://redditinc.com/policies/data-api-terms
https://docs.x.com/x-api/introduction
https://docs.bsky.app/docs/api/at-protocol-xrpc-api

SECTION 4: Source admission tiers

Design source tiers.

Tier 0:
- Local fixtures only.
- No network.
- Used for tests.

Tier 1:
- Official APIs, official open data, RSS/Atom from official agencies.
- Best first live candidates.

Tier 2:
- Official HTML pages with stable public data but no obvious feed/API.
- Candidate only after source-policy review.
- Prefer source-health checks and manual review before parser implementation.

Tier 3:
- Local news RSS or publisher-provided feeds.
- Store headline metadata only.
- No article-body archive.
- No paywall bypass.

Tier 4:
- Neighborhood blogs.
- Valuable because they often beat large outlets for hyperlocal events.
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
- Unofficial aggregators.
- Example: SFD Live.
- Useful as a human comparison or secondary source-health reference.
- Do not treat as primary authority over official sources.
- Do not clone their work or scrape aggressively.
- If used later, source-health-only or manual-review-only unless policy review supports more.

SECTION 5: LOCAL event model

Design a LOCAL event model that sits above raw items.

The system should not only store "news items." It should also be able to infer that multiple recent items refer to the same local event.

Propose a future local_events table or explain how news_clusters should be extended.

A LOCAL event should have:

- local_event_id
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
- transport_impact_score
- utility_impact_score
- hazard_score
- airport_port_score
- first_seen_at
- last_seen_at
- last_elevated_at
- expires_at
- geography_json
- neighborhoods_json
- source_ids_json
- item_ids_json
- evidence_json
- ranking_explanation_json
- status

Event types should include at least:

- fire
- rescue
- medical_public_impact
- police_public_safety
- traffic_collision
- road_closure
- bridge_disruption
- transit_disruption
- ferry_disruption
- airport_disruption
- port_disruption
- power_outage
- utility_disruption
- weather_alert
- smoke_air_quality
- earthquake
- flood
- school_closure
- civic_alert
- major_event
- news_story
- community_signal
- source_health_problem

Make clear that raw low-acuity calls should not automatically become elevated LOCAL events.

SECTION 6: Cross-source convergence ranking

Design deterministic ranking around the user’s idea:

If something appears in official sources, local news, neighborhood blogs, transit/traffic feeds, and community/social signals within a short window, it is probably important or interesting.

Implement this as design only.

Do not design an LLM summarizer.

The scoring model must be explainable.

Required scoring factors:

1. Official severity

Examples:

- SFD unit count.
- SFD incident type.
- Multiple alarm.
- Aid response vs rescue vs fire vs motor vehicle incident.
- SPD significant incident report.
- AlertSeattle emergency alert.
- NWS alert severity.
- WSDOT road closure or major delay.
- City Light customers affected.
- FAA/SEA ground delay, stop, closure, or operational advisory.
- Metro/Sound Transit/WSF major service disruption.

2. Source diversity

Independent source families count more than repeated mentions from the same family.

Example families:

- sfd
- spd
- alertseattle
- sdot
- wsdot
- metro
- sound_transit
- city_light
- port_sea
- nws
- usgs
- air_quality
- local_tv
- local_radio
- local_newspaper
- neighborhood_blog
- reddit
- bluesky
- x_api
- source_health

3. Temporal proximity

Items closer in time are more likely to be the same event.

Propose matching windows:

- SFD/SPD/traffic: 0 to 6 hours.
- Breaking news: 0 to 24 hours.
- Weather/hazard/outage: active alert duration or 0 to 48 hours.
- Airport/port: 0 to 24 hours.
- Major civic story: 0 to 72 hours.

4. Geographic proximity

Match by:

- exact location, if safe and appropriate
- street intersection
- neighborhood
- facility, such as SEA Airport, Port, West Seattle Bridge, I-5, SR 99, ferry terminal
- route ID
- utility outage area
- weather zone
- citywide or countywide flag

5. Public impact

Boost:

- port
- airport
- bridges
- ferries
- I-5
- SR 99
- West Seattle Bridge
- hospitals
- schools
- downtown
- major transit stations
- major power outages
- major public events
- official emergency alerts
- citywide impacts

6. Recency

Recent items matter more, but older active hazards can stay elevated if still active.

7. User-configured priority

Allow future config to boost:

- Seattle proper
- nearby neighborhood
- SEA Airport
- Port
- West Seattle
- Capitol Hill
- traffic
- power
- weather
- fire
- transit
- major civic alerts

8. Privacy and low-public-value penalty

De-emphasize:

- ordinary medical aid calls
- overdose calls
- low-acuity response
- private residential calls with no broader public impact
- single-source minor police calls
- noisy social-only posts
- vague reports with no official confirmation

The design must include a sample scoring formula.

Example:

score =
  recency_score
  + official_severity_score
  + source_diversity_score
  + public_impact_score
  + source_priority_score
  + active_alert_score
  + cluster_size_score
  - privacy_penalty
  - duplicate_family_penalty
  - stale_source_penalty
  - low_confidence_penalty

The design must explain that "frequency of appearance" means independent cross-source convergence, not raw duplicate counts.

Bad ranking:
- 20 syndicated copies of the same article dominate.

Good ranking:
- SFD 10-unit incident at Port of Seattle.
- SDOT or WSDOT nearby road impact.
- SEA or Port notice.
- West Seattle Blog or local TV report.
- Reddit/Bluesky chatter, only if compliant.
- All within a short time window.

SECTION 7: Public safety privacy posture

Design this carefully.

The source data may be public, but the dashboard should not amplify private distress by default.

Rules:

- Store source-provided public metadata only.
- Do not store full narratives from police/fire articles beyond bounded descriptions.
- Do not archive social posts long term.
- Do not surface exact addresses for low-acuity medical or private residential aid calls unless an official source clearly frames it as a public-impact incident.
- Prefer neighborhood or intersection-level display for sensitive calls.
- Preserve source links in evidence so the user can click official sources.
- For major incidents, show the public operational facts:
  incident type, source, unit count if available, neighborhood, public impact, observed time, source link.
- For SPD Significant Incident Reports, include a design note that early incident reports can differ from final reports and should be treated as preliminary.
- Do not turn LOCAL into a fear dashboard or crime ticker.
- The UI should group low-acuity public safety data into "background pulse" counts unless elevated by severity or cross-source convergence.

SECTION 8: LOCAL source freshness and retention

Design short retention.

Default candidate retention:

- Raw fetch diagnostics: 7 days or less.
- Raw payload debug: disabled by default. If ever enabled, 6 hours max by default.
- Official incident metadata: 3 to 7 days.
- Active alerts: until expiration plus 24 hours.
- News headline metadata: 7 days.
- Local event clusters: 7 to 14 days.
- Source health: 30 days.
- Ranking explanations: same as event/item retention.
- Social metadata, if ever enabled: 24 to 72 hours unless source terms require shorter or prohibit storage.

Every ingest run in later phases must purge expired data.

No article body archive.

No permanent local news archive.

No permanent social archive.

SECTION 9: Adapter design for LOCAL

Design future adapter families.

Do not implement now.

Required adapter families:

socrata_json:
- Seattle Open Data Fire 911.
- SPD Call Data.
- Other future data.seattle.gov datasets.
- Must support app token later but must run without secrets for public low-volume usage if permitted.
- Must support SoQL fields, ordering, limits, and updated-since queries.
- Must cap rows per run.
- Must preserve dataset ID and row ID.

rss_atom:
- AlertSeattle feed if verified.
- SPD Blotter feed if verified.
- SDOT Blog feed if verified.
- King County Metro RSS.
- Local news/blog feeds.
- Must parse title, URL, published timestamp, description, categories.
- Must bound description length.
- Must not fetch article bodies.

official_api_json:
- NWS alerts.
- FAA/NAS airport status, if verified.
- Air quality APIs if configured.
- USGS GeoJSON.
- WSDOT Traveler Information API.
- Must support ETag/Last-Modified if available.
- Must use timeouts and response size caps.

gtfs_realtime_alerts:
- Sound Transit service alerts.
- Possibly transit feeds later.
- Must be optional because protobuf support may need dependency review.
- If dependency is needed, backlog it instead of adding it.

arcgis_dashboard_research:
- SPD dashboard.
- City Light outage ArcGIS/Experience pages.
- Traffic cameras / ArcGIS feature services.
- Must not screen scrape dashboard HTML.
- Later work should identify underlying feature services or official APIs.
- If no official data endpoint is found, mark manual_review_only or source_health_only.

static_html_headline_candidate:
- Only for official pages or local news pages with no RSS/API.
- Disabled unless homepage extractor support is explicitly allowed.
- Must use per-source selectors.
- No recursive crawling.
- No article-body fetch.
- Robots/policy review required.

wordpress_feed_candidate:
- WordPress-style /feed/ endpoints.
- Must be verified before implementation.
- Treat as RSS/Atom if valid.
- Store headline metadata only.

source_health_probe_only:
- For pages useful as human status references but not suitable for ingestion.
- Examples: maps, dashboards, unofficial aggregators.

manual_review_only:
- For policy-sensitive or parser-risky targets.

SECTION 10: Candidate source registry example

Include a YAML-like example in the design document.

Do not edit config.example.yml yet unless the previous architecture already established that this doc should include a future config sketch only.

The example must be disabled by default.

Example shape:

local_sources:
  enabled: false
  label: "Seattle"
  retention:
    official_incident_days: 7
    headline_days: 7
    event_cluster_days: 14
    source_health_days: 30
    raw_payload_debug_enabled: false
    raw_payload_debug_ttl_hours: 6
  ranking:
    source_diversity_weight: 3.0
    official_severity_weight: 3.0
    public_impact_weight: 2.5
    recency_weight: 2.0
    social_echo_weight: 0.75
    privacy_penalty_weight: 3.0
  privacy:
    suppress_low_acuity_exact_addresses: true
    sensitive_incident_neighborhood_only: true
    social_retention_hours: 48
  sources:
    - id: seattle_sfd_realtime_911_socrata
      enabled: false
      source_family: sfd
      source_class: official_incident
      adapter: socrata_json
      url: "https://data.seattle.gov/Public-Safety/Seattle-Real-Time-Fire-911-Calls/kzjm-xkqj"
      api_url: "https://data.seattle.gov/resource/kzjm-xkqj.json"
      priority: 90
      interval_minutes: 5
      row_limit: 200
      privacy_risk: medium
      public_impact_rules:
        major_unit_threshold: 5
        critical_unit_threshold: 10
        suppress_low_acuity_exact_addresses: true

    - id: alertseattle
      enabled: false
      source_family: alertseattle
      source_class: official_alert
      adapter: rss_atom
      url: "https://alert.seattle.gov/feed/"
      homepage_url: "https://alert.seattle.gov/"
      priority: 100
      interval_minutes: 10
      verification_status: candidate_needs_verification

    - id: wsdot_traveler_api
      enabled: false
      source_family: wsdot
      source_class: official_transport
      adapter: official_api_json
      url: "https://wsdot.wa.gov/traffic/api/"
      priority: 85
      interval_minutes: 10
      verification_status: candidate_needs_verification

    - id: west_seattle_blog
      enabled: false
      source_family: neighborhood_blog
      source_class: neighborhood_blog
      adapter: wordpress_feed_candidate
      homepage_url: "https://westseattleblog.com/"
      url: "https://westseattleblog.com/feed/"
      priority: 55
      interval_minutes: 15
      store_article_bodies: false
      verification_status: candidate_needs_verification

SECTION 11: LOCAL UI architecture

Design the eventual LOCAL page.

Do not implement it.

The LOCAL page should use the same console style.

Propose four bays.

Bay 1:
- "Attention now"
- Highest-ranking LOCAL events.
- Must show why each item is ranked.
- Must show source-family badges.
- Must show official vs news vs community convergence.
- Must show observed time and last seen.
- Must avoid dumping raw low-acuity incidents.

Bay 2:
- "Official operations"
- AlertSeattle, SFD, SPD, SDOT, WSDOT, City Light, Port/SEA, NWS.
- Show active official alerts first.
- Show major public-safety incidents only when elevated.
- Show source freshness.

Bay 3:
- "Movement and utilities"
- Traffic, bridges, transit, ferries, airport, port, power, weather/air.
- Useful for "will this affect getting around or staying functional?"

Bay 4:
- "Local press and neighborhood pulse"
- West Seattle Blog, Capitol Hill Seattle, KUOW, KING5, KIRO, KOMO, FOX 13, Cascade PBS, The Urbanist, Seattle Bike Blog, and future configured sources.
- Social/community signals only if configured and compliant.
- No fake headlines.
- If disabled, show "LOCAL news sources not configured."

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

Empty states:

- LOCAL recent-signal layer disabled.
- LOCAL sources not configured.
- LOCAL sources configured but disabled.
- LOCAL sources configured but never scanned.
- LOCAL sources stale.
- LOCAL source policy blocked.
- LOCAL parser failed.
- LOCAL social sources disabled by policy.
- LOCAL homepage extraction disabled by policy.

SECTION 12: Evidence model for LOCAL

Every item/event must trace back to source evidence.

For a LOCAL event, evidence should include:

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
- privacy redaction decision
- retention expiration
- matching tokens
- geographic match basis
- event type
- event confidence
- policy notes

For public safety events, evidence must also include:

- whether exact location was suppressed
- why it was elevated
- whether it was official-only, news-only, social-only, or cross-source
- whether the source describes the data as preliminary, delayed, or otherwise limited

SECTION 13: Source health for LOCAL

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

Source health must be visible in SYSTEM later and summarized in LOCAL Bay 4 or a footer strip.

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

SECTION 14: First implementation sequence for LOCAL

Design future phases.

Phase L0: this design
- Create design doc.
- Update BACKLOG.
- No runtime behavior change.

Phase L1: source registry scaffolding
- Add disabled source config.
- Add source registry schema or tables if not already done by global architecture.
- Add tests proving LOCAL disabled by default.
- No network.

Phase L2: local fixtures only
- Create fixture files for:
  SFD Socrata JSON.
  AlertSeattle RSS.
  Metro RSS.
  NWS alert JSON.
  WSDOT alert JSON.
  Local blog RSS.
  City Light outage fixture.
  FAA airport status fixture.
- Parse fixtures only.
- Store normalized metadata.
- No live fetch.

Phase L3: LOCAL event correlation
- Deterministic token/location/time matching.
- No LLM.
- Tests for convergence.
- Tests for duplicate suppression.
- Tests for source-family diversity.

Phase L4: LOCAL ranking
- Implement scoring model.
- Explain ranking in JSON.
- Tests for official severity, source diversity, recency, public impact, privacy penalty.

Phase L5: LOCAL UI disabled and fixture-backed states
- Replace LOCAL placeholders with honest states.
- Fixture-backed in tests only.
- No live fetch.
- No fake headlines.

Phase L6: official API/RSS live fetch, opt-in only
- Start with one safe official source.
- Suggested first candidates:
  Seattle SFD Fire 911 Socrata.
  NWS alerts.
  King County Metro RSS.
  WSDOT API.
- Must be disabled by default.
- Must use explicit command.
- No page-load fetch.

Phase L7: additional official sources
- City Light outage source only after endpoint verification.
- SEA/FAA status after endpoint verification.
- SPD Call Data after privacy posture is tested.
- Sound Transit GTFS alerts after dependency review.

Phase L8: local news RSS
- Publisher feeds only.
- Store metadata only.
- No article bodies.
- No paywall bypass.

Phase L9: neighborhood blogs
- RSS first.
- Homepage extraction only if explicitly allowed and reviewed.

Phase L10: social/community
- Bluesky AT Protocol candidate.
- Reddit official API candidate.
- X official API only if explicitly configured.
- No HTML scraping.
- Short retention.
- Disabled by default.

SECTION 15: Testing strategy

Design tests.

Required tests:

Config:
- LOCAL disabled by default.
- Source disabled by default.
- Invalid source class rejected.
- Invalid adapter rejected.
- Social source rejected unless allow_social_sources true.
- Homepage extraction rejected unless allow_homepage_extractors true.
- Source without URL rejected unless adapter supports no URL.
- Secrets not allowed in config.example.yml.

Registry:
- Source keys unique.
- Source family valid.
- Source class valid.
- Verification status valid.
- Retention settings valid.

Parser fixture tests:
- SFD Socrata fixture parses.
- AlertSeattle RSS fixture parses.
- Metro RSS fixture parses.
- NWS alert JSON fixture parses.
- WSDOT alert fixture parses.
- Local blog RSS fixture parses.
- Malformed feed fails soft.
- Oversized payload blocked or truncated.

Privacy tests:
- Low-acuity medical call does not elevate.
- Low-acuity call exact address suppressed.
- Multi-unit major incident can elevate.
- SPD preliminary report gets preliminary evidence flag.
- Social-only vague report does not outrank official alert.

Correlation tests:
- SFD plus SDOT plus blog within time window becomes one event.
- Same event from multiple news outlets counts as news family convergence but not endless duplicate inflation.
- Same source repeated does not inflate source diversity.
- Different source families increase diversity.
- Geo/time mismatch prevents false merge.

Ranking tests:
- Official severe alert outranks generic news.
- Major traffic disruption outranks minor blog post.
- Airport ground stop outranks normal flight-status page.
- Citywide power outage outranks single-customer outage.
- Stale source lowers confidence.
- Source policy blocked item never displays as live.

API design tests for later:
- GET routes read SQLite only.
- GET routes do not fetch network.
- Disabled/not configured/stale/failing states distinct.

UI tests for later:
- No fake headlines.
- Empty states clear.
- Evidence visible.
- Ranking reason visible.
- Source health visible.

SECTION 16: Backlog update requirements

Update BACKLOG.md.

Add a section named:

LOCAL Seattle Recent Signal Layer

Add concrete backlog items with Status: not implemented.

Include at least:

- LOCAL source registry design implemented from document.
- Disabled-by-default LOCAL config.
- LOCAL SQLite schema or extension.
- LOCAL fixture pack.
- Socrata parser for SFD Fire 911.
- RSS/Atom parser for official and local feeds.
- NWS alert fixture parser.
- WSDOT official API fixture parser.
- Metro RSS parser.
- FAA/SEA airport status research.
- City Light outage endpoint research.
- SPD Call Data privacy review.
- ArcGIS dashboard underlying endpoint research.
- LOCAL deterministic event correlation.
- LOCAL deterministic ranking.
- LOCAL privacy redaction rules.
- LOCAL UI disabled states.
- LOCAL source health states.
- LOCAL evidence drawer contract.
- LOCAL official-source live ingest phase, disabled by default.
- LOCAL news/blog RSS ingest phase, disabled by default.
- LOCAL social source policy review, disabled by default.
- Documentation for source verification.
- Tests for no page-load external fetches.

SECTION 17: Non-goals

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
- No exact-address amplification for low-value private incidents.
- No scraping behind login.
- No bypassing Reddit/X/API restrictions.
- No claiming social chatter is verified fact.
- No treating SFD Live as official.
- No treating duplicate articles as independent confirmation.
- No turning LOCAL into a fear dashboard.

SECTION 18: Final response requirements

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
6. Confirmation that LOCAL remains disabled by default.
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
