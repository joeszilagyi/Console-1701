Use this as `build_order/002_regional.md`.

I kept it in the same design-only lane as the uploaded architecture prompt: no implementation, no live fetches, no runtime changes, BACKLOG law, and proof at the end.

I anchored the regional target set in official or source-identifiable targets: WSDOT Traveler API and real-time travel pages, WA DNR wildfire dashboard, WA Emergency Management alerts, NWS API/alerts, USGS GeoJSON earthquake feeds, USGS Water APIs, WA Ecology air-quality map, King County Emergency News, ODOT TripCheck API, DriveBC Open511, and regional/public news feeds where available. ([WSDOT][1])

```text
You are working in the console-1706 repository.

This task assumes the prior scoped recent-signal architecture prompt and the LOCAL Seattle source-target design prompt have either already been run, or will be pasted above this prompt.

This is a REGIONAL scope architecture, source-target inventory, and ranking design task only.

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

Your job is to design the REGIONAL recent-signal layer in enough detail that later Codex passes can implement it safely, source by source, without guessing.

Before doing anything, inspect the current repo state and previous design outputs.

Required first checks:

pwd
git status --short
find docs/project -maxdepth 1 -type f -print | sort || true
grep -n "Recent Signal\|News Ingestion\|LOCAL\|REGIONAL" BACKLOG.md || true

If previous docs exist, read them first and extend them cleanly:

- docs/project/NEWS_SCOPE_INGESTION_ARCHITECTURE_DESIGN.md
- docs/project/LOCAL_SEATTLE_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md

Do not duplicate BACKLOG sections already added by previous tasks. Extend the relevant section cleanly or add a new REGIONAL subsection.

The user intent:

console-1706 is a local-only home dashboard running at http://127.0.0.1:1706/.

The REGIONAL tab should eventually answer:

"What is happening around Washington, Puget Sound, the Pacific Northwest, and the nearby Cascadia region that may matter to me?"

The REGIONAL scope should eventually combine recent signals from:

- Washington state emergency management and public alerts.
- County and regional emergency pages around Puget Sound.
- WSDOT, WSF, mountain passes, bridges, ferries, road closures, and statewide travel disruption.
- Transit disruptions with regional impact.
- Wildfire, smoke, air quality, burn restrictions, evacuation, and emergency fire information.
- NWS, NOAA, river forecast, flood, landslide, tsunami, earthquake, volcano, and weather hazards.
- USGS/PNSN seismic feeds and Cascades volcano sources.
- Public health alerts from Washington state and county public-health sources.
- Regional utility outages and energy/grid signals where public.
- Regional ports, airports, ferries, rail, and freight corridor disruptions.
- State government and official agency news when it has public-impact value.
- Regional news outlets, public radio, TV, and nonprofit journalism.
- Community/social regional signals only when accessible through compliant, explicitly configured methods.
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

   docs/project/REGIONAL_PNW_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md

   Create docs/project if it does not exist.

2. Update BACKLOG.md with concrete future implementation tasks flowing from this REGIONAL design.

3. Do not touch application code unless absolutely necessary. This should normally be docs plus BACKLOG only.

4. Do not perform live source verification. The source links below are seed targets. Classify them as candidate links and design how they should be verified in a later phase.

5. The final response must prove what changed and what did not change.

The design document must include the following sections.

SECTION 1: Purpose

Explain the REGIONAL scope in plain engineering language.

The REGIONAL scope is the Washington / Puget Sound / Pacific Northwest recent-signal layer. It should tell the user what is happening regionally, with source provenance, observed time, source kind, ranking reason, and evidence.

It is not:

- A general PNW web crawler.
- A regional news archive.
- A state politics firehose.
- A social media monitoring system.
- A permanent incident database.
- A police scanner clone.
- A wildfire scanner clone.
- A replacement for LOCAL Seattle.
- A replacement for NATIONAL news.
- A hidden LLM summarizer.
- A cloud service.

It is:

- A local, short-retention metadata dashboard.
- A deterministic cross-source event detector for regional public-impact signals.
- A source-health aware recent-signal system.
- A REGIONAL tab in console-1706 that can surface official alerts, hazards, transportation disruption, wildfire, smoke, weather, seismic activity, ferry and pass problems, public-health alerts, major regional civic news, local journalism, and compliant community echoes.
- A way to rank items by independent source convergence, official severity, geographic relevance, public impact, freshness, and user-configured source priority.

Make clear that "regional" means useful public, configured, lawful, recent signals that the user chooses to enable. It does not mean unbounded crawling or private data collection.

SECTION 2: Regional scope boundaries

Define REGIONAL geography.

Default REGIONAL scope:

- Washington state.
- Puget Sound outside Seattle proper.
- King, Snohomish, Pierce, Kitsap, Thurston, Skagit, Whatcom, Island, Mason, Lewis, Kittitas, Yakima, Chelan, Clallam, Jefferson, and San Juan counties when events have regional public impact.
- Major Washington corridors: I-5, I-90, SR 99, SR 520, SR 167, SR 18, US 2, US 101, US 97, SR 20, ferry routes, mountain passes, border crossings.
- The Cascades and Olympic Peninsula for weather, wildfire, smoke, seismic, landslide, avalanche, flood, pass, and recreation-access impacts.
- Oregon and British Columbia only when the event plausibly affects Washington, Puget Sound, regional transportation, smoke, wildfire, weather systems, earthquakes, ports, ferries, airports, or cross-border travel.
- Pacific Northwest and Cascadia only for hazards, infrastructure, and news with plausible regional relevance.

Out of REGIONAL by default:

- Generic Seattle neighborhood items. Those belong in LOCAL unless they create wider impact.
- Generic national politics unless it directly affects Washington or the PNW.
- Generic global stories.
- Routine county press releases with no broader public impact.
- Single-source social chatter.
- Crime blotter noise.
- Full police scanner streams.
- Private medical or residential distress.
- Sources requiring login, payment, scraping around controls, or tokens not explicitly configured by the user.

Design a later config escape hatch:

regional:
  enabled: false
  default_place_label: "Washington / PNW"
  include_washington_state: true
  include_puget_sound: true
  include_cascadia_hazards: true
  include_oregon_when_relevant: true
  include_bc_when_relevant: true
  include_transport_corridors: true
  include_wildfire_smoke: true
  include_seismic_volcano: true
  include_public_health: true
  include_state_government: true
  include_regional_news: true
  include_social_sources: false
  earthquake_min_magnitude: 3.5
  hazard_radius_miles: 250
  wildfire_min_acres_attention: 100
  smoke_aqi_attention_threshold: 100
  river_alert_minimum: "action"
  ferry_delay_attention_minutes: 30
  mountain_pass_delay_attention_minutes: 30

SECTION 3: Relationship to LOCAL and OVERVIEW

Explain how REGIONAL interacts with other scopes.

Rules:

- REGIONAL should not duplicate LOCAL Seattle unless the Seattle item has broader regional impact.
- LOCAL should own Seattle fire, local roads, local utility outages, neighborhood blogs, and immediate city services.
- REGIONAL should own statewide and PNW hazards, highways, ferries, mountain passes, wildfires, smoke, floods, air quality, earthquakes, public-health alerts, and regional travel disruption.
- OVERVIEW should select the highest-priority items from LOCAL and REGIONAL without burying urgent local/system issues under broad regional headlines.
- If a regional item directly affects Seattle or the user's configured local interests, it can be tagged both REGIONAL and LOCAL_IMPACT, but the canonical scope remains REGIONAL.
- If a local Seattle item becomes regionally significant, such as port disruption, airport disruption, major I-5 closure, bridge failure, regional protest/event, or widespread outage, it can be promoted to REGIONAL with evidence.

Examples:

- SFD 1-unit medical aid in Seattle: LOCAL background or ignored.
- Major Port of Seattle fire affecting regional freight: LOCAL and REGIONAL.
- WSDOT closes Snoqualmie Pass: REGIONAL.
- Smoke plume from Cascades wildfire degrading Puget Sound AQI: REGIONAL.
- AlertSeattle city warming center update: LOCAL.
- WA EMD tsunami warning affecting the coast and Puget Sound: REGIONAL and OVERVIEW.
- King County flood warning affecting major rivers: REGIONAL.
- Seattle Times statewide election story: REGIONAL only if immediate public impact is high, otherwise lower-priority news.

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
- official_incident
- official_open_data
- official_transport
- official_ferry
- official_transit
- official_utility
- official_airport_port
- official_weather_hazard
- official_air_quality
- official_wildfire
- official_water_flood
- official_seismic_volcano
- official_public_health
- official_state_civic
- regional_news
- public_media
- local_tv_radio
- county_emergency
- social_candidate
- unofficial_aggregator
- source_health_only
- manual_review_only

Use these adapter types:

- rss_atom
- wordpress_feed_candidate
- static_html_headline_candidate
- official_api_json
- socrata_json
- arcgis_feature_service_candidate
- arcgis_dashboard_research
- open511_json
- gtfs_realtime_alerts
- cap_alerts
- geojson_feed
- hydrology_api_json
- airport_status_json_or_xml
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

Washington emergency management and statewide alerts:

https://mil.wa.gov/alerts
https://mil.wa.gov/emergency-management-division
https://mil.wa.gov/emergency-alert-system
https://mil.wa.gov/tsunami
https://mil.wa.gov/preparedness
https://mil.wa.gov/news
https://www.weather.gov/alerts
https://api.weather.gov/alerts/active
https://www.weather.gov/documentation/services-web-api
https://www.weather.gov/documentation/services-web-alerts

County and Puget Sound emergency sources:

https://kcemergency.com/
https://kcemergency.com/tag/alerts/
https://kingcounty.gov/en/dept/executive-services/health-safety/safety-injury-prevention/emergency-preparedness/alert-king-county
https://flood.kingcounty.gov/
https://kingcountyfloodcontrol.org/flood-resources/flood-warnings-alerts/
https://snohomishcountywa.gov/620/Public-Alert-Resources
https://snohomishcountywa.gov/5326/Emergency-News
https://snohomishcountywa.gov/AlertCenter.aspx
https://snohomishcountywa.gov/894/River-Levels-Flood-Stages
https://www.piercecountywa.gov/921/Pierce-County-ALERT
https://www.piercecountywa.gov/AlertCenter.aspx
https://www.thurstoncountywa.gov/departments/emergency-management
https://www.thurstoncountywa.gov/departments/emergency-management/emergency-information
https://www.thurstoncountywa.gov/departments/emergency-management/emergency-information/alert-and-notification
https://www.whatcomcounty.us/200/Emergency-Management
https://www.skagitcounty.net/Departments/EmergencyManagement/main.htm
https://www.kitsapdem.com/
https://www.clallamcountywa.gov/333/Emergency-Management
https://www.jeffersoncountypublichealth.org/202/Emergency-Management

Washington state civic and agency news:

https://governor.wa.gov/news
https://governor.wa.gov/news/news-releases
https://governor.wa.gov/office-governor/office/official-actions/executive-orders
https://doh.wa.gov/
https://doh.wa.gov/newsroom
https://doh.wa.gov/newsroom/archive/category/health-news
https://wsp.wa.gov/
https://wsp.wa.gov/media/
https://wsp.wa.gov/media/media-releases/
https://wsp.wa.gov/media/subscribe/
https://www.atg.wa.gov/news
https://www.atg.wa.gov/pressrelease.aspx
https://www.atg.wa.gov/washington-ago-rss-feeds
https://ecology.wa.gov/
https://ecology.wa.gov/about-us/who-we-are/news
https://data.wa.gov/
https://geo.wa.gov/

Transportation, ferries, passes, roads, borders:

https://wsdot.wa.gov/
https://wsdot.wa.gov/traffic/api/
https://wsdot.wa.gov/traffic/api/Documentation/annotated.html
https://wsdot.com/travel/real-time/
https://wsdot.com/travel/real-time/map/
https://wsdot.wa.gov/travel
https://wsdot.wa.gov/travel/sign-wsdot-travel-alerts
https://wsdot.wa.gov/travel/roads-bridges/mountain-pass-conditions
https://wsdot.wa.gov/travel/roads-bridges/border-crossings
https://wsdot.com/ferries/schedule/bulletin.aspx
https://wsdot.wa.gov/travel/washington-state-ferries
https://www.wsdot.wa.gov/ferries/api/schedule/documentation/
https://www.wsdot.wa.gov/ferries/api/terminals/documentation/
https://www.wsdot.wa.gov/ferries/api/vessels/documentation/
https://wsdotblog.blogspot.com/
https://wsdot.wa.gov/about/news
https://tripcheck.com/
https://tripcheck.com/Pages/API
https://apiportal.odot.state.or.us/product/tripcheck-data-api
https://www.drivebc.ca/
https://api.open511.gov.bc.ca/help
https://open.canada.ca/data/en/dataset/23a839e3-8fb4-4569-bb3d-c28a7621f687

Regional transit:

https://kingcounty.gov/en/dept/metro/rider-tools/service-advisories
https://kingcounty.gov/en/dept/metro/rider-tools/service-advisories/rss
https://kingcountymetro.blog/
https://kingcountymetro.blog/feed/
https://www.soundtransit.org/ride-with-us/service-alerts
https://www.soundtransit.org/help-contacts/business-information/open-transit-data-otd/otd-downloads
https://www.communitytransit.org/service-alerts
https://www.piercetransit.org/rider-alerts/
https://www.amtrakcascades.com/

Wildfire, smoke, fire weather, evacuations:

https://dnr.wa.gov/wildfire-resources
https://dnr.wa.gov/wildfire-resources/current-wildfire-incident-information
https://experience.arcgis.com/experience/6cdda73cf6154949a1fae76ccb2900a0
https://data-wadnr.opendata.arcgis.com/
https://nwccinfo.blogspot.com/
https://nwccinfo.blogspot.com/p/who-we-are.html
https://www.fs.usda.gov/r06/fire/info
https://inciweb.wildfire.gov/
https://www.nifc.gov/fire-information
https://www.weather.gov/fire/
https://www.spc.noaa.gov/products/fire_wx/
https://wasmoke.blogspot.com/
https://ecology.wa.gov/air-climate/air-quality
https://ecology.wa.gov/research-data/monitoring-assessment/air-quality-index
https://airqualitymap.ecology.wa.gov/
https://pscleanair.gov/27/Air-Quality
https://pscleanair.gov/rss.aspx
https://pscleanair.gov/sensormap
https://www.airnow.gov/
https://docs.airnowapi.org/
https://www.oregon.gov/odf/fire/pages/firestats.aspx
https://geo.maps.arcgis.com/apps/instant/portfolio/index.html?appid=22d04c007866419c91ccf00d097526c8
https://www.emergencyinfobc.gov.bc.ca/
https://www2.gov.bc.ca/gov/content/safety/public-safety/emergency-alerts

Weather, river, flood, landslide, hydrology:

https://www.weather.gov/sew/
https://www.weather.gov/pqr/
https://www.weather.gov/otx/
https://www.weather.gov/pdt/
https://www.weather.gov/alerts
https://api.weather.gov/alerts/active
https://www.weather.gov/documentation/services-web-api
https://www.nwrfc.noaa.gov/
https://www.nwrfc.noaa.gov/river/river_summary.php
https://www.nwrfc.noaa.gov/weather/10_day.cgi
https://api.waterdata.usgs.gov/
https://waterservices.usgs.gov/
https://www.usgs.gov/centers/washington-water-science-center
https://landslides.usgs.gov/
https://www.dnr.wa.gov/programs-and-services/geology/geologic-hazards/landslides

Earthquake, tsunami, volcano:

https://earthquake.usgs.gov/
https://earthquake.usgs.gov/earthquakes/feed/
https://earthquake.usgs.gov/earthquakes/feed/v1.0/
https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php
https://pnsn.org/
https://pnsn.org/earthquakes/recent
https://pnsn.org/earthquakes/recent/list
https://www.usgs.gov/observatories/cascades-volcano-observatory
https://www.usgs.gov/programs/VHP
https://volcanoes.usgs.gov/
https://www.tsunami.gov/
https://mil.wa.gov/tsunami

Utilities and regional outages:

https://www.pse.com/outage/outage-map
https://www.pse.com/en/outage
https://outagemap.snopud.com/
https://www.snopud.com/outages-safety/outage-center/
https://www.mytpu.org/outages-safety/power-outages/
https://www.mytpu.org/outages-safety/
https://www.seattle.gov/city-light/outages
https://scl.datacapable.com/map/
https://experience.arcgis.com/experience/66636c38766c4fb4aca16976d79b0527/page/Energy-Page---Seattle-Light-Outage-Map
https://experience.arcgis.com/experience/66636c38766c4fb4aca16976d79b0527/page/Energy-Page---Puget-Sound-Outage-Map
https://www.bpa.gov/

Ports, airports, rail, freight, maritime:

https://www.portseattle.org/
https://www.portseattle.org/news
https://www.portseattle.org/sea
https://www.portseattle.org/sea/flight-status
https://www.portseattle.org/actions/airport-traveler-updates
https://www.portseattle.org/page/live-estimated-checkpoint-wait-times
https://www.portoftacoma.com/
https://www.portoftacoma.com/news-releases
https://www.portofeverett.com/
https://www.portofeverett.com/news/
https://www.portvancouverusa.com/
https://www.portvancouverusa.com/news-releases/
https://www.flypainefield.com/
https://www.painefield.com/
https://www.portofbellingham.com/173/Airport
https://spokaneairports.net/
https://www.flypdx.com/
https://www.yvr.ca/en/passengers/flights
https://www.fly.faa.gov/fly/flyfaa/flyfaaindex?ARPT=SEA&p=1
https://nasstatus.faa.gov/
https://nasstatus.faa.gov/api/airport-status-information
https://www.faa.gov/airport-status/SEA
https://github.com/Federal-Aviation-Administration/ASWS

Regional news, public media, TV, radio:

https://www.seattletimes.com/seattle-news/
https://www.seattletimes.com/feed/
https://www.heraldnet.com/
https://www.heraldnet.com/feed/
https://www.thenewstribune.com/
https://www.spokesman.com/
https://www.columbian.com/
https://www.bellinghamherald.com/
https://www.tri-cityherald.com/
https://washingtonstatestandard.com/
https://washingtonstatestandard.com/news/
https://washingtonstatestandard.com/feed/
https://statesnewsroom.com/rss-feeds/
https://www.cascadepbs.org/news/
https://www.kuow.org/
https://www.knkx.org/
https://www.opb.org/
https://www.opb.org/rss-feeds/
https://www.opb.org/tag/pacific-northwest/
https://www.king5.com/rss
https://www.kiro7.com/homepage
https://www.kiro7.com/rss-snd/
https://komonews.com/
https://komonews.com/news/local
https://www.fox13seattle.com/
https://www.oregonlive.com/
https://www.seattletimes.com/seattle-news/pacific-nw-magazine/

Regional recreation and access, candidate only:

https://www.nps.gov/mora/planyourvisit/conditions.htm
https://www.nps.gov/olym/planyourvisit/current-road-conditions.htm
https://www.nps.gov/noca/planyourvisit/road-conditions.htm
https://www.wta.org/go-outside/trip-reports
https://www.wta.org/go-outside/trail-smarts/pass-news
https://www.fs.usda.gov/r06

Community and social candidates, policy-sensitive:

https://www.reddit.com/r/Washington/
https://www.reddit.com/r/PacificNorthwest/
https://www.reddit.com/r/SeattleWA/
https://www.reddit.com/r/Bellingham/
https://www.reddit.com/r/Tacoma/
https://www.reddit.com/r/Spokane/
https://www.reddit.com/r/Portland/
https://x.com/waEMD
https://x.com/wsdot
https://x.com/wsdot_traffic
https://x.com/wsdot_passes
https://x.com/wsferries
https://x.com/WashDNR
https://x.com/WADeptHealth
https://x.com/wastatepatrol
https://x.com/PNSN1
https://x.com/NWCCInfo
https://x.com/NWSSeattle
https://x.com/NWSPortland
https://x.com/NWSSpokane
https://bsky.app/search?q=Washington%20wildfire
https://bsky.app/search?q=Puget%20Sound
https://bsky.app/search?q=Pacific%20Northwest
https://bsky.app/search?q=WSDOT
https://bsky.app/search?q=Snoqualmie%20Pass

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
- Official APIs, official open data, RSS/Atom, CAP feeds, GeoJSON feeds, hydrology APIs, and official agency JSON endpoints.
- Best first live candidates.

Tier 2:
- Official pages with stable public operational data but no obvious feed/API.
- Candidate only after source-policy review.
- Prefer source-health checks and manual review before parser implementation.

Tier 3:
- Regional news RSS or publisher-provided feeds.
- Store headline metadata only.
- No article-body archive.
- No paywall bypass.

Tier 4:
- Public media, nonprofit regional outlets, and regional blogs.
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

SECTION 6: REGIONAL event model

Design a REGIONAL event model that sits above raw items.

The system should not only store "news items." It should infer that multiple recent items refer to the same regional event.

Propose a future regional_events table or explain how news_clusters should be extended.

A REGIONAL event should have:

- regional_event_id
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
- transportation_impact_score
- ferry_impact_score
- wildfire_impact_score
- smoke_air_quality_score
- flood_hydrology_score
- seismic_volcano_score
- public_health_score
- utility_impact_score
- airport_port_score
- first_seen_at
- last_seen_at
- last_elevated_at
- expires_at
- geography_json
- counties_json
- corridors_json
- source_ids_json
- item_ids_json
- evidence_json
- ranking_explanation_json
- status

Event types should include at least:

- state_emergency_alert
- county_emergency_alert
- wildfire
- smoke_air_quality
- evacuation_order
- red_flag_warning
- weather_alert
- atmospheric_river
- flood
- river_flood
- landslide
- earthquake
- tsunami
- volcano_unrest
- mountain_pass_closure
- highway_closure
- ferry_disruption
- bridge_disruption
- transit_disruption
- airport_disruption
- port_disruption
- power_outage
- utility_disruption
- public_health_alert
- food_water_shellfish_alert
- state_civic_action
- major_regional_news
- recreation_access_closure
- border_crossing_disruption
- source_health_problem
- community_signal

Make clear that routine small incidents should not automatically become elevated REGIONAL events.

SECTION 7: Cross-source convergence ranking

Design deterministic ranking around this idea:

If something appears in official sources, regional news, transport feeds, utility feeds, hazard feeds, and community/social signals within a short window, it is probably important or interesting.

Implement this as design only.

Do not design an LLM summarizer.

The scoring model must be explainable.

Required scoring factors:

1. Official severity

Examples:

- WA EMD alert.
- County emergency alert.
- NWS warning or severe weather statement.
- Tsunami warning, watch, advisory, or emergency test.
- USGS earthquake above configured magnitude or intensity threshold.
- PNSN cluster around Cascades volcano or urban fault zone.
- WA DNR wildfire with size, evacuation, closure, or smoke impact.
- NWCC large fire.
- WSDOT major highway closure.
- WSDOT pass closure.
- WSF route cancellation or major delay.
- City, county, PSE, SnoPUD, Tacoma Power, or Seattle City Light outage with regional customer impact.
- DOH health or safety alert.
- WSP major traffic/public-safety release.
- FAA/NAS airport ground delay, ground stop, or major airport disruption.

2. Source diversity

Independent source families count more than repeated mentions from the same family.

Example families:

- wa_emd
- county_emergency
- nws
- nwrfc
- usgs
- pnsn
- wa_dnr
- nwcc
- ecology
- airnow
- wsdot
- wsf
- metro
- sound_transit
- community_transit
- pierce_transit
- pse
- snopud
- tacoma_power
- city_light
- port_seattle
- port_tacoma
- airport_faa
- wa_doh
- wsp
- governor
- attorney_general
- regional_newspaper
- public_radio
- local_tv
- nonprofit_news
- reddit
- bluesky
- x_api
- source_health

3. Temporal proximity

Items closer in time are more likely to be the same event.

Propose matching windows:

- Travel disruption: 0 to 12 hours.
- Ferry disruption: 0 to 12 hours.
- Weather/hazard/outage: active alert duration or 0 to 48 hours.
- Wildfire/smoke: 0 to 72 hours, longer only if active.
- Earthquake: 0 to 24 hours, with aftershock clustering.
- Volcano unrest: 0 to 7 days, but only official sources.
- Public health alert: 0 to 7 days.
- Breaking regional news: 0 to 24 hours.
- State civic action: 0 to 72 hours unless still active.

4. Geographic proximity

Match by:

- county
- city
- route
- mountain pass
- ferry route
- airport
- port
- river basin
- weather zone
- fire incident name
- volcano
- seismic region
- air-quality station
- evacuation zone
- public-health jurisdiction
- regional label, such as Puget Sound, Olympic Peninsula, Cascades, Inland Northwest, Southwest Washington, North Sound, South Sound, Columbia River Gorge

5. Public impact

Boost:

- statewide alerts
- evacuations
- major bridge or highway closures
- ferry route shutdowns
- pass closures
- airport ground stops
- port disruptions
- large wildfires
- smoke affecting Puget Sound
- AQI above threshold
- earthquake above threshold or felt in Puget Sound
- tsunami notices
- flood stage or evacuation
- utility outages above configured customer count
- public-health alerts with action guidance
- official emergency declarations
- school closures at regional scale
- infrastructure damage
- cross-border travel disruptions

6. Recency

Recent items matter more, but older active hazards can stay elevated while still active.

7. User-configured priority

Allow future config to boost:

- Puget Sound
- King County
- Snohomish County
- Pierce County
- Kitsap County
- I-5
- I-90
- Snoqualmie Pass
- Stevens Pass
- Blewett Pass
- ferries
- WSF
- wildfires
- smoke
- air quality
- earthquakes
- flood
- public health
- power outages
- airports
- ports
- state government

8. Privacy and low-public-value penalty

De-emphasize:

- routine local police/fire incidents outside Seattle unless regional impact exists
- isolated residential outages below threshold
- small traffic incidents with no corridor impact
- vague social-only reports
- single-source rumor
- agency news releases with no immediate public effect
- duplicate syndicated stories

The design must include a sample scoring formula.

Example:

score =
  recency_score
  + official_severity_score
  + source_diversity_score
  + public_impact_score
  + geographic_relevance_score
  + active_alert_score
  + source_priority_score
  + cluster_size_score
  - privacy_penalty
  - duplicate_family_penalty
  - stale_source_penalty
  - low_confidence_penalty
  - out_of_region_penalty

The design must explain that "frequency of appearance" means independent cross-source convergence, not raw duplicate counts.

Bad ranking:

- 20 syndicated copies of the same wire story dominate.

Good ranking:

- WA DNR wildfire and NWCC brief.
- NWS red flag warning.
- Ecology / AirNow smoke impact.
- WSDOT closure nearby.
- County evacuation alert.
- Local TV or public radio report.
- Bluesky/Reddit chatter only if compliant.
- All within a plausible time window.

SECTION 8: REGIONAL source category design

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

1. Emergency alerts and county emergency pages.

2. Transportation and ferries.

3. Wildfire, smoke, and air quality.

4. Weather, river, flood, hydrology, landslide.

5. Earthquake, tsunami, and volcano.

6. Utilities and regional outages.

7. Public health and environmental health.

8. Ports, airports, rail, and freight.

9. State civic and agency news.

10. Regional news and public media.

11. Social/community echoes.

12. Source health and disabled states.

SECTION 9: REGIONAL public-safety and privacy posture

Design this carefully.

Rules:

- Store source-provided public metadata only.
- Do not store full narratives from public-safety articles beyond bounded descriptions.
- Do not archive social posts long term.
- Do not surface exact private addresses unless an official source clearly frames it as a public-impact incident.
- Prefer county, route, neighborhood, facility, zone, basin, or corridor display.
- Preserve source links in evidence so the user can click official sources.
- For major incidents, show public operational facts:
  event type, source, source family, affected county/corridor/zone, public impact, observed time, source link.
- Treat early official reports as preliminary where applicable.
- Do not turn REGIONAL into a fear dashboard or crime ticker.
- Low-acuity public safety data should be background pulse only unless elevated by official severity or cross-source convergence.

SECTION 10: REGIONAL source freshness and retention

Design short retention.

Default candidate retention:

- Raw fetch diagnostics: 7 days or less.
- Raw payload debug: disabled by default. If ever enabled, 6 hours max by default.
- Official alert metadata: expiration plus 24 hours.
- Transportation/ferry/pass disruption metadata: 3 to 7 days.
- Weather/hazard metadata: expiration plus 24 to 48 hours.
- Wildfire/smoke metadata: 7 to 14 days while active, then expire.
- Earthquake metadata: 7 days for small regional events, 14 days for felt/significant events.
- Volcano unrest metadata: 14 days while active, official-only.
- News headline metadata: 7 days.
- Regional event clusters: 7 to 14 days.
- Source health: 30 days.
- Ranking explanations: same as event/item retention.
- Social metadata, if ever enabled: 24 to 72 hours unless source terms require shorter or prohibit storage.

Every ingest run in later phases must purge expired data.

No article body archive.

No permanent regional incident archive.

No permanent social archive.

SECTION 11: Adapter design for REGIONAL

Design future adapter families.

Do not implement now.

Required adapter families:

rss_atom:
- WSDOT blog if feed verified.
- Metro RSS.
- Regional news/blog feeds.
- Public media feeds.
- County alert RSS where available.
- Must parse title, URL, published timestamp, description, categories.
- Must bound description length.
- Must not fetch article bodies.

official_api_json:
- NWS alerts.
- WSDOT Traveler API.
- WSF API, noting access-code requirement where applicable.
- NWRFC or NOAA endpoints if verified.
- WA Ecology or AirNow APIs if configured.
- FAA/NAS airport status.
- Must support timeouts, response size caps, source-specific rate limits, and conditional requests when available.

open511_json:
- DriveBC Open511.
- ODOT TripCheck only if endpoint terms and access permit.
- Must be disabled by default and region-filtered.

geojson_feed:
- USGS earthquake GeoJSON.
- Possible wildfire or ArcGIS feature layers if verified.
- Must support bounding boxes, magnitude/severity filters, and source provenance.

hydrology_api_json:
- USGS Water Data APIs.
- NWRFC source candidates if machine-readable endpoints are verified.
- Must support gauge allowlists and river-basin filters.

arcgis_feature_service_candidate:
- WA DNR wildfire dashboard underlying layers.
- WA Ecology or outage dashboards only if official feature services are found.
- Do not screen scrape ArcGIS dashboard HTML.
- Research underlying feature services in a later source-verification phase.

cap_alerts:
- NWS CAP or API alert records if useful.
- Must preserve severity, urgency, certainty, effective time, expiration, area, and instruction URL.

static_html_headline_candidate:
- Only for official pages or regional news pages with no RSS/API.
- Disabled unless homepage extractor support is explicitly allowed.
- Must use per-source selectors.
- No recursive crawling.
- No article-body fetch.
- Robots/policy review required.

source_health_probe_only:
- For maps, dashboards, and portals useful as human status references but not suitable for ingestion.

manual_review_only:
- For policy-sensitive, parser-risky, login-required, or unclear targets.

SECTION 12: Candidate regional source registry example

Include a YAML-like example in the design document.

Do not edit config.example.yml yet unless prior architecture already requires disabled examples.

The example must be disabled by default.

Example shape:

regional_sources:
  enabled: false
  label: "Washington / PNW"
  retention:
    official_alert_days: 7
    transport_days: 7
    wildfire_days: 14
    weather_hazard_days: 7
    earthquake_days: 7
    headline_days: 7
    event_cluster_days: 14
    source_health_days: 30
    raw_payload_debug_enabled: false
    raw_payload_debug_ttl_hours: 6
  ranking:
    source_diversity_weight: 3.0
    official_severity_weight: 3.0
    public_impact_weight: 2.75
    geographic_relevance_weight: 2.5
    recency_weight: 2.0
    social_echo_weight: 0.5
    privacy_penalty_weight: 3.0
    out_of_region_penalty_weight: 3.0
  privacy:
    suppress_private_exact_addresses: true
    social_retention_hours: 48
    social_sources_disabled_by_default: true
  geography:
    primary_region: "Washington"
    secondary_regions:
      - "Puget Sound"
      - "Pacific Northwest"
      - "Cascadia"
    include_oregon_when_relevant: true
    include_bc_when_relevant: true
    hazard_radius_miles: 250
  sources:
    - id: wa_emd_alerts
      enabled: false
      source_family: wa_emd
      source_class: official_alert
      adapter: static_html_headline_candidate
      homepage_url: "https://mil.wa.gov/alerts"
      priority: 100
      interval_minutes: 10
      verification_status: candidate_needs_verification
      notes: "Official Washington emergency alert page. Prefer RSS/API if discovered later."

    - id: nws_active_alerts_wa
      enabled: false
      source_family: nws
      source_class: official_weather_hazard
      adapter: official_api_json
      url: "https://api.weather.gov/alerts/active"
      priority: 100
      interval_minutes: 10
      verification_status: official_page_seen
      filters:
        area:
          - WA
        zones: []
      evidence_notes: "Use NWS API metadata and alert expiration."

    - id: wsdot_traveler_api
      enabled: false
      source_family: wsdot
      source_class: official_transport
      adapter: official_api_json
      url: "https://wsdot.wa.gov/traffic/api/"
      priority: 95
      interval_minutes: 5
      verification_status: official_page_seen
      filters:
        corridors:
          - I-5
          - I-90
          - US-2
          - US-101
          - SR-20

    - id: wa_dnr_wildfire_dashboard
      enabled: false
      source_family: wa_dnr
      source_class: official_wildfire
      adapter: arcgis_feature_service_candidate
      homepage_url: "https://dnr.wa.gov/wildfire-resources/current-wildfire-incident-information"
      priority: 95
      interval_minutes: 15
      verification_status: official_page_seen
      notes: "Later phase must identify official feature services. Do not screen scrape dashboard HTML."

    - id: usgs_eq_geojson
      enabled: false
      source_family: usgs
      source_class: official_seismic_volcano
      adapter: geojson_feed
      url: "https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php"
      priority: 85
      interval_minutes: 5
      verification_status: official_page_seen
      filters:
        min_magnitude: 3.5
        region_hint: "Washington / PNW"

    - id: nwcc_fire_info
      enabled: false
      source_family: nwcc
      source_class: official_wildfire
      adapter: rss_atom
      homepage_url: "https://nwccinfo.blogspot.com/"
      priority: 85
      interval_minutes: 30
      verification_status: official_page_seen
      notes: "Verify feed endpoint and policy before ingest."

    - id: king_county_emergency_news
      enabled: false
      source_family: county_emergency
      source_class: county_emergency
      adapter: wordpress_feed_candidate
      homepage_url: "https://kcemergency.com/"
      priority: 90
      interval_minutes: 10
      verification_status: official_page_seen

    - id: pse_outage_map
      enabled: false
      source_family: pse
      source_class: official_utility
      adapter: source_health_probe_only
      homepage_url: "https://www.pse.com/outage/outage-map"
      priority: 75
      interval_minutes: 15
      verification_status: official_page_seen
      notes: "Do not scrape map. Research official data endpoint later."

SECTION 13: REGIONAL UI architecture

Design the eventual REGIONAL page.

Do not implement it.

The REGIONAL page should use the same console style.

Propose four bays.

Bay 1:
- "Regional attention now"
- Highest-ranking REGIONAL events.
- Must show why each item is ranked.
- Must show source-family badges.
- Must show official vs news vs community convergence.
- Must show observed time and last seen.
- Must not dump raw low-impact incidents.

Bay 2:
- "Hazards and emergency"
- WA EMD, county emergency pages, NWS, NWRFC, WA DNR, NWCC, USGS, PNSN, Ecology, AirNow.
- Show active official alerts first.
- Show wildfire, smoke, flood, earthquake, tsunami, volcano, and public-health signals.
- Show source freshness.

Bay 3:
- "Movement and infrastructure"
- WSDOT, WSF, passes, bridges, highways, border crossings, transit, ports, airports, utilities.
- Useful for "will this affect getting around, power, travel, freight, airport, ferry, or region-wide operations?"

Bay 4:
- "Regional press and civic pulse"
- Washington State Standard, KUOW, KNKX, OPB, Cascade PBS, Seattle Times, Herald, Tacoma News Tribune, Spokesman, KING5, KIRO, KOMO, FOX 13, and future configured sources.
- Social/community signals only if configured and compliant.
- No fake headlines.
- If disabled, show "REGIONAL news sources not configured."

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
- geographic label, such as county, route, pass, basin, zone, corridor, or region

Empty states:

- REGIONAL recent-signal layer disabled.
- REGIONAL sources not configured.
- REGIONAL sources configured but disabled.
- REGIONAL sources configured but never scanned.
- REGIONAL sources stale.
- REGIONAL source policy blocked.
- REGIONAL parser failed.
- REGIONAL social sources disabled by policy.
- REGIONAL homepage extraction disabled by policy.

SECTION 14: Evidence model for REGIONAL

Every item/event must trace back to source evidence.

For a REGIONAL event, evidence should include:

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
- geographic match basis
- public impact basis
- source diversity basis
- privacy redaction decision
- retention expiration
- matching tokens
- event type
- event confidence
- policy notes

For hazard events, evidence must also include, where available:

- alert severity
- urgency
- certainty
- effective time
- expiration time
- affected zones
- county
- route
- river gauge
- AQI station
- fire name
- fire size
- containment
- evacuation level
- earthquake magnitude
- earthquake depth
- volcano alert level
- tsunami status
- source instructions URL

For transport events, evidence must include, where available:

- route
- direction
- pass
- ferry route
- terminal
- airport
- port
- start time
- end time
- delay estimate
- closure status
- detour note
- source update time

SECTION 15: Source health for REGIONAL

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

Source health must be visible in SYSTEM later and summarized in REGIONAL Bay 4 or a footer strip.

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

SECTION 16: First implementation sequence for REGIONAL

Design future phases.

Phase R0: this design
- Create design doc.
- Update BACKLOG.
- No runtime behavior change.

Phase R1: source registry scaffolding
- Add disabled REGIONAL source config.
- Add source registry schema or tables if not already done by global architecture.
- Add tests proving REGIONAL disabled by default.
- No network.

Phase R2: local fixtures only
- Create fixture files for:
  NWS active alert JSON for Washington.
  WSDOT travel alert JSON.
  WSF bulletin fixture.
  WA DNR wildfire fixture.
  NWCC RSS or Atom fixture if feed verified later.
  USGS earthquake GeoJSON fixture.
  USGS water API fixture.
  King County emergency WordPress feed fixture.
  Ecology AQI fixture.
  Regional news RSS fixture.
  PSE outage fixture if endpoint verified later.
- Parse fixtures only.
- Store normalized metadata.
- No live fetch.

Phase R3: REGIONAL event correlation
- Deterministic token/location/time matching.
- No LLM.
- Tests for convergence.
- Tests for duplicate suppression.
- Tests for source-family diversity.
- Tests for route/pass/county/basin matching.

Phase R4: REGIONAL ranking
- Implement scoring model.
- Explain ranking in JSON.
- Tests for official severity, source diversity, recency, public impact, out-of-region penalty, stale-source penalty, and privacy penalty.

Phase R5: REGIONAL UI disabled and fixture-backed states
- Replace REGIONAL placeholders with honest states.
- Fixture-backed in tests only.
- No live fetch.
- No fake headlines.

Phase R6: official API/RSS live fetch, opt-in only
- Start with one safe official source.
- Suggested first candidates:
  NWS alerts for Washington.
  WSDOT Traveler API.
  USGS earthquake GeoJSON.
  King County Emergency News feed if valid.
- Must be disabled by default.
- Must use explicit command.
- No page-load fetch.

Phase R7: additional official sources
- WA DNR wildfire source only after official endpoint verification.
- NWRFC/USGS water after endpoint/filter design.
- WSF API after access-code/auth handling is designed.
- Ecology/AirNow after endpoint and policy review.
- County emergency sources after feed verification.

Phase R8: regional news RSS
- Publisher feeds only.
- Store metadata only.
- No article bodies.
- No paywall bypass.

Phase R9: official dashboards and ArcGIS research
- WA DNR dashboard, outage maps, and other dashboards only through official feature services if found.
- No HTML dashboard scraping.
- If no official data endpoint is found, keep source_health_probe_only or manual_review_only.

Phase R10: social/community
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
- REGIONAL disabled by default.
- Source disabled by default.
- Invalid source class rejected.
- Invalid adapter rejected.
- Social source rejected unless allow_social_sources true.
- Homepage extraction rejected unless allow_homepage_extractors true.
- Oregon/BC sources rejected unless include_oregon_when_relevant or include_bc_when_relevant true.
- Source without URL rejected unless adapter supports no URL.
- Secrets not allowed in config.example.yml.

Registry:
- Source keys unique.
- Source family valid.
- Source class valid.
- Verification status valid.
- Retention settings valid.
- Geography filters valid.
- Corridor filters valid.

Parser fixture tests:
- NWS alert JSON fixture parses.
- WSDOT travel alert fixture parses.
- WSF bulletin fixture parses.
- USGS earthquake GeoJSON fixture parses.
- USGS water API fixture parses.
- WA DNR wildfire fixture parses.
- King County emergency feed fixture parses.
- Regional news RSS fixture parses.
- Malformed feed fails soft.
- Oversized payload blocked or truncated.

Privacy tests:
- Routine local police/fire item does not elevate to REGIONAL.
- Exact private address suppressed unless official public-impact incident.
- Social-only vague report does not outrank official alert.
- State/county public-health alert shows official source and action URL, not invented advice.

Correlation tests:
- WSDOT pass closure plus NWS winter storm warning plus regional news becomes one event.
- WA DNR wildfire plus NWS red flag plus Ecology smoke/AQI plus news becomes one event.
- Same event from multiple news outlets counts as news-family convergence but not endless duplicate inflation.
- Same source repeated does not inflate source diversity.
- Different source families increase diversity.
- Route/county mismatch prevents false merge.
- Out-of-region Oregon/BC item only appears if relevant to configured REGIONAL rules.

Ranking tests:
- Official severe weather warning outranks generic news.
- Major pass closure outranks minor local road incident.
- WSF route shutdown outranks small local traffic delay.
- Large wildfire with evacuation and smoke impact outranks generic wildfire article.
- Earthquake above threshold near Puget Sound outranks small distant quake.
- Regional outage above customer threshold outranks single small outage.
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
- Geographic label visible.

Safety tests:
- No page-load external fetches.
- No hidden LLM calls.
- No telemetry.
- No package install.
- No sudo.
- No social fetch unless explicitly configured.

SECTION 18: Backlog update requirements

Update BACKLOG.md.

Add a section named:

REGIONAL Pacific Northwest Recent Signal Layer

Add concrete backlog items with Status: not implemented.

Include at least:

- REGIONAL source registry design implemented from document.
- Disabled-by-default REGIONAL config.
- REGIONAL SQLite schema or extension.
- REGIONAL fixture pack.
- NWS alert parser for Washington.
- WSDOT Traveler API fixture parser.
- WSF bulletin/API fixture parser.
- WA DNR wildfire endpoint research.
- NWCC feed verification.
- USGS earthquake GeoJSON parser.
- USGS water/hydrology fixture parser.
- NWRFC endpoint research.
- Ecology/AirNow AQI endpoint research.
- PSE/SnoPUD/Tacoma outage endpoint research.
- King County emergency feed parser.
- County emergency alert source verification.
- Regional news RSS parser.
- REGIONAL deterministic event correlation.
- REGIONAL deterministic ranking.
- REGIONAL privacy and public-impact rules.
- REGIONAL UI disabled states.
- REGIONAL source health states.
- REGIONAL evidence drawer contract.
- REGIONAL official-source live ingest phase, disabled by default.
- REGIONAL news RSS ingest phase, disabled by default.
- REGIONAL social source policy review, disabled by default.
- Documentation for source verification.
- Tests for no page-load external fetches.

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
- No exact-address amplification for low-value private incidents.
- No scraping behind login.
- No bypassing Reddit/X/API restrictions.
- No claiming social chatter is verified fact.
- No treating unofficial aggregators as official.
- No treating duplicate articles as independent confirmation.
- No turning REGIONAL into a fear dashboard.
- No burying LOCAL urgent items under REGIONAL headlines.
- No importing Oregon or BC content unless regional relevance rules allow it.

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
6. Confirmation that REGIONAL remains disabled by default.
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

Do not run curl against source targets for this t
::contentReference[oaicite:2]{index=2}
ask.
```

This one should run after `001_local.md` finishes and you either commit it or knowingly accept the dirty diff. The next natural prompt after this is `003_national.md`, same source-target design lane.

[1]: https://wsdot.wa.gov/traffic/api/?utm_source=chatgpt.com "Traveler Information API"
