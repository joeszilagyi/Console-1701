# ORBITAL Space Recent Signal Source Targets Design

## SECTION 1: Purpose

The ORBITAL scope is the space, sky, and near-Earth environment recent-signal layer for
console-1701. It should eventually tell the user what is happening above Earth and in nearby space,
with source provenance, observed time, source kind, ranking reason, freshness, and evidence.

ORBITAL is not:

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

ORBITAL is:

- A local, short-retention metadata dashboard.
- A deterministic cross-source event detector for orbital, space weather, near-Earth object, launch,
  mission, satellite, and sky signals.
- A source-health aware recent-signal system.
- An ORBITAL tab in console-1701 that can surface official space weather alerts, aurora chances,
  solar storms, NEO close approaches, fireballs, launch events, spacecraft anomalies, ISS and
  crewed-flight updates, orbital debris and reentry notices, official agency news, mission
  milestones, and spaceflight news.
- A way to rank items by independent source convergence, official severity, public impact,
  operational relevance, local or global effect, freshness, and user-configured source priority.

"Orbital" means useful public, configured, lawful, recent signals that the user chooses to enable.
It does not mean unbounded space data harvesting, restricted satellite tracking, private operator
monitoring, or automated space intelligence.

The daily runtime goal is no LLM usage. LLMs may help during development to design adapters,
inspect fixtures, write tests, or analyze source options, but the application itself must not
require LLM calls for normal operation.

## SECTION 2: ORBITAL scope boundaries

Default ORBITAL scope:

- Near-Earth space.
- Earth orbit.
- Space weather affecting Earth, satellites, radio, GPS, aviation, power grids, and aurora
  visibility.
- Solar system objects with potential Earth relevance.
- Near-Earth object close approaches and fireballs.
- Space launch, mission, docking, reentry, and crewed-spaceflight events.
- Public satellite catalog and orbital element metadata only where lawful and policy-compliant.
- Orbital debris, reentry, and space sustainability signals where public and non-tactical.
- Space agency mission updates and science releases where timely.
- Astronomy and sky events only when time-sensitive or useful for situational awareness.
- Spaceflight news only when it covers real operational, launch, mission, hazard, policy, science,
  or infrastructure events.

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
- Global terrestrial disasters, unless caused by or directly tied to space weather, reentry,
  asteroid impact, or orbital infrastructure.
- Local Seattle sky visibility except as a tagged local impact for aurora, ISS passes, major meteor
  events, or visible reentry.

Future disabled-by-default config escape hatch:

```yaml
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
```

## SECTION 3: Relationship to LOCAL, REGIONAL, NATIONAL, GLOBAL, and OVERVIEW

ORBITAL should complement other scopes rather than duplicate them.

Rules:

- ORBITAL owns space weather, solar storms, aurora, NEOs, fireballs, launches, spacecraft
  operations, satellites, reentries, orbital debris, and space agency mission signals.
- GLOBAL owns world terrestrial events unless the cause or infrastructure is orbital or
  space-weather related.
- NATIONAL owns U.S. domestic federal and public-impact signals unless the primary subject is
  orbital or space-weather.
- REGIONAL owns Washington / PNW terrestrial impacts.
- LOCAL owns Seattle local impacts.
- OVERVIEW should select the highest-priority items from LOCAL, REGIONAL, NATIONAL, GLOBAL,
  ORBITAL, and SYSTEM without burying urgent local/system issues.
- If an ORBITAL event affects Earth systems, tag it with `GLOBAL_IMPACT`, `NATIONAL_IMPACT`,
  `REGIONAL_IMPACT`, or `LOCAL_IMPACT` where supported by evidence.
- If a space weather event creates aurora potential over Washington, canonical scope remains
  ORBITAL with `REGIONAL_IMPACT` or `LOCAL_IMPACT`.
- If a launch causes road or airspace disruption in Florida, canonical scope remains ORBITAL but
  NATIONAL or LOCAL impact can be tagged only if relevant source data exists.
- If an asteroid close approach is routine and low-risk, it stays low priority.
- If a fireball is widely reported and has official JPL/CNEOS or NASA/NOAA support, it can rise in
  ORBITAL and possibly GLOBAL or NATIONAL attention.
- If a satellite reentry has credible official public-risk or airspace impact, ORBITAL can tag
  `GLOBAL_IMPACT` or `NATIONAL_IMPACT`.
- If a solar storm affects power grids, aviation, GPS, HF radio, satellites, aurora, or
  communications, ORBITAL can feed OVERVIEW strongly.

Examples:

- SWPC G4 geomagnetic storm watch: ORBITAL, possible NATIONAL/GLOBAL impact.
- Kp 6 with aurora visibility in Washington: ORBITAL with REGIONAL_IMPACT and LOCAL_IMPACT.
- NASA Artemis launch: ORBITAL, possible NATIONAL impact.
- SpaceX routine Starlink launch: ORBITAL, likely lower unless scrub, failure, crewed, visible, or
  payload/conjunction relevance exists.
- JPL CNEOS close approach under 1 lunar distance for a sizeable NEO: ORBITAL.
- Small NEO at 20 lunar distances: background ORBITAL or ignored.
- ISS docking or EVA: ORBITAL.
- Routine NASA science article: ORBITAL press pulse, low priority unless mission-impact or
  discovery event.
- CelesTrak catalog update: source health or background unless reentry/debris relevance exists.
- Space weather impacting aviation HF communications: ORBITAL with GLOBAL or NATIONAL impact tag.
- Space policy article with no operational relevance: low priority ORBITAL or NATIONAL depending
  content.

## SECTION 4: Seed source target inventory

This table is a candidate inventory, not a verification result. No live source verification was
performed in this task. `official_page_seen` means the source is a source-identifiable official
candidate from prompt context, not that parser behavior has been tested. URLs requiring endpoint
review, auth, account, token, terms review, policy review, selector review, or volume review remain
`candidate_needs_verification`, `candidate_policy_sensitive`, or `restricted_auth_required`.

Risk values use `low`, `medium`, or `high`. Future phases use `O0` through `O11` from the
implementation sequence.

| source_key | source_name | source_family | source_class | scope | raw_url | expected_access_kind | likely_adapter_type | likely_refresh_interval | initial_priority | official_status | privacy_risk | policy_risk | parser_risk | retention_sensitivity | verification_status | why_it_matters | future_phase |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| swpc_home | NOAA SWPC | swpc | official_space_weather | ORBITAL | https://www.swpc.noaa.gov/ | public official webpage | source_health_probe_only | 24 h | 70 | official | low | low | low | low | official_page_seen | Space-weather authority reference. | O1 |
| swpc_products_data | SWPC products and data | swpc | source_health_only | ORBITAL | https://www.swpc.noaa.gov/products-and-data | public official product index | source_health_probe_only | 24 h | 35 | official | low | low | low | low | official_page_seen | Product discovery reference, not an item source by itself. | O1 |
| swpc_data_access | SWPC data access | swpc | source_health_only | ORBITAL | https://www.swpc.noaa.gov/content/data-access | public official data docs | manual_review_only | manual | 10 | official | low | low | low | low | user_seeded | Access and product reference for later verification. | O1 |
| swpc_alerts_page | SWPC alerts watches warnings page | swpc | official_space_weather | ORBITAL | https://www.swpc.noaa.gov/products/alerts-watches-and-warnings | public official product page | swpc_product_text | 5 min | 95 | official | low | low | medium | medium | official_page_seen | Human-readable official alert source and text product reference. | O6 |
| swpc_alerts_json | SWPC alerts JSON | swpc | official_space_weather_json | ORBITAL | https://services.swpc.noaa.gov/products/alerts.json | public official JSON product | swpc_alerts_json | 5 min | 100 | official | low | low | medium | medium | official_page_seen | Best first candidate for space-weather watches, warnings, and alerts. | O6 |
| swpc_noaa_scales_json | SWPC NOAA scales JSON | swpc | official_space_weather_json | ORBITAL | https://services.swpc.noaa.gov/products/noaa-scales.json | public official JSON product | swpc_json | 5 min | 95 | official | low | low | medium | medium | official_page_seen | Official G/R/S scale state for ranking. | O6 |
| swpc_kp_summary_json | SWPC planetary K-index summary | swpc | official_space_weather_json | ORBITAL | https://services.swpc.noaa.gov/products/summary/planetary-k-index.json | public official JSON product | swpc_json | 5 min | 90 | official | low | low | medium | low | official_page_seen | Kp summary for geomagnetic and aurora ranking. | O6 |
| swpc_kp_1m_json | SWPC planetary K-index 1m JSON | swpc | official_space_weather_json | ORBITAL | https://services.swpc.noaa.gov/json/planetary_k_index_1m.json | public official JSON product | swpc_json | 5 min | 85 | official | low | low | medium | low | candidate_needs_verification | High-frequency Kp candidate; use caps and retention. | O6 |
| swpc_boulder_k_json | SWPC Boulder K-index JSON | swpc | official_space_weather_json | ORBITAL | https://services.swpc.noaa.gov/json/boulder_k_index_1m.json | public official JSON product | swpc_json | 5 min | 60 | official | low | low | medium | low | candidate_needs_verification | Regional geomagnetic context, lower than planetary Kp. | O6 |
| swpc_solar_wind_summary | SWPC solar wind speed summary | swpc | official_solar_data | ORBITAL | https://services.swpc.noaa.gov/products/summary/solar-wind-speed.json | public official JSON product | swpc_json | 5 min | 80 | official | low | low | medium | low | official_page_seen | Solar wind evidence for CME/shock events. | O6 |
| swpc_xray_flux_summary | SWPC X-ray flux summary | swpc | official_solar_data | ORBITAL | https://services.swpc.noaa.gov/products/summary/x-ray-flux.json | public official JSON product | swpc_json | 5 min | 80 | official | low | low | medium | low | official_page_seen | Solar flare ranking evidence. | O6 |
| swpc_10cm_flux_summary | SWPC 10cm flux summary | swpc | official_solar_data | ORBITAL | https://services.swpc.noaa.gov/products/summary/10cm-flux.json | public official JSON product | swpc_json | 60 min | 45 | official | low | low | medium | low | official_page_seen | Solar context, lower priority. | O6 |
| swpc_goes_xray_page | SWPC GOES X-ray flux page | swpc | official_solar_data | ORBITAL | https://www.swpc.noaa.gov/products/goes-x-ray-flux | public official product page | source_health_probe_only | 24 h | 30 | official | low | low | low | low | official_page_seen | Human reference for X-ray product. | O1 |
| swpc_goes_proton_page | SWPC GOES proton flux page | swpc | official_solar_data | ORBITAL | https://www.swpc.noaa.gov/products/goes-proton-flux | public official product page | source_health_probe_only | 24 h | 30 | official | low | low | low | low | official_page_seen | Human reference for radiation storm evidence. | O1 |
| swpc_aurora_page | SWPC aurora 30-minute forecast | swpc | official_aurora | ORBITAL | https://www.swpc.noaa.gov/products/aurora-30-minute-forecast | public official product page | source_health_probe_only | 24 h | 65 | official | low | low | low | low | official_page_seen | Aurora product reference. | O1 |
| swpc_aurora_json | SWPC OVATION aurora JSON | swpc | official_aurora | ORBITAL | https://services.swpc.noaa.gov/json/ovation_aurora_latest.json | public official JSON product | swpc_json | 10 min | 85 | official | low | low | medium | low | official_page_seen | Local/regional aurora interest candidate. | O6 |
| swpc_icao_json | SWPC ICAO space weather advisories JSON | swpc | official_space_weather_json | ORBITAL | https://services.swpc.noaa.gov/json/icao-space-weather-advisories.json | public official JSON product | swpc_json | 15 min | 85 | official | low | low | medium | medium | official_page_seen | Aviation-relevant space-weather source. | O6 |
| swpc_icao_page | SWPC ICAO advisory page | swpc | official_space_weather | ORBITAL | https://www.swpc.noaa.gov/products/icao-space-weather-advisories | public official product page | swpc_product_text | 15 min | 70 | official | low | low | medium | medium | candidate_needs_verification | Human-readable aviation advisory reference. | O6 |
| weather_space_safety | NWS space weather safety | nws | source_health_only | ORBITAL | https://www.weather.gov/safety/space-ww | public official safety page | source_health_probe_only | 24 h | 20 | official | low | low | low | low | official_page_seen | Safety guidance reference; not a signal feed. | O1 |
| ncei_swpc_products | NCEI SWPC products partner page | noaa_ncei | source_health_only | ORBITAL | https://www.ncei.noaa.gov/products/space-weather/partners/swpc-products-and-data | public official reference | source_health_probe_only | 24 h | 20 | official | low | low | low | low | official_page_seen | Product reference and archival context. | O1 |
| noaa_space_weather_aws | NOAA space weather AWS open data | noaa_open_data | manual_review_only | ORBITAL | https://registry.opendata.aws/noaa-space-weather/ | public open data registry | manual_review_only | disabled | 10 | official_candidate | low | medium | high | medium | candidate_policy_sensitive | Heavy/open-data candidate, not early dashboard source. | O9 |
| nasa_open_apis | NASA Open APIs | nasa | official_mission_news | ORBITAL | https://api.nasa.gov/ | public official API docs | nasa_api_json | disabled | 35 | official | low | medium | medium | low | official_page_seen | Candidate small APIs only; no imagery-heavy default use. | O9 |
| nasa_rss_feeds | NASA RSS feeds | nasa | official_space_agency_news | ORBITAL | https://www.nasa.gov/rss-feeds/ | public official RSS index | rss_atom | 60 min | 75 | official | low | low | medium | low | official_page_seen | Official NASA metadata path after feed verification. | O6 |
| nasa_news | NASA news | nasa | official_space_agency_news | ORBITAL | https://www.nasa.gov/news/ | public official webpage/feed candidate | rss_atom | 60 min | 65 | official | low | low | medium | low | candidate_needs_verification | Official NASA news, filtered to orbital relevance. | O6 |
| nasa_blogs | NASA blogs | nasa_blogs | official_mission_news | ORBITAL | https://blogs.nasa.gov/ | public official blog index/feed candidate | rss_atom | 60 min | 65 | official | low | low | medium | low | candidate_needs_verification | Mission blogs can carry timely launch/station updates. | O6 |
| nasa_launches | NASA launches | nasa | official_launch | ORBITAL | https://www.nasa.gov/launches/ | public official webpage/feed candidate | rss_atom | 60 min | 75 | official | low | low | medium | low | candidate_needs_verification | Official launch source. | O7 |
| nasa_missions | NASA missions | nasa | official_mission_news | ORBITAL | https://www.nasa.gov/missions/ | public official webpage | static_html_headline_candidate | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | Mission update source when no feed exists. | O6 |
| nasa_iss_page | NASA International Space Station | nasa_space_station | official_iss | ORBITAL | https://www.nasa.gov/international-space-station/ | public official webpage/feed candidate | rss_atom | 60 min | 70 | official | low | low | medium | low | candidate_needs_verification | ISS operational and mission updates. | O7 |
| nasa_spacestation_blog | NASA Space Station blog | nasa_space_station | official_iss | ORBITAL | https://blogs.nasa.gov/spacestation/ | public official blog/feed candidate | rss_atom | 60 min | 80 | official | low | low | medium | low | candidate_needs_verification | Strong ISS and crewed-spaceflight source. | O7 |
| nasa_artemis | NASA Artemis | nasa | official_crewed_spaceflight | ORBITAL | https://www.nasa.gov/artemis/ | public official webpage/feed candidate | rss_atom | 60 min | 65 | official | low | low | medium | low | candidate_needs_verification | Crewed lunar program source. | O7 |
| nasa_artemis_blog | NASA Artemis blog | nasa_blogs | official_crewed_spaceflight | ORBITAL | https://blogs.nasa.gov/artemis/ | public official blog/feed candidate | rss_atom | 60 min | 65 | official | low | low | medium | low | candidate_needs_verification | Mission milestone source. | O7 |
| nasa_kennedy_blog | NASA Kennedy blog | nasa_blogs | official_launch | ORBITAL | https://blogs.nasa.gov/kennedy/ | public official blog/feed candidate | rss_atom | 60 min | 60 | official | low | low | medium | low | candidate_needs_verification | Launch campaign and range context. | O7 |
| jpl_news | JPL news | nasa_jpl | official_mission_news | ORBITAL | https://www.jpl.nasa.gov/news/ | public official webpage/feed candidate | rss_atom | 60 min | 70 | official | low | low | medium | low | candidate_needs_verification | JPL mission and NEO context. | O6 |
| jpl_rss | JPL RSS | nasa_jpl | official_mission_news | ORBITAL | https://www.jpl.nasa.gov/rss/ | public official RSS index | rss_atom | 60 min | 70 | official | low | low | medium | low | official_page_seen | Preferred JPL metadata path if stable. | O6 |
| nasa_science_news | NASA science news | nasa_science | official_science_release | ORBITAL | https://science.nasa.gov/news/ | public official webpage/feed candidate | rss_atom | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | Science releases can be ORBITAL if timely/mission-relevant. | O9 |
| parker_solar_probe | Parker Solar Probe | nasa_science | official_solar_data | ORBITAL | https://science.nasa.gov/mission/parker-solar-probe/ | public official mission page | source_health_probe_only | 24 h | 35 | official | low | low | low | low | user_seeded | Solar mission context; not a live alert source. | O1 |
| jpl_ssd_home | JPL SSD API | jpl_cneos | official_neo | ORBITAL | https://ssd-api.jpl.nasa.gov/ | public official API landing | jpl_ssd_api | 60 min | 70 | official | low | low | medium | low | official_page_seen | JPL small-body API authority reference. | O6 |
| jpl_ssd_doc | JPL SSD API docs | jpl_cneos | source_health_only | ORBITAL | https://ssd-api.jpl.nasa.gov/doc/index.php | public official docs | manual_review_only | manual | 10 | official | low | low | low | low | official_page_seen | Implementation reference for JPL SSD adapters. | O1 |
| jpl_cad_api | JPL close approach API | jpl_cneos | official_neo | ORBITAL | https://ssd-api.jpl.nasa.gov/cad.api | public official API endpoint | jpl_ssd_api | 60 min | 90 | official | low | low | medium | medium | official_page_seen | Strong candidate for NEO close approach events. | O6 |
| jpl_cad_doc | JPL CAD docs | jpl_cneos | source_health_only | ORBITAL | https://ssd-api.jpl.nasa.gov/doc/cad.html | public official docs | manual_review_only | manual | 10 | official | low | low | low | low | official_page_seen | Query-shape reference. | O1 |
| jpl_fireball_api | JPL fireball API | jpl_cneos | official_fireball | ORBITAL | https://ssd-api.jpl.nasa.gov/fireball.api | public official API endpoint | cneos_api | 60 min | 85 | official | low | low | medium | medium | official_page_seen | Fireball/bolide metadata source. | O6 |
| jpl_fireball_doc | JPL fireball docs | jpl_cneos | source_health_only | ORBITAL | https://ssd-api.jpl.nasa.gov/doc/fireball.html | public official docs | manual_review_only | manual | 10 | official | low | low | low | low | official_page_seen | Fireball parser reference. | O1 |
| jpl_sentry_api | JPL Sentry API | jpl_cneos | official_neo | ORBITAL | https://ssd-api.jpl.nasa.gov/sentry.api | public official API endpoint | jpl_ssd_api | 6 h | 70 | official | low | low | medium | medium | candidate_needs_verification | Impact-risk source, must avoid panic language. | O6 |
| jpl_scout_api | JPL Scout API | jpl_cneos | official_neo | ORBITAL | https://ssd-api.jpl.nasa.gov/scout.api | public official API endpoint | jpl_ssd_api | 6 h | 60 | official | low | low | medium | medium | candidate_needs_verification | NEO candidate/risk context, verified later. | O6 |
| jpl_sbdb_api | JPL SBDB API | jpl_cneos | official_minor_planet | ORBITAL | https://ssd-api.jpl.nasa.gov/sbdb.api | public official API endpoint | jpl_ssd_api | 6 h | 45 | official | low | low | medium | low | candidate_needs_verification | Object metadata enrichment for NEO events. | O6 |
| jpl_horizons_doc | JPL Horizons docs | jpl_cneos | manual_review_only | ORBITAL | https://ssd-api.jpl.nasa.gov/doc/horizons.html | public official docs | manual_review_only | disabled | 5 | official | low | medium | high | medium | candidate_policy_sensitive | Too query-heavy for early dashboard; manual review only. | O9 |
| cneos_home | CNEOS | jpl_cneos | official_neo | ORBITAL | https://cneos.jpl.nasa.gov/ | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | official_page_seen | NEO authority reference. | O1 |
| cneos_ca | CNEOS close approaches | jpl_cneos | official_neo | ORBITAL | https://cneos.jpl.nasa.gov/ca/ | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | official_page_seen | Human close-approach reference. | O1 |
| cneos_fireballs | CNEOS fireballs | jpl_cneos | official_fireball | ORBITAL | https://cneos.jpl.nasa.gov/fireballs/ | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | official_page_seen | Human fireball reference. | O1 |
| cneos_sentry | CNEOS Sentry | jpl_cneos | official_neo | ORBITAL | https://cneos.jpl.nasa.gov/sentry/ | public official webpage | source_health_probe_only | 24 h | 35 | official | low | low | low | low | official_page_seen | Risk-list human reference. | O1 |
| mpc_home | Minor Planet Center | mpc | official_minor_planet | ORBITAL | https://www.minorplanetcenter.net/ | public official-ish webpage | source_health_probe_only | 24 h | 45 | official_candidate | low | low | low | low | official_page_seen | Minor planet authority reference. | O1 |
| mpc_docs | MPC API documentation | mpc | source_health_only | ORBITAL | https://www.minorplanetcenter.net/mpcops/documentation/ | public docs | manual_review_only | manual | 10 | official_candidate | low | low | low | low | official_page_seen | MPC API implementation reference. | O1 |
| mpc_mpecs_api | MPC MPECs API docs | mpc | official_minor_planet | ORBITAL | https://www.minorplanetcenter.net/mpcops/documentation/mpecs-api/ | public API docs | mpc_api | 60 min | 55 | official_candidate | low | low | medium | medium | official_page_seen | MPEC metadata candidate after endpoint review. | O6 |
| mpc_recent_mpecs | Recent MPECs | mpc | official_minor_planet | ORBITAL | https://www.minorplanetcenter.net/mpec/RecentMPECs.html | public page | mpc_api | 60 min | 45 | official_candidate | low | low | medium | medium | candidate_needs_verification | Recent MPEC page candidate. | O6 |
| mpc_neocp_api | MPC NEOCP observations API | mpc | official_minor_planet | ORBITAL | https://cgi.minorplanetcenter.net/mpcops/documentation/neocp-observations-api/ | public API docs | mpc_api | disabled | 35 | official_candidate | low | medium | medium | medium | candidate_policy_sensitive | Needs careful filters and no observation firehose. | O6 |
| mpc_observations_api | MPC observations API | mpc | manual_review_only | ORBITAL | https://www.minorplanetcenter.net/mpcops/documentation/observations-api/ | public API docs | manual_review_only | disabled | 10 | official_candidate | low | medium | high | medium | candidate_policy_sensitive | Observation firehose risk; manual review only. | O9 |
| launch_library_home | Launch Library 2 | launch_library | launch_event_api | ORBITAL | https://ll.thespacedevs.com/ | public launch/event API landing | launch_library_api | 30 min | 80 | public_api | low | medium | medium | low | official_page_seen | Launch/event API candidate, disabled by default. | O7 |
| launch_library_launches | Launch Library launches | launch_library | launch_event_api | ORBITAL | https://ll.thespacedevs.com/2.3.0/launches/ | public launch API endpoint | launch_library_api | 30 min | 75 | public_api | low | medium | medium | low | candidate_needs_verification | Launch metadata candidate. | O7 |
| launch_library_upcoming | Launch Library upcoming launches | launch_library | launch_event_api | ORBITAL | https://ll.thespacedevs.com/2.3.0/launches/upcoming/ | public launch API endpoint | launch_library_api | 30 min | 80 | public_api | low | medium | medium | low | official_page_seen | Best fixture candidate for launch schedule/status. | O7 |
| launch_library_events | Launch Library upcoming events | launch_library | launch_event_api | ORBITAL | https://ll.thespacedevs.com/2.3.0/events/upcoming/ | public event API endpoint | launch_library_api | 30 min | 65 | public_api | low | medium | medium | low | candidate_needs_verification | Docking, EVA, and spaceflight event candidate. | O7 |
| spacedevs_llapi | The Space Devs LL API docs | launch_library | source_health_only | ORBITAL | https://thespacedevs.com/llapi | public API docs | manual_review_only | manual | 10 | public_api | low | medium | low | low | user_seeded | API terms and docs reference. | O1 |
| spaceflight_news_api_docs | Spaceflight News API docs | spaceflight_news_api | spaceflight_news_api | ORBITAL | https://api.spaceflightnewsapi.net/v4/docs/ | public API docs | spaceflight_news_api | 60 min | 55 | public_api | low | medium | medium | low | official_page_seen | News metadata API candidate for correlation only. | O7 |
| spaceflight_news_articles | Spaceflight News API articles | spaceflight_news_api | spaceflight_news_api | ORBITAL | https://api.spaceflightnewsapi.net/v4/articles/ | public API endpoint | spaceflight_news_api | 60 min | 55 | public_api | low | medium | medium | low | candidate_needs_verification | Headline metadata source, not primary authority. | O7 |
| spaceflight_news_blogs | Spaceflight News API blogs | spaceflight_news_api | spaceflight_news_api | ORBITAL | https://api.spaceflightnewsapi.net/v4/blogs/ | public API endpoint | spaceflight_news_api | 60 min | 35 | public_api | low | medium | medium | low | candidate_needs_verification | Blog metadata, lower priority. | O10 |
| spacex_launches | SpaceX launches | spacex | commercial_launch_provider | ORBITAL | https://www.spacex.com/launches/ | public provider page | static_html_headline_candidate | 30 min | 55 | commercial_provider | low | medium | medium | low | candidate_needs_verification | Provider source, verify policy/selectors before use. | O7 |
| spacex_updates | SpaceX updates | spacex | commercial_launch_provider | ORBITAL | https://www.spacex.com/updates/ | public provider page | static_html_headline_candidate | 60 min | 45 | commercial_provider | low | medium | medium | low | candidate_needs_verification | Provider update candidate. | O7 |
| blue_origin_news | Blue Origin news | blue_origin | commercial_launch_provider | ORBITAL | https://www.blueorigin.com/news | public provider page/feed candidate | rss_atom | 60 min | 35 | commercial_provider | low | medium | medium | low | candidate_needs_verification | Provider source, lower than official agency/API. | O7 |
| rocket_lab_next_mission | Rocket Lab next mission | rocket_lab | commercial_launch_provider | ORBITAL | https://www.rocketlabusa.com/missions/next-mission/ | public provider page | static_html_headline_candidate | 60 min | 45 | commercial_provider | low | medium | medium | low | candidate_needs_verification | Launch provider source candidate. | O7 |
| ula_next_launch | ULA next launch | ula | commercial_launch_provider | ORBITAL | https://www.ulalaunch.com/missions/next-launch | public provider page | static_html_headline_candidate | 60 min | 45 | commercial_provider | low | medium | medium | low | candidate_needs_verification | Launch provider source candidate. | O7 |
| arianespace_mission_updates | Arianespace mission updates | arianespace | commercial_launch_provider | ORBITAL | https://www.arianespace.com/mission-updates/ | public provider page/feed candidate | rss_atom | 60 min | 45 | commercial_provider | low | medium | medium | low | candidate_needs_verification | Launch provider source candidate. | O7 |
| isro_press | ISRO press | isro | official_space_agency_news | ORBITAL | https://www.isro.gov.in/Press.html | public official page/feed candidate | rss_atom | 2 h | 40 | official | low | low | medium | low | candidate_needs_verification | International agency launch/mission source. | O6 |
| jaxa_press | JAXA press | jaxa | official_space_agency_news | ORBITAL | https://global.jaxa.jp/press/ | public official page/feed candidate | rss_atom | 2 h | 40 | official | low | low | medium | low | candidate_needs_verification | International agency source. | O6 |
| esa_rss | ESA RSS feeds | esa | official_space_agency_news | ORBITAL | https://www.esa.int/Services/RSS_Feeds | public official RSS index | rss_atom | 60 min | 70 | official | low | low | medium | low | official_page_seen | First safe ESA metadata candidate. | O6 |
| csa_news | CSA news | csa | official_space_agency_news | ORBITAL | https://www.asc-csa.gc.ca/eng/news/ | public official page/feed candidate | rss_atom | 2 h | 35 | official | low | low | medium | low | candidate_needs_verification | Canadian agency source. | O6 |
| cnsa_english | CNSA English | cnsa | official_space_agency_news | ORBITAL | https://www.cnsa.gov.cn/english/ | public official page | static_html_headline_candidate | 6 h | 25 | official | low | medium | medium | low | candidate_needs_verification | Agency source, verify before use. | O6 |
| celestrak_home | CelesTrak | celestrak | official_satellite_catalog | ORBITAL | https://celestrak.org/ | public satellite data site | source_health_probe_only | 24 h | 35 | official_candidate | low | medium | low | low | official_page_seen | Public satellite source reference, not tracking UI. | O1 |
| celestrak_elements | CelesTrak GP elements | celestrak | official_satellite_catalog | ORBITAL | https://celestrak.org/NORAD/elements/gp.php | public GP data endpoint | celestrak_gp_json | disabled | 45 | official_candidate | low | high | high | high | candidate_policy_sensitive | Tiny allowlisted fixture only; no tactical tracker. | O8 |
| celestrak_gp_formats | CelesTrak GP data formats | celestrak | source_health_only | ORBITAL | https://www.celestrak.org/NORAD/documentation/gp-data-formats.php | public docs | manual_review_only | manual | 10 | official_candidate | low | medium | low | low | official_page_seen | Format reference for tiny fixture parser. | O1 |
| celestrak_satcat | CelesTrak SATCAT | celestrak | official_satellite_catalog | ORBITAL | https://celestrak.org/satcat/ | public catalog page/data candidate | celestrak_satcat_csv_json | disabled | 35 | official_candidate | low | high | high | high | candidate_policy_sensitive | Metadata only, no broad satellite archive. | O8 |
| celestrak_socrates | CelesTrak SOCRATES | celestrak | official_conjunction_awareness | ORBITAL | https://celestrak.org/SOCRATES/ | public conjunction page | celestrak_socrates_candidate | disabled | 25 | official_candidate | low | high | high | high | candidate_policy_sensitive | Conjunction candidate, high sensitivity and manual review. | O8 |
| celestrak_supplemental | CelesTrak supplemental GP data | celestrak | official_satellite_catalog | ORBITAL | https://celestrak.org/NORAD/elements/supplemental/ | public GP data page | manual_review_only | disabled | 10 | official_candidate | low | high | high | high | candidate_policy_sensitive | Supplemental data not needed for early dashboard. | O8 |
| space_track_home | Space-Track | space_track | restricted_auth_candidate | ORBITAL | https://www.space-track.org/ | auth-required service | space_track_api_candidate | disabled | 15 | official | low | high | high | high | restricted_auth_required | Restricted/auth source; never bypass account controls. | O8 |
| space_track_docs | Space-Track documentation | space_track | restricted_auth_candidate | ORBITAL | https://www.space-track.org/documentation | auth-required docs/service | space_track_api_candidate | disabled | 15 | official | low | high | high | high | restricted_auth_required | Terms/auth review before any use. | O8 |
| nasa_cara | NASA CARA | nasa_cara | official_conjunction_awareness | ORBITAL | https://www.nasa.gov/cara/ | public official webpage | source_health_probe_only | 24 h | 30 | official | low | medium | low | low | official_page_seen | Conjunction assessment authority reference. | O8 |
| nasa_conjunction_assessment | NASA conjunction assessment | nasa_cara | official_conjunction_awareness | ORBITAL | https://www.nasa.gov/conjunction-assessment/ | public official webpage | source_health_probe_only | 24 h | 30 | official | low | medium | low | low | official_page_seen | Human reference, not a tracker. | O8 |
| nasa_orbital_debris_home | NASA Orbital Debris Program | nasa_orbital_debris | official_orbital_debris | ORBITAL | https://orbitaldebris.jsc.nasa.gov/ | public official webpage | source_health_probe_only | 24 h | 40 | official | low | low | low | low | official_page_seen | Orbital debris authority reference. | O8 |
| nasa_orbital_debris_news | NASA Orbital Debris Quarterly News | nasa_orbital_debris | official_orbital_debris | ORBITAL | https://orbitaldebris.jsc.nasa.gov/quarterly-news/ | public official page/feed candidate | rss_atom | 6 h | 45 | official | low | low | medium | low | candidate_needs_verification | Debris news source, low refresh. | O8 |
| nasa_orbital_debris_reentry | NASA orbital debris reentry | nasa_orbital_debris | official_reentry | ORBITAL | https://orbitaldebris.jsc.nasa.gov/reentry/ | public official page | source_health_probe_only | 24 h | 40 | official | low | medium | medium | medium | candidate_needs_verification | Reentry context source; verify machine-readable options. | O8 |
| esa_reentry | ESA reentry predictions | esa_reentry | official_reentry | ORBITAL | https://reentry.esoc.esa.int/ | public official page | esa_reentry_page_candidate | disabled | 55 | official | low | medium | high | medium | candidate_needs_verification | Reentry source candidate; no scraping before policy review. | O8 |
| esa_space_debris | ESA Space Debris | esa_space_safety | official_orbital_debris | ORBITAL | https://www.esa.int/Space_Safety/Space_Debris | public official page/feed candidate | rss_atom | 6 h | 35 | official | low | low | medium | low | candidate_needs_verification | Space debris/sustainability context. | O8 |
| esa_space_safety | ESA Space Safety | esa_space_safety | official_space_safety | ORBITAL | https://www.esa.int/Space_Safety | public official page/feed candidate | rss_atom | 6 h | 40 | official | low | low | medium | low | candidate_needs_verification | Space safety source for debris/reentry/NEO context. | O8 |
| esa_clean_space | ESA Clean Space | esa_space_safety | official_space_safety | ORBITAL | https://www.esa.int/Space_Safety/Clean_Space | public official page | static_html_headline_candidate | 6 h | 25 | official | low | low | medium | low | candidate_needs_verification | Sustainability signal, low default. | O8 |
| nasa_humans_space | NASA humans in space | nasa | official_crewed_spaceflight | ORBITAL | https://www.nasa.gov/humans-in-space/ | public official page/feed candidate | rss_atom | 60 min | 55 | official | low | low | medium | low | candidate_needs_verification | Crewed-spaceflight source. | O7 |
| nasa_commercial_crew | NASA Commercial Crew | nasa | official_crewed_spaceflight | ORBITAL | https://www.nasa.gov/humans-in-space/commercial-crew-program/ | public official page/feed candidate | rss_atom | 60 min | 55 | official | low | low | medium | low | candidate_needs_verification | Crewed launch/docking source. | O7 |
| esa_iss | ESA ISS | esa | official_iss | ORBITAL | https://www.esa.int/Science_Exploration/Human_and_Robotic_Exploration/International_Space_Station | public official page/feed candidate | rss_atom | 2 h | 35 | official | low | low | medium | low | candidate_needs_verification | ISS source-family diversity. | O7 |
| jaxa_iss | JAXA ISS/Human spaceflight | jaxa | official_iss | ORBITAL | https://global.jaxa.jp/projects/iss_human/ | public official page/feed candidate | rss_atom | 2 h | 30 | official | low | low | medium | low | candidate_needs_verification | ISS source-family diversity. | O7 |
| csa_iss | CSA ISS | csa | official_iss | ORBITAL | https://www.asc-csa.gc.ca/eng/iss/ | public official page/feed candidate | rss_atom | 2 h | 30 | official | low | low | medium | low | candidate_needs_verification | ISS source-family diversity. | O7 |
| spot_the_station | NASA Spot the Station | nasa | official_iss | ORBITAL | https://spotthestation.nasa.gov/ | public official page/API candidate | source_health_probe_only | 24 h | 25 | official | low | medium | medium | low | candidate_needs_verification | Local sky interest candidate, not early ingest. | O9 |
| open_notify_iss | Open Notify ISS location | open_notify | unofficial_aggregator | ORBITAL | https://open-notify.org/Open-Notify-API/ISS-Location-Now/ | public unofficial API | official_api_json | disabled | 5 | unofficial | low | medium | medium | low | unofficial_secondary | Unofficial ISS API, not primary authority. | O9 |
| noaa_satellites | NOAA satellites | noaa | official_space_agency_news | ORBITAL | https://www.noaa.gov/satellites | public official page/feed candidate | rss_atom | 2 h | 35 | official | low | low | medium | low | candidate_needs_verification | Satellite agency news. | O6 |
| nesdis_news | NOAA NESDIS news | noaa_nesdis | official_space_agency_news | ORBITAL | https://www.nesdis.noaa.gov/news | public official page/feed candidate | rss_atom | 2 h | 35 | official | low | low | medium | low | candidate_needs_verification | NOAA satellite source. | O6 |
| eumetsat_news | EUMETSAT news | eumetsat | official_space_agency_news | ORBITAL | https://www.eumetsat.int/news | public official page/feed candidate | rss_atom | 2 h | 30 | official | low | low | medium | low | candidate_needs_verification | Meteorological satellite source. | O6 |
| eumetsat_rss | EUMETSAT RSS feeds | eumetsat | official_space_agency_news | ORBITAL | https://www.eumetsat.int/rss-feeds | public official feed index | rss_atom | 2 h | 30 | official | low | low | medium | low | candidate_needs_verification | Feed candidate for satellite agency news. | O6 |
| copernicus_news | Copernicus news | copernicus | official_space_agency_news | ORBITAL | https://www.copernicus.eu/en/news | public official page/feed candidate | rss_atom | 6 h | 25 | official | low | low | medium | low | candidate_needs_verification | Earth-observation program news, low default. | O6 |
| exoplanet_archive | NASA Exoplanet Archive | nasa_exoplanet_archive | official_astronomy_data | ORBITAL | https://exoplanetarchive.ipac.caltech.edu/ | public official archive | source_health_probe_only | 24 h | 20 | official | low | low | low | low | official_page_seen | Astronomy data reference; Solar System Beyond canonical for deep science. | O9 |
| exoplanet_api_docs | Exoplanet Archive program interfaces | nasa_exoplanet_archive | official_astronomy_data | ORBITAL | https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html | public official API docs | astronomy_tap_api_candidate | disabled | 15 | official | low | medium | high | medium | candidate_policy_sensitive | Strict filters only; not early ORBITAL ingest. | O9 |
| mast_api | MAST API | mast | official_astronomy_data | ORBITAL | https://mast.stsci.edu/api/v0/ | public official API docs | astronomy_tap_api_candidate | disabled | 15 | official | low | medium | high | medium | candidate_policy_sensitive | Heavy astronomy archive, avoid broad ingest. | O9 |
| heasarc_archive | HEASARC archive | heasarc | official_astronomy_data | ORBITAL | https://heasarc.gsfc.nasa.gov/docs/archive.html | public official archive page | astronomy_tap_api_candidate | disabled | 15 | official | low | medium | high | medium | candidate_policy_sensitive | High-energy archive, not early ORBITAL source. | O9 |
| astronomers_telegram | Astronomers Telegram | atel | official_transient_astronomy | ORBITAL | https://www.astronomerstelegram.org/ | public astronomy alert site | source_health_probe_only | 24 h | 30 | official_candidate | low | low | low | low | official_page_seen | Transient astronomy reference. | O9 |
| astronomers_telegram_rss | Astronomers Telegram RSS | atel | official_transient_astronomy | ORBITAL | https://www.astronomerstelegram.org/?rss | public RSS feed | rss_atom | 30 min | 45 | official_candidate | low | low | medium | medium | candidate_needs_verification | Time-sensitive astronomy signal candidate. | O9 |
| gcn_home | NASA GCN | gcn | official_transient_astronomy | ORBITAL | https://gcn.nasa.gov/ | public official alert portal | source_health_probe_only | 24 h | 40 | official | low | low | low | low | official_page_seen | Transient alert authority reference. | O9 |
| gcn_circulars | GCN circulars | gcn | official_transient_astronomy | ORBITAL | https://gcn.nasa.gov/circulars | public official circular page/API candidate | rss_atom | 30 min | 40 | official | low | medium | medium | medium | candidate_needs_verification | Time-sensitive astronomy candidate. | O9 |
| ligo_news | LIGO Caltech news | ligo | official_transient_astronomy | ORBITAL | https://www.ligo.caltech.edu/news | public official page/feed candidate | rss_atom | 2 h | 25 | official_candidate | low | low | medium | low | candidate_needs_verification | Gravitational-wave news candidate; SYSTEM_SOLAR has deeper canonical design. | O9 |
| iau_news | IAU news | iau | official_science_release | ORBITAL | https://www.iau.org/news/ | public official page/feed candidate | rss_atom | 6 h | 20 | official | low | low | medium | low | candidate_needs_verification | Official astronomy institution news, low default. | O9 |
| sky_telescope_feed | Sky and Telescope feed | sky_telescope | astronomy_news | ORBITAL | https://skyandtelescope.org/feed/ | public RSS feed | rss_atom | 2 h | 25 | publisher | low | medium | medium | low | candidate_needs_verification | Sky event and astronomy news echo. | O10 |
| spacenews_feed | SpaceNews feed | spacenews | space_news | ORBITAL | https://spacenews.com/feed/ | public RSS feed | rss_atom | 60 min | 45 | publisher | low | medium | medium | low | candidate_needs_verification | Space industry/policy news metadata. | O10 |
| spaceflightnow_feed | Spaceflight Now feed | spaceflightnow | space_news | ORBITAL | https://spaceflightnow.com/feed/ | public RSS feed | rss_atom | 60 min | 45 | publisher | low | medium | medium | low | candidate_needs_verification | Launch/news metadata source. | O10 |
| space_com_feed | Space.com feed | space_com | space_news | ORBITAL | https://www.space.com/feeds/all | public RSS feed | rss_atom | 60 min | 25 | publisher | low | medium | medium | low | unofficial_secondary | Broad space news echo, hype/low-value penalties apply. | O10 |
| nasaspaceflight_feed | NASASpaceflight feed | nasaspaceflight | space_news | ORBITAL | https://www.nasaspaceflight.com/feed/ | public RSS feed | rss_atom | 60 min | 35 | publisher | low | medium | medium | low | candidate_needs_verification | Specialist launch/news source, not official. | O10 |
| arstechnica_space_feed | Ars Technica space feed | ars_technica | space_news | ORBITAL | https://arstechnica.com/space/feed/ | public RSS feed | rss_atom | 2 h | 30 | publisher | low | medium | medium | low | candidate_needs_verification | Space journalism echo only. | O10 |
| planetary_society_feed | Planetary Society RSS | planetary_society | space_news | ORBITAL | https://www.planetary.org/rss.xml | public nonprofit RSS | rss_atom | 2 h | 30 | nonprofit | low | medium | medium | low | candidate_needs_verification | Space/planetary public-interest source. | O10 |
| bbc_science_rss | BBC science RSS | bbc | public_media_space | ORBITAL | https://feeds.bbci.co.uk/news/science_and_environment/rss.xml | public RSS feed | rss_atom | 2 h | 25 | public_media | low | medium | medium | low | candidate_needs_verification | Public-media science/space echo. | O10 |
| nature_astronomy_rss | Nature astronomy RSS | nature | astronomy_news | ORBITAL | https://www.nature.com/subjects/astronomy-and-planetary-science.rss | public RSS feed | rss_atom | 6 h | 15 | publisher | low | medium | medium | low | candidate_policy_sensitive | Paywall-sensitive metadata only. | O10 |
| reddit_space | Reddit r/space | reddit | social_candidate | ORBITAL | https://www.reddit.com/r/space/ | platform community page/API candidate | manual_review_only | disabled | 5 | platform | high | high | high | high | candidate_policy_sensitive | Community echo only through compliant API. | O11 |
| reddit_spacex | Reddit r/SpaceX | reddit | social_candidate | ORBITAL | https://www.reddit.com/r/SpaceX/ | platform community page/API candidate | manual_review_only | disabled | 3 | platform | high | high | high | high | candidate_policy_sensitive | Provider community echo only, disabled. | O11 |
| x_swpc | X SWPC account | x_api | social_candidate | ORBITAL | https://x.com/SWPC | platform account/API candidate | manual_review_only | disabled | 5 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Official account echo only if compliant API configured. | O11 |
| x_spacex | X SpaceX account | x_api | social_candidate | ORBITAL | https://x.com/SpaceX | platform account/API candidate | manual_review_only | disabled | 3 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Provider social echo only, never primary. | O11 |
| bluesky_solar_storm | Bluesky solar storm search | bluesky | social_candidate | ORBITAL | https://bsky.app/search?q=solar%20storm | platform search/API candidate | manual_review_only | disabled | 2 | platform | high | high | high | high | reject_for_now | Broad social search is too noisy for current design. | O11 |
| orbital_fixture_pack | ORBITAL local fixture pack | local_fixture | manual_review_only | ORBITAL | tests/fixtures/orbital/ | local repository fixtures | local_file_fixture | none | 0 | fixture | low | low | low | low | assistant_seeded | Fixture-only parser target; must never fetch network. | O2 |
| orbital_arcgis_reentry_candidate | ORBITAL ArcGIS reentry/debris candidate | orbital_open_data | official_reentry | ORBITAL | docs/project/ORBITAL_ARCGIS_REENTRY_CANDIDATE_TBD | future verified official feature service only | arcgis_feature_service_candidate | disabled | 5 | unknown | low | high | high | high | candidate_needs_verification | Placeholder for later verified official feature-service source; do not scrape dashboards. | O8 |
| rfc9309_robots | RFC 9309 Robots Exclusion Protocol | policy_reference | source_health_only | ORBITAL | https://www.rfc-editor.org/rfc/rfc9309.html | public standards reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | Policy reference for robots handling. | O1 |
| rss_specification | RSS specification | policy_reference | source_health_only | ORBITAL | https://www.rssboard.org/rss-specification | public standards reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | RSS parser reference. | O1 |
| schema_newsarticle | Schema.org NewsArticle | policy_reference | source_health_only | ORBITAL | https://schema.org/NewsArticle | public schema reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | Metadata vocabulary reference. | O1 |
| reddit_data_api_terms | Reddit Data API Terms | policy_reference | source_health_only | ORBITAL | https://redditinc.com/policies/data-api-terms | public platform policy | manual_review_only | none | 0 | reference | low | high | low | low | candidate_policy_sensitive | Must be reviewed before Reddit enablement. | O11 |
| x_api_docs | X API introduction | policy_reference | source_health_only | ORBITAL | https://docs.x.com/x-api/introduction | public platform API docs | manual_review_only | none | 0 | reference | low | high | low | low | candidate_policy_sensitive | Must be reviewed before X source enablement. | O11 |
| bluesky_atproto_docs | Bluesky AT Protocol docs | policy_reference | source_health_only | ORBITAL | https://docs.bsky.app/docs/api/at-protocol-xrpc-api | public platform API docs | manual_review_only | none | 0 | reference | low | medium | low | low | candidate_policy_sensitive | Reference for possible compliant Bluesky adapter. | O11 |

## SECTION 5: Source admission tiers

Tier 0 - local fixtures only:

- No network.
- Used for tests.
- Best for parser contracts, ranking, source health, safety filtering, and scope-routing behavior.

Tier 1 - official APIs, official JSON products, official RSS/Atom, official open data, official
CNEOS/JPL/NASA/NOAA/SWPC/MPC data, and official agency feeds:

- Best first live candidates.
- First candidates: SWPC alerts JSON, SWPC NOAA scales JSON, SWPC Kp JSON, SWPC aurora JSON, JPL
  CNEOS close approach API, JPL fireball API, NASA RSS, ESA RSS.
- Disabled by default and opt-in.

Tier 2 - official pages with stable public operational data but no obvious feed/API:

- Candidate only after source-policy review.
- Prefer source-health checks and manual review before parser implementation.
- No recursive crawling or page-load extraction.

Tier 3 - public launch and event APIs:

- Candidate source: Launch Library 2.
- Must be disabled by default.
- Must use rate limits, caching, source health, and strict event windows.

Tier 4 - spaceflight news RSS or publisher-provided feeds:

- Store headline metadata only.
- No article-body archive.
- No paywall bypass.
- These sources support convergence but do not outrank official alerts without corroboration.

Tier 5 - public satellite catalog and orbital element sources:

- Use cautiously.
- Public catalog metadata can support high-level reentry, debris, ISS, and source-health summaries.
- Do not build a tactical tracker.
- Do not track restricted or sensitive targets beyond source-provided public aggregate metadata.
- Do not infer classified activity.

Tier 6 - restricted or auth-required sources:

- Example: Space-Track.
- Disabled by default.
- Must require explicit user config, credentials outside repo, terms review, and narrow source
  purpose.
- Never bypass account controls.
- Never store credentials in repo.
- Prefer public CelesTrak or official agency pages if the restricted source is not necessary.

Tier 7 - social/community signals:

- Policy-sensitive and disabled by default.
- Reddit only through compliant official API or permitted feed access.
- X/Twitter only through official API access if explicitly configured.
- Bluesky only through official AT Protocol later.
- No HTML scraping to bypass platform restrictions.

Tier 8 - unofficial aggregators:

- Useful as human comparison or source-health reference.
- Do not treat as primary authority over official sources.
- Do not clone their work or scrape aggressively.
- Source-health-only or manual-review-only unless policy review supports more.

## SECTION 6: ORBITAL event model

The system should not only store news items. It should infer that multiple recent items refer to the
same orbital or space event. This can be implemented as a future `orbital_events` table or as a
scope-specific extension of the common `news_clusters` model once the recent-signal schema exists.

Candidate event fields:

| Field | Purpose |
| --- | --- |
| `orbital_event_id` | Internal integer primary key. |
| `scope` | Always `ORBITAL` initially. |
| `event_key` | Deterministic key from event type, source event ids, mission/object ids, source families, and normalized title tokens. |
| `event_type` | Controlled ORBITAL event type. |
| `title` | Human-readable representative title. |
| `representative_item_id` | Item selected for display. |
| `severity` | `info`, `notice`, `watch`, `warning`, or `alert` style local enum. |
| `public_impact_score` | Earth, communications, aurora, flight, grid, public visibility, or risk relevance. |
| `operational_impact_score` | Launch, spacecraft, ISS, reentry, satellite, or mission operations relevance. |
| `source_diversity_score` | Independent source-family count and weight. |
| `official_confirmation_score` | Official agency/API/feed confirmation. |
| `space_weather_score` | SWPC alert, scale, Kp, flare, radiation, solar wind, or aurora score. |
| `neo_score` | Close approach, fireball, Sentry, Scout, MPEC, or MPC score. |
| `launch_score` | Launch schedule, scrub, success, failure, or payload status score. |
| `crewed_spaceflight_score` | Crewed mission, ISS, docking, EVA, or anomaly score. |
| `satellite_reentry_score` | Reentry prediction, confirmation, object metadata, and public impact score. |
| `debris_conjunction_score` | Debris, conjunction, space safety, and sustainability score. |
| `mission_science_score` | Time-sensitive mission/science release score. |
| `sky_visibility_score` | Aurora, ISS pass, meteor, or visible reentry local/regional interest. |
| `social_echo_score` | Low-weight social echo only if compliant and configured. |
| `news_echo_score` | Space news and public media convergence. |
| `global_impact_score` | GLOBAL impact tag contribution. |
| `national_impact_score` | NATIONAL impact tag contribution. |
| `regional_impact_score` | REGIONAL impact tag contribution. |
| `local_impact_score` | LOCAL impact tag contribution. |
| `first_seen_at` | First local observation time. |
| `last_seen_at` | Last local observation time. |
| `last_elevated_at` | Last time event crossed attention threshold. |
| `expires_at` | Retention purge time. |
| `space_domain_json` | Space weather, launch, NEO, reentry, satellite, mission, science, or sky domain labels. |
| `objects_json` | NEOs, spacecraft, satellites, payloads, mission objects, or fireball metadata. |
| `missions_json` | Mission names and campaign metadata. |
| `agencies_json` | Source agencies and organizations. |
| `launch_sites_json` | Launch site and pad metadata where source-provided. |
| `impacted_systems_json` | GPS, HF radio, aviation, satellites, power, aurora, crewed, NEO, or other impact tags. |
| `source_ids_json` | Source ids contributing to the event. |
| `item_ids_json` | Normalized item ids contributing to the event. |
| `evidence_json` | Source, parser, policy, and matching evidence. |
| `ranking_explanation_json` | Score features and penalties. |
| `status` | `candidate`, `active`, `watch`, `warning`, `confirmed`, `scrubbed`, `retracted`, `stale`, or `suppressed`. |

Controlled event types should include at least:

- `space_weather_watch`
- `space_weather_warning`
- `geomagnetic_storm`
- `solar_flare`
- `radio_blackout`
- `solar_radiation_storm`
- `cme_arrival`
- `solar_wind_shock`
- `aurora_opportunity`
- `icao_space_weather_advisory`
- `neo_close_approach`
- `asteroid_impact_risk_update`
- `fireball_bolide`
- `mpec_neo_candidate`
- `comet_or_minor_body_notice`
- `launch_scheduled`
- `launch_window_change`
- `launch_scrub`
- `launch_success`
- `launch_failure`
- `payload_deployed`
- `spacecraft_anomaly`
- `docking_undocking`
- `crewed_mission_event`
- `eva_spacewalk`
- `iss_operation`
- `reentry_prediction`
- `uncontrolled_reentry`
- `orbital_debris_notice`
- `conjunction_awareness`
- `satellite_catalog_update`
- `mission_milestone`
- `science_release`
- `astronomy_transient`
- `meteor_shower_sky_event`
- `source_health_problem`
- `community_signal`

Routine low-impact space news should not automatically become elevated ORBITAL events. The event
layer should distinguish "stored recent metadata" from "attention-worthy."

## SECTION 7: Cross-source convergence ranking

Ranking must be deterministic and explainable. The core idea is that an item appearing in official
space weather products, agency feeds, launch/event APIs, mission blogs, CNEOS/MPC data,
satellite/reentry sources, spaceflight news, and compliant community/social signals within a short
window is more likely to be important or interesting than a lone article or rumor.

Required scoring factors:

1. Official severity.

Examples include SWPC geomagnetic storm watch/warning/alert, SWPC NOAA G/R/S scale values, Kp at or
above configured threshold, M-class or X-class flare, proton/radiation storm alert, ICAO space
weather advisory, JPL/CNEOS close approach within configured threshold, CNEOS fireball above energy
threshold, Sentry or Scout risk-list update, MPC NEO confirmation item, crewed launch, docking,
undocking, EVA, ISS emergency-type official update, launch failure or scrub, official reentry
prediction, official debris/conjunction notice, agency anomaly notice, or space weather with
documented aviation/GPS/HF/satellite/grid relevance.

2. Source diversity.

Independent source families count more than repeated mentions from the same family. Candidate
families include `swpc`, `noaa_ncei`, `nasa`, `nasa_blogs`, `nasa_jpl`, `jpl_cneos`, `mpc`, `esa`,
`esa_reentry`, `jaxa`, `csa`, `isro`, `celestrak`, `space_track`, `launch_library`,
`spaceflight_news_api`, `launch_provider`, `spacex`, `blue_origin`, `rocket_lab`, `ula`,
`arianespace`, `nasa_space_station`, `orbital_debris_program`, `space_agency_news`, `space_news`,
`public_media_space`, `reddit`, `bluesky`, `x_api`, and `source_health`.

3. Temporal proximity.

| Event kind | Matching window |
| --- | --- |
| Space weather alert | Active alert duration or 0 to 72 hours |
| Aurora opportunity | 0 to 48 hours |
| Solar flare | 0 to 24 hours |
| CME/solar wind event | 0 to 72 hours |
| NEO close approach | Event date minus 7 days through event date plus 24 hours |
| Fireball | 0 to 72 hours |
| Launch event | Launch window minus 7 days through launch plus 48 hours |
| Launch scrub | 0 to 48 hours |
| Launch failure/anomaly | 0 to 14 days |
| Crewed-spaceflight event | 0 to 14 days |
| Docking/undocking/EVA | 0 to 72 hours |
| Reentry | Prediction window minus 7 days through confirmed reentry plus 48 hours |
| Conjunction/debris | 0 to 7 days, official or specialist sources preferred |
| Mission milestone/science release | 0 to 7 days |
| Astronomy transient | 0 to 7 days, source-specific |
| Routine space news | 0 to 72 hours unless still active |

4. Object and mission proximity.

Match by mission name, launch vehicle, payload name, NORAD catalog number where safe and
appropriate, COSPAR ID where safe and appropriate, asteroid/comet designation, CNEOS event id, MPC
designation, fireball time/location, space weather product id, storm scale, launch provider, launch
site, spacecraft name, ISS expedition/mission, reentry object, and source event id.

5. Public impact.

Boost geomagnetic storms affecting communications, satellites, aviation, GPS, aurora, or power
grids; aurora potential for configured local/regional location; major solar flare or radiation
storm; crewed launch or mission issue; ISS operational issue; launch failure or payload anomaly; NEO
close approach with size/distance above threshold; fireball with reported energy or wide public
observation; uncontrolled reentry of large object; debris/conjunction notice involving crewed assets
or major active spacecraft; official agency alert or mission update; and events with GLOBAL,
NATIONAL, REGIONAL, or LOCAL impact tags.

6. Recency.

Recent items matter more, but active alert windows and launch windows can remain elevated while
active.

7. User-configured priority.

Future config can boost space weather, aurora, Seattle aurora visibility, NOAA/SWPC, NASA,
JPL/CNEOS, NEOs, fireballs, crewed spaceflight, ISS, Artemis, launches, SpaceX, ULA, Blue Origin,
Rocket Lab, ESA, JAXA, reentries, debris, astronomy transients, mission science releases, specific
launch sites, and specific missions.

8. Low-public-value penalty.

De-emphasize routine promotional space company posts, generic science explainers, low-risk NEOs far
from Earth, routine Starlink or satellite launches unless configured, duplicate launch schedule
pages, social-only claims, single-source launch rumors, non-operational fan chatter, orbital data
firehose updates with no event significance, stale TLE/catalog churn, and routine agency
newsletters.

9. Safety and sensitivity penalty.

De-emphasize or block restricted/auth-only data without explicit configuration, tactical or
sensitive satellite targeting, attempts to infer classified activity, data that would turn the app
into a real-time operational tracker, conjunction or satellite information without source-policy
confidence, social posts revealing private person-level details, and unverified reentry panic
claims.

Sample scoring formula:

```text
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
```

"Frequency of appearance" means independent cross-source convergence, not raw duplicate counts.

Bad ranking:

- Fifty reposts of the same routine launch article dominate.

Good ranking:

- SWPC issues a G4 geomagnetic storm watch.
- NOAA scale JSON and planetary Kp products support the event.
- NASA/NOAA or agency news explains impacts.
- Regional aurora sources or weather pages suggest visibility.
- News coverage confirms public interest.
- Social chatter appears only as a low-weight echo if compliant.
- All signals fall within an active alert window.

## SECTION 8: ORBITAL source category design

Each category must define purpose, safe first sources, adapter class, refresh interval, risk, source
health, sample fields, ranking contribution, and later phase.

| Category | Why it exists | First safe sources | Parser/adaptor class | Refresh interval | Risks | Source-health signals | Sample item fields | Ranking contribution | Phase |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Space weather alerts and measurements | Captures official operational space-weather severity and evidence. | SWPC alerts JSON, NOAA scales, Kp, X-ray, proton, solar wind. | `swpc_alerts_json`, `swpc_json`, `swpc_product_text` | 5 to 15 min if enabled | Privacy low, policy low, parser medium | disabled, stale, parser_failed, healthy | product id, issue time, valid time, G/R/S scale, Kp, flare class, source URL | Highest official severity boost. | O6 |
| Aurora and local sky-impact signals | Connects space weather to configured local/regional interest. | SWPC aurora JSON, Kp products, NWS safety page as reference. | `swpc_json`, `source_health_probe_only` | 10 min if enabled | Privacy low, policy low, parser medium | stale, parser_failed, needs_scope_filter | aurora timestamp, Kp, location label, local impact tag | Boosts LOCAL/REGIONAL impact when configured. | O6 |
| Near-Earth objects, fireballs, and minor planet notices | Tracks official NEO and fireball signals without panic language. | JPL CAD, JPL Fireball, Sentry/Scout fixtures, MPC MPECs. | `jpl_ssd_api`, `cneos_api`, `mpc_api` | 60 min to 6 h if enabled | Privacy low, policy low/medium, parser medium | stale, parser_failed, needs_scope_filter | designation, close approach time, lunar distance, energy, source URL | NEO/fireball score with official risk framing. | O6 |
| Launch schedules and launch status | Tracks launch windows, scrubs, failures, successes, and payload deployment. | Launch Library fixtures, NASA launches/blogs, provider pages after review. | `launch_library_api`, `rss_atom`, `static_html_headline_candidate` | 30 to 60 min if enabled | Privacy low, policy medium, parser medium | stale, rate_limited, parser_failed, policy_blocked | launch id, provider, vehicle, pad, window, status | Launch/operational score and active-window boost. | O7 |
| Crewed spaceflight and ISS operations | Elevates crewed missions, dockings, EVAs, ISS events, and anomalies. | NASA Space Station blog, NASA humans in space, ESA/JAXA/CSA ISS pages. | `rss_atom`, `static_html_headline_candidate` | 60 min if enabled | Privacy low, policy low, parser medium | stale, parser_failed, policy_blocked | mission, crewed flag, ISS flag, event time, source URL | Crewed/ISS boost and public impact. | O7 |
| Mission news and space agency feeds | Provides official context and source diversity. | NASA RSS, ESA RSS, JPL RSS, JAXA, CSA, ISRO, NOAA/NESDIS. | `rss_atom`, `static_html_headline_candidate` | 60 min to 6 h if enabled | Privacy low, policy low/medium, parser medium | stale, parser_failed, policy_blocked | title, URL, agency, mission, published time | Official source diversity and mission relevance. | O6 |
| Satellite catalog, reentry, debris, and conjunction-awareness sources | Supports safe high-level context without tactical tracking. | CelesTrak tiny fixtures, NASA Orbital Debris, ESA reentry after review. | `celestrak_gp_json`, `celestrak_satcat_csv_json`, `celestrak_socrates_candidate`, `esa_reentry_page_candidate`, `space_track_api_candidate` | Disabled until safety gates exist | Privacy low, policy high, parser high | restricted_source_disabled, sensitivity_blocked, auth_required | object name, NORAD/COSPAR if safe, reentry window, uncertainty | Reentry/debris score only after safety review. | O8 |
| Space safety, orbital debris, and sustainability sources | Adds official safety/sustainability context. | NASA Orbital Debris Quarterly News, ESA Space Safety, ESA Clean Space. | `rss_atom`, `static_html_headline_candidate`, `source_health_probe_only` | 6 h to 24 h | Privacy low, policy low, parser medium | stale, parser_failed, manual_review_only | title, URL, source org, debris/safety label | Contextual boost, usually low unless public impact. | O8 |
| Astronomy transients and sky events | Covers time-sensitive sky signals, not deep astronomy archives. | ATel RSS, GCN circulars, IAU news, Sky and Telescope feed. | `rss_atom`, `astronomy_tap_api_candidate`, `manual_review_only` | 30 min to 6 h if enabled | Privacy low, policy medium, parser medium/high | stale, parser_failed, manual_review_only | event id, object, published time, source URL | Sky/transient boost if time-sensitive. | O9 |
| Space news, public media, and specialist journalism | Adds independent coverage and public-interest context. | SpaceNews RSS, Spaceflight Now RSS, Ars space, BBC science. | `rss_atom`, `spaceflight_news_api` | 60 min to 2 h if enabled | Privacy low, policy medium, parser medium | stale, parser_failed, policy_blocked | title, URL, publisher, published time | News echo, not primary authority. | O10 |
| Social/community echoes | Optional low-weight signals after policy review. | Reddit, X, Bluesky via compliant APIs only. | `manual_review_only` initially | Disabled | Privacy high, policy high, parser high | social_disabled, auth_required, policy_blocked | public post metadata if allowed, no long retention | Very low weight; never primary evidence. | O11 |
| Source health and disabled states | Keeps the scope honest and prevents fake data. | All registry sources. | `source_health_probe_only`, `local_file_fixture` | Local only until enabled | Privacy low, policy low unless probes run | disabled, not_configured, stale, failing, parser_failed | source id, state, last success, message | Stale/blocked source penalties. | O1/O2 |

## SECTION 9: ORBITAL safety, sensitivity, and public-impact posture

Rules:

- Store source-provided public metadata only.
- Do not store full article bodies.
- Do not archive social posts long term.
- Do not scrape or bypass restricted satellite databases.
- Do not store API credentials in repo.
- Do not build tactical target tracking.
- Do not infer classified or sensitive orbital activity.
- Do not present orbital-element churn as operational intelligence.
- Do not elevate military or intelligence satellite tracking unless the source is official public
  news and the event has legitimate public-impact value.
- Prefer aggregate, public, source-backed event summaries over object-by-object tracking.
- For Space-Track or other restricted/account sources, mark `auth_required` and policy-sensitive
  until explicit user configuration exists.
- For CelesTrak, use public data only and avoid turning the dashboard into a tactical tracker.
- For reentries, avoid panic language. Show source, object, uncertainty, window, confidence, and
  official link.
- For NEOs, avoid impact scare language. Show distance, size estimate if available, confidence,
  event date, official source, and risk framing from CNEOS/MPC only.
- For space weather, show official severity scale, affected systems, and source URL. Do not invent
  impacts.
- For public-health or aviation impact from space weather, link to official source language.
- For launch failures or crewed-spaceflight anomalies, show official facts and label preliminary
  information.
- Social-only orbital claims should never outrank official alerts or trusted spaceflight reporting.

## SECTION 10: ORBITAL source freshness and retention

ORBITAL is a short-retention recent-signal layer, not a permanent archive.

| Data | Default retention |
| --- | --- |
| Raw fetch diagnostics | 7 days or less |
| Raw payload debug | Disabled by default; 6 hours max if enabled |
| Space weather alert metadata | Expiration plus 24 to 72 hours |
| Space weather measurements | 24 to 72 hours unless aggregated |
| Aurora opportunity metadata | 48 hours |
| NEO close approach metadata | 7 days before event through 48 hours after event |
| Fireball metadata | 7 to 14 days |
| MPEC/NEO confirmation metadata | 7 to 14 days |
| Launch schedule metadata | Until launch plus 7 days |
| Launch scrub/failure/anomaly metadata | 7 to 14 days |
| Crewed mission and ISS event metadata | 7 to 14 days |
| Reentry prediction metadata | Until confirmed reentry plus 72 hours |
| Debris/conjunction metadata | 7 days, with sensitivity limits |
| Mission news headline metadata | 7 days |
| Science release metadata | 7 days unless configured |
| Astronomy transient metadata | 7 to 14 days |
| ORBITAL event clusters | 7 to 14 days |
| Source health | 30 days |
| Ranking explanations | Same as event/item retention |
| Social metadata | 24 to 72 hours if ever enabled, unless terms require shorter or prohibit storage |

Every ingest run in later phases must purge expired data. There must be no article body archive, no
permanent satellite tracking archive, and no permanent social archive.

## SECTION 11: Adapter design for ORBITAL

Do not implement adapters in this task. Future adapters should be pure parser/normalizer units
against local fixtures before any live fetch exists.

`swpc_json`

- Targets: NOAA SWPC JSON directory and product JSON files.
- Preserve product name, issue time, valid time, observed time, severity, NOAA scale, Kp, flare
  class, proton flux, solar wind, aurora product metadata, and source URL.
- Handle format changes and source-health failures.
- Do not assume every JSON file has identical schema.

`swpc_alerts_json`

- Targets: SWPC alerts/watches/warnings JSON.
- Preserve alert product id, issue time, valid period, severity, message type, NOAA scale, affected
  systems if source provides it, and source URL.

`swpc_product_text`

- Targets: SWPC text products only if needed and explicitly configured.
- Parser should be conservative.
- Prefer JSON where available.

`nasa_api_json`

- Targets: NASA Open APIs.
- Use only configured APIs.
- Avoid imagery-heavy APIs unless needed.
- Respect API key handling.
- `DEMO_KEY` may be usable only for development if allowed, but production config should use
  explicit local config and rate limits.
- Do not store API keys in repo.

`jpl_ssd_api`

- Targets: JPL SSD/CNEOS APIs.
- Preserve object designation, close approach time, distance, relative velocity, estimated diameter
  where available, condition code if available, and source URL.
- Do not invent impact risk.
- Treat Sentry/Scout risk fields as official source framing only.

`cneos_api`

- Targets: CNEOS fireball and close-approach APIs.
- Preserve event time, location if available, energy, velocity, altitude, and source URL.
- Use thresholds to avoid firehose behavior.

`mpc_api`

- Targets: MPC MPECs, NEOCP observations, observations, orbits, and designation APIs.
- Verify exact endpoints and usage guidance.
- Store metadata only.
- Avoid high-volume observation ingestion unless strictly filtered.

`launch_library_api`

- Targets: Launch Library 2 launch and event endpoints.
- Preserve launch id, provider, mission, vehicle, pad, launch window, status, webcast URL if source
  provides it, and source URL.
- Handle scrubs and status changes as event updates, not duplicates.
- Obey API throttling and disabled-by-default config.

`spaceflight_news_api`

- Targets: Spaceflight News API candidate.
- Use as news metadata and correlation with Launch Library events.
- Store headline metadata only.
- Do not let it outrank official launch provider or agency sources without convergence.

`rss_atom`

- Targets: NASA RSS, ESA RSS, JPL RSS, agency feeds, space news feeds, public media feeds.
- Parse title, URL, published timestamp, source-provided description, and categories.
- Bound description length.
- Do not fetch article bodies.

`celestrak_gp_json`

- Targets: CelesTrak GP data candidates.
- Use only where useful for high-level public orbital context.
- Avoid tactical tracking UI.
- Cap object counts and use allowlisted object groups if ever implemented.

`celestrak_satcat_csv_json`

- Targets: public SATCAT metadata candidates.
- Useful for identifying objects in reentry/debris events.
- Cap rows and retain only short-term derived metadata unless explicitly configured.

`celestrak_socrates_candidate`

- Targets: CelesTrak SOCRATES format candidate.
- Source-policy and sensitivity review required.
- May be source-health-only or manual-review-only initially.
- Do not present predictions as official warnings.

`space_track_api_candidate`

- Targets: Space-Track.
- Auth-required and disabled by default.
- Require credentials outside repo.
- Record `auth_required` state if no credentials exist.
- Do not bypass account controls or terms.
- Avoid restricted or sensitive use.

`esa_reentry_page_candidate`

- Targets: ESA reentry prediction page candidate.
- Prefer source-health/manual review unless a machine-readable endpoint is verified.
- Do not screen scrape complex pages without policy review.

`arcgis_feature_service_candidate`

- Targets: only a later verified official reentry/debris/safety feature service.
- Do not screen scrape dashboards.
- Keep disabled by default and require source ownership verification.

`astronomy_tap_api_candidate`

- Targets: NASA Exoplanet Archive, MAST, HEASARC, or TAP-style APIs.
- Useful for configured science release or transient tracking only.
- Do not ingest large catalogs.
- Prefer news/RSS unless a specific scientific signal is configured.

`official_api_json`

- Targets: other official JSON endpoints from agencies or public services.
- Must use timeouts, response size caps, source-specific rate limits, and fail-soft source health.

`static_html_headline_candidate`

- Targets: official pages or space news pages with no RSS/API.
- Disabled unless homepage extractor support is explicitly allowed.
- Use per-source selectors.
- No recursive crawling.
- No article-body fetch.
- Robots and policy review required.

`source_health_probe_only`

- Targets: dashboards and portals useful as human status references but not suitable for ingestion.
- Page loads must not run probes.

`local_file_fixture`

- Targets: future fixtures under `tests/fixtures/orbital/`.
- Must never fetch network.
- Covers parser, ranking, source health, auth-required, restricted-disabled, and safety-blocked
  states.

`manual_review_only`

- Targets: policy-sensitive, parser-risky, login-required, auth-required, account-required,
  paywalled, restricted, or unclear targets.

## SECTION 12: Candidate orbital source registry example

Do not edit `config.example.yml` for this design pass. A later implementation can add disabled
examples after the common recent-signal registry exists. The candidate shape below is intentionally
disabled by default.

```yaml
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
      safety_notes: "Do not build tactical tracking. Use only allowlisted object groups."
    - id: space_track_auth_candidate
      enabled: false
      source_family: space_track
      source_class: restricted_auth_candidate
      adapter: space_track_api_candidate
      homepage_url: "https://www.space-track.org/documentation"
      priority: 20
      interval_minutes: 120
      verification_status: restricted_auth_required
      safety_notes: "Disabled by default. Requires credentials outside repo and terms review."
```

## SECTION 13: ORBITAL UI architecture

Do not implement the ORBITAL UI in this task. The eventual page should use the same console style
and show honest disabled/not-configured states.

Proposed four bays:

| Bay | Name | Purpose |
| --- | --- | --- |
| 1 | Orbital attention now | Highest-ranking ORBITAL events. Show ranking reasons, source-family badges, official/news/community convergence, observed time, last seen, and impact tags such as GLOBAL, NATIONAL, REGIONAL, LOCAL, SKY, RADIO, GPS, AVIATION, SATELLITE, POWER, AURORA, CREWED, and NEO. |
| 2 | Space weather and sky | SWPC alerts, watches, warnings, Kp, solar wind, X-ray flux, proton flux, aurora, ICAO advisories, NEOs, fireballs, and time-sensitive sky events. Show active official alerts first and source freshness. |
| 3 | Launch, mission, and orbit ops | Launch schedules, scrubs, launch results, crewed missions, ISS events, dockings, undockings, EVAs, reentries, debris, conjunction-awareness, and mission anomalies. |
| 4 | Space press and source health | NASA, ESA, JPL, agency feeds, SpaceNews, Spaceflight Now, NASASpaceflight, Space.com, Ars space, Planetary Society, public media, future configured sources, and source-health problems. |

Each row should show:

- Title.
- Event type.
- Source or representative source.
- Source-family badges.
- Confidence/convergence count.
- Observed time.
- Last seen.
- Ranking reason.
- Evidence affordance.
- Object or mission label where applicable.
- Impact tag where applicable.
- Severity scale where applicable.

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
- ORBITAL source marked `manual_review_only`.

## SECTION 14: Evidence model for ORBITAL

Every item and event must trace back to source evidence.

For an ORBITAL event, evidence should include:

- Source ids.
- Source names.
- Source families.
- Source classes.
- Item URLs.
- Canonical URLs.
- Official source flags.
- First seen.
- Last seen.
- Source published times.
- Fetch run ids.
- Parser names.
- Source health state.
- Ranking features.
- Operational impact basis.
- Public impact basis.
- Source diversity basis.
- Local/global impact basis.
- Sensitivity decision.
- Retention expiration.
- Matching tokens.
- Event type.
- Event confidence.
- Policy notes.
- Low-public-value penalty if applied.
- Sensitivity penalty if applied.
- Rumor penalty if applied.
- Out-of-scope penalty if applied.

For space weather events, evidence must include, where available:

- Product id.
- Issue time.
- Valid start and end time.
- NOAA scale category.
- G/R/S level.
- Kp value.
- Flare class.
- Proton/radiation storm level.
- Solar wind values.
- Aurora product timestamp.
- Affected systems from source text if provided.
- Source instructions URL.

For NEO and fireball events, evidence must include, where available:

- Object designation.
- CNEOS or MPC event id.
- Close approach date/time.
- Miss distance.
- Lunar distance.
- Relative velocity.
- Estimated diameter range.
- Condition code if provided.
- Fireball energy.
- Fireball altitude.
- Fireball latitude/longitude if source provides it.
- Official risk framing.
- Source URL.

For launch and mission events, evidence must include, where available:

- Mission name.
- Launch id.
- Provider.
- Vehicle.
- Payload.
- Launch site.
- Launch window.
- Launch status.
- Status update time.
- Webcast URL if provided by source.
- Crewed flag.
- ISS or docking flag.
- Scrub/anomaly reason if source provides it.
- Official provider or agency URL.

For satellite, reentry, debris, and conjunction-awareness events, evidence must include, where
available and safe:

- Object name.
- NORAD catalog number, only if source-provided and safe.
- COSPAR ID, only if source-provided and safe.
- Source family.
- Reentry prediction window.
- Uncertainty window.
- Object mass class if source provides it.
- Official or unofficial status.
- Sensitivity classification.
- Reason for suppression or de-emphasis if applied.
- Source URL.

For science and astronomy events, evidence must include, where available:

- Mission or instrument.
- Source organization.
- Object name.
- Discovery or release date.
- Source publication URL.
- Whether this is operationally time-sensitive or only general science news.

## SECTION 15: Source health for ORBITAL

Source health must be visible in SYSTEM later and summarized in ORBITAL Bay 4 or a footer strip.

Required states:

- `disabled`
- `not_configured`
- `configured_never_run`
- `healthy`
- `stale`
- `failing`
- `parser_failed`
- `policy_blocked`
- `robots_blocked`
- `auth_required`
- `rate_limited`
- `unsupported`
- `manual_review_only`
- `restricted_source_disabled`
- `needs_terms_review`
- `needs_scope_filter`
- `sensitivity_blocked`

Each source health row should have:

| Field | Purpose |
| --- | --- |
| `source_id` | Stable source id. |
| `state` | One of the required source-health states. |
| `last_attempt_at` | Last attempted fetch or fixture parse. |
| `last_success_at` | Last successful fetch or fixture parse. |
| `last_failure_at` | Last failure time. |
| `next_eligible_fetch_at` | Backoff/rate-limit marker. |
| `consecutive_failures` | Consecutive failure count. |
| `last_http_status` | Last HTTP status if applicable. |
| `item_count_last_success` | Count from last successful run. |
| `stale_after_minutes` | Per-source stale threshold. |
| `message` | Human-readable source-health state. |
| `evidence_json` | Policy, parser, timing, and config evidence. |

## SECTION 16: First implementation sequence for ORBITAL

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

- Create fixture files for SWPC alerts JSON, SWPC NOAA scales JSON, SWPC Kp JSON, SWPC aurora JSON,
  JPL CNEOS close approach JSON, JPL CNEOS fireball JSON, JPL Sentry or Scout fixture, MPC MPEC
  fixture, Launch Library upcoming launch fixture, Spaceflight News API fixture, NASA RSS fixture,
  ESA RSS fixture, CelesTrak GP JSON tiny allowlisted fixture, Space-Track auth-required fake
  source-health fixture with no real credentials, reentry page fixture if later verified, and space
  news RSS fixture.
- Parse fixtures only.
- Store normalized metadata.
- No live fetch.

Phase O3: ORBITAL event correlation

- Deterministic token/object/time/source-family matching.
- No LLM.
- Tests for convergence, duplicate suppression, source-family diversity, mission/object/event-id
  matching, and orbital vs global/national/regional/local scope routing.

Phase O4: ORBITAL ranking

- Implement scoring model.
- Explain ranking in JSON.
- Tests for official severity, source diversity, recency, operational impact, public impact, local
  impact tags, low-public-value penalty, sensitivity penalty, stale-source penalty, and out-of-scope
  penalty.

Phase O5: ORBITAL UI disabled and fixture-backed states

- Replace ORBITAL placeholders with honest states.
- Fixture-backed in tests only.
- No live fetch.
- No fake headlines.

Phase O6: official API/RSS live fetch, opt-in only

- Start with one safe official source.
- Suggested first candidates are SWPC alerts JSON, SWPC NOAA scales JSON, SWPC Kp JSON, JPL CNEOS
  close approach API, JPL CNEOS fireball API, and NASA RSS.
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
- Space-Track stays auth-required and disabled unless explicitly configured.
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

## SECTION 17: Testing strategy

Config tests:

- ORBITAL disabled by default.
- Source disabled by default.
- Invalid source class rejected.
- Invalid adapter rejected.
- Social source rejected unless `allow_social_sources` is true.
- Restricted/auth source rejected unless `include_restricted_or_auth_sources` is true.
- Space-Track source marked `auth_required` unless credentials are explicitly configured outside
  repo.
- CelesTrak source rejected unless source scope and object-group filters are configured.
- Homepage extraction rejected unless `allow_homepage_extractors` is true.
- Source without URL rejected unless adapter supports no URL.
- Secrets not allowed in `config.example.yml`.

Registry tests:

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
- Restricted Space-Track source returns `auth_required` without network.
- Space news RSS fixture parses.
- Malformed feed fails soft.
- Oversized payload blocked or truncated.

Safety and sensitivity tests:

- Space-Track source does not run without explicit credentials.
- No credentials are stored in repo.
- Tactical tracking UI is not created.
- Restricted source item is not displayed as live.
- Routine catalog churn does not elevate to ORBITAL attention.
- Military or sensitive satellite tracking is blocked or de-emphasized unless official public news
  and public-impact rules apply.
- Social-only reentry rumor does not outrank official sources.
- NEO close approach does not use panic language.
- Space weather alert shows official source and scale, not invented impacts.

Correlation tests:

- SWPC G-level alert plus Kp product plus NOAA scale plus news coverage becomes one space weather
  event.
- SWPC aurora product plus Kp threshold plus regional interest becomes one aurora event.
- CNEOS close approach plus MPC notice plus news coverage becomes one NEO event.
- CNEOS fireball plus news coverage becomes one fireball event.
- Launch Library event plus NASA/provider update plus space news becomes one launch event.
- Same event from multiple news outlets counts as news-family convergence but not endless duplicate
  inflation.
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
- Disabled, not configured, stale, failing, auth-required, and restricted-source-disabled states are
  distinct.

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

## SECTION 18: Backlog update requirements

`BACKLOG.md` must include a section named `ORBITAL Space Recent Signal Layer`. Every ORBITAL
backlog item added for this design must say `Status: not implemented.` Future tasks should be
concrete enough for a later agent to implement without reading chat history.

Required backlog work areas:

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

## SECTION 19: Non-goals

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

## SECTION 20: Final response requirements

The final response for this task should include:

- Files changed.
- Confirmation that no application code was changed, unless it was.
- Confirmation that no external network fetches were added.
- Confirmation that no dependencies were added.
- Confirmation that no collectors were implemented.
- Confirmation that ORBITAL remains disabled by default.
- Test commands run and exact results.
- `git diff --check` result.
- `git status --short`.
- BACKLOG entries added.
- Uncertainties and source targets needing later verification.

Do not commit. Do not push.
