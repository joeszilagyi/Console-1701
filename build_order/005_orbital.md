Use this as `build_order/005_orbital.md`.

I kept it design-only like `001_local.md`: source architecture, target inventory, ranking model, no collectors, no live fetches, no dependencies, no runtime changes, BACKLOG law, and proof at the end.

I anchored ORBITAL around official or documented source families first: NASA Open APIs and RSS, JPL SSD/CNEOS APIs, NOAA SWPC JSON/products, CelesTrak GP data, Space-Track API documentation, Launch Library 2, ESA RSS, Spaceflight News API, and Minor Planet Center APIs. ([NASA Open APIs][1])

Raw source URLs for that anchor set:

[https://api.nasa.gov/](https://api.nasa.gov/)
[https://www.nasa.gov/rss-feeds/](https://www.nasa.gov/rss-feeds/)
[https://ssd-api.jpl.nasa.gov/](https://ssd-api.jpl.nasa.gov/)
[https://ssd-api.jpl.nasa.gov/doc/index.php](https://ssd-api.jpl.nasa.gov/doc/index.php)
[https://www.swpc.noaa.gov/products/alerts-watches-and-warnings](https://www.swpc.noaa.gov/products/alerts-watches-and-warnings)
[https://services.swpc.noaa.gov/json/](https://services.swpc.noaa.gov/json/)
[https://www.celestrak.org/NORAD/documentation/gp-data-formats.php](https://www.celestrak.org/NORAD/documentation/gp-data-formats.php)
[https://www.space-track.org/documentation](https://www.space-track.org/documentation)
[https://ll.thespacedevs.com/](https://ll.thespacedevs.com/)
[https://www.esa.int/Services/RSS_Feeds](https://www.esa.int/Services/RSS_Feeds)
[https://api.spaceflightnewsapi.net/v4/docs/](https://api.spaceflightnewsapi.net/v4/docs/)
[https://www.minorplanetcenter.net/mpcops/documentation/](https://www.minorplanetcenter.net/mpcops/documentation/)

```text
You are working in the console-1701 repository.

This task assumes the prior scoped recent-signal architecture prompt, LOCAL Seattle design prompt, REGIONAL Pacific Northwest design prompt, NATIONAL United States design prompt, and GLOBAL World design prompt have either already been run, or will be pasted above this prompt.

This is an ORBITAL scope architecture, source-target inventory, and ranking design task only.

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

Your job is to design the ORBITAL recent-signal layer in enough detail that later Codex passes can implement it safely, source by source, without guessing.

Before doing anything, inspect the current repo state and previous design outputs.

Required first checks:

pwd
git status --short
find docs/project -maxdepth 1 -type f -print | sort || true
grep -n "Recent Signal\|News Ingestion\|LOCAL\|REGIONAL\|NATIONAL\|GLOBAL\|ORBITAL" BACKLOG.md || true

If previous docs exist, read them first and extend them cleanly:

- docs/project/NEWS_SCOPE_INGESTION_ARCHITECTURE_DESIGN.md
- docs/project/LOCAL_SEATTLE_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md
- docs/project/REGIONAL_PNW_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md
- docs/project/NATIONAL_US_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md
- docs/project/GLOBAL_WORLD_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md

Do not duplicate BACKLOG sections already added by previous tasks. Extend the relevant section cleanly or add a new ORBITAL subsection.

The user intent:

console-1701 is a local-only home dashboard running at http://127.0.0.1:1701/.

The ORBITAL tab should eventually answer:

"What is happening above Earth and in near space that may matter right now?"

The ORBITAL scope should eventually combine recent signals from:

- Space weather alerts, watches, warnings, forecasts, and measurements.
- Solar flares, geomagnetic storms, radiation storms, radio blackouts, aurora signals, solar wind, Kp, proton flux, X-ray flux, CME-related products, and ICAO space weather advisories.
- NASA, JPL, CNEOS, MPC, ESA, NOAA, and other official agency sources.
- Near-Earth object close approaches, fireballs, bolides, risk list updates, and MPEC/NEO confirmation signals.
- Launch schedules, launch status changes, scrubs, successes, failures, deployments, dockings, undockings, reentries, and mission milestones.
- ISS and crewed-spaceflight operational news where public and source-backed.
- Public satellite catalog, orbital element, reentry, debris, and conjunction-awareness sources where safe and policy-compliant.
- Orbital debris, space sustainability, reentry prediction, and space traffic coordination sources.
- Astronomical transient and sky-event sources where useful.
- Major space agency news, mission blogs, science releases, and spaceflight journalism.
- Community/social orbital signals only when accessible through compliant, explicitly configured methods.
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
- Bind only to 127.0.0.1 on port 1701.
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
- console-1701-codex-plan-01.md
- docs/project/NEWS_SCOPE_INGESTION_ARCHITECTURE_DESIGN.md, if it exists
- docs/project/LOCAL_SEATTLE_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md, if it exists
- docs/project/REGIONAL_PNW_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md, if it exists
- docs/project/NATIONAL_US_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md, if it exists
- docs/project/GLOBAL_WORLD_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md, if it exists
- console1701/schema.sql
- console1701/config.py
- console1701/db.py
- console1701/scanner.py
- console1701/api.py
- console1701/templates/index.html
- console1701/static/app.css
- console1701/static/app.js
- console1701/evidence.py
- console1701/system_probe.py
- tests/

Deliverables:

1. Create this document:

   docs/project/ORBITAL_SPACE_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md

   Create docs/project if it does not exist.

2. Update BACKLOG.md with concrete future implementation tasks flowing from this ORBITAL design.

3. Do not touch application code unless absolutely necessary. This should normally be docs plus BACKLOG only.

4. Do not perform live source verification. The source links below are seed targets. Classify them as candidate links and design how they should be verified in a later phase.

5. The final response must prove what changed and what did not change.

The design document must include the following sections.

SECTION 1: Purpose

Explain the ORBITAL scope in plain engineering language.

The ORBITAL scope is the space, sky, and near-Earth environment recent-signal layer. It should tell the user what is happening above Earth and in nearby space, with source provenance, observed time, source kind, ranking reason, and evidence.

It is not:

- A military space intelligence dashboard.
- A tactical satellite tracking tool.
- A general astronomy archive.
- A launch livestream scraper.
- A satellite surveillance system.
- A space debris panic board.
- A rocket fandom feed.
- A UFO dashboard.
- A hidden LLM summarizer.
- A cloud service.
- A replacement for GLOBAL world signals.
- A replacement for NATIONAL United States signals.
- A replacement for LOCAL weather or REGIONAL emergency alerts.

It is:

- A local, short-retention metadata dashboard.
- A deterministic cross-source event detector for orbital, space weather, near-Earth object, launch, mission, satellite, and sky signals.
- A source-health aware recent-signal system.
- An ORBITAL tab in console-1701 that can surface official space weather alerts, aurora chances, solar storms, NEO close approaches, fireballs, launch events, spacecraft anomalies, ISS and crewed-flight updates, orbital debris and reentry notices, official agency news, mission milestones, and spaceflight news.
- A way to rank items by independent source convergence, official severity, public impact, operational relevance, local or global effect, freshness, and user-configured source priority.

Make clear that "orbital" means useful public, configured, lawful, recent signals that the user chooses to enable. It does not mean unbounded space data harvesting, restricted satellite tracking, private operator monitoring, or automated space intelligence.

SECTION 2: ORBITAL scope boundaries

Define ORBITAL geography and relevance.

Default ORBITAL scope:

- Near-Earth space.
- Earth orbit.
- Space weather affecting Earth, satellites, radio, GPS, aviation, power grids, and aurora visibility.
- Solar system objects with potential Earth relevance.
- Near-Earth object close approaches and fireballs.
- Space launch, mission, docking, reentry, and crewed-spaceflight events.
- Public satellite catalog and orbital element metadata only where lawful and policy-compliant.
- Orbital debris, reentry, and space sustainability signals where public and non-tactical.
- Space agency mission updates and science releases where timely.
- Astronomy and sky events only when they are time-sensitive or useful for situational awareness.
- Spaceflight news only when it covers real operational, launch, mission, hazard, policy, science, or infrastructure events.

Out of ORBITAL by default:

- Routine astronomy feature stories with no recent-signal value.
- Generic science explainers.
- Routine corporate promotion.
- Commodity investment angles around space companies.
- Tactical tracking of military or sensitive satellites.
- Any attempt to infer classified orbital behavior.
- Any attempt to bypass Space-Track account terms or restricted data controls.
- Any scraping behind login or API restrictions.
- Full article archives.
- Social-only claims.
- UFO content unless a future explicit source family and scope rule is added.
- Global terrestrial disasters, unless caused by or directly tied to space weather, reentry, asteroid impact, or orbital infrastructure.
- Local Seattle sky visibility except as a tagged local impact for aurora, ISS passes, major meteor events, or visible reentry.

Design a later config escape hatch:

orbital:
  enabled: false
  default_place_label: "Orbit / Space"
  include_space_weather: true
  include_aurora: true
  include_neo_close_approaches: true
  include_fireballs: true
  include_launches: true
  include_crewed_spaceflight: true
  include_iss: true
  include_reentries: true
  include_debris: true
  include_satellite_catalog: false
  include_conjunction_awareness: false
  include_space_agency_news: true
  include_spaceflight_news: true
  include_astronomy_transients: false
  include_social_sources: false
  include_restricted_or_auth_sources: false
  space_weather_attention_minimum:
    geomagnetic: "G2"
    radio_blackout: "R2"
    radiation_storm: "S1"
    kp: 5
  aurora_local_interest:
    enabled: true
    location_label: "Seattle area"
    kp_attention_minimum: 5
  neo_attention:
    max_lunar_distances: 10
    min_estimated_diameter_meters: 20
    fireball_min_energy_kt: 0.1
  launch_attention:
    include_crewed: true
    include_iss_docking: true
    include_payload_deployments: true
    include_scrubs: true
  reentry_attention:
    only_official_or_high_confidence: true
    suppress_tactical_tracking: true

SECTION 3: Relationship to LOCAL, REGIONAL, NATIONAL, GLOBAL, and OVERVIEW

Explain how ORBITAL interacts with other scopes.

Rules:

- ORBITAL owns space weather, solar storms, aurora, NEOs, fireballs, launches, spacecraft operations, satellites, reentries, orbital debris, and space agency mission signals.
- GLOBAL owns world terrestrial events unless the cause or infrastructure is orbital or space-weather related.
- NATIONAL owns U.S. domestic federal and public-impact signals unless the primary subject is orbital or space-weather.
- REGIONAL owns Washington / PNW terrestrial impacts.
- LOCAL owns Seattle local impacts.
- OVERVIEW should select the highest-priority items from LOCAL, REGIONAL, NATIONAL, GLOBAL, ORBITAL, and SYSTEM without burying urgent local/system issues.
- If an ORBITAL event affects Earth systems, tag it with GLOBAL_IMPACT, NATIONAL_IMPACT, REGIONAL_IMPACT, or LOCAL_IMPACT where supported by evidence.
- If a space weather event creates aurora potential over Washington, canonical scope remains ORBITAL with REGIONAL_IMPACT or LOCAL_IMPACT.
- If a launch causes road or airspace disruption in Florida, canonical scope remains ORBITAL but NATIONAL/LOCAL impact can be tagged only if relevant source data exists.
- If an asteroid close approach is routine and low-risk, it stays low priority.
- If a fireball is widely reported and has official JPL/CNEOS or NASA/NOAA support, it can rise in ORBITAL and possibly GLOBAL or NATIONAL attention.
- If a satellite reentry has credible official public-risk or airspace impact, ORBITAL can tag GLOBAL_IMPACT or NATIONAL_IMPACT.
- If a solar storm affects power grids, aviation, GPS, HF radio, satellites, aurora, or communications, ORBITAL can feed OVERVIEW strongly.

Examples:

- SWPC G4 geomagnetic storm watch: ORBITAL, possible NATIONAL/GLOBAL impact.
- Kp 6 with aurora visibility in Washington: ORBITAL with REGIONAL_IMPACT and LOCAL_IMPACT.
- NASA Artemis launch: ORBITAL, possible NATIONAL impact.
- SpaceX routine Starlink launch: ORBITAL, likely lower unless scrub, failure, crewed, visible, or payload/conjunction relevance exists.
- JPL CNEOS close approach under 1 lunar distance for a sizeable NEO: ORBITAL.
- Small NEO at 20 lunar distances: background ORBITAL or ignored.
- ISS docking or EVA: ORBITAL.
- Routine NASA science article: ORBITAL press pulse, low priority unless mission-impact or discovery event.
- CelesTrak catalog update: source health or background unless reentry/debris relevance exists.
- Space weather impacting aviation HF communications: ORBITAL with GLOBAL or NATIONAL impact tag.
- Space policy article with no operational relevance: low priority ORBITAL or NATIONAL depending content.

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

- official_space_weather
- official_space_weather_json
- official_solar_data
- official_aurora
- official_neo
- official_fireball
- official_minor_planet
- official_launch
- official_crewed_spaceflight
- official_iss
- official_mission_news
- official_space_agency_news
- official_science_release
- official_satellite_catalog
- official_orbital_debris
- official_reentry
- official_conjunction_awareness
- official_space_safety
- official_astronomy_data
- official_transient_astronomy
- launch_event_api
- spaceflight_news_api
- commercial_launch_provider
- space_news
- astronomy_news
- public_media_space
- social_candidate
- restricted_auth_candidate
- unofficial_aggregator
- source_health_only
- manual_review_only

Use these adapter types:

- rss_atom
- static_html_headline_candidate
- official_api_json
- swpc_json
- swpc_product_text
- swpc_alerts_json
- jpl_ssd_api
- cneos_api
- mpc_api
- launch_library_api
- spaceflight_news_api
- nasa_api_json
- celestrak_gp_json
- celestrak_satcat_csv_json
- celestrak_socrates_candidate
- space_track_api_candidate
- esa_reentry_page_candidate
- arcgis_feature_service_candidate
- astronomy_tap_api_candidate
- local_file_fixture
- source_health_probe_only
- manual_review_only

Use these verification_status values:

- user_seeded
- assistant_seeded
- official_page_seen
- candidate_needs_verification
- candidate_policy_sensitive
- restricted_auth_required
- unofficial_secondary
- reject_for_now

Do not overstate verification. If a URL is only a likely feed endpoint, mark it candidate_needs_verification.

Seed source targets:

NOAA / SWPC space weather and aurora:

https://www.swpc.noaa.gov/
https://www.swpc.noaa.gov/products-and-data
https://www.swpc.noaa.gov/content/data-access
https://www.swpc.noaa.gov/products/alerts-watches-and-warnings
https://www.swpc.noaa.gov/alerts-watches-and-warnings
https://www.swpc.noaa.gov/products/notifications-timeline
https://www.swpc.noaa.gov/products/planetary-k-index
https://www.swpc.noaa.gov/products/real-time-solar-wind
https://www.swpc.noaa.gov/products/goes-x-ray-flux
https://www.swpc.noaa.gov/products/goes-proton-flux
https://www.swpc.noaa.gov/products/goes-electron-flux
https://www.swpc.noaa.gov/products/aurora-30-minute-forecast
https://www.swpc.noaa.gov/products/3-day-forecast
https://www.swpc.noaa.gov/products/27-day-outlook-107-cm-radio-flux-and-geomagnetic-indices
https://www.swpc.noaa.gov/products/solar-cycle-progression
https://www.swpc.noaa.gov/products/space-weather-overview
https://www.swpc.noaa.gov/products/satellite-environment
https://www.swpc.noaa.gov/products/icao-space-weather-advisories
https://www.swpc.noaa.gov/news/new-json-data-now-available
https://services.swpc.noaa.gov/json/
https://services.swpc.noaa.gov/products/
https://services.swpc.noaa.gov/products/alerts.json
https://services.swpc.noaa.gov/products/noaa-scales.json
https://services.swpc.noaa.gov/products/summary/solar-wind-speed.json
https://services.swpc.noaa.gov/products/summary/planetary-k-index.json
https://services.swpc.noaa.gov/products/summary/x-ray-flux.json
https://services.swpc.noaa.gov/products/summary/10cm-flux.json
https://services.swpc.noaa.gov/json/planetary_k_index_1m.json
https://services.swpc.noaa.gov/json/boulder_k_index_1m.json
https://services.swpc.noaa.gov/json/ovation_aurora_latest.json
https://services.swpc.noaa.gov/json/icao-space-weather-advisories.json
https://www.weather.gov/safety/space-ww
https://www.ncei.noaa.gov/products/space-weather/partners/swpc-products-and-data
https://registry.opendata.aws/noaa-space-weather/

NASA APIs, NASA feeds, and NASA mission news:

https://api.nasa.gov/
https://www.nasa.gov/rss-feeds/
https://www.nasa.gov/news/
https://www.nasa.gov/news-release/
https://www.nasa.gov/blogs/
https://blogs.nasa.gov/
https://www.nasa.gov/launches/
https://www.nasa.gov/missions/
https://www.nasa.gov/international-space-station/
https://blogs.nasa.gov/spacestation/
https://www.nasa.gov/artemis/
https://blogs.nasa.gov/artemis/
https://www.nasa.gov/kennedy/
https://blogs.nasa.gov/kennedy/
https://www.nasa.gov/centers-and-facilities/ames/
https://www.jpl.nasa.gov/news/
https://www.jpl.nasa.gov/rss/
https://science.nasa.gov/news/
https://science.nasa.gov/solar-system/
https://science.nasa.gov/mission/parker-solar-probe/
https://science.nasa.gov/mission/hubble/
https://science.nasa.gov/mission/jwst/
https://science.nasa.gov/mission/tess/
https://science.nasa.gov/mission/roman-space-telescope/
https://science.nasa.gov/mission/lucy/
https://science.nasa.gov/mission/osiris-apex/

JPL SSD / CNEOS / NEO / fireball / impact-risk sources:

https://ssd-api.jpl.nasa.gov/
https://ssd-api.jpl.nasa.gov/doc/index.php
https://ssd-api.jpl.nasa.gov/doc/cad.html
https://ssd-api.jpl.nasa.gov/cad.api
https://ssd-api.jpl.nasa.gov/doc/fireball.html
https://ssd-api.jpl.nasa.gov/fireball.api
https://ssd-api.jpl.nasa.gov/doc/sentry.html
https://ssd-api.jpl.nasa.gov/sentry.api
https://ssd-api.jpl.nasa.gov/doc/scout.html
https://ssd-api.jpl.nasa.gov/scout.api
https://ssd-api.jpl.nasa.gov/doc/sbdb.html
https://ssd-api.jpl.nasa.gov/sbdb.api
https://ssd-api.jpl.nasa.gov/doc/horizons.html
https://cneos.jpl.nasa.gov/
https://cneos.jpl.nasa.gov/ca/
https://cneos.jpl.nasa.gov/fireballs/
https://cneos.jpl.nasa.gov/sentry/
https://cneos.jpl.nasa.gov/scout/

Minor Planet Center and astronomical object sources:

https://www.minorplanetcenter.net/
https://www.minorplanetcenter.net/data
https://www.minorplanetcenter.net/mpcops/documentation/
https://www.minorplanetcenter.net/mpcops/documentation/mpecs-api/
https://www.minorplanetcenter.net/mpec/RecentMPECs.html
https://cgi.minorplanetcenter.net/mpcops/documentation/neocp-observations-api/
https://www.minorplanetcenter.net/neocp_obs
https://www.minorplanetcenter.net/mpcops/documentation/observations-api/
https://www.minorplanetcenter.net/mpcops/documentation/orbits-api/
https://www.minorplanetcenter.net/mpcops/documentation/designation-identifier-api/
https://www.minorplanetcenter.net/mpcops/documentation/obscodes-api/

Launch schedules, launch events, and spaceflight event APIs:

https://ll.thespacedevs.com/
https://ll.thespacedevs.com/2.3.0/
https://ll.thespacedevs.com/2.3.0/launches/
https://ll.thespacedevs.com/2.3.0/launches/upcoming/
https://ll.thespacedevs.com/2.3.0/events/upcoming/
https://thespacedevs.com/llapi
https://www.spaceflightnewsapi.net/
https://api.spaceflightnewsapi.net/v4/docs/
https://api.spaceflightnewsapi.net/v4/articles/
https://api.spaceflightnewsapi.net/v4/blogs/
https://api.spaceflightnewsapi.net/v4/reports/

Official and commercial launch provider sources:

https://www.spacex.com/launches/
https://www.spacex.com/updates/
https://www.blueorigin.com/news
https://www.blueorigin.com/missions/
https://www.rocketlabusa.com/missions/next-mission/
https://www.rocketlabusa.com/updates/
https://www.ulalaunch.com/missions/next-launch
https://www.ulalaunch.com/about/news
https://www.arianespace.com/mission-updates/
https://www.arianespace.com/press-release/
https://www.northropgrumman.com/space
https://www.virgingalactic.com/news/
https://www.fireflyspace.com/missions/
https://www.isro.gov.in/
https://www.isro.gov.in/Press.html
https://global.jaxa.jp/press/
https://www.esa.int/Newsroom
https://www.esa.int/Services/RSS_Feeds
https://www.asc-csa.gc.ca/eng/news/
https://www.cnsa.gov.cn/english/

Satellite catalog, orbital data, debris, reentry, and conjunction awareness:

https://celestrak.org/
https://celestrak.org/NORAD/elements/
https://celestrak.org/NORAD/documentation/gp-data-formats.php
https://celestrak.org/NORAD/elements/gp.php
https://celestrak.org/satcat/
https://celestrak.org/SOCRATES/
https://celestrak.org/SOCRATES/socrates-format.php
https://celestrak.org/NORAD/elements/supplemental/
https://www.space-track.org/
https://www.space-track.org/documentation
https://www.space-track.org/documents/Spacetrack_Handbook_for_Operators.pdf
https://www.space-track.org/documents/Launch_Handbook_For_Operators_V3.1.pdf
https://www.nasa.gov/cara/
https://www.nasa.gov/conjunction-assessment/
https://orbitaldebris.jsc.nasa.gov/
https://orbitaldebris.jsc.nasa.gov/quarterly-news/
https://orbitaldebris.jsc.nasa.gov/reentry/
https://reentry.esoc.esa.int/
https://www.esa.int/Space_Safety/Space_Debris
https://www.esa.int/Space_Safety
https://www.esa.int/Space_Safety/Clean_Space

ISS, crewed spaceflight, and station operations:

https://www.nasa.gov/international-space-station/
https://blogs.nasa.gov/spacestation/
https://www.nasa.gov/humans-in-space/
https://www.nasa.gov/humans-in-space/commercial-crew-program/
https://www.nasa.gov/directorates/somd/commercial-resupply/
https://www.esa.int/Science_Exploration/Human_and_Robotic_Exploration/International_Space_Station
https://global.jaxa.jp/projects/iss_human/
https://www.asc-csa.gc.ca/eng/iss/
https://spotthestation.nasa.gov/
https://open-notify.org/Open-Notify-API/ISS-Location-Now/

Space agency feeds and public space science releases:

https://www.nasa.gov/rss-feeds/
https://www.esa.int/Services/RSS_Feeds
https://global.jaxa.jp/press/
https://www.asc-csa.gc.ca/eng/news/
https://www.jpl.nasa.gov/news/
https://www.esa.int/Science_Exploration
https://www.esa.int/Applications
https://www.esa.int/Space_Safety
https://www.nasa.gov/universe/
https://science.nasa.gov/
https://www.noaa.gov/satellites
https://www.nesdis.noaa.gov/news
https://www.eumetsat.int/news
https://www.eumetsat.int/rss-feeds
https://www.copernicus.eu/en/news
https://dataspace.copernicus.eu/stay-informed/RSSfeeds

Astronomy, exoplanet, transient, and sky-event candidates:

https://exoplanetarchive.ipac.caltech.edu/
https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html
https://exoplanetarchive.ipac.caltech.edu/docs/exonews_archive.html
https://mast.stsci.edu/api/v0/
https://heasarc.gsfc.nasa.gov/docs/archive.html
https://www.astronomerstelegram.org/
https://www.astronomerstelegram.org/?rss
https://gcn.nasa.gov/
https://gcn.nasa.gov/circulars
https://gcn.nasa.gov/notices
https://www.ligo.caltech.edu/news
https://www.ligo.org/news.php
https://www.iau.org/news/
https://skyandtelescope.org/astronomy-news/
https://skyandtelescope.org/feed/

Space news, public media, and specialist journalism:

https://spacenews.com/
https://spacenews.com/feed/
https://spaceflightnow.com/
https://spaceflightnow.com/feed/
https://www.space.com/
https://www.space.com/feeds/all
https://www.nasaspaceflight.com/
https://www.nasaspaceflight.com/feed/
https://arstechnica.com/space/
https://arstechnica.com/space/feed/
https://www.planetary.org/articles
https://www.planetary.org/rss.xml
https://www.universetoday.com/
https://www.universetoday.com/feed/
https://www.astronomy.com/
https://www.astronomy.com/feed/
https://www.scientificamerican.com/space/
https://www.scientificamerican.com/platform/syndication/rss/
https://www.nature.com/subjects/astronomy-and-planetary-science
https://www.nature.com/subjects/astronomy-and-planetary-science.rss
https://www.science.org/topic/category/space
https://www.bbc.com/news/science_and_environment
https://feeds.bbci.co.uk/news/science_and_environment/rss.xml

Community and social candidates, policy-sensitive:

https://www.reddit.com/r/space/
https://www.reddit.com/r/spaceflight/
https://www.reddit.com/r/SpaceX/
https://www.reddit.com/r/SpaceXLounge/
https://www.reddit.com/r/BlueOrigin/
https://www.reddit.com/r/RocketLab/
https://www.reddit.com/r/Arianespace/
https://www.reddit.com/r/nasa/
https://www.reddit.com/r/astronomy/
https://www.reddit.com/r/Astronomy/
https://www.reddit.com/r/Satellites/
https://www.reddit.com/r/Starlink/
https://x.com/NASA
https://x.com/NASASpaceflight
https://x.com/SpaceX
https://x.com/blueorigin
https://x.com/RocketLab
https://x.com/ulalaunch
https://x.com/esa
https://x.com/JAXA_en
https://x.com/csa_asc
https://x.com/NASAJPL
https://x.com/Space_Station
https://x.com/SWPC
https://x.com/USGS_Quakes
https://x.com/MinorPlanetCtr
https://x.com/SpaceNews_Inc
https://bsky.app/search?q=space%20weather
https://bsky.app/search?q=solar%20storm
https://bsky.app/search?q=aurora
https://bsky.app/search?q=NASA%20launch
https://bsky.app/search?q=SpaceX%20launch
https://bsky.app/search?q=asteroid%20close%20approach
https://bsky.app/search?q=fireball%20meteor
https://bsky.app/search?q=satellite%20reentry
https://bsky.app/search?q=ISS%20docking

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
- Official APIs, official JSON products, official RSS/Atom, official open data, official CNEOS/JPL/NASA/NOAA/SWPC/MPC data, and official agency feeds.
- Best first live candidates.

Tier 2:
- Official pages with stable public operational data but no obvious feed/API.
- Candidate only after source-policy review.
- Prefer source-health checks and manual review before parser implementation.

Tier 3:
- Public launch and event APIs.
- Example: Launch Library 2.
- Must be disabled by default.
- Must use rate limits, caching, source health, and strict event windows.

Tier 4:
- Spaceflight news RSS or publisher-provided feeds.
- Store headline metadata only.
- No article-body archive.
- No paywall bypass.

Tier 5:
- Public satellite catalog and orbital element sources.
- Use cautiously.
- Public catalog metadata can support high-level reentry, debris, ISS, and source-health summaries.
- Do not build a tactical tracker.
- Do not track restricted or sensitive targets beyond source-provided public aggregate metadata.
- Do not infer classified activity.

Tier 6:
- Restricted or auth-required sources.
- Example: Space-Track.
- Disabled by default.
- Must require explicit user config, credentials outside repo, terms review, and narrow source purpose.
- Never bypass account controls.
- Never store credentials in repo.
- If not needed, prefer public CelesTrak or official agency pages.

Tier 7:
- Social/community signals.
- Policy-sensitive.
- Disabled by default.
- Reddit only through compliant official API or permitted feed access.
- X/Twitter only through official API access if explicitly configured.
- Bluesky may be explored through official AT Protocol later.
- No HTML scraping to bypass platform restrictions.

Tier 8:
- Unofficial aggregators.
- Useful as human comparison or source-health reference.
- Do not treat as primary authority over official sources.
- Do not clone their work or scrape aggressively.
- If used later, source-health-only or manual-review-only unless policy review supports more.

SECTION 6: ORBITAL event model

Design an ORBITAL event model that sits above raw items.

The system should not only store "news items." It should infer that multiple recent items refer to the same orbital or space event.

Propose a future orbital_events table or explain how news_clusters should be extended.

An ORBITAL event should have:

- orbital_event_id
- scope
- event_key
- event_type
- title
- representative_item_id
- severity
- public_impact_score
- operational_impact_score
- source_diversity_score
- official_confirmation_score
- space_weather_score
- neo_score
- launch_score
- crewed_spaceflight_score
- satellite_reentry_score
- debris_conjunction_score
- mission_science_score
- sky_visibility_score
- social_echo_score
- news_echo_score
- global_impact_score
- national_impact_score
- regional_impact_score
- local_impact_score
- first_seen_at
- last_seen_at
- last_elevated_at
- expires_at
- space_domain_json
- objects_json
- missions_json
- agencies_json
- launch_sites_json
- impacted_systems_json
- source_ids_json
- item_ids_json
- evidence_json
- ranking_explanation_json
- status

Event types should include at least:

- space_weather_watch
- space_weather_warning
- geomagnetic_storm
- solar_flare
- radio_blackout
- solar_radiation_storm
- cme_arrival
- solar_wind_shock
- aurora_opportunity
- icao_space_weather_advisory
- neo_close_approach
- asteroid_impact_risk_update
- fireball_bolide
- mpec_neo_candidate
- comet_or_minor_body_notice
- launch_scheduled
- launch_window_change
- launch_scrub
- launch_success
- launch_failure
- payload_deployed
- spacecraft_anomaly
- docking_undocking
- crewed_mission_event
- eva_spacewalk
- iss_operation
- reentry_prediction
- uncontrolled_reentry
- orbital_debris_notice
- conjunction_awareness
- satellite_catalog_update
- mission_milestone
- science_release
- astronomy_transient
- meteor_shower_sky_event
- source_health_problem
- community_signal

Make clear that routine low-impact space news should not automatically become elevated ORBITAL events.

SECTION 7: Cross-source convergence ranking

Design deterministic ranking around this idea:

If something appears in official space weather products, agency feeds, launch/event APIs, mission blogs, CNEOS/MPC data, satellite/reentry sources, spaceflight news, and community/social signals within a short window, it is probably important or interesting.

Implement this as design only.

Do not design an LLM summarizer.

The scoring model must be explainable.

Required scoring factors:

1. Official severity

Examples:

- SWPC geomagnetic storm watch, warning, or alert.
- SWPC NOAA scale values for G, R, or S categories.
- Kp at or above configured threshold.
- M-class or X-class solar flare, with higher scores for X-class.
- Proton/radiation storm alert.
- ICAO space weather advisory.
- JPL/CNEOS close approach within configured lunar-distance threshold.
- CNEOS fireball above configured energy threshold.
- Sentry or Scout risk-list update.
- MPC NEO confirmation item.
- Crewed launch, docking, undocking, EVA, or ISS emergency-type official update.
- Launch failure, scrub, payload deployment issue, or range safety event.
- Official reentry prediction for large object.
- Official orbital debris or conjunction notice.
- NASA, ESA, JAXA, NOAA, or other agency mission anomaly notice.
- Space weather with documented aviation, GPS, HF radio, satellite, or power-grid relevance.

2. Source diversity

Independent source families count more than repeated mentions from the same family.

Example families:

- swpc
- noaa_ncei
- nasa
- nasa_blogs
- nasa_jpl
- jpl_cneos
- mpc
- esa
- esa_reentry
- jaxa
- csa
- isro
- celestrak
- space_track
- launch_library
- spaceflight_news_api
- launch_provider
- spacex
- blue_origin
- rocket_lab
- ula
- arianespace
- nasa_space_station
- orbital_debris_program
- space_agency_news
- space_news
- public_media_space
- reddit
- bluesky
- x_api
- source_health

3. Temporal proximity

Items closer in time are more likely to be the same event.

Propose matching windows:

- Space weather alert: active alert duration or 0 to 72 hours.
- Aurora opportunity: 0 to 48 hours.
- Solar flare: 0 to 24 hours.
- CME/solar wind event: 0 to 72 hours.
- NEO close approach: event date minus 7 days through event date plus 24 hours.
- Fireball: 0 to 72 hours.
- Launch event: launch window minus 7 days through launch plus 48 hours.
- Launch scrub: 0 to 48 hours.
- Launch failure/anomaly: 0 to 14 days.
- Crewed-spaceflight event: 0 to 14 days.
- Docking/undocking/EVA: 0 to 72 hours.
- Reentry: prediction window minus 7 days through confirmed reentry plus 48 hours.
- Conjunction/debris: 0 to 7 days, official or specialist sources preferred.
- Mission milestone/science release: 0 to 7 days.
- Astronomy transient: 0 to 7 days, source-specific.
- Routine space news: 0 to 72 hours unless still active.

4. Object and mission proximity

Match by:

- mission name
- launch vehicle
- payload name
- NORAD catalog number where safe and appropriate
- COSPAR ID where safe and appropriate
- asteroid/comet designation
- CNEOS event id
- MPC designation
- fireball time/location
- space weather product id
- storm scale
- launch provider
- launch site
- spacecraft name
- ISS expedition/mission
- reentry object
- source event id

5. Public impact

Boost:

- geomagnetic storms affecting communications, satellites, aviation, GPS, aurora, or power grids
- aurora potential for configured local/regional location
- major solar flare or radiation storm
- crewed launch or crewed mission issue
- ISS operational issue
- launch failure or payload anomaly
- NEO close approach with size and distance above threshold
- fireball with reported energy or wide public observation
- uncontrolled reentry of large object
- debris/conjunction notice involving crewed assets or major active spacecraft
- official agency alert or mission update
- space event with GLOBAL, NATIONAL, REGIONAL, or LOCAL impact tag

6. Recency

Recent items matter more, but active alert windows and launch windows can remain elevated while active.

7. User-configured priority

Allow future config to boost:

- space weather
- aurora
- Seattle aurora visibility
- NOAA/SWPC
- NASA
- JPL/CNEOS
- NEOs
- fireballs
- crewed spaceflight
- ISS
- Artemis
- launches
- SpaceX
- ULA
- Blue Origin
- Rocket Lab
- ESA
- JAXA
- reentries
- debris
- astronomy transients
- mission science releases
- specific launch sites
- specific missions

8. Low-public-value penalty

De-emphasize:

- routine promotional space company posts
- generic science explainers
- low-risk NEOs far from Earth
- routine Starlink or satellite launches unless configured
- duplicate launch schedule pages
- social-only claims
- single-source launch rumors
- non-operational fan chatter
- orbital data firehose updates with no event significance
- stale TLE/catalog churn
- routine agency newsletters

9. Safety and sensitivity penalty

De-emphasize or block:

- restricted/auth-only data without explicit configuration
- tactical or sensitive satellite targeting
- attempts to infer classified activity
- data that would turn the app into a real-time operational tracker
- conjunction or satellite information without source-policy confidence
- social posts revealing private person-level details
- unverified reentry panic claims

The design must include a sample scoring formula.

Example:

score =
  recency_score
  + official_severity_score
  + source_diversity_score
  + public_impact_score
  + operational_impact_score
  + active_window_score
  + source_priority_score
  + cluster_size_score
  + local_or_global_impact_score
  - duplicate_family_penalty
  - stale_source_penalty
  - low_confidence_penalty
  - low_public_value_penalty
  - out_of_scope_penalty
  - sensitivity_penalty
  - rumor_penalty

The design must explain that "frequency of appearance" means independent cross-source convergence, not raw duplicate counts.

Bad ranking:

- 50 reposts of the same routine launch article dominate.

Good ranking:

- SWPC issues G4 geomagnetic storm watch.
- NOAA scale JSON and planetary Kp products support the event.
- NASA/NOAA or agency news explains impacts.
- Regional aurora sources or weather pages suggest visibility.
- News coverage confirms public interest.
- Social chatter appears only as a low-weight echo if compliant.
- All within an active alert window.

SECTION 8: ORBITAL source category design

Design source categories.

Each category must have:

- why it exists
- first safe sources
- parser/adaptor class
- likely refresh interval
- privacy risk
- policy risk
- parser risk
- source-health signals
- sample item fields
- how it contributes to ranking
- later implementation phase

Categories:

1. Space weather alerts and measurements.

2. Aurora and local sky-impact signals.

3. Near-Earth objects, fireballs, and minor planet notices.

4. Launch schedules and launch status.

5. Crewed spaceflight and ISS operations.

6. Mission news and space agency feeds.

7. Satellite catalog, reentry, debris, and conjunction-awareness sources.

8. Space safety, orbital debris, and sustainability sources.

9. Astronomy transients and sky events.

10. Space news, public media, and specialist journalism.

11. Social/community echoes.

12. Source health and disabled states.

SECTION 9: ORBITAL safety, sensitivity, and public-impact posture

Design this carefully.

Rules:

- Store source-provided public metadata only.
- Do not store full article bodies.
- Do not archive social posts long term.
- Do not scrape or bypass restricted satellite databases.
- Do not store API credentials in repo.
- Do not build tactical target tracking.
- Do not infer classified or sensitive orbital activity.
- Do not present orbital-element churn as operational intelligence.
- Do not elevate military or intelligence satellite tracking unless the source is official public news and the event has legitimate public-impact value.
- Prefer aggregate, public, source-backed event summaries over object-by-object tracking.
- For Space-Track or other restricted/account sources, mark auth_required and policy_sensitive until explicit user configuration exists.
- For CelesTrak, use public data only and avoid turning the dashboard into a tactical tracker.
- For reentries, avoid panic language. Show source, object, uncertainty, window, confidence, and official link.
- For NEOs, avoid impact scare language. Show distance, size estimate if available, confidence, event date, official source, and risk framing from CNEOS/MPC only.
- For space weather, show official severity scale, affected systems, and source URL. Do not invent impacts.
- For public-health or aviation impact from space weather, link to official source language.
- For launch failures or crewed-spaceflight anomalies, show official facts and label preliminary information.
- Social-only orbital claims should never outrank official alerts or trusted spaceflight reporting.

SECTION 10: ORBITAL source freshness and retention

Design short retention.

Default candidate retention:

- Raw fetch diagnostics: 7 days or less.
- Raw payload debug: disabled by default. If ever enabled, 6 hours max by default.
- Space weather alert metadata: expiration plus 24 to 72 hours.
- Space weather measurements: 24 to 72 hours unless aggregated.
- Aurora opportunity metadata: 48 hours.
- NEO close approach metadata: 7 days before event through 48 hours after event.
- Fireball metadata: 7 to 14 days.
- MPEC/NEO confirmation metadata: 7 to 14 days.
- Launch schedule metadata: until launch plus 7 days.
- Launch scrub/failure/anomaly metadata: 7 to 14 days.
- Crewed mission and ISS event metadata: 7 to 14 days.
- Reentry prediction metadata: until confirmed reentry plus 72 hours.
- Debris/conjunction metadata: 7 days, with sensitivity limits.
- Mission news headline metadata: 7 days.
- Science release metadata: 7 days unless configured.
- Astronomy transient metadata: 7 to 14 days.
- ORBITAL event clusters: 7 to 14 days.
- Source health: 30 days.
- Ranking explanations: same as event/item retention.
- Social metadata, if ever enabled: 24 to 72 hours unless source terms require shorter or prohibit storage.

Every ingest run in later phases must purge expired data.

No article body archive.

No permanent satellite tracking archive.

No permanent social archive.

SECTION 11: Adapter design for ORBITAL

Design future adapter families.

Do not implement now.

Required adapter families:

swpc_json:
- NOAA SWPC JSON directory and product JSON files.
- Must preserve product name, issue time, valid time, observed time, severity, NOAA scale, Kp, flare class, proton flux, solar wind, aurora product metadata, and source URL.
- Must handle format changes and source-health failures.
- Must not assume every JSON file has identical schema.

swpc_alerts_json:
- SWPC alerts/watches/warnings JSON.
- Must preserve alert product id, issue time, valid period, severity, message type, NOAA scale, affected systems if source provides it, and source URL.

swpc_product_text:
- Text products only if needed and explicitly configured.
- Parser should be conservative.
- Prefer JSON where available.

nasa_api_json:
- NASA Open APIs.
- Use only configured APIs.
- Avoid imagery-heavy APIs unless needed.
- Respect API key handling.
- DEMO_KEY may be usable only for development if allowed, but production config should use explicit local config and rate limits.
- Do not store API keys in repo.

jpl_ssd_api:
- JPL SSD/CNEOS APIs.
- Preserve object designation, close approach time, distance, relative velocity, estimated diameter where available, condition code if available, and source URL.
- Must not invent impact risk.
- Must treat Sentry/Scout risk fields as official source framing only.

cneos_api:
- Fireball and close-approach APIs.
- Preserve event time, location if available, energy, velocity, altitude, and source URL.
- Use thresholds to avoid firehose behavior.

mpc_api:
- MPC MPECs, NEOCP observations, observations, orbits, and designation APIs.
- Must verify exact endpoints and usage guidance.
- Store metadata only.
- Avoid high-volume observation ingestion unless strictly filtered.

launch_library_api:
- Launch Library 2 launch and event endpoints.
- Must preserve launch id, provider, mission, vehicle, pad, launch window, status, webcast URL if source provides it, and source URL.
- Must handle scrubs and status changes as event updates, not duplicates.
- Must obey API throttling and disabled-by-default config.

spaceflight_news_api:
- Spaceflight News API candidate.
- Useful as news metadata and correlation with Launch Library events.
- Must store headline metadata only.
- Do not let it outrank official launch provider or agency sources without convergence.

rss_atom:
- NASA RSS, ESA RSS, JPL RSS, agency feeds, space news feeds, public media feeds.
- Must parse title, URL, published timestamp, description, categories.
- Must bound description length.
- Must not fetch article bodies.

celestrak_gp_json:
- CelesTrak GP data candidates.
- Use only where useful for high-level public orbital context.
- Must avoid building tactical tracking UI.
- Must cap object counts and use allowlisted object groups if ever implemented.

celestrak_satcat_csv_json:
- Public SATCAT metadata candidate.
- Useful for identifying objects in reentry/debris events.
- Must cap rows and retain only short-term derived metadata unless explicitly configured.

celestrak_socrates_candidate:
- CelesTrak SOCRATES format candidate.
- Source-policy and sensitivity review required.
- May be source-health-only or manual-review-only initially.
- Do not present predictions as official warnings.

space_track_api_candidate:
- Auth-required candidate.
- Disabled by default.
- Must require credentials outside repo.
- Must record auth_required state if no credentials exist.
- Must not bypass account controls or terms.
- Must avoid restricted or sensitive use.

esa_reentry_page_candidate:
- ESA reentry prediction page candidate.
- Prefer source-health/manual review unless machine-readable endpoint is verified.
- Do not screen scrape complex pages without policy review.

astronomy_tap_api_candidate:
- NASA Exoplanet Archive, MAST, HEASARC, or TAP-style APIs.
- Useful for configured science release or transient tracking.
- Do not ingest large catalogs.
- Prefer news/RSS unless a specific scientific signal is configured.

static_html_headline_candidate:
- Only for official pages or space news pages with no RSS/API.
- Disabled unless homepage extractor support is explicitly allowed.
- Must use per-source selectors.
- No recursive crawling.
- No article-body fetch.
- Robots/policy review required.

source_health_probe_only:
- For dashboards and portals useful as human status references but not suitable for ingestion.

manual_review_only:
- For policy-sensitive, parser-risky, login-required, auth-required, account-required, paywalled, restricted, or unclear targets.

SECTION 12: Candidate orbital source registry example

Include a YAML-like example in the design document.

Do not edit config.example.yml yet unless prior architecture already requires disabled examples.

The example must be disabled by default.

Example shape:

orbital_sources:
  enabled: false
  label: "Orbit / Space"
  retention:
    space_weather_alert_days: 7
    space_weather_measurement_hours: 72
    aurora_hours: 48
    neo_days: 14
    fireball_days: 14
    launch_days: 14
    crewed_spaceflight_days: 14
    reentry_days: 7
    debris_days: 7
    mission_news_days: 7
    headline_days: 7
    event_cluster_days: 14
    source_health_days: 30
    raw_payload_debug_enabled: false
    raw_payload_debug_ttl_hours: 6
  ranking:
    source_diversity_weight: 3.0
    official_severity_weight: 3.5
    operational_impact_weight: 3.0
    public_impact_weight: 2.75
    local_or_global_impact_weight: 2.0
    recency_weight: 2.0
    social_echo_weight: 0.35
    low_public_value_penalty_weight: 3.0
    sensitivity_penalty_weight: 4.0
    rumor_penalty_weight: 4.0
  safety:
    suppress_tactical_satellite_tracking: true
    restricted_sources_disabled_by_default: true
    social_retention_hours: 48
    social_sources_disabled_by_default: true
    require_policy_review_for_space_track: true
    require_policy_review_for_conjunction_sources: true
  local_impact:
    aurora_location_label: "Seattle area"
    aurora_kp_attention_minimum: 5
  sources:
    - id: swpc_alerts
      enabled: false
      source_family: swpc
      source_class: official_space_weather
      adapter: swpc_alerts_json
      homepage_url: "https://www.swpc.noaa.gov/products/alerts-watches-and-warnings"
      url: "https://services.swpc.noaa.gov/products/alerts.json"
      priority: 100
      interval_minutes: 5
      verification_status: official_page_seen
      evidence_notes: "Use official SWPC alerts, watches, warnings, and issue times."

    - id: swpc_noaa_scales
      enabled: false
      source_family: swpc
      source_class: official_space_weather_json
      adapter: swpc_json
      homepage_url: "https://www.swpc.noaa.gov/products/space-weather-overview"
      url: "https://services.swpc.noaa.gov/products/noaa-scales.json"
      priority: 95
      interval_minutes: 5
      verification_status: official_page_seen

    - id: swpc_aurora_forecast
      enabled: false
      source_family: swpc
      source_class: official_aurora
      adapter: swpc_json
      homepage_url: "https://www.swpc.noaa.gov/products/aurora-30-minute-forecast"
      url: "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json"
      priority: 85
      interval_minutes: 10
      verification_status: official_page_seen
      filters:
        local_interest_label: "Seattle area"
        kp_attention_minimum: 5

    - id: jpl_cneos_close_approaches
      enabled: false
      source_family: jpl_cneos
      source_class: official_neo
      adapter: jpl_ssd_api
      homepage_url: "https://cneos.jpl.nasa.gov/ca/"
      url: "https://ssd-api.jpl.nasa.gov/cad.api"
      priority: 90
      interval_minutes: 60
      verification_status: official_page_seen
      filters:
        max_lunar_distances: 10
        min_estimated_diameter_meters: 20

    - id: jpl_cneos_fireballs
      enabled: false
      source_family: jpl_cneos
      source_class: official_fireball
      adapter: cneos_api
      homepage_url: "https://cneos.jpl.nasa.gov/fireballs/"
      url: "https://ssd-api.jpl.nasa.gov/fireball.api"
      priority: 85
      interval_minutes: 60
      verification_status: official_page_seen
      filters:
        min_energy_kt: 0.1

    - id: launch_library_upcoming
      enabled: false
      source_family: launch_library
      source_class: launch_event_api
      adapter: launch_library_api
      homepage_url: "https://ll.thespacedevs.com/"
      url: "https://ll.thespacedevs.com/2.3.0/launches/upcoming/"
      priority: 80
      interval_minutes: 30
      verification_status: official_page_seen
      filters:
        include_crewed: true
        include_status_changes: true

    - id: nasa_rss_general
      enabled: false
      source_family: nasa
      source_class: official_space_agency_news
      adapter: rss_atom
      homepage_url: "https://www.nasa.gov/rss-feeds/"
      priority: 75
      interval_minutes: 60
      verification_status: official_page_seen

    - id: esa_rss_top_news
      enabled: false
      source_family: esa
      source_class: official_space_agency_news
      adapter: rss_atom
      homepage_url: "https://www.esa.int/Services/RSS_Feeds"
      priority: 70
      interval_minutes: 60
      verification_status: official_page_seen

    - id: celestrak_gp_public
      enabled: false
      source_family: celestrak
      source_class: official_satellite_catalog
      adapter: celestrak_gp_json
      homepage_url: "https://celestrak.org/NORAD/documentation/gp-data-formats.php"
      priority: 45
      interval_minutes: 120
      verification_status: official_page_seen
      safety_notes: "Do not build tactical tracking. Use only allowlisted object groups and high-level context."

    - id: space_track_auth_candidate
      enabled: false
      source_family: space_track
      source_class: restricted_auth_candidate
      adapter: space_track_api_candidate
      homepage_url: "https://www.space-track.org/documentation"
      priority: 20
      interval_minutes: 120
      verification_status: restricted_auth_required
      safety_notes: "Disabled by default. Requires credentials outside repo and explicit terms review."

SECTION 13: ORBITAL UI architecture

Design the eventual ORBITAL page.

Do not implement it.

The ORBITAL page should use the same console style.

Propose four bays.

Bay 1:
- "Orbital attention now"
- Highest-ranking ORBITAL events.
- Must show why each item is ranked.
- Must show source-family badges.
- Must show official vs news vs community convergence.
- Must show observed time and last seen.
- Must show impact tags such as GLOBAL, NATIONAL, REGIONAL, LOCAL, SKY, RADIO, GPS, AVIATION, SATELLITE, POWER, AURORA, CREWED, NEO.
- Must not dump routine space headlines or catalog churn.

Bay 2:
- "Space weather and sky"
- SWPC alerts, watches, warnings, Kp, solar wind, X-ray flux, proton flux, aurora, ICAO advisories, NEOs, fireballs, and time-sensitive sky events.
- Show active official alerts first.
- Show source freshness.
- Show local aurora interest when configured.
- Show source-backed "no active severe space weather" only when sources are healthy and recently scanned.

Bay 3:
- "Launch, mission, and orbit ops"
- Launch schedules, scrubs, launch results, crewed missions, ISS events, dockings, undockings, EVAs, reentries, debris, conjunction-awareness, and mission anomalies.
- Useful for "what is happening operationally in spaceflight?"

Bay 4:
- "Space press and source health"
- NASA, ESA, JPL, agency feeds, SpaceNews, Spaceflight Now, NASASpaceflight, Space.com, Ars space, Planetary Society, public media, and future configured sources.
- Social/community signals only if configured and compliant.
- Show source-health problems for SWPC, CNEOS, Launch Library, agency RSS, and any auth-required sources.
- No fake headlines.
- If disabled, show "ORBITAL sources not configured."

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
- object or mission label where applicable
- impact tag where applicable
- severity scale where applicable

Empty states:

- ORBITAL recent-signal layer disabled.
- ORBITAL sources not configured.
- ORBITAL sources configured but disabled.
- ORBITAL sources configured but never scanned.
- ORBITAL sources stale.
- ORBITAL source policy blocked.
- ORBITAL parser failed.
- ORBITAL social sources disabled by policy.
- ORBITAL homepage extraction disabled by policy.
- ORBITAL restricted/auth source disabled by policy.
- ORBITAL source requires token/account and is not configured.
- ORBITAL source marked manual_review_only.

SECTION 14: Evidence model for ORBITAL

Every item/event must trace back to source evidence.

For an ORBITAL event, evidence should include:

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
- operational impact basis
- public impact basis
- source diversity basis
- local/global impact basis
- sensitivity decision
- retention expiration
- matching tokens
- event type
- event confidence
- policy notes
- low-public-value penalty if applied
- sensitivity penalty if applied
- rumor penalty if applied
- out-of-scope penalty if applied

For space weather events, evidence must include, where available:

- product id
- issue time
- valid start and end time
- NOAA scale category
- G/R/S level
- Kp value
- flare class
- proton/radiation storm level
- solar wind values
- aurora product timestamp
- affected systems from source text if provided
- source instructions URL

For NEO and fireball events, evidence must include, where available:

- object designation
- CNEOS or MPC event id
- close approach date/time
- miss distance
- lunar distance
- relative velocity
- estimated diameter range
- condition code if provided
- fireball energy
- fireball altitude
- fireball latitude/longitude if source provides it
- official risk framing
- source URL

For launch and mission events, evidence must include, where available:

- mission name
- launch id
- provider
- vehicle
- payload
- launch site
- launch window
- launch status
- status update time
- webcast URL if provided by source
- crewed flag
- ISS or docking flag
- scrub/anomaly reason if source provides it
- official provider or agency URL

For satellite, reentry, debris, and conjunction-awareness events, evidence must include, where available and safe:

- object name
- NORAD catalog number, only if source-provided and safe
- COSPAR ID, only if source-provided and safe
- source family
- reentry prediction window
- uncertainty window
- object mass class if source provides it
- official or unofficial status
- sensitivity classification
- reason for suppression or de-emphasis if applied
- source URL

For science and astronomy events, evidence must include, where available:

- mission or instrument
- source organization
- object name
- discovery or release date
- source publication URL
- whether this is operationally time-sensitive or only general science news

SECTION 15: Source health for ORBITAL

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
- restricted_source_disabled
- needs_terms_review
- needs_scope_filter
- sensitivity_blocked

Source health must be visible in SYSTEM later and summarized in ORBITAL Bay 4 or a footer strip.

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

SECTION 16: First implementation sequence for ORBITAL

Design future phases.

Phase O0: this design
- Create design doc.
- Update BACKLOG.
- No runtime behavior change.

Phase O1: source registry scaffolding
- Add disabled ORBITAL source config.
- Add source registry schema or tables if not already done by global architecture.
- Add tests proving ORBITAL disabled by default.
- No network.

Phase O2: local fixtures only
- Create fixture files for:
  SWPC alerts JSON.
  SWPC NOAA scales JSON.
  SWPC Kp JSON.
  SWPC aurora JSON.
  JPL CNEOS close approach JSON.
  JPL CNEOS fireball JSON.
  JPL Sentry or Scout fixture.
  MPC MPEC fixture.
  Launch Library upcoming launch fixture.
  Spaceflight News API fixture.
  NASA RSS fixture.
  ESA RSS fixture.
  CelesTrak GP JSON tiny allowlisted fixture.
  Space-Track auth-required fake source-health fixture, with no real credentials.
  Reentry page fixture if later verified.
  Space news RSS fixture.
- Parse fixtures only.
- Store normalized metadata.
- No live fetch.

Phase O3: ORBITAL event correlation
- Deterministic token/object/time/source-family matching.
- No LLM.
- Tests for convergence.
- Tests for duplicate suppression.
- Tests for source-family diversity.
- Tests for mission/object/event-id matching.
- Tests for orbital vs global vs national vs regional vs local scope routing.

Phase O4: ORBITAL ranking
- Implement scoring model.
- Explain ranking in JSON.
- Tests for official severity, source diversity, recency, operational impact, public impact, local impact tags, low-public-value penalty, sensitivity penalty, stale-source penalty, and out-of-scope penalty.

Phase O5: ORBITAL UI disabled and fixture-backed states
- Replace ORBITAL placeholders with honest states.
- Fixture-backed in tests only.
- No live fetch.
- No fake headlines.

Phase O6: official API/RSS live fetch, opt-in only
- Start with one safe official source.
- Suggested first candidates:
  SWPC alerts JSON.
  SWPC NOAA scales JSON.
  SWPC Kp JSON.
  JPL CNEOS close approach API.
  JPL CNEOS fireball API.
  NASA RSS.
- Must be disabled by default.
- Must use explicit command.
- No page-load fetch.

Phase O7: launch/event sources
- Launch Library 2 only after throttling and fixture tests exist.
- Spaceflight News API only as headline metadata.
- Official launch provider pages or feeds only after source-policy review.
- No live launch scraping.

Phase O8: satellite/debris/reentry sources
- CelesTrak only with safety rules and allowlisted object groups.
- ESA reentry page only after endpoint/parser review.
- NASA Orbital Debris Quarterly News as RSS or manual source if available.
- Space-Track stays auth_required and disabled unless explicitly configured.
- No tactical tracking UI.

Phase O9: astronomy and science signals
- NASA Exoplanet Archive, MAST, GCN, ATel, MPC, or similar only with strict filters.
- Prefer official news/RSS and time-sensitive alerts.
- No large catalog ingestion.

Phase O10: space news RSS
- Publisher feeds only.
- Store metadata only.
- No article bodies.
- No paywall bypass.
- Do not let news-only clusters outrank official SWPC/CNEOS/agency alerts without convergence.

Phase O11: social/community
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
- ORBITAL disabled by default.
- Source disabled by default.
- Invalid source class rejected.
- Invalid adapter rejected.
- Social source rejected unless allow_social_sources true.
- Restricted/auth source rejected unless include_restricted_or_auth_sources true.
- Space-Track source marked auth_required unless credentials are explicitly configured outside repo.
- CelesTrak source rejected unless source scope and object-group filters are configured.
- Homepage extraction rejected unless allow_homepage_extractors true.
- Source without URL rejected unless adapter supports no URL.
- Secrets not allowed in config.example.yml.

Registry:
- Source keys unique.
- Source family valid.
- Source class valid.
- Verification status valid.
- Retention settings valid.
- Space weather thresholds valid.
- NEO filters valid.
- Launch filters valid.
- Satellite safety filters valid.
- Restricted-source flags valid.

Parser fixture tests:
- SWPC alerts JSON fixture parses.
- SWPC NOAA scales JSON fixture parses.
- SWPC Kp JSON fixture parses.
- SWPC aurora JSON fixture parses.
- JPL CNEOS close approach fixture parses.
- JPL CNEOS fireball fixture parses.
- JPL Sentry or Scout fixture parses.
- MPC MPEC fixture parses.
- Launch Library upcoming launch fixture parses.
- Spaceflight News API fixture parses.
- NASA RSS fixture parses.
- ESA RSS fixture parses.
- CelesTrak tiny allowlisted fixture parses.
- Restricted Space-Track source returns auth_required without network.
- Space news RSS fixture parses.
- Malformed feed fails soft.
- Oversized payload blocked or truncated.

Safety and sensitivity tests:
- Space-Track source does not run without explicit credentials.
- No credentials are stored in repo.
- Tactical tracking UI is not created.
- Restricted source item is not displayed as live.
- Routine catalog churn does not elevate to ORBITAL attention.
- Military or sensitive satellite tracking is blocked or de-emphasized unless official public news and public-impact rules apply.
- Social-only reentry rumor does not outrank official sources.
- NEO close approach does not use panic language.
- Space weather alert shows official source and scale, not invented impacts.

Correlation tests:
- SWPC G-level alert plus Kp product plus NOAA scale plus news coverage becomes one space weather event.
- SWPC aurora product plus Kp threshold plus regional interest becomes one aurora event.
- CNEOS close approach plus MPC notice plus news coverage becomes one NEO event.
- CNEOS fireball plus news coverage becomes one fireball event.
- Launch Library event plus NASA/provider update plus space news becomes one launch event.
- Same event from multiple news outlets counts as news-family convergence but not endless duplicate inflation.
- Same source repeated does not inflate source diversity.
- Different source families increase diversity.
- Global terrestrial item without orbital cause does not appear in ORBITAL.
- National policy item without space/orbital relevance does not appear in ORBITAL.

Ranking tests:
- SWPC G4 storm outranks routine space news.
- X-class flare outranks generic mission article.
- Crewed launch outranks routine commercial satellite launch unless configured otherwise.
- Launch failure or scrub outranks ordinary launch schedule entry.
- NEO close approach under configured distance/size threshold outranks distant low-risk object.
- Official reentry prediction outranks social-only reentry claim.
- Space weather with local aurora tag outranks generic astronomy article.
- Stale source lowers confidence.
- Source policy blocked item never displays as live.
- Restricted/auth source item never displays unless explicitly configured and policy-approved.

API design tests for later:
- GET routes read SQLite only.
- GET routes do not fetch network.
- Disabled/not configured/stale/failing/auth_required/restricted_source_disabled states distinct.

UI tests for later:
- No fake headlines.
- Empty states clear.
- Evidence visible.
- Ranking reason visible.
- Source health visible.
- Mission/object/severity label visible.
- Local/global impact tags visible when applicable.
- Restricted source disabled state visible when relevant.

Safety tests:
- No page-load external fetches.
- No hidden LLM calls.
- No telemetry.
- No package install.
- No sudo.
- No social fetch unless explicitly configured.
- No restricted source fetch unless explicitly configured.
- No API-key source runs without key configuration.
- No tactical tracking output.

SECTION 18: Backlog update requirements

Update BACKLOG.md.

Add a section named:

ORBITAL Space Recent Signal Layer

Add concrete backlog items with Status: not implemented.

Include at least:

- ORBITAL source registry design implemented from document.
- Disabled-by-default ORBITAL config.
- ORBITAL SQLite schema or extension.
- ORBITAL fixture pack.
- SWPC alerts JSON parser.
- SWPC NOAA scales parser.
- SWPC Kp and aurora fixture parsers.
- JPL CNEOS close approach parser.
- JPL CNEOS fireball parser.
- JPL Sentry/Scout source verification.
- MPC MPEC and NEOCP source verification.
- Launch Library 2 fixture parser.
- Spaceflight News API fixture parser.
- NASA RSS parser.
- ESA RSS parser.
- Official launch provider source verification.
- ISS and crewed-spaceflight source verification.
- CelesTrak public GP safety review and tiny allowlisted fixture parser.
- Space-Track auth-required policy design.
- ESA reentry source verification.
- NASA Orbital Debris source verification.
- ORBITAL deterministic event correlation.
- ORBITAL deterministic ranking.
- ORBITAL safety and sensitivity rules.
- ORBITAL local/global impact tag rules.
- ORBITAL UI disabled states.
- ORBITAL source health states.
- ORBITAL evidence drawer contract.
- ORBITAL official-source live ingest phase, disabled by default.
- ORBITAL launch/event API ingest phase, disabled by default.
- ORBITAL space news RSS ingest phase, disabled by default.
- ORBITAL restricted/auth source policy review, disabled by default.
- ORBITAL social source policy review, disabled by default.
- Documentation for source verification.
- Tests for no page-load external fetches.
- Tests for no restricted source running without explicit config.
- Tests for no API-key source running without config.
- Tests for no tactical satellite tracking output.

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
- No permanent satellite catalog archive.
- No private data collection.
- No tactical satellite tracking.
- No military or intelligence satellite monitoring.
- No classified activity inference.
- No launch livestream scraping.
- No scraping behind login.
- No bypassing Space-Track, Reddit, X, API, or account restrictions.
- No claiming social chatter is verified fact.
- No treating unofficial aggregators as official.
- No treating duplicate articles as independent confirmation.
- No NEO panic language.
- No reentry panic language.
- No orbital debris fear dashboard.
- No space-company fandom feed.
- No investment advice.
- No medical advice.
- No legal advice.
- No burying LOCAL, REGIONAL, NATIONAL, GLOBAL, or SYSTEM urgent items under ORBITAL headlines.
- No importing GLOBAL terrestrial content unless orbital relevance rules allow it.
- No automatic API key discovery or secret storage.
- No broad satellite firehose ingestion.

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
6. Confirmation that ORBITAL remains disabled by default.
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

This one is stricter on safety than the others because ORBITAL can accidentally become a satellite tracker or space-rumor board. The prompt pushes Codex toward SWPC, NASA, JPL/CNEOS, MPC, ESA, Launch Library, and agency feeds first, while putting Space-Track, CelesTrak-heavy use, social, and debris/conjunction sources behind policy and sensitivity gates.

[1]: https://api.nasa.gov/?utm_source=chatgpt.com "NASA Open APIs"
