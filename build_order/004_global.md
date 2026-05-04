Use this as `build_order/004_global.md`.

I kept it design-only like `001_local.md`: source architecture, target inventory, ranking model, no collectors, no live fetches, no dependencies, no runtime changes, BACKLOG law, and proof at the end.

For GLOBAL, I biased the source set toward official or documented global feeds/APIs first: GDACS feeds/API for global disasters, ReliefWeb API for humanitarian reports and disasters, WHO Disease Outbreak News API, HDX HAPI, WMO severe weather CAP warning sources, NASA FIRMS fire APIs, USGS global earthquake feeds, NHC RSS, ECDC RSS, World Bank Indicators API, and ACLED/GDELT only as policy-sensitive or heavy-source candidates. ([GDACS][1])

```text
You are working in the console-1706 repository.

This task assumes the prior scoped recent-signal architecture prompt, LOCAL Seattle design prompt, REGIONAL Pacific Northwest design prompt, and NATIONAL United States design prompt have either already been run, or will be pasted above this prompt.

This is a GLOBAL scope architecture, source-target inventory, and ranking design task only.

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

Your job is to design the GLOBAL recent-signal layer in enough detail that later Codex passes can implement it safely, source by source, without guessing.

Before doing anything, inspect the current repo state and previous design outputs.

Required first checks:

pwd
git status --short
find docs/project -maxdepth 1 -type f -print | sort || true
grep -n "Recent Signal\|News Ingestion\|LOCAL\|REGIONAL\|NATIONAL\|GLOBAL" BACKLOG.md || true

If previous docs exist, read them first and extend them cleanly:

- docs/project/NEWS_SCOPE_INGESTION_ARCHITECTURE_DESIGN.md
- docs/project/LOCAL_SEATTLE_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md
- docs/project/REGIONAL_PNW_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md
- docs/project/NATIONAL_US_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md

Do not duplicate BACKLOG sections already added by previous tasks. Extend the relevant section cleanly or add a new GLOBAL subsection.

The user intent:

console-1706 is a local-only home dashboard running at http://127.0.0.1:1706/.

The GLOBAL tab should eventually answer:

"What is happening around the world that may matter right now?"

The GLOBAL scope should eventually combine recent signals from:

- Global disaster alert systems.
- Humanitarian crisis feeds.
- International organizations.
- Disease outbreak and public-health alert sources.
- Global weather, cyclone, flood, fire, drought, earthquake, tsunami, volcano, and other hazard sources.
- Global air quality, smoke, and environmental emergency signals.
- International conflict, diplomacy, humanitarian, and human-rights sources where public and policy-compliant.
- Global transportation, aviation, maritime, supply-chain, and infrastructure disruption sources where public and useful.
- Global cyber and technology-risk sources where public and useful.
- Global economic and institutional data releases, but only when configured and public-impact relevant.
- Global news outlets, wires, public media, and nonprofit journalism.
- Community/social global signals only when accessible through compliant, explicitly configured methods.
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
- docs/project/NATIONAL_US_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md, if it exists
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

   docs/project/GLOBAL_WORLD_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md

   Create docs/project if it does not exist.

2. Update BACKLOG.md with concrete future implementation tasks flowing from this GLOBAL design.

3. Do not touch application code unless absolutely necessary. This should normally be docs plus BACKLOG only.

4. Do not perform live source verification. The source links below are seed targets. Classify them as candidate links and design how they should be verified in a later phase.

5. The final response must prove what changed and what did not change.

The design document must include the following sections.

SECTION 1: Purpose

Explain the GLOBAL scope in plain engineering language.

The GLOBAL scope is the world recent-signal layer. It should tell the user what is happening globally, with source provenance, observed time, source kind, ranking reason, and evidence.

It is not:

- A global web crawler.
- A world news archive.
- A doom feed.
- A war tracker.
- A surveillance system.
- A social media monitoring system.
- A conflict intelligence platform.
- A financial trading dashboard.
- A diplomatic intelligence dashboard.
- A hidden LLM summarizer.
- A cloud service.
- A replacement for NATIONAL United States.
- A replacement for REGIONAL Washington / PNW.
- A replacement for ORBITAL space and sky signals.

It is:

- A local, short-retention metadata dashboard.
- A deterministic cross-source event detector for global public-impact signals.
- A source-health aware recent-signal system.
- A GLOBAL tab in console-1706 that can surface disasters, humanitarian crises, disease outbreaks, severe weather, tropical cyclones, earthquakes, volcanoes, air quality, international public-health alerts, geopolitical crises, supply-chain disruption, global cyber risk, international institutional actions, and global news.
- A way to rank items by independent source convergence, official severity, global reach, U.S. or local relevance, freshness, and user-configured source priority.

Make clear that "global" means useful public, configured, lawful, recent signals that the user chooses to enable. It does not mean unbounded crawling, private data collection, global social surveillance, or automated geopolitical analysis.

SECTION 2: Global scope boundaries

Define GLOBAL geography and relevance.

Default GLOBAL scope:

- World events outside the United States.
- International events that affect multiple countries.
- International organizations and global systems.
- Global disaster, humanitarian, health, weather, hazard, conflict, infrastructure, economy, transport, and cyber signals.
- U.S. events only when they are part of a global event or directly affect global systems.
- Washington or Seattle events only when they are part of a global signal, such as port logistics, aviation systems, international health, major earthquake/tsunami basin impacts, or global supply chain.
- Global news outlets and international public media when they cover events with broad world importance.
- Country-level official signals only when they are strong enough to matter globally or when configured by the user.

Out of GLOBAL by default:

- Routine Seattle items. Those belong in LOCAL.
- Routine Washington / PNW items. Those belong in REGIONAL.
- Routine U.S. national items. Those belong in NATIONAL.
- Ordinary foreign domestic politics with no broader public impact.
- Generic punditry.
- Conflict rumor.
- Single-source social chatter.
- Graphic violence amplification.
- Private distress.
- Commodity price speculation.
- Investment advice.
- Sources requiring login, payment, scraping around controls, or tokens not explicitly configured by the user.

Design a later config escape hatch:

global:
  enabled: false
  default_place_label: "World"
  include_disasters: true
  include_humanitarian: true
  include_public_health: true
  include_weather_hazards: true
  include_tropical_cyclones: true
  include_earthquakes: true
  include_tsunami: true
  include_volcanoes: true
  include_wildfire_smoke: true
  include_air_quality: true
  include_conflict_humanitarian: true
  include_diplomacy_institutions: true
  include_transport_supply_chain: true
  include_cybersecurity: true
  include_global_economy: false
  include_global_news: true
  include_social_sources: false
  include_us_impact_tags: true
  include_local_impact_tags: true
  earthquake_min_magnitude: 6.0
  tsunami_attention_minimum: "watch"
  tropical_cyclone_attention_minimum: "watch"
  gdacs_attention_minimum: "orange"
  humanitarian_attention_minimum: "disaster"
  outbreak_attention_minimum: "who_don"
  conflict_attention_minimum: "official_or_multi_source"
  wildfire_attention_minimum: "major_or_smoke_impact"

SECTION 3: Relationship to NATIONAL, REGIONAL, LOCAL, ORBITAL, and OVERVIEW

Explain how GLOBAL interacts with other scopes.

Rules:

- GLOBAL should not duplicate NATIONAL unless the U.S. item has direct international or global-system impact.
- GLOBAL should not duplicate REGIONAL or LOCAL unless the regional/local item is part of a global event or has global impact.
- NATIONAL owns U.S. federal, domestic, regulatory, recall, national weather, U.S. aviation, U.S. cyber, and U.S. official public-impact signals.
- REGIONAL owns Washington / PNW hazards, transit, state emergency, wildfire, smoke, and regional news.
- LOCAL owns Seattle-level signals.
- ORBITAL owns space, astronomy, satellites, solar weather, launch, NEO, NASA/JPL sky signals, and orbital infrastructure signals.
- GLOBAL may link to ORBITAL only when a space-weather or satellite disruption has global human impact, but canonical space telemetry stays ORBITAL.
- OVERVIEW should select the highest-priority items from LOCAL, REGIONAL, NATIONAL, GLOBAL, ORBITAL, and SYSTEM without burying urgent local/system issues.
- If a GLOBAL item directly affects Seattle, Washington, or the United States, it can be tagged LOCAL_IMPACT, REGIONAL_IMPACT, or NATIONAL_IMPACT while canonical scope remains GLOBAL.
- If a NATIONAL item becomes global, such as a U.S. policy action causing international market or diplomatic effects, it can be promoted or cross-listed into GLOBAL with evidence.

Examples:

- Major earthquake in Japan with tsunami watch across the Pacific: GLOBAL, possible REGIONAL_IMPACT or LOCAL_IMPACT.
- Global WHO Disease Outbreak News item: GLOBAL.
- CDC domestic health alert: NATIONAL unless WHO/ECDC/other international sources also show global spread.
- Seattle port issue: LOCAL and REGIONAL, GLOBAL only if international shipping impact is clear.
- Russia/Ukraine diplomatic development from UN plus Reuters/BBC: GLOBAL.
- U.S. FAA ground stop: NATIONAL, GLOBAL only if international aviation impact is clear.
- Solar storm warning affecting satellites and grids: ORBITAL canonical, GLOBAL impact tag if widespread infrastructure relevance exists.
- GDACS orange/red cyclone alert: GLOBAL.
- Routine foreign election story: GLOBAL only if configured or major public-impact threshold is met.
- Routine UN speech: low priority unless tied to an active crisis, sanction, resolution, humanitarian emergency, or global event.

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

- official_global_alert
- official_disaster
- official_humanitarian
- official_public_health
- official_weather_hazard
- official_tropical_cyclone
- official_wildfire
- official_air_quality
- official_water_flood
- official_seismic_volcano
- official_tsunami
- official_conflict_humanitarian
- official_human_rights
- official_diplomacy
- official_nuclear_safety
- official_transport
- official_aviation
- official_maritime
- official_cybersecurity
- official_economic
- official_development
- official_environment
- global_news
- wire_service
- public_media
- nonprofit_news
- regional_global_news
- social_candidate
- heavy_open_data_candidate
- unofficial_aggregator
- source_health_only
- manual_review_only

Use these adapter types:

- rss_atom
- static_html_headline_candidate
- official_api_json
- cap_alerts
- geojson_feed
- disaster_api_json
- humanitarian_api_json
- hdx_hapi_json
- who_api_json
- ecdc_rss
- gdacs_feed
- gdacs_api
- reliefweb_api
- acled_api_candidate
- gdelt_api_candidate
- worldbank_api_json
- imf_api_candidate
- csv_download_candidate
- data_catalog_candidate
- arcgis_feature_service_candidate
- nasa_firms_api_candidate
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

Global disaster, humanitarian, and crisis sources:

https://www.gdacs.org/
https://www.gdacs.org/feed_reference.aspx
https://www.gdacs.org/gdacsapi/swagger/index.html
https://www.gdacs.org/Documents/2025/GDACS_API_quickstart_v1.pdf
https://reliefweb.int/
https://reliefweb.int/disasters
https://reliefweb.int/updates
https://reliefweb.int/help/api
https://apidoc.reliefweb.int/
https://apidoc.reliefweb.int/endpoints
https://data.humdata.org/
https://data.humdata.org/hapi
https://hapi.humdata.org/
https://data.humdata.org/faqs/devs
https://www.unocha.org/
https://www.unocha.org/news-and-stories
https://reports.unocha.org/
https://cerf.un.org/
https://www.ifrc.org/emergencies
https://go.ifrc.org/
https://www.icrc.org/en/news-and-events
https://www.ifrc.org/rss.xml

United Nations, diplomacy, human rights, and international institutions:

https://news.un.org/en/
https://news.un.org/en/rss.xml
https://press.un.org/en
https://press.un.org/en/rss.xml
https://www.un.org/securitycouncil/
https://www.un.org/securitycouncil/content/news
https://www.un.org/en/ga/rss/index.shtml
https://www.ungeneva.org/en/news-media/rss
https://www.ohchr.org/en/press-releases
https://www.ohchr.org/en/rss.xml
https://www.undp.org/news-centre
https://www.unhcr.org/news
https://www.unhcr.org/rss.xml
https://www.unicef.org/press-releases
https://www.unicef.org/rss-feeds
https://www.wfp.org/news
https://www.fao.org/newsroom/en
https://www.fao.org/news/rss
https://www.iaea.org/news
https://www.iaea.org/feeds
https://www-news.iaea.org/
https://www.nato.int/cps/en/natohq/news.htm
https://www.osce.org/press-releases

Global public health and outbreak sources:

https://www.who.int/
https://www.who.int/emergencies/disease-outbreak-news
https://www.who.int/api/news/diseaseoutbreaknews/sfhelp
https://www.who.int/api/news/outbreaks/sfhelp
https://www.who.int/news-room
https://www.who.int/news-room/rss-feeds
https://www.emro.who.int/rss-feeds.html
https://www.afro.who.int/rss-feeds
https://www.paho.org/en/news
https://www.paho.org/en/rss.xml
https://www.ecdc.europa.eu/en/news-events
https://www.ecdc.europa.eu/en/rss-feeds
https://africacdc.org/news/
https://africacdc.org/rss-feed/
https://www.cdc.gov/travel/notices
https://www.cdc.gov/travel/rss
https://www.woah.org/en/what-we-do/animal-health-and-welfare/disease-data-collection/world-animal-health-information-system/
https://wahis.woah.org/
https://www.fao.org/animal-health/en
https://www.fao.org/plant-health/en

Global weather, severe weather, tropical cyclones, and multi-hazard warnings:

https://severeweather.wmo.int/
https://severeweather.wmo.int/sources.html
https://public.wmo.int/
https://wmo.int/news
https://wmo.int/rss.xml
https://www.nhc.noaa.gov/
https://www.nhc.noaa.gov/aboutrss.shtml
https://www.nhc.noaa.gov/data/
https://www.nhc.noaa.gov/gis/
https://www.metoffice.gov.uk/weather/warnings-and-advice/world-warnings
https://www.cyclocane.com/
https://www.cyclocane.com/rss/
https://www.cnmoc.usff.navy.mil/Our-Commands/Fleet-Weather-Center-San-Diego/Joint-Typhoon-Warning-Center/
https://www.tropicalstormrisk.com/
https://www.tropicalstormrisk.com/tracker/dynamic/main_.html
https://www.weather.gov/alerts
https://api.weather.gov/alerts/active

Global earthquake, tsunami, volcano, fire, smoke, air quality, and environment:

https://earthquake.usgs.gov/
https://earthquake.usgs.gov/earthquakes/feed/
https://earthquake.usgs.gov/earthquakes/feed/v1.0/
https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php
https://earthquake.usgs.gov/fdsnws/event/1/
https://www.tsunami.gov/
https://www.weather.gov/tsunami/
https://volcano.si.edu/
https://volcano.si.edu/reports_weekly.cfm
https://www.usgs.gov/programs/VHP
https://volcanoes.usgs.gov/
https://firms.modaps.eosdis.nasa.gov/
https://firms.modaps.eosdis.nasa.gov/api/
https://firms.modaps.eosdis.nasa.gov/web-services/
https://www.airnow.gov/
https://docs.airnowapi.org/
https://www.eea.europa.eu/en
https://www.eea.europa.eu/en/newsroom
https://www.copernicus.eu/en
https://atmosphere.copernicus.eu/
https://climate.copernicus.eu/
https://emergency.copernicus.eu/
https://emergency.copernicus.eu/mapping/list-of-components/EMSR

Global conflict, security, instability, and humanitarian impact candidates:

https://acleddata.com/
https://acleddata.com/acled-api-documentation
https://acleddata.com/terms-and-conditions
https://www.crisisgroup.org/
https://www.crisisgroup.org/latest-updates
https://www.crisisgroup.org/rss.xml
https://www.sipri.org/media/press-release
https://www.sipri.org/rss.xml
https://www.start.umd.edu/data-tools/GTD
https://www.start.umd.edu/gtd-faqs
https://www.undss.org/
https://www.un.org/peacekeeping/
https://peacekeeping.un.org/en/news
https://www.icrc.org/en/news-and-events
https://www.msf.org/latest
https://www.msf.org/rss.xml
https://www.amnesty.org/en/latest/news/
https://www.hrw.org/news
https://www.hrw.org/rss.xml

Global cyber, technology, and infrastructure risk:

https://www.cisa.gov/news-events/cybersecurity-advisories
https://www.cisa.gov/news-events/alerts
https://www.cisa.gov/known-exploited-vulnerabilities-catalog
https://nvd.nist.gov/
https://nvd.nist.gov/developers/start-here
https://www.cve.org/
https://www.first.org/
https://www.first.org/newsroom
https://www.cert.europa.eu/
https://www.cert.europa.eu/publications/security-advisories
https://www.enisa.europa.eu/
https://www.enisa.europa.eu/news
https://www.ncsc.gov.uk/section/keep-up-to-date/all
https://www.ncsc.gov.uk/api/1/services/v1/news-rss-feed.xml
https://www.circl.lu/doc/misp/feed-osint/
https://www.shadowserver.org/news/

Global transport, aviation, maritime, ports, and supply chain:

https://www.icao.int/
https://www.icao.int/Newsroom/Pages/default.aspx
https://www.iata.org/en/pressroom/
https://www.eurocontrol.int/
https://www.eurocontrol.int/network-operations
https://www.eurocontrol.int/rss.xml
https://www.faa.gov/newsroom
https://nasstatus.faa.gov/
https://www.imo.org/
https://www.imo.org/en/MediaCentre/PressBriefings
https://www.imo.org/en/MediaCentre/Pages/WhatsNew.aspx
https://www.marinetraffic.com/
https://www.marinetraffic.com/en/ais-api-services
https://www.porttechnology.org/news/
https://www.supplychaindive.com/
https://www.supplychaindive.com/feeds/news/
https://www.fmc.gov/news/
https://www.bimco.org/news

Global economy, finance, trade, energy, and development:

https://www.imf.org/
https://www.imf.org/en/News
https://www.imf.org/en/News/RSS
https://data.imf.org/
https://www.worldbank.org/en/news
https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation
https://datahelpdesk.worldbank.org/knowledgebase/articles/898599-indicator-api-queries
https://api.worldbank.org/v2
https://www.oecd.org/en/about/data.html
https://www.oecd.org/en/about/newsroom.html
https://www.wto.org/english/news_e/news_e.htm
https://www.wto.org/english/res_e/statis_e/statis_e.htm
https://unctad.org/news
https://unctadstat.unctad.org/
https://www.iea.org/news
https://www.iea.org/data-and-statistics
https://www.opec.org/opec_web/en/press_room/28.htm
https://www.fao.org/worldfoodsituation/foodpricesindex/en/
https://www.fao.org/giews/en/
https://www.fsinplatform.org/global-report-food-crises
https://unstats.un.org/home/
https://sdg.data.gov/

Global open data and trend candidates:

https://www.gdeltproject.org/
https://gdelt.github.io/
https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
https://registry.opendata.aws/gdelt/
https://ourworldindata.org/
https://docs.owid.io/projects/etl/api/chart-api/
https://ourworldindata.org/easier-to-reuse-our-data
https://data.un.org/
https://data.worldbank.org/
https://datacatalog.worldbank.org/
https://data.humdata.org/
https://www.kaggle.com/datasets
https://www.google.org/crisismap/weather_and_events

Global news, public media, wires, and nonprofit journalism:

https://www.reuters.com/world/
https://www.reuters.com/world/rss
https://apnews.com/world-news
https://apnews.com/hub/world-news
https://www.bbc.com/news/world
https://feeds.bbci.co.uk/news/world/rss.xml
https://www.aljazeera.com/
https://www.aljazeera.com/xml/rss/all.xml
https://www.theguardian.com/world
https://www.theguardian.com/world/rss
https://www.france24.com/en/
https://www.france24.com/en/rss
https://www.dw.com/en/top-stories/s-9097
https://rss.dw.com/xml/rss-en-all
https://www.npr.org/sections/world/
https://feeds.npr.org/1004/rss.xml
https://www.pbs.org/newshour/world
https://www.pbs.org/newshour/feeds/rss/world
https://www.cbc.ca/news/world
https://www.cbc.ca/cmlink/rss-world
https://www.abc.net.au/news/world
https://www.abc.net.au/news/feed/51120/rss.xml
https://www3.nhk.or.jp/nhkworld/en/news/
https://www3.nhk.or.jp/rss/news/cat0.xml
https://www.euronews.com/news/international
https://www.euronews.com/rss?level=theme&name=news
https://www.lemonde.fr/en/international/
https://www.lemonde.fr/en/rss/
https://www.propublica.org/
https://www.propublica.org/feeds
https://www.bellingcat.com/
https://www.bellingcat.com/feed/
https://www.occrp.org/en
https://www.occrp.org/en/rss
https://globalvoices.org/
https://globalvoices.org/feed/

Global social/community candidates, policy-sensitive:

https://www.reddit.com/r/worldnews/
https://www.reddit.com/r/news/
https://www.reddit.com/r/geopolitics/
https://www.reddit.com/r/europe/
https://www.reddit.com/r/asia/
https://www.reddit.com/r/africa/
https://www.reddit.com/r/latinamerica/
https://www.reddit.com/r/worldevents/
https://www.reddit.com/r/disasterrelief/
https://x.com/UN
https://x.com/WHO
https://x.com/UNOCHA
https://x.com/UNReliefChief
https://x.com/reliefweb
https://x.com/GDACS
https://x.com/WMO
https://x.com/iaeaorg
https://x.com/ICRC
https://x.com/MSF
https://x.com/ReutersWorld
https://x.com/AP
https://x.com/BBCWorld
https://x.com/aljazeera
https://x.com/USGS_Quakes
https://bsky.app/search?q=global%20breaking%20news
https://bsky.app/search?q=earthquake
https://bsky.app/search?q=GDACS
https://bsky.app/search?q=WHO%20outbreak
https://bsky.app/search?q=humanitarian%20crisis
https://bsky.app/search?q=Reuters%20world
https://bsky.app/search?q=BBC%20world
https://bsky.app/search?q=UN%20Security%20Council

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
- Official APIs, official open data, RSS/Atom, CAP feeds, GeoJSON feeds, disaster APIs, humanitarian APIs, WHO APIs, GDACS feeds, ReliefWeb API, WMO CAP source links, official UN feeds, and official international organization feeds.
- Best first live candidates.

Tier 2:
- Official pages with stable public operational data but no obvious feed/API.
- Candidate only after source-policy review.
- Prefer source-health checks and manual review before parser implementation.

Tier 3:
- Global news RSS or publisher-provided feeds.
- Store headline metadata only.
- No article-body archive.
- No paywall bypass.

Tier 4:
- Public media, nonprofit outlets, humanitarian organizations, and specialist topic outlets.
- Prefer RSS/Atom or documented APIs.
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
- Heavy open-data aggregators.
- Examples: GDELT, ACLED, Our World in Data, large humanitarian catalogs.
- Useful, but must be scoped, filtered, rate-limited, and carefully documented.
- Do not ingest firehoses.
- Do not let heavy sources dominate the dashboard.
- Some may require accounts, attribution, or terms review.
- Prefer manual review or fixture-only exploration first.

Tier 7:
- Unofficial aggregators and dashboards.
- Useful as human comparison or source-health reference.
- Do not treat as primary authority over official sources.
- Do not clone their work or scrape aggressively.
- If used later, source-health-only or manual-review-only unless policy review supports more.

SECTION 6: GLOBAL event model

Design a GLOBAL event model that sits above raw items.

The system should not only store "news items." It should infer that multiple recent items refer to the same global event.

Propose a future global_events table or explain how news_clusters should be extended.

A GLOBAL event should have:

- global_event_id
- scope
- event_key
- event_type
- title
- representative_item_id
- severity
- public_impact_score
- source_diversity_score
- official_confirmation_score
- humanitarian_impact_score
- health_impact_score
- disaster_score
- weather_hazard_score
- conflict_humanitarian_score
- diplomacy_institution_score
- transport_supply_chain_score
- cyber_impact_score
- economic_impact_score
- social_echo_score
- news_echo_score
- us_impact_score
- regional_impact_score
- local_impact_score
- first_seen_at
- last_seen_at
- last_elevated_at
- expires_at
- geography_json
- countries_json
- regions_json
- organizations_json
- source_ids_json
- item_ids_json
- evidence_json
- ranking_explanation_json
- status

Event types should include at least:

- global_disaster_alert
- earthquake_global
- tsunami_global
- tropical_cyclone
- flood_global
- wildfire_global
- smoke_air_quality_global
- volcano_unrest_global
- drought_food_security
- disease_outbreak
- public_health_emergency
- humanitarian_crisis
- displacement_crisis
- famine_food_security
- conflict_humanitarian
- ceasefire_peacekeeping
- sanctions_diplomacy
- international_institution_action
- human_rights_alert
- nuclear_safety_event
- aviation_global_disruption
- maritime_port_disruption
- supply_chain_disruption
- cyber_global_advisory
- global_economic_release
- commodity_food_energy_shock
- major_global_news
- community_signal
- source_health_problem

Make clear that routine low-impact global news should not automatically become elevated GLOBAL events.

SECTION 7: Cross-source convergence ranking

Design deterministic ranking around this idea:

If something appears in official international sources, disaster feeds, humanitarian feeds, health feeds, hazard feeds, global news, and community/social signals within a short window, it is probably important or interesting.

Implement this as design only.

Do not design an LLM summarizer.

The scoring model must be explainable.

Required scoring factors:

1. Official severity

Examples:

- GDACS orange or red alert.
- ReliefWeb disaster record or multi-source humanitarian update cluster.
- WHO Disease Outbreak News item.
- WMO severe weather CAP warning where available.
- USGS earthquake above configured magnitude or intensity threshold.
- Tsunami watch, warning, advisory, or basin-wide bulletin.
- Smithsonian / USGS Weekly Volcanic Activity Report item with new or elevated activity.
- NASA FIRMS active fire cluster where configured and public-impact relevant.
- IAEA official nuclear safety alert or emergency-related news.
- UN Security Council action on an active crisis.
- UN OCHA situation report or humanitarian update.
- UNHCR or WFP emergency update.
- ECDC or PAHO outbreak update.
- ACLED conflict signal only if configured, terms-reviewed, and independently corroborated.
- GDELT trend signal only as low-weight echo unless confirmed by official or trusted news sources.

2. Source diversity

Independent source families count more than repeated mentions from the same family.

Example families:

- gdacs
- reliefweb
- unocha
- hdx
- who
- ecdc
- paho
- africa_cdc
- woah
- wmo
- noaa_nhc
- usgs
- tsunami_gov
- smithsonian_gvp
- nasa_firms
- copernicus
- iaea
- un_news
- un_press
- un_security_council
- unhcr
- wfp
- fao
- ifrc
- icrc
- msf
- ohchr
- acled
- gdelt
- reuters
- ap
- bbc
- al_jazeera
- guardian
- france24
- dw
- npr_world
- public_media
- nonprofit_investigative
- reddit
- bluesky
- x_api
- source_health

3. Temporal proximity

Items closer in time are more likely to be the same event.

Propose matching windows:

- Breaking global news: 0 to 24 hours.
- Disaster alert: active alert duration or 0 to 72 hours.
- Earthquake/tsunami: 0 to 24 hours, with aftershock clustering.
- Tropical cyclone: active advisory cycle or 0 to 7 days.
- Flood/wildfire/smoke: 0 to 72 hours, longer only if active.
- Volcano unrest: 0 to 7 days, official sources preferred.
- Disease outbreak: 0 to 14 days, with active event extension.
- Humanitarian crisis: 0 to 14 days, with active event extension.
- Conflict humanitarian event: 0 to 72 hours for breaking events, 0 to 14 days for official situation reports.
- International institution action: 0 to 72 hours unless tied to active crisis.
- Supply-chain/transport disruption: 0 to 48 hours.
- Cyber advisory: 0 to 14 days.
- Economic release: release day plus 24 hours unless follow-up coverage converges.

4. Geographic proximity and reach

Match by:

- country
- region
- continent
- ocean basin
- disaster id
- storm id
- earthquake id
- volcano name
- humanitarian operation id
- UN region
- WHO region
- affected border
- affected airspace
- affected sea lane
- affected port
- affected agency
- affected population group
- affected disease/outbreak name
- affected infrastructure sector

5. Public impact

Boost:

- official global disaster alerts
- large earthquakes
- tsunami warnings
- tropical cyclone watches/warnings
- major floods
- major wildfires or smoke events
- disease outbreaks
- humanitarian crises
- evacuation/displacement
- famine/food insecurity
- nuclear safety incidents
- major aviation or maritime disruption
- major cyber advisories with global exploitation
- international institutional action tied to active crises
- global supply-chain disruption
- events with U.S., PNW, or Seattle impact tags
- multi-source news convergence from independent regions or source families

6. Recency

Recent items matter more, but older active hazards can stay elevated while still active.

7. User-configured priority

Allow future config to boost:

- global disasters
- humanitarian crises
- disease outbreaks
- earthquakes
- tsunami
- volcanoes
- tropical cyclones
- aviation
- maritime
- cyber
- nuclear safety
- food security
- Europe
- Middle East
- East Asia
- Pacific
- Latin America
- Africa
- Arctic
- U.S. impact
- Seattle impact
- Washington impact
- specific countries
- specific organizations
- specific source families

8. Low-public-value penalty

De-emphasize:

- routine diplomatic remarks
- generic summit coverage
- single-source political opinion
- minor foreign domestic politics with no wider impact
- conflict rumor without official or trusted reporting
- social-only claims
- duplicate syndicated stories
- old humanitarian updates that do not change the situation
- data releases not on the configured attention list
- commodity speculation
- content that lacks source provenance

The design must include a sample scoring formula.

Example:

score =
  recency_score
  + official_severity_score
  + source_diversity_score
  + public_impact_score
  + geographic_reach_score
  + active_alert_score
  + humanitarian_impact_score
  + us_or_local_impact_score
  + source_priority_score
  + cluster_size_score
  - duplicate_family_penalty
  - stale_source_penalty
  - low_confidence_penalty
  - low_public_value_penalty
  - out_of_scope_penalty
  - rumor_penalty

The design must explain that "frequency of appearance" means independent cross-source convergence, not raw duplicate counts.

Bad ranking:

- 40 syndicated versions of the same foreign politics article dominate.

Good ranking:

- GDACS red earthquake alert.
- USGS earthquake record confirms magnitude.
- Tsunami center posts basin notice.
- ReliefWeb or OCHA begins situation reporting.
- Reuters/BBC/AP cover impact.
- Local/regional impact tag appears only if tsunami or travel relevance exists.
- Social chatter appears only as a low-weight echo if compliant.
- All within a plausible time window.

SECTION 8: GLOBAL source category design

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

1. Global disaster alerts.

2. Humanitarian crises and response.

3. Global public health and outbreaks.

4. Weather, tropical cyclones, flood, drought, and severe hazards.

5. Earthquake, tsunami, volcano, fire, smoke, and environmental emergencies.

6. Conflict-humanitarian and human-rights sources.

7. United Nations, diplomacy, and international institutions.

8. Cybersecurity and global technology risk.

9. Transport, aviation, maritime, ports, and supply chain.

10. Global economy, finance, trade, food, energy, and development.

11. Global open-data and trend candidates.

12. Global news, wires, public media, and nonprofit journalism.

13. Social/community echoes.

14. Source health and disabled states.

SECTION 9: GLOBAL conflict, health, and humanitarian sensitivity posture

Design this carefully.

Rules:

- Store source-provided public metadata only.
- Do not store full narratives beyond bounded descriptions.
- Do not archive social posts long term.
- Do not store graphic content.
- Do not reproduce casualty lists or identifiable victim details.
- Do not infer blame, attribution, responsibility, or intent beyond source metadata.
- Do not treat social reports as verified fact.
- Do not turn GLOBAL into a war ticker.
- Do not turn GLOBAL into a fear dashboard.
- Preserve source links in evidence so the user can click official sources.
- For major incidents, show public operational facts:
  event type, source, source family, affected country/region, public impact, observed time, source link.
- Treat early official reports as preliminary where applicable.
- For public-health events, show official source and action URL, not invented advice.
- For conflict-humanitarian events, prefer humanitarian impact framing over sensational framing.
- For human-rights or conflict sources, use extra caution around advocacy-source vs official-source labeling.
- For ACLED, GDELT, Crisis Group, human-rights NGOs, and similar sources, preserve source-family labels and policy notes.
- Social-only global claims should never outrank official alerts or trusted news.

SECTION 10: GLOBAL source freshness and retention

Design short retention.

Default candidate retention:

- Raw fetch diagnostics: 7 days or less.
- Raw payload debug: disabled by default. If ever enabled, 6 hours max by default.
- Official disaster alert metadata: expiration plus 24 to 72 hours.
- Humanitarian crisis metadata: 14 days, with active event extension only if source updates continue.
- Public health outbreak metadata: 14 to 30 days depending on source expiration and severity.
- Tropical cyclone/advisory metadata: active storm plus 7 days.
- Weather/hazard metadata: expiration plus 24 to 48 hours.
- Earthquake metadata: 7 days for significant global events, 14 days for major events.
- Tsunami metadata: expiration plus 48 hours.
- Volcano unrest metadata: 14 days while active, official or specialist sources preferred.
- Fire/smoke metadata: 7 to 14 days while active, then expire.
- Conflict-humanitarian metadata: 7 to 14 days, with careful source labeling.
- Global cyber advisory metadata: 14 to 30 days.
- Transport/supply-chain disruption metadata: 3 to 7 days.
- Economic release metadata: 3 to 7 days.
- Global news headline metadata: 7 days.
- Global event clusters: 7 to 14 days.
- Source health: 30 days.
- Ranking explanations: same as event/item retention.
- Social metadata, if ever enabled: 24 to 72 hours unless source terms require shorter or prohibit storage.

Every ingest run in later phases must purge expired data.

No article body archive.

No permanent global incident archive.

No permanent social archive.

SECTION 11: Adapter design for GLOBAL

Design future adapter families.

Do not implement now.

Required adapter families:

rss_atom:
- UN News RSS.
- UN Press RSS.
- WHO regional RSS where useful.
- ECDC RSS.
- IAEA feeds.
- global news feeds.
- nonprofit and public-media feeds.
- Must parse title, URL, published timestamp, description, categories.
- Must bound description length.
- Must not fetch article bodies.

gdacs_feed:
- GDACS RSS/XML feeds.
- Must preserve alert level, event id, event type, countries, coordinates if available, event start/update times, severity, and official URL.
- Should use feed reference paths only after verification.

gdacs_api:
- GDACS API candidate.
- Must be disabled by default until fixture tests exist.
- Must preserve event id and avoid duplicate feed/API inflation.

reliefweb_api:
- ReliefWeb API for reports and disasters.
- Must preserve disaster id, report id, source, country, date, format, theme, and official ReliefWeb URL.
- Must not store full report bodies by default.

humanitarian_api_json:
- OCHA and IFRC candidates.
- Must preserve source organization, situation id if available, country, affected population metadata if source provides it, and source URL.
- Must not infer casualty or displacement numbers beyond source metadata.

hdx_hapi_json:
- HDX HAPI candidate.
- Useful for curated humanitarian indicators.
- Disabled by default until scoped query rules exist.
- Must not ingest broad catalogs into dashboard.

who_api_json:
- WHO Disease Outbreak News and outbreak API candidates.
- Must preserve disease/outbreak name, country, WHO region, publication date, summary metadata, and official URL.
- Must not invent medical advice.

ecdc_rss:
- ECDC RSS feeds.
- Must preserve feed category and source URL.
- Useful for Europe-focused public health signals.

cap_alerts:
- WMO SWIC / CAP warning sources, where machine-readable CAP links are verified.
- Must preserve severity, urgency, certainty, effective time, expiration, affected area, issuing authority, and instruction URL.
- Must not treat every national weather warning as global. Use threshold filters.

geojson_feed:
- USGS earthquake GeoJSON.
- Tsunami or hazard geospatial feeds if verified.
- Must support magnitude, region, depth, tsunami flag, distance, and bounding filters.

nasa_firms_api_candidate:
- NASA FIRMS API candidate for global active fire data.
- Requires map key handling if needed.
- Must be disabled by default.
- Must use strict geographic and severity filters.
- Must not ingest global firehose data.

official_api_json:
- WHO, UN, ECDC, World Bank, IMF, OECD, IEA, CISA, NVD, or other official JSON endpoints where verified.
- Must support timeouts, response size caps, source-specific rate limits, and conditional requests when available.

worldbank_api_json:
- World Bank Indicators API.
- Must be allowlisted by indicator and country/region.
- Must not become a general economic database.
- Dashboard use should focus on scheduled release or specific configured indicators, not constant polling.

imf_api_candidate:
- IMF data source candidate.
- Must verify current API and usage terms before implementation.
- Disabled by default.

acled_api_candidate:
- ACLED API candidate.
- Policy-sensitive.
- Must require explicit configuration, terms review, credentials if required, attribution notes, and short retention.
- Do not implement in early phases.

gdelt_api_candidate:
- GDELT candidate.
- Heavy open-data firehose.
- Must be disabled by default.
- Must use strict query allowlists, time windows, and result caps.
- Treat as low-weight media-trend echo, not authoritative fact.

csv_download_candidate:
- Only for official CSV data with stable schema.
- Disabled by default until fixture tests exist.
- Must cap rows and support updated-since or short retention.

data_catalog_candidate:
- Data catalogs are discovery surfaces, not live dashboard feeds.
- Manual review only unless a specific dataset is promoted.

arcgis_feature_service_candidate:
- Only if official global feature services are discovered.
- Do not screen scrape dashboards.

static_html_headline_candidate:
- Only for official pages or global news pages with no RSS/API.
- Disabled unless homepage extractor support is explicitly allowed.
- Must use per-source selectors.
- No recursive crawling.
- No article-body fetch.
- Robots/policy review required.

source_health_probe_only:
- For dashboards and portals useful as human status references but not suitable for ingestion.

manual_review_only:
- For policy-sensitive, parser-risky, login-required, auth-required, account-required, paywalled, or unclear targets.

SECTION 12: Candidate global source registry example

Include a YAML-like example in the design document.

Do not edit config.example.yml yet unless prior architecture already requires disabled examples.

The example must be disabled by default.

Example shape:

global_sources:
  enabled: false
  label: "World"
  retention:
    official_alert_days: 7
    disaster_days: 14
    humanitarian_days: 14
    public_health_days: 30
    weather_hazard_days: 7
    earthquake_days: 14
    tsunami_days: 7
    volcano_days: 14
    conflict_humanitarian_days: 14
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
    official_severity_weight: 3.5
    public_impact_weight: 3.0
    humanitarian_impact_weight: 3.0
    geographic_reach_weight: 2.5
    recency_weight: 2.0
    us_or_local_impact_weight: 1.5
    social_echo_weight: 0.35
    low_public_value_penalty_weight: 3.0
    rumor_penalty_weight: 4.0
    out_of_scope_penalty_weight: 3.0
  sensitivity:
    suppress_graphic_content: true
    suppress_identifiable_victim_details: true
    social_retention_hours: 48
    social_sources_disabled_by_default: true
    conflict_sources_require_policy_review: true
  relevance:
    include_us_impact_tags: true
    include_regional_impact_tags: true
    include_local_impact_tags: true
    preferred_regions:
      - "Pacific"
      - "East Asia"
      - "Europe"
      - "Middle East"
      - "Americas"
    preferred_country_allowlist: []
  sources:
    - id: gdacs_all_events
      enabled: false
      source_family: gdacs
      source_class: official_global_alert
      adapter: gdacs_feed
      homepage_url: "https://www.gdacs.org/"
      url: "https://www.gdacs.org/feed_reference.aspx"
      priority: 100
      interval_minutes: 10
      verification_status: official_page_seen
      filters:
        alert_minimum: "orange"
      evidence_notes: "Use official GDACS feed reference. Verify exact feed endpoint before live ingest."

    - id: reliefweb_disasters
      enabled: false
      source_family: reliefweb
      source_class: official_humanitarian
      adapter: reliefweb_api
      homepage_url: "https://reliefweb.int/disasters"
      url: "https://apidoc.reliefweb.int/endpoints"
      priority: 95
      interval_minutes: 30
      verification_status: official_page_seen
      filters:
        endpoints:
          - "disasters"
          - "reports"
        limit: 50
      notes: "Store metadata only. Do not store full report bodies."

    - id: who_disease_outbreak_news
      enabled: false
      source_family: who
      source_class: official_public_health
      adapter: who_api_json
      homepage_url: "https://www.who.int/emergencies/disease-outbreak-news"
      url: "https://www.who.int/api/news/diseaseoutbreaknews/sfhelp"
      priority: 100
      interval_minutes: 60
      verification_status: official_page_seen
      notes: "Do not invent medical advice. Preserve official URL and publication time."

    - id: usgs_global_earthquake_geojson
      enabled: false
      source_family: usgs
      source_class: official_seismic_volcano
      adapter: geojson_feed
      url: "https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php"
      priority: 90
      interval_minutes: 5
      verification_status: official_page_seen
      filters:
        min_magnitude: 6.0
        tsunami_flag_attention: true

    - id: wmo_swic_cap_sources
      enabled: false
      source_family: wmo
      source_class: official_weather_hazard
      adapter: cap_alerts
      homepage_url: "https://severeweather.wmo.int/"
      url: "https://severeweather.wmo.int/sources.html"
      priority: 90
      interval_minutes: 15
      verification_status: official_page_seen
      notes: "Later phase must verify CAP source URLs and source-specific warning thresholds."

    - id: nasa_firms_global_fire
      enabled: false
      source_family: nasa_firms
      source_class: official_wildfire
      adapter: nasa_firms_api_candidate
      homepage_url: "https://firms.modaps.eosdis.nasa.gov/"
      url: "https://firms.modaps.eosdis.nasa.gov/api/"
      priority: 80
      interval_minutes: 60
      verification_status: official_page_seen
      notes: "Requires key/config review if map key is needed. Use strict filters. Do not ingest firehose."

    - id: un_news_global
      enabled: false
      source_family: un_news
      source_class: official_diplomacy
      adapter: rss_atom
      homepage_url: "https://news.un.org/en/"
      url: "https://news.un.org/en/rss.xml"
      priority: 70
      interval_minutes: 60
      verification_status: candidate_needs_verification

    - id: gdelt_global_trends
      enabled: false
      source_family: gdelt
      source_class: heavy_open_data_candidate
      adapter: gdelt_api_candidate
      homepage_url: "https://www.gdeltproject.org/"
      priority: 35
      interval_minutes: 120
      verification_status: candidate_policy_sensitive
      notes: "Low-weight trend echo only. Do not ingest broad firehose. Requires strict query allowlist."

SECTION 13: GLOBAL UI architecture

Design the eventual GLOBAL page.

Do not implement it.

The GLOBAL page should use the same console style.

Propose four bays.

Bay 1:
- "Global attention now"
- Highest-ranking GLOBAL events.
- Must show why each item is ranked.
- Must show source-family badges.
- Must show official vs news vs community convergence.
- Must show observed time and last seen.
- Must show country/region label.
- Must not dump low-impact international churn.

Bay 2:
- "Disasters, health, and hazards"
- GDACS, ReliefWeb, OCHA, WHO, ECDC, WMO, USGS, tsunami, volcano, NASA FIRMS, Copernicus, AirNow where useful.
- Show active official alerts first.
- Show source freshness.
- Show disaster, humanitarian, disease outbreak, cyclone, earthquake, tsunami, wildfire, smoke, flood, and volcano signals.

Bay 3:
- "World systems and institutions"
- UN, IAEA, ICRC, IFRC, FAO, WFP, UNHCR, global aviation/maritime, cyber, economy, trade, development, diplomacy.
- Useful for "will this affect global systems, international travel, supply chains, health, security, economy, or institutions?"

Bay 4:
- "Global press and civic pulse"
- Reuters, AP, BBC, Al Jazeera, Guardian, France 24, DW, NPR World, PBS World, NHK, Euronews, Le Monde English, Global Voices, OCCRP, Bellingcat, and future configured sources.
- Social/community signals only if configured and compliant.
- No fake headlines.
- If disabled, show "GLOBAL news sources not configured."

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
- geographic label, such as global, country, region, ocean basin, UN region, WHO region, affected country, affected agency, or affected sector
- U.S., regional, or local impact tag where applicable

Empty states:

- GLOBAL recent-signal layer disabled.
- GLOBAL sources not configured.
- GLOBAL sources configured but disabled.
- GLOBAL sources configured but never scanned.
- GLOBAL sources stale.
- GLOBAL source policy blocked.
- GLOBAL parser failed.
- GLOBAL social sources disabled by policy.
- GLOBAL homepage extraction disabled by policy.
- GLOBAL heavy open-data source disabled by policy.
- GLOBAL source requires token/account and is not configured.

SECTION 14: Evidence model for GLOBAL

Every item/event must trace back to source evidence.

For a GLOBAL event, evidence should include:

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
- humanitarian impact basis
- U.S. or local impact basis
- retention expiration
- matching tokens
- event type
- event confidence
- policy notes
- low-public-value penalty if applied
- rumor penalty if applied
- out-of-scope penalty if applied

For disaster and hazard events, evidence must include, where available:

- alert source
- alert level
- event id
- event type
- affected countries
- affected regions
- coordinates if available and safe to store
- magnitude
- depth
- storm name
- basin
- advisory number
- tsunami status
- volcano name
- fire/smoke indicator
- affected population if source provides it
- effective time
- expiration time
- source instructions URL

For humanitarian and conflict-humanitarian events, evidence must include, where available:

- issuing organization
- country
- region
- crisis/disaster id
- report type
- situation report date
- affected population metadata if source provides it
- source labels/themes
- whether the source is official, NGO, media, or open-data
- whether numbers are preliminary
- official URL

For public health events, evidence must include, where available:

- issuing organization
- disease/outbreak name
- countries or WHO region
- publication date
- source-provided risk framing
- official advice URL
- whether the information is preliminary
- no invented medical advice

For cyber events, evidence must include, where available:

- advisory id
- CVE ids
- product/vendor
- severity if provided
- exploited-in-the-wild flag if provided
- mitigation URL
- issuing organization
- global impact basis

For transport, aviation, maritime, and supply-chain events, evidence must include, where available:

- airport
- port
- route
- airspace
- sea lane
- system
- event type
- delay estimate
- closure status
- start time
- end time
- source update time
- affected countries or regions

SECTION 15: Source health for GLOBAL

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
- heavy_source_disabled
- needs_terms_review
- needs_scope_filter

Source health must be visible in SYSTEM later and summarized in GLOBAL Bay 4 or a footer strip.

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

SECTION 16: First implementation sequence for GLOBAL

Design future phases.

Phase G0: this design
- Create design doc.
- Update BACKLOG.
- No runtime behavior change.

Phase G1: source registry scaffolding
- Add disabled GLOBAL source config.
- Add source registry schema or tables if not already done by global architecture.
- Add tests proving GLOBAL disabled by default.
- No network.

Phase G2: local fixtures only
- Create fixture files for:
  GDACS RSS/XML feed.
  GDACS API response.
  ReliefWeb disasters API response.
  ReliefWeb reports API response.
  WHO Disease Outbreak News API response.
  ECDC RSS feed.
  WMO CAP warning fixture.
  USGS earthquake GeoJSON fixture.
  NHC RSS fixture.
  Smithsonian GVP weekly report fixture.
  NASA FIRMS small filtered response fixture.
  UN News RSS fixture.
  IAEA RSS fixture.
  Reuters/BBC/Al Jazeera RSS fixture.
  GDELT tiny fixture, if policy review allows fixture-only exploration.
- Parse fixtures only.
- Store normalized metadata.
- No live fetch.

Phase G3: GLOBAL event correlation
- Deterministic token/location/time/source-family matching.
- No LLM.
- Tests for convergence.
- Tests for duplicate suppression.
- Tests for source-family diversity.
- Tests for country/region/basin/event-id matching.
- Tests for global vs national vs regional vs local scope routing.

Phase G4: GLOBAL ranking
- Implement scoring model.
- Explain ranking in JSON.
- Tests for official severity, source diversity, recency, public impact, humanitarian impact, U.S./local impact tag, low-public-value penalty, rumor penalty, stale-source penalty, and out-of-scope penalty.

Phase G5: GLOBAL UI disabled and fixture-backed states
- Replace GLOBAL placeholders with honest states.
- Fixture-backed in tests only.
- No live fetch.
- No fake headlines.

Phase G6: official API/RSS live fetch, opt-in only
- Start with one safe official source.
- Suggested first candidates:
  GDACS feed.
  ReliefWeb disasters API.
  WHO Disease Outbreak News API.
  USGS earthquake GeoJSON.
  UN News RSS.
- Must be disabled by default.
- Must use explicit command.
- No page-load fetch.

Phase G7: additional official sources
- WMO CAP warning source after exact source URLs are verified.
- ECDC RSS.
- NHC RSS.
- IAEA feeds.
- Smithsonian GVP fixture/parser.
- NASA FIRMS only after key/config and strict filter design.
- HDX HAPI only after scoped query rules exist.

Phase G8: global news RSS
- Publisher feeds only.
- Store metadata only.
- No article bodies.
- No paywall bypass.
- Do not let news-only clusters outrank official alerts without convergence.

Phase G9: heavy open-data candidates
- ACLED only after terms/auth/attribution review.
- GDELT only with strict allowlists and low-weight trend echo.
- Our World in Data and World Bank only for configured indicators, not firehose ingestion.
- No broad catalogs.

Phase G10: social/community
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
- GLOBAL disabled by default.
- Source disabled by default.
- Invalid source class rejected.
- Invalid adapter rejected.
- Social source rejected unless allow_social_sources true.
- Heavy open-data source rejected unless allow_heavy_open_data_sources true.
- Homepage extraction rejected unless allow_homepage_extractors true.
- Conflict source rejected unless conflict_sources_require_policy_review is satisfied.
- Source without URL rejected unless adapter supports no URL.
- Secrets not allowed in config.example.yml.

Registry:
- Source keys unique.
- Source family valid.
- Source class valid.
- Verification status valid.
- Retention settings valid.
- Country filters valid.
- Region filters valid.
- Organization filters valid.
- Heavy-source filters required.

Parser fixture tests:
- GDACS feed fixture parses.
- GDACS API fixture parses.
- ReliefWeb disasters fixture parses.
- ReliefWeb reports fixture parses.
- WHO Disease Outbreak News fixture parses.
- ECDC RSS fixture parses.
- WMO CAP fixture parses.
- USGS earthquake GeoJSON fixture parses.
- NHC RSS fixture parses.
- Smithsonian GVP fixture parses.
- NASA FIRMS filtered fixture parses.
- UN News RSS fixture parses.
- IAEA RSS fixture parses.
- Global news RSS fixture parses.
- Malformed feed fails soft.
- Oversized payload blocked or truncated.

Sensitivity and low-public-value tests:
- Routine diplomatic statement does not elevate to GLOBAL attention.
- Social-only vague report does not outrank official alert.
- Conflict rumor gets rumor penalty.
- Public-health event shows official source and action URL, not invented advice.
- Humanitarian report preserves source labels and does not invent numbers.
- Graphic or victim-identifying content is not stored.
- Economic data release does not become advice.
- Global news-only event does not outrank official GDACS/WHO/USGS alert unless convergence and public-impact rules justify it.

Correlation tests:
- GDACS earthquake plus USGS earthquake plus Reuters/BBC coverage becomes one event.
- WHO DON plus ECDC/PAHO/Reuters coverage becomes one outbreak event.
- Tropical cyclone NHC/JTWC/GDACS plus news coverage becomes one event.
- ReliefWeb disaster plus OCHA/IFRC report plus news coverage becomes one humanitarian event.
- Same event from multiple news outlets counts as news-family convergence but not endless duplicate inflation.
- Same source repeated does not inflate source diversity.
- Different source families increase diversity.
- National item without global impact does not appear in GLOBAL.
- Regional/local item without global impact does not appear in GLOBAL.
- ORBITAL item without global human impact remains ORBITAL.

Ranking tests:
- GDACS red alert outranks generic world headline.
- WHO Disease Outbreak News item outranks generic health article.
- USGS major earthquake outranks small distant quake.
- Tsunami warning outranks routine tsunami information page.
- Active humanitarian crisis with OCHA/ReliefWeb convergence outranks generic diplomatic remarks.
- IAEA nuclear safety event outranks routine IAEA press item.
- Stale source lowers confidence.
- Source policy blocked item never displays as live.
- Heavy-source GDELT/ACLED item is low-weight unless corroborated.

API design tests for later:
- GET routes read SQLite only.
- GET routes do not fetch network.
- Disabled/not configured/stale/failing/auth_required/heavy_source_disabled states distinct.

UI tests for later:
- No fake headlines.
- Empty states clear.
- Evidence visible.
- Ranking reason visible.
- Source health visible.
- Country/region/organization label visible.
- U.S., regional, and local impact tags visible when applicable.

Safety tests:
- No page-load external fetches.
- No hidden LLM calls.
- No telemetry.
- No package install.
- No sudo.
- No social fetch unless explicitly configured.
- No heavy open-data source fetch unless explicitly configured.
- No token/account source runs without key configuration.

SECTION 18: Backlog update requirements

Update BACKLOG.md.

Add a section named:

GLOBAL World Recent Signal Layer

Add concrete backlog items with Status: not implemented.

Include at least:

- GLOBAL source registry design implemented from document.
- Disabled-by-default GLOBAL config.
- GLOBAL SQLite schema or extension.
- GLOBAL fixture pack.
- GDACS feed parser.
- GDACS API fixture parser.
- ReliefWeb disasters API parser.
- ReliefWeb reports API parser.
- WHO Disease Outbreak News parser.
- ECDC RSS parser.
- WMO CAP warning source verification.
- USGS global earthquake GeoJSON parser.
- NHC RSS parser.
- Smithsonian GVP weekly report parser.
- NASA FIRMS API review and filtered fixture parser.
- UN News RSS parser.
- UN Press RSS parser.
- IAEA RSS parser.
- Humanitarian source evidence contract.
- Conflict-humanitarian sensitivity rules.
- GDELT policy review and strict allowlist design.
- ACLED policy/auth/attribution review.
- World Bank / IMF / OWID configured-indicator design.
- Global news RSS parser.
- GLOBAL deterministic event correlation.
- GLOBAL deterministic ranking.
- GLOBAL low-public-value, rumor, and public-impact rules.
- GLOBAL UI disabled states.
- GLOBAL source health states.
- GLOBAL evidence drawer contract.
- GLOBAL official-source live ingest phase, disabled by default.
- GLOBAL news RSS ingest phase, disabled by default.
- GLOBAL heavy open-data phase, disabled by default.
- GLOBAL social source policy review, disabled by default.
- Documentation for source verification.
- Tests for no page-load external fetches.
- Tests for no heavy source running without explicit config.
- Tests for no token/account source running without config.

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
- No global conflict intelligence platform.
- No war ticker.
- No social surveillance.
- No investment advice.
- No medical advice.
- No legal advice.
- No commodity speculation.
- No scraping behind login.
- No bypassing Reddit/X/API restrictions.
- No claiming social chatter is verified fact.
- No treating advocacy sources as official.
- No treating unofficial aggregators as official.
- No treating duplicate articles as independent confirmation.
- No burying LOCAL, REGIONAL, NATIONAL, SYSTEM, or ORBITAL urgent items under GLOBAL headlines.
- No importing NATIONAL content unless global relevance rules allow it.
- No importing ORBITAL content unless global human-impact rules allow it.
- No automatic API key discovery or secret storage.
- No broad GDELT, ACLED, HDX, World Bank, or OWID firehose ingestion.

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
6. Confirmation that GLOBAL remains disabled by default.
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

This one is deliberately stricter than NATIONAL. GLOBAL can turn into garbage fast: war ticker, doom feed, pundit slurry, GDELT firehose, or pseudo-intel dashboard. The prompt forces it toward official disaster, humanitarian, health, hazard, and institution sources first, with global news as corroborating signal and social/heavy open-data sources locked behind later policy gates.

[1]: https://www.gdacs.org/feed_reference.aspx?utm_source=chatgpt.com "Feed Reference"
