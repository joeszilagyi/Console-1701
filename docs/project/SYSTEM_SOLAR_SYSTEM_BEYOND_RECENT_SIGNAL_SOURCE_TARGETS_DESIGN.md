# SYSTEM_SOLAR Solar System and Beyond Recent Signal Source Targets Design

## SECTION 1: Purpose

The Solar System and Beyond layer is the deep-space, planetary-science, astronomy,
astrophysics, and cosmic-events recent-signal layer for console-1706. It should eventually tell the
user what is happening beyond near-Earth operations, with source provenance, observed time, source
kind, ranking reason, freshness, and evidence. This document uses `SYSTEM_SOLAR` as a working
design label only. The final UI label remains a user decision.

The layer is not:

- A telescope archive mirror.
- A peer-reviewed literature archive.
- A generic astronomy encyclopedia.
- A science hype feed.
- A UFO dashboard.
- A SETI rumor board.
- A space religion board.
- A social media monitoring system.
- A hidden LLM summarizer.
- A cloud service.
- A replacement for ORBITAL.
- A replacement for GLOBAL.
- A replacement for app-health SYSTEM unless the user later chooses a scope rename.

The layer is:

- A local, short-retention metadata dashboard.
- A deterministic cross-source event detector for solar-system, exoplanet, transient, telescope,
  mission, and astrophysics signals.
- A source-health aware recent-signal system.
- A possible future scope in console-1706 that can surface official mission updates, planetary
  events, exoplanet discoveries, transient alerts, gravitational-wave alerts, gamma-ray bursts,
  supernovae, major telescope releases, agency news, astronomy news, and credible public science
  signals.
- A way to rank items by independent source convergence, official or scientific provenance, event
  rarity, public interest, scientific significance, freshness, and user-configured source priority.

"Solar system and beyond" means useful public, configured, lawful, recent signals that the user
chooses to enable. It does not mean unbounded astronomy catalog ingestion, downloading huge archive
products, scraping paper databases, or turning console-1706 into a research data warehouse.

The daily runtime goal is no LLM usage. LLMs may help during development to design adapters, inspect
fixtures, write tests, or analyze source options, but the application itself must not require LLM
calls for normal operation.

## SECTION 2: Scope naming collision

This task is named `006_system.md`, but its content is "solar system and beyond." Earlier
architecture already reserves `SYSTEM` for console-1706 app health, source health, ingest health,
stale-source warnings, configuration warnings, retention state, database health, and evidence that
page loads are not secretly fetching external sources.

This is a real naming collision. The design must not pretend the collision is resolved.

Current meanings:

- `SYSTEM` as app-health is already useful for source health, ingest health, stale-source warnings,
  config warnings, database health, retention status, and evidence that the dashboard remains
  honest.
- Solar System and Beyond is semantically unrelated to app-health. It is a science and astronomy
  recent-signal scope.
- Using `SYSTEM` for both would confuse code, docs, tests, UI labels, source-health screens,
  evidence payloads, and future operators.
- This task designs the deep-space layer without implementing a tab change, route change, template
  change, CSS change, or runtime behavior change.

Possible future naming choices:

| Option | Meaning | Tradeoff |
| --- | --- | --- |
| A | Keep SYSTEM as console app-health. Add a future COSMIC or DEEP tab for solar system and beyond. | Conservative and least disruptive. |
| B | Rename console app-health to CONSOLE or HEALTH later. Use SYSTEM for Solar System and Beyond. | Possible, but requires route, UI, docs, tests, and migration work. |
| C | Keep ORBITAL for near-Earth space. Add SOLAR or COSMIC for solar system and beyond. | Clear semantic split while preserving current app-health SYSTEM. |

Recommended path:

- Keep existing SYSTEM app-health semantics untouched for now.
- Design this new layer under the working name `SYSTEM_SOLAR` or `SOLAR_SYSTEM_BEYOND`.
- Add a backlog item to resolve the naming collision before implementation.
- Candidate UI labels are `COSMIC`, `SOLAR`, `DEEP`, `DEEP SPACE`, `SYSTEM`, `SKY`, and `BEYOND`.
- Do not change existing routes or tabs in this task.

## SECTION 3: Relationship to ORBITAL and other scopes

Solar System and Beyond should complement existing scopes rather than duplicate them.

Scope ownership rules:

- ORBITAL owns near-Earth operations and immediate space-environment effects: space weather, aurora,
  satellites, launches, NEOs, fireballs, reentries, debris, ISS, launch status, and operational
  spaceflight.
- Solar System and Beyond owns deeper scientific and observational signals: planetary science,
  interplanetary mission science, exoplanets, stars, galaxies, cosmology, supernovae, gamma-ray
  bursts, gravitational waves, neutrinos, transients, major telescope science, and credible
  astronomy discoveries.
- GLOBAL owns terrestrial world events unless the cause or primary signal is astronomical or
  space-science related.
- NATIONAL owns U.S. federal and domestic signals unless the primary signal is astronomy, planetary
  science, or astrophysics.
- REGIONAL and LOCAL own geographic impacts such as sky visibility, local observing, aurora
  visibility, meteor showers visible from Seattle, or regional observatory news only when relevant.
- OVERVIEW should select the highest-priority items from all scopes without burying urgent local,
  regional, national, global, orbital, app-health, or host-machine issues.
- App-health SYSTEM should continue as the source-health, ingest-health, stale-source warning,
  config-warning, and database-health scope unless the user later renames it.

Examples:

- SWPC G4 geomagnetic storm: ORBITAL.
- Aurora visible in Seattle: ORBITAL with LOCAL or REGIONAL impact.
- JPL CNEOS close approach: ORBITAL unless there is deeper science coverage; Solar System and
  Beyond may link to it as science context.
- NASA planetary mission discovers active geology on a moon: Solar System and Beyond.
- JWST releases major exoplanet atmosphere result: Solar System and Beyond.
- New exoplanet catalog update: Solar System and Beyond, low priority unless major or multi-source.
- Routine telescope image of a nebula: low-priority Solar System and Beyond.
- Gamma-ray burst GCN alert with follow-up circulars: Solar System and Beyond.
- LIGO/Virgo/KAGRA gravitational-wave candidate alert: Solar System and Beyond.
- Supernova report in TNS plus ATel plus GCN follow-up: Solar System and Beyond.
- Launch of a telescope: ORBITAL during launch, Solar System and Beyond for science milestones.
- NASA budget story about science programs: NATIONAL unless directly tied to mission operation or
  telescope output.
- UFO story: out of scope unless the user later defines a separate explicit scope.

## SECTION 4: Scope boundaries

Default Solar System and Beyond scope:

- Solar system science beyond immediate near-Earth operations.
- Planetary bodies, moons, comets, asteroids, Kuiper Belt objects, and interplanetary missions.
- Solar physics as science, while space-weather effects remain ORBITAL.
- Exoplanets and planetary systems.
- Stellar astronomy.
- Galactic astronomy.
- Extragalactic astronomy.
- Cosmology.
- Gravitational-wave astronomy.
- Gamma-ray bursts and high-energy transients.
- Supernovae, novae, kilonovae, tidal disruption events, fast radio bursts, neutrinos, and
  multi-messenger astronomy.
- Major telescope and observatory science releases.
- Public alerts from recognized astronomy alert networks.
- Peer-reviewed or agency-backed discovery news when recent and significant.
- Major public science news from official agencies, observatories, or reliable science journalism.

Out of scope by default:

- Routine catalog churn.
- Huge archive downloads.
- Full scientific data products.
- Full paper indexing.
- Generic astronomy explainers.
- Low-significance press releases.
- Speculative alien-life clickbait.
- UFO material.
- Astrobiology rumor not tied to credible agency or peer-reviewed source.
- Social-only claims.
- Private observatory chatter.
- Paywalled article scraping.
- ADS full-paper mining.
- Bulk SIMBAD, VizieR, Gaia, MAST, HEASARC, PDS, or exoplanet archive ingestion.
- Data-intensive telescope queries without strict allowlists.
- Anything that turns console-1706 into an astronomy research platform rather than a recent-signal
  dashboard.

Future disabled-by-default config escape hatch:

```yaml
solar_system_beyond:
  enabled: false
  label: "Solar System and Beyond"
  final_scope_label: "TBD"
  naming_collision_with_system: true
  include_planetary_science: true
  include_interplanetary_missions: true
  include_exoplanets: true
  include_telescope_science: true
  include_major_space_agency_science: true
  include_transients: true
  include_gcn: true
  include_tns: false
  include_gravitational_waves: false
  include_neutrino_alerts: false
  include_catalog_archives: false
  include_literature_metadata: false
  include_social_sources: false
  include_large_archive_queries: false
  transient_attention_minimum: "official_alert_or_multi_source"
  exoplanet_attention_minimum: "agency_release_or_confirmed_catalog_delta"
  telescope_science_attention_minimum: "official_release_or_multi_source"
  planetary_attention_minimum: "mission_update_or_agency_release"
  literature_attention_minimum: "disabled"
```

## SECTION 5: Seed source target inventory

This table is a candidate inventory, not a verification result. No live source verification was
performed in this task. `official_page_seen` means the source is identifiable from the prompt
context or source family, not that parser behavior has been tested. URLs requiring endpoint review,
feed verification, auth, account, token, data licensing, terms review, row caps, selector review,
or protocol review remain `candidate_needs_verification`, `candidate_policy_sensitive`,
`auth_required`, or `heavy_archive_risk`.

Risk values use `low`, `medium`, or `high`. Future phases use `S0` through `S12` from the
implementation sequence.

| source_key | source_name | source_family | source_class | scope | raw_url | expected_access_kind | likely_adapter_type | likely_refresh_interval | initial_priority | official_status | privacy_risk | policy_risk | parser_risk | retention_sensitivity | verification_status | why_it_matters | future_phase |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nasa_science_solar_system | NASA Solar System science | nasa_science | official_planetary_science | SYSTEM_SOLAR | https://science.nasa.gov/solar-system/ | public official webpage | source_health_probe_only | 24 h | 55 | official | low | low | low | low | official_page_seen | Human reference for planetary science scope and taxonomy. | S2 |
| nasa_solar_system_news | NASA Solar System news | nasa_science | official_planetary_science | SYSTEM_SOLAR | https://science.nasa.gov/solar-system/news/ | public official webpage/feed candidate | rss_atom | 60 min | 85 | official | low | low | medium | low | candidate_needs_verification | First safe source candidate for planetary-science headlines. | S7 |
| nasa_mission_index | NASA mission index | nasa_science | official_solar_system_mission | SYSTEM_SOLAR | https://science.nasa.gov/mission/ | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | medium | low | official_page_seen | Mission registry context for object and mission matching. | S2 |
| nasa_science_news | NASA science news | nasa_science | official_science_release | SYSTEM_SOLAR | https://science.nasa.gov/news/ | public official webpage/feed candidate | rss_atom | 60 min | 75 | official | low | low | medium | low | candidate_needs_verification | Broad NASA science releases, filtered to this scope. | S7 |
| nasa_missions_news | NASA missions | nasa_news | official_science_release | SYSTEM_SOLAR | https://www.nasa.gov/missions/ | public official webpage | static_html_headline_candidate | 2 h | 60 | official | low | low | medium | low | candidate_needs_verification | Mission announcements when no feed is available. | S8 |
| nasa_news | NASA news | nasa_news | official_science_release | SYSTEM_SOLAR | https://www.nasa.gov/news/ | public official webpage/feed candidate | rss_atom | 60 min | 60 | official | low | low | medium | low | candidate_needs_verification | Broad official NASA source filtered to astronomy science. | S7 |
| nasa_rss_feeds | NASA RSS feeds | nasa_news | source_health_only | SYSTEM_SOLAR | https://www.nasa.gov/rss-feeds/ | public official feed index | rss_atom | manual | 20 | official | low | low | low | low | official_page_seen | Feed discovery reference, not an event source by itself. | S2 |
| nasa_open_api_docs | NASA Open APIs | nasa_api | official_science_release | SYSTEM_SOLAR | https://api.nasa.gov/ | public official API docs | nasa_api_json | disabled | 20 | official | low | medium | medium | low | assistant_seeded | Candidate for later small official JSON sources, not an early fetch. | S8 |
| jpl_news | JPL news | nasa_jpl | official_planetary_science | SYSTEM_SOLAR | https://www.jpl.nasa.gov/news/ | public official webpage/feed candidate | rss_atom | 60 min | 90 | official | low | low | medium | low | candidate_needs_verification | Strong first candidate for mission and planetary-science releases. | S7 |
| jpl_rss | JPL RSS | nasa_jpl | official_planetary_science | SYSTEM_SOLAR | https://www.jpl.nasa.gov/rss/ | public official RSS feed index | rss_atom | 60 min | 90 | official | low | low | medium | low | official_page_seen | Preferred JPL metadata path if feed remains stable. | S7 |
| jpl_missions | JPL missions | nasa_jpl | official_solar_system_mission | SYSTEM_SOLAR | https://www.jpl.nasa.gov/missions/ | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | medium | low | official_page_seen | Mission taxonomy and source-health reference. | S2 |
| solarsystem_nasa | NASA Solar System Exploration | nasa_solar_system | official_planetary_science | SYSTEM_SOLAR | https://solarsystem.nasa.gov/ | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | medium | low | official_page_seen | Solar system reference source, likely not a live ingest. | S2 |
| nasa_planets | NASA planets | nasa_solar_system | official_planetary_science | SYSTEM_SOLAR | https://science.nasa.gov/solar-system/planets/ | public official webpage | source_health_probe_only | 24 h | 25 | official | low | low | low | low | user_seeded | Reference for planetary-body taxonomy. | S2 |
| nasa_moons | NASA moons | nasa_solar_system | official_planetary_science | SYSTEM_SOLAR | https://science.nasa.gov/solar-system/moons/ | public official webpage | source_health_probe_only | 24 h | 25 | official | low | low | low | low | user_seeded | Reference for moon/body taxonomy. | S2 |
| nasa_comets | NASA comets | nasa_solar_system | official_minor_body_science | SYSTEM_SOLAR | https://science.nasa.gov/solar-system/comets/ | public official webpage | source_health_probe_only | 24 h | 25 | official | low | low | low | low | user_seeded | Reference for comet-science routing. | S2 |
| nasa_asteroids | NASA asteroids | nasa_solar_system | official_minor_body_science | SYSTEM_SOLAR | https://science.nasa.gov/solar-system/asteroids/ | public official webpage | source_health_probe_only | 24 h | 25 | official | low | low | low | low | user_seeded | Reference for asteroid-science routing. | S2 |
| voyager_mission | NASA Voyager mission | nasa_mission | official_solar_system_mission | SYSTEM_SOLAR | https://science.nasa.gov/mission/voyager/ | public official mission page | source_health_probe_only | 24 h | 35 | official | low | low | low | low | user_seeded | Deep solar-system mission context. | S2 |
| juno_mission | NASA Juno mission | nasa_mission | official_solar_system_mission | SYSTEM_SOLAR | https://science.nasa.gov/mission/juno/ | public official mission page | source_health_probe_only | 24 h | 35 | official | low | low | low | low | user_seeded | Jupiter science mission context. | S2 |
| europa_clipper_mission | NASA Europa Clipper mission | nasa_mission | official_solar_system_mission | SYSTEM_SOLAR | https://science.nasa.gov/mission/europa-clipper/ | public official mission page | source_health_probe_only | 24 h | 45 | official | low | low | low | low | user_seeded | High-interest planetary mission context. | S2 |
| mars_perseverance_mission | NASA Mars 2020 Perseverance | nasa_mission | official_solar_system_mission | SYSTEM_SOLAR | https://science.nasa.gov/mission/mars-2020-perseverance/ | public official mission page | source_health_probe_only | 24 h | 45 | official | low | low | low | low | user_seeded | Mars mission context. | S2 |
| curiosity_mission | NASA Curiosity | nasa_mission | official_solar_system_mission | SYSTEM_SOLAR | https://science.nasa.gov/mission/curiosity/ | public official mission page | source_health_probe_only | 24 h | 35 | official | low | low | low | low | user_seeded | Mars science mission context. | S2 |
| lucy_mission | NASA Lucy | nasa_mission | official_solar_system_mission | SYSTEM_SOLAR | https://science.nasa.gov/mission/lucy/ | public official mission page | source_health_probe_only | 24 h | 35 | official | low | low | low | low | user_seeded | Trojan asteroid mission context. | S2 |
| osiris_apex_mission | NASA OSIRIS-APEX | nasa_mission | official_solar_system_mission | SYSTEM_SOLAR | https://science.nasa.gov/mission/osiris-apex/ | public official mission page | source_health_probe_only | 24 h | 35 | official | low | low | low | low | user_seeded | Asteroid mission context. | S2 |
| parker_solar_probe | NASA Parker Solar Probe | nasa_mission | official_solar_science | SYSTEM_SOLAR | https://science.nasa.gov/mission/parker-solar-probe/ | public official mission page | source_health_probe_only | 24 h | 50 | official | low | low | low | low | official_page_seen | Solar physics science source; operational effects stay ORBITAL. | S2 |
| solar_orbiter | Solar Orbiter | nasa_mission | official_solar_science | SYSTEM_SOLAR | https://science.nasa.gov/mission/solar-orbiter/ | public official mission page | source_health_probe_only | 24 h | 45 | official | low | low | low | low | official_page_seen | Solar science mission context. | S2 |
| pds_home | NASA Planetary Data System | pds | official_planetary_data_archive | SYSTEM_SOLAR | https://pds.nasa.gov/ | public official archive | source_health_probe_only | 24 h | 50 | official | low | low | low | low | official_page_seen | Planetary archive authority reference. | S2 |
| pds_data_search | PDS data search | pds | heavy_archive_candidate | SYSTEM_SOLAR | https://pds.nasa.gov/datasearch/data-search/ | public archive search | manual_review_only | disabled | 15 | official | low | medium | high | medium | heavy_archive_risk | Search UI is not an ingest source; avoid product downloads. | S10 |
| pds_api | PDS API | pds | official_planetary_data_archive | SYSTEM_SOLAR | https://nasa-pds.github.io/pds-api/ | public official API docs | pds_api_candidate | 24 h | 65 | official | low | medium | medium | medium | official_page_seen | Metadata-only release checks after row caps. | S8 |
| pds_api_github | NASA PDS API GitHub | pds | source_health_only | SYSTEM_SOLAR | https://github.com/NASA-PDS/pds-api | public code/docs page | manual_review_only | manual | 10 | official_candidate | low | medium | low | low | candidate_policy_sensitive | Implementation reference, not a runtime source. | S2 |
| pds_subscription | PDS subscription service | pds | official_planetary_data_archive | SYSTEM_SOLAR | https://pds.nasa.gov/datasearch/subscription-service/ | public official page | manual_review_only | disabled | 20 | official | low | medium | medium | low | candidate_needs_verification | Possible release metadata path after verification. | S8 |
| jpl_ssd_api_home | JPL SSD API | jpl_ssd | official_minor_body_science | SYSTEM_SOLAR | https://ssd-api.jpl.nasa.gov/ | public official API landing | jpl_ssd_api | 6 h | 55 | official | low | low | medium | low | official_page_seen | Minor-body science context, with ORBITAL overlap handling. | S8 |
| jpl_ssd_doc | JPL SSD API docs | jpl_ssd | source_health_only | SYSTEM_SOLAR | https://ssd-api.jpl.nasa.gov/doc/index.php | public official API docs | manual_review_only | manual | 10 | official | low | low | low | low | official_page_seen | Implementation reference for JPL SSD adapters. | S2 |
| jpl_sbdb_api | JPL SBDB API | jpl_ssd | official_minor_body_science | SYSTEM_SOLAR | https://ssd-api.jpl.nasa.gov/sbdb.api | public official API endpoint | jpl_ssd_api | 6 h | 45 | official | low | low | medium | low | candidate_needs_verification | Small-body metadata candidate, not a firehose. | S8 |
| jpl_cad_api | JPL close approach API | jpl_ssd | official_minor_body_science | SYSTEM_SOLAR | https://ssd-api.jpl.nasa.gov/cad.api | public official API endpoint | jpl_ssd_api | 6 h | 35 | official | low | low | medium | low | candidate_needs_verification | ORBITAL canonical for close approaches; science context only here. | S8 |
| jpl_sentry_api | JPL Sentry API | jpl_ssd | official_minor_body_science | SYSTEM_SOLAR | https://ssd-api.jpl.nasa.gov/sentry.api | public official API endpoint | jpl_ssd_api | 6 h | 35 | official | low | low | medium | low | candidate_needs_verification | Risk monitoring is ORBITAL first; science context only here. | S8 |
| jpl_horizons_doc | JPL Horizons docs | jpl_ssd | heavy_archive_candidate | SYSTEM_SOLAR | https://ssd-api.jpl.nasa.gov/doc/horizons.html | public official API docs | manual_review_only | disabled | 15 | official | low | medium | high | medium | heavy_archive_risk | Useful manually, but too query-heavy for early dashboard work. | S10 |
| cneos_home | CNEOS | cneos | official_minor_body_science | SYSTEM_SOLAR | https://cneos.jpl.nasa.gov/ | public official webpage | source_health_probe_only | 24 h | 30 | official | low | low | low | low | official_page_seen | ORBITAL overlap reference for small-body context. | S2 |
| mpc_home | Minor Planet Center | mpc | official_minor_body_science | SYSTEM_SOLAR | https://www.minorplanetcenter.net/ | public official-ish webpage | source_health_probe_only | 24 h | 45 | official_candidate | low | low | low | low | official_page_seen | Minor-body authority reference. | S2 |
| mpc_data | MPC data | mpc | official_minor_body_science | SYSTEM_SOLAR | https://www.minorplanetcenter.net/data | public data page | manual_review_only | manual | 20 | official_candidate | low | medium | medium | medium | candidate_needs_verification | Data listing requires scope and volume review. | S8 |
| mpc_recent_mpecs | Recent MPECs | mpc | official_minor_body_science | SYSTEM_SOLAR | https://www.minorplanetcenter.net/mpec/RecentMPECs.html | public official-ish page | mpc_api | 60 min | 55 | official_candidate | low | low | medium | medium | candidate_needs_verification | Small-body circular metadata source if stable. | S8 |
| mpc_mpecs_api | MPECs API docs | mpc | official_minor_body_science | SYSTEM_SOLAR | https://www.minorplanetcenter.net/mpcops/documentation/mpecs-api/ | public API docs | mpc_api | 60 min | 55 | official_candidate | low | low | medium | medium | official_page_seen | Machine-readable MPEC candidate after verification. | S8 |
| mpc_neocp_api | MPC NEOCP observations API | mpc | official_minor_body_science | SYSTEM_SOLAR | https://cgi.minorplanetcenter.net/mpcops/documentation/neocp-observations-api/ | public API docs | mpc_api | disabled | 30 | official_candidate | low | medium | medium | medium | candidate_policy_sensitive | NEOCP is ORBITAL-sensitive; use only scoped science context. | S8 |
| exoplanet_archive_home | NASA Exoplanet Archive | nasa_exoplanet_archive | official_exoplanet_archive | SYSTEM_SOLAR | https://exoplanetarchive.ipac.caltech.edu/ | public official archive | source_health_probe_only | 24 h | 55 | official | low | low | low | low | official_page_seen | Exoplanet archive authority reference. | S2 |
| exoplanet_archive_program | NASA Exoplanet Archive program interfaces | nasa_exoplanet_archive | official_exoplanet_archive | SYSTEM_SOLAR | https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html | public official API docs | exoplanet_archive_api | 6 h | 80 | official | low | low | medium | low | official_page_seen | Seed for allowlisted exoplanet metadata queries. | S8 |
| exoplanet_archive_api_queries | NASA Exoplanet Archive API queries | nasa_exoplanet_archive | official_exoplanet_archive | SYSTEM_SOLAR | https://exoplanetarchive.ipac.caltech.edu/docs/API_queries.html | public official API docs | exoplanet_archive_api | 6 h | 80 | official | low | low | medium | low | official_page_seen | Query-shape reference for tiny metadata parser. | S8 |
| exoplanet_archive_tap | NASA Exoplanet Archive TAP | nasa_exoplanet_archive | official_exoplanet_archive | SYSTEM_SOLAR | https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html | public official TAP docs | tap_adql_candidate | disabled | 55 | official | low | medium | high | medium | heavy_archive_risk | TAP requires strict allowlists and row caps. | S10 |
| exoplanet_archive_columns | Exoplanet Archive PS columns | nasa_exoplanet_archive | source_health_only | SYSTEM_SOLAR | https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html | public official docs | manual_review_only | manual | 10 | official | low | low | low | low | official_page_seen | Schema reference for exoplanet evidence fields. | S2 |
| exoplanet_archive_news | Exoplanet Archive news archive | nasa_exoplanet_archive | official_exoplanet | SYSTEM_SOLAR | https://exoplanetarchive.ipac.caltech.edu/docs/exonews_archive.html | public official news archive | static_html_headline_candidate | 6 h | 45 | official | low | low | medium | low | candidate_needs_verification | Archive news candidate, lower priority than agency releases. | S8 |
| exo_mast_docs | Exo.MAST docs | mast | official_exoplanet | SYSTEM_SOLAR | https://exo.mast.stsci.edu/docs/ | public official docs | mast_api_candidate | disabled | 35 | official | low | medium | high | medium | heavy_archive_risk | Exoplanet metadata candidate only after narrow query contract. | S10 |
| mast_api | MAST API | mast | official_astronomy_archive | SYSTEM_SOLAR | https://mast.stsci.edu/api/v0/ | public official API docs | mast_api_candidate | disabled | 55 | official | low | medium | high | medium | heavy_archive_risk | Archive metadata source; no science product downloads. | S10 |
| mast_catalogs | MAST catalogs docs | mast | heavy_archive_candidate | SYSTEM_SOLAR | https://catalogs.mast.stsci.edu/docs/index.html | public archive docs | mast_api_candidate | disabled | 25 | official | low | medium | high | medium | heavy_archive_risk | Catalog source, blocked unless strict use case exists. | S10 |
| jwst_mast_docs | JWST MAST API access | mast | official_space_telescope | SYSTEM_SOLAR | https://jwst-docs.stsci.edu/accessing-jwst-data/mast-api-access | public official docs | mast_api_candidate | disabled | 35 | official | low | medium | high | medium | heavy_archive_risk | JWST data access reference; no product downloads. | S10 |
| stsci_jwst_archive | STScI JWST archive | stsci | official_space_telescope | SYSTEM_SOLAR | https://archive.stsci.edu/missions-and-data/jwst | public official archive page | source_health_probe_only | 24 h | 30 | official | low | low | low | low | official_page_seen | JWST archive reference. | S2 |
| stsci_hubble_archive | STScI Hubble archive | stsci | official_space_telescope | SYSTEM_SOLAR | https://archive.stsci.edu/missions-and-data/hubble | public official archive page | source_health_probe_only | 24 h | 25 | official | low | low | low | low | official_page_seen | Hubble archive reference. | S2 |
| nasa_hubble_mission | NASA Hubble mission | nasa_science | official_space_telescope | SYSTEM_SOLAR | https://science.nasa.gov/mission/hubble/ | public official mission page | source_health_probe_only | 24 h | 35 | official | low | low | low | low | official_page_seen | Telescope mission context. | S2 |
| nasa_jwst_mission | NASA JWST mission | nasa_science | official_space_telescope | SYSTEM_SOLAR | https://science.nasa.gov/mission/jwst/ | public official mission page | source_health_probe_only | 24 h | 45 | official | low | low | low | low | official_page_seen | JWST mission context. | S2 |
| nasa_tess_mission | NASA TESS mission | nasa_science | official_exoplanet | SYSTEM_SOLAR | https://science.nasa.gov/mission/tess/ | public official mission page | source_health_probe_only | 24 h | 40 | official | low | low | low | low | official_page_seen | Exoplanet survey mission context. | S2 |
| nasa_roman_mission | NASA Roman Space Telescope | nasa_science | official_space_telescope | SYSTEM_SOLAR | https://science.nasa.gov/mission/roman-space-telescope/ | public official mission page | source_health_probe_only | 24 h | 40 | official | low | low | low | low | official_page_seen | Future telescope mission context. | S2 |
| hubblesite_news | HubbleSite news | hubble | official_space_telescope | SYSTEM_SOLAR | https://hubblesite.org/news | public official webpage/feed candidate | rss_atom | 60 min | 70 | official | low | low | medium | low | candidate_needs_verification | Hubble science-release candidate. | S7 |
| hubblesite_rss | HubbleSite RSS feeds | hubble | official_space_telescope | SYSTEM_SOLAR | https://hubblesite.org/resource-gallery/rss-feeds | public official feed index | rss_atom | 60 min | 70 | official | low | low | medium | low | official_page_seen | Preferred Hubble metadata path after feed verification. | S7 |
| webb_news | Webb Telescope news | webb | official_space_telescope | SYSTEM_SOLAR | https://webbtelescope.org/news | public official webpage/feed candidate | rss_atom | 60 min | 85 | official | low | low | medium | low | candidate_needs_verification | JWST science-release candidate. | S7 |
| webb_releases | Webb news releases | webb | official_space_telescope | SYSTEM_SOLAR | https://webbtelescope.org/contents/news-releases | public official webpage | static_html_headline_candidate | 60 min | 80 | official | low | low | medium | low | candidate_needs_verification | JWST release metadata if feed is not sufficient. | S8 |
| webb_rss | Webb RSS feed | webb | official_space_telescope | SYSTEM_SOLAR | https://webbtelescope.org/resource-gallery/rss-feed | public official feed | rss_atom | 60 min | 85 | official | low | low | medium | low | official_page_seen | Preferred JWST metadata path after verification. | S7 |
| roman_news | Roman news | roman | official_space_telescope | SYSTEM_SOLAR | https://roman.gsfc.nasa.gov/news/ | public official webpage/feed candidate | rss_atom | 2 h | 55 | official | low | low | medium | low | candidate_needs_verification | Roman science and mission updates. | S7 |
| nasa_universe | NASA universe | nasa_science | official_science_release | SYSTEM_SOLAR | https://science.nasa.gov/universe/ | public official webpage | source_health_probe_only | 24 h | 40 | official | low | low | low | low | official_page_seen | Broad astrophysics taxonomy source. | S2 |
| nasa_astrophysics | NASA astrophysics | nasa_science | official_science_release | SYSTEM_SOLAR | https://science.nasa.gov/astrophysics/ | public official webpage | source_health_probe_only | 24 h | 40 | official | low | low | low | low | official_page_seen | Astrophysics taxonomy source. | S2 |
| stsci_news | STScI news | stsci | official_observatory_news | SYSTEM_SOLAR | https://www.stsci.edu/contents/news | public official webpage/feed candidate | rss_atom | 60 min | 65 | official | low | low | medium | low | candidate_needs_verification | Observatory science release source. | S7 |
| heasarc_home | HEASARC | heasarc | official_high_energy_astrophysics | SYSTEM_SOLAR | https://heasarc.gsfc.nasa.gov/ | public official archive | source_health_probe_only | 24 h | 45 | official | low | low | low | low | official_page_seen | High-energy archive reference. | S2 |
| heasarc_archive | HEASARC archive | heasarc | heavy_archive_candidate | SYSTEM_SOLAR | https://heasarc.gsfc.nasa.gov/docs/archive.html | public official archive page | manual_review_only | disabled | 20 | official | low | medium | high | medium | heavy_archive_risk | Archive is too broad without strict query contract. | S10 |
| heasarc_webservices | HEASARC web services | heasarc | official_high_energy_astrophysics | SYSTEM_SOLAR | https://heasarc.gsfc.nasa.gov/docs/software/webservices/ | public official API docs | heasarc_api_candidate | disabled | 50 | official | low | medium | high | medium | candidate_needs_verification | High-energy metadata source after endpoint review. | S8 |
| gcn_home | NASA GCN | gcn | official_transient_alert | SYSTEM_SOLAR | https://gcn.nasa.gov/ | public official alert portal | source_health_probe_only | 24 h | 70 | official | low | low | low | low | official_page_seen | Transient alert authority reference. | S2 |
| gcn_notices | NASA GCN notices | gcn | official_transient_alert | SYSTEM_SOLAR | https://gcn.nasa.gov/docs/notices | public official alert docs | gcn_notice_candidate | 5 min | 95 | official | low | medium | high | medium | official_page_seen | Key candidate for gamma-ray burst and transient notices. | S9 |
| gcn_notice_schema | NASA GCN notice schema | gcn | source_health_only | SYSTEM_SOLAR | https://gcn.nasa.gov/docs/notices/schema | public official schema docs | manual_review_only | manual | 10 | official | low | low | low | low | official_page_seen | Schema reference for fixture parser. | S3 |
| gcn_notice_archive | NASA GCN notice archive | gcn | official_transient_alert | SYSTEM_SOLAR | https://gcn.nasa.gov/docs/notices/archive | public official archive docs | gcn_notice_candidate | disabled | 40 | official | low | medium | high | medium | candidate_policy_sensitive | Archive use needs volume and retention limits. | S9 |
| gcn_circulars_docs | NASA GCN circular docs | gcn | official_transient_alert | SYSTEM_SOLAR | https://gcn.nasa.gov/docs/circulars | public official docs | gcn_circular_candidate | 30 min | 80 | official | low | medium | medium | medium | candidate_needs_verification | Follow-up circular metadata candidate. | S9 |
| gcn_circulars | NASA GCN circulars | gcn | official_transient_alert | SYSTEM_SOLAR | https://gcn.nasa.gov/circulars | public official circular page | gcn_circular_candidate | 30 min | 80 | official | low | medium | medium | medium | candidate_needs_verification | Follow-up signal for transients. | S9 |
| gcn_sample | NASA GCN sample code | gcn | source_health_only | SYSTEM_SOLAR | https://gcn.nasa.gov/docs/sample | public official docs | manual_review_only | manual | 10 | official | low | low | low | low | user_seeded | Implementation reference, not an ingest source. | S2 |
| gcn_schema_github | NASA GCN schema GitHub | gcn | source_health_only | SYSTEM_SOLAR | https://github.com/nasa-gcn/gcn-schema | public code/docs page | manual_review_only | manual | 10 | official_candidate | low | medium | low | low | candidate_policy_sensitive | Schema reference; do not add dependency from it in this task. | S2 |
| gcn_neutrino_candidate | GCN neutrino notices candidate | gcn | official_neutrino_candidate | SYSTEM_SOLAR | https://gcn.nasa.gov/docs/notices | public official alert docs | gcn_notice_candidate | 5 min | 70 | official | low | medium | high | medium | assistant_seeded | Neutrino alerts may arrive through recognized alert networks; fixture-first. | S9 |
| swift_uk | Swift UK | swift | official_high_energy_astrophysics | SYSTEM_SOLAR | https://www.swift.ac.uk/ | public official-ish science page | source_health_probe_only | 24 h | 35 | official_candidate | low | low | medium | low | candidate_needs_verification | High-energy mission context. | S2 |
| swift_gsfc | Swift GSFC | swift | official_high_energy_astrophysics | SYSTEM_SOLAR | https://swift.gsfc.nasa.gov/ | public official mission page | source_health_probe_only | 24 h | 35 | official | low | low | medium | low | official_page_seen | GRB/transient mission context. | S2 |
| fermi_home | Fermi GSFC | fermi | official_high_energy_astrophysics | SYSTEM_SOLAR | https://fermi.gsfc.nasa.gov/ | public official mission page | source_health_probe_only | 24 h | 35 | official | low | low | medium | low | official_page_seen | Gamma-ray mission context. | S2 |
| fermi_ssc | Fermi Science Support Center | fermi | official_high_energy_astrophysics | SYSTEM_SOLAR | https://fermi.gsfc.nasa.gov/ssc/ | public official support center | source_health_probe_only | 24 h | 35 | official | low | low | medium | low | official_page_seen | High-energy science support reference. | S2 |
| igwn_userguide | IGWN public alerts user guide | igwn | official_gravitational_wave | SYSTEM_SOLAR | https://rtd.igwn.org/projects/userguide/en/v3/index.html | public official-ish docs | gracedb_api_candidate | disabled | 75 | official_candidate | low | medium | medium | medium | official_page_seen | Gravitational-wave public-alert implementation reference. | S9 |
| gracedb_home | GraceDB | ligo | official_gravitational_wave | SYSTEM_SOLAR | https://gracedb.ligo.org/ | public/service portal | gracedb_api_candidate | disabled | 80 | official_candidate | low | medium | high | medium | candidate_policy_sensitive | Public alert candidate; preserve preliminary/retraction state. | S9 |
| gracedb_api_docs | GraceDB API docs | ligo | official_gravitational_wave | SYSTEM_SOLAR | https://ligo-gracedb.readthedocs.io/en/latest/api.html | public API docs | gracedb_api_candidate | disabled | 80 | official_candidate | low | medium | high | medium | candidate_policy_sensitive | API candidate requiring auth/protocol review. | S9 |
| ligo_caltech_news | LIGO Caltech news | ligo | official_gravitational_wave | SYSTEM_SOLAR | https://www.ligo.caltech.edu/news | public official webpage/feed candidate | rss_atom | 2 h | 50 | official_candidate | low | low | medium | low | candidate_needs_verification | Gravitational-wave science news. | S7 |
| ligo_org_news | LIGO news | ligo | official_gravitational_wave | SYSTEM_SOLAR | https://www.ligo.org/news.php | public official webpage/feed candidate | rss_atom | 2 h | 50 | official_candidate | low | low | medium | low | candidate_needs_verification | Gravitational-wave collaboration news. | S7 |
| virgo_news | Virgo news | virgo | official_gravitational_wave | SYSTEM_SOLAR | https://www.virgo-gw.eu/news/ | public official webpage/feed candidate | rss_atom | 2 h | 40 | official_candidate | low | low | medium | low | candidate_needs_verification | Independent gravitational-wave source family. | S7 |
| kagra_news | KAGRA news | kagra | official_gravitational_wave | SYSTEM_SOLAR | https://gwcenter.icrr.u-tokyo.ac.jp/en/ | public official webpage/feed candidate | rss_atom | 2 h | 35 | official_candidate | low | low | medium | low | candidate_needs_verification | Independent gravitational-wave source family. | S7 |
| gwosc_home | GWOSC | gwosc | official_gravitational_wave | SYSTEM_SOLAR | https://www.gw-openscience.org/ | public official-ish data portal | source_health_probe_only | 24 h | 30 | official_candidate | low | low | low | low | official_page_seen | Public data reference, not early live source. | S2 |
| gwosc_eventapi | GWOSC event API | gwosc | official_gravitational_wave | SYSTEM_SOLAR | https://www.gw-openscience.org/eventapi/ | public official-ish API docs | official_api_json | 24 h | 45 | official_candidate | low | medium | medium | medium | candidate_needs_verification | Confirmed event metadata candidate after scope filters. | S8 |
| astronomers_telegram_home | Astronomers Telegram | atel | official_transient_alert | SYSTEM_SOLAR | https://www.astronomerstelegram.org/ | public astronomy alert site | source_health_probe_only | 24 h | 45 | official_candidate | low | low | low | low | official_page_seen | Transient communication authority reference. | S2 |
| astronomers_telegram_rss | Astronomers Telegram RSS | atel | official_transient_alert | SYSTEM_SOLAR | https://www.astronomerstelegram.org/?rss | public RSS feed | astronomers_telegram_rss | 30 min | 80 | official_candidate | low | low | medium | medium | official_page_seen | Strong fixture-first transient follow-up source. | S9 |
| tns_home | Transient Name Server | tns | official_supernova_transient | SYSTEM_SOLAR | https://www.wis-tns.org/ | public official transient site | source_health_probe_only | 24 h | 50 | official_candidate | low | medium | medium | medium | official_page_seen | IAU mechanism for astronomical transient names. | S2 |
| tns_getting_started | TNS getting started | tns | official_supernova_transient | SYSTEM_SOLAR | https://www.wis-tns.org/content/tns-getting-started | public docs/account guide | tns_api_candidate | disabled | 70 | official_candidate | low | high | high | medium | auth_required | Auth and terms review required before use. | S9 |
| tns_news | TNS news | tns | official_supernova_transient | SYSTEM_SOLAR | https://www.wis-tns.org/content/tns-news | public page | static_html_headline_candidate | 6 h | 35 | official_candidate | low | medium | medium | low | candidate_needs_verification | TNS news source, not transient database ingest. | S9 |
| tns_api_manual | TNS API manual PDF | tns | auth_required_candidate | SYSTEM_SOLAR | https://www.wis-tns.org/sites/default/files/api/TNS_APIs_manual.pdf | public API manual | tns_api_candidate | manual | 15 | official_candidate | low | high | medium | low | auth_required | Implementation reference; credentials must stay outside repo. | S9 |
| rubin_lsst_news | LSST news | rubin_lsst | official_observatory_news | SYSTEM_SOLAR | https://www.lsst.org/news | public observatory page/feed candidate | rss_atom | 2 h | 45 | official_candidate | low | low | medium | low | candidate_needs_verification | Survey telescope science and operations context. | S7 |
| rubin_news | Rubin Observatory news | rubin | official_observatory_news | SYSTEM_SOLAR | https://rubinobservatory.org/news | public official page/feed candidate | rss_atom | 2 h | 45 | official_candidate | low | low | medium | low | candidate_needs_verification | Observatory science release candidate. | S7 |
| ztf_news | ZTF news | ztf | official_observatory_news | SYSTEM_SOLAR | https://www.ztf.caltech.edu/news.html | public observatory page | static_html_headline_candidate | 6 h | 30 | official_candidate | low | low | medium | low | candidate_needs_verification | Time-domain astronomy context. | S8 |
| lco_news | Las Cumbres Observatory news | lco | official_observatory_news | SYSTEM_SOLAR | https://www.lco.global/news/ | public observatory page/feed candidate | rss_atom | 6 h | 30 | official_candidate | low | low | medium | low | candidate_needs_verification | Follow-up network and observatory context. | S7 |
| esa_rss | ESA RSS feeds | esa | official_science_release | SYSTEM_SOLAR | https://www.esa.int/Services/RSS_Feeds | public official feed index | rss_atom | 60 min | 75 | official | low | low | medium | low | official_page_seen | First safe international agency feed candidate. | S7 |
| esa_science_exploration | ESA Science and Exploration | esa | official_science_release | SYSTEM_SOLAR | https://www.esa.int/Science_Exploration | public official webpage/feed candidate | rss_atom | 60 min | 70 | official | low | low | medium | low | candidate_needs_verification | ESA science release candidate. | S7 |
| esa_sci | ESA Science | esa | official_science_release | SYSTEM_SOLAR | https://sci.esa.int/ | public official science page | rss_atom | 60 min | 70 | official | low | low | medium | low | candidate_needs_verification | ESA science mission source. | S7 |
| esa_sci_rss | ESA science RSS | esa | official_science_release | SYSTEM_SOLAR | https://sci.esa.int/web/services/rss | public official RSS index | rss_atom | 60 min | 70 | official | low | low | medium | low | official_page_seen | Preferred ESA science metadata path if stable. | S7 |
| esdc_home | ESA Science Data Centre | esdc | official_astronomy_archive | SYSTEM_SOLAR | https://www.cosmos.esa.int/web/esdc | public official archive page | source_health_probe_only | 24 h | 30 | official | low | low | low | low | official_page_seen | Archive reference, not broad ingest. | S2 |
| esasky | ESASky | esasky | heavy_archive_candidate | SYSTEM_SOLAR | https://sky.esa.int/ | public sky archive portal | tap_adql_candidate | disabled | 15 | official | low | medium | high | medium | heavy_archive_risk | Heavy archive portal; no live ingest by default. | S10 |
| esasky_js_api | ESASky JavaScript API | esasky | manual_review_only | SYSTEM_SOLAR | https://www.cosmos.esa.int/web/esdc/esasky-javascript-api | public API docs | manual_review_only | disabled | 5 | official | low | medium | high | medium | reject_for_now | Browser/visual archive API is not appropriate for backend ingest now. | S10 |
| jaxa_press | JAXA press releases | jaxa | official_science_release | SYSTEM_SOLAR | https://global.jaxa.jp/press/ | public official page/feed candidate | rss_atom | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | International agency source family. | S7 |
| isro_press | ISRO press | isro | official_science_release | SYSTEM_SOLAR | https://www.isro.gov.in/Press.html | public official page/feed candidate | rss_atom | 2 h | 40 | official | low | low | medium | low | candidate_needs_verification | International agency source family. | S7 |
| csa_news | CSA news | csa | official_science_release | SYSTEM_SOLAR | https://www.asc-csa.gc.ca/eng/news/ | public official page/feed candidate | rss_atom | 2 h | 40 | official | low | low | medium | low | candidate_needs_verification | International agency source family. | S7 |
| eso_news | ESO news | eso | official_observatory_news | SYSTEM_SOLAR | https://www.eso.org/public/news/ | public official webpage/feed candidate | rss_atom | 60 min | 60 | official | low | low | medium | low | candidate_needs_verification | Observatory science releases. | S7 |
| eso_rss | ESO RSS | eso | official_observatory_news | SYSTEM_SOLAR | https://www.eso.org/public/rss/ | public official feed index | rss_atom | 60 min | 60 | official | low | low | medium | low | official_page_seen | Preferred ESO metadata path if stable. | S7 |
| eso_archive | ESO Archive | eso_archive | heavy_archive_candidate | SYSTEM_SOLAR | https://archive.eso.org/ | public official archive | source_health_probe_only | 24 h | 20 | official | low | medium | high | medium | heavy_archive_risk | Archive reference only unless strict query use case exists. | S10 |
| eso_archive_programmatic | ESO archive programmatic access | eso_archive | heavy_archive_candidate | SYSTEM_SOLAR | https://archive.eso.org/programmatic/ | public official API docs | tap_adql_candidate | disabled | 25 | official | low | medium | high | medium | heavy_archive_risk | Programmatic archive access requires strict row caps. | S10 |
| noirlab_news | NOIRLab news | noirlab | official_observatory_news | SYSTEM_SOLAR | https://noirlab.edu/public/news/ | public official page/feed candidate | rss_atom | 60 min | 55 | official | low | low | medium | low | candidate_needs_verification | Observatory science releases. | S7 |
| noirlab_rss | NOIRLab RSS | noirlab | official_observatory_news | SYSTEM_SOLAR | https://noirlab.edu/public/news/rss/ | public official RSS | rss_atom | 60 min | 55 | official | low | low | medium | low | official_page_seen | Preferred NOIRLab metadata path if stable. | S7 |
| nrao_public_news | NRAO public news | nrao | official_observatory_news | SYSTEM_SOLAR | https://public.nrao.edu/news/ | public official page/feed candidate | rss_atom | 60 min | 45 | official_candidate | low | low | medium | low | candidate_needs_verification | Radio astronomy source family. | S7 |
| nrao_feed | NRAO feed | nrao | official_observatory_news | SYSTEM_SOLAR | https://public.nrao.edu/feed/ | public RSS feed | rss_atom | 60 min | 45 | official_candidate | low | low | medium | low | candidate_needs_verification | Radio astronomy RSS candidate. | S7 |
| alma_news | ALMA news | alma | official_observatory_news | SYSTEM_SOLAR | https://www.almaobservatory.org/en/news/ | public official page/feed candidate | rss_atom | 60 min | 45 | official_candidate | low | low | medium | low | candidate_needs_verification | Radio/submillimeter astronomy source family. | S7 |
| alma_feed | ALMA feed | alma | official_observatory_news | SYSTEM_SOLAR | https://www.almaobservatory.org/en/feed/ | public feed | rss_atom | 60 min | 45 | official_candidate | low | low | medium | low | candidate_needs_verification | ALMA RSS candidate. | S7 |
| nao_news | NAOJ news | naoj | official_observatory_news | SYSTEM_SOLAR | https://www.nao.ac.jp/en/news/ | public official page/feed candidate | rss_atom | 2 h | 35 | official | low | low | medium | low | candidate_needs_verification | International observatory source family. | S7 |
| nao_rss | NAOJ RSS | naoj | official_observatory_news | SYSTEM_SOLAR | https://www.nao.ac.jp/en/news/rss.xml | public official RSS | rss_atom | 2 h | 35 | official | low | low | medium | low | candidate_needs_verification | NAOJ RSS candidate. | S7 |
| skao_news | SKAO news | skao | official_observatory_news | SYSTEM_SOLAR | https://www.skao.int/en/news | public official page/feed candidate | rss_atom | 2 h | 35 | official_candidate | low | low | medium | low | candidate_needs_verification | Future radio observatory source family. | S7 |
| simbad_home | SIMBAD | simbad | astronomy_catalog_candidate | SYSTEM_SOLAR | https://simbad.u-strasbg.fr/ | public catalog portal | source_health_probe_only | 24 h | 20 | official_candidate | low | medium | high | medium | heavy_archive_risk | Object resolver reference; not broad ingest. | S10 |
| simbad_query_guide | SIMBAD query guide | simbad | astronomy_catalog_candidate | SYSTEM_SOLAR | https://simbad.u-strasbg.fr/Pages/guide/sim-q.htx | public catalog docs | manual_review_only | manual | 10 | official_candidate | low | medium | medium | low | official_page_seen | Query reference for later object-name lookup. | S10 |
| simbad_tap | SIMBAD TAP | simbad | astronomy_catalog_candidate | SYSTEM_SOLAR | https://simbad.u-strasbg.fr/simbad/sim-tap | public TAP endpoint/docs | simbad_tap_candidate | disabled | 25 | official_candidate | low | medium | high | medium | heavy_archive_risk | Strict object-lookup candidate only. | S10 |
| vizier_tap | VizieR TAP | vizier | astronomy_catalog_candidate | SYSTEM_SOLAR | https://tapvizier.cds.unistra.fr/adql/ | public TAP docs/endpoint | vizier_tap_candidate | disabled | 25 | official_candidate | low | medium | high | medium | heavy_archive_risk | Catalog metadata only if narrowly scoped. | S10 |
| vizier_home | VizieR | vizier | astronomy_catalog_candidate | SYSTEM_SOLAR | https://vizier.cds.unistra.fr/ | public catalog portal | source_health_probe_only | 24 h | 15 | official_candidate | low | medium | high | medium | heavy_archive_risk | Human reference; no catalog ingestion. | S10 |
| cds_home | CDS | cds | source_health_only | SYSTEM_SOLAR | https://cds.unistra.fr/ | public institution page | source_health_probe_only | 24 h | 15 | official_candidate | low | low | low | low | official_page_seen | Catalog institution reference. | S2 |
| gaia_archive | ESA Gaia Archive | gaia | heavy_archive_candidate | SYSTEM_SOLAR | https://www.cosmos.esa.int/web/gaia-users/archive | public official archive | source_health_probe_only | 24 h | 25 | official | low | medium | high | medium | heavy_archive_risk | Gaia archive reference, not early ingest. | S10 |
| gaia_programmatic | ESA Gaia programmatic access | gaia | astronomy_catalog_candidate | SYSTEM_SOLAR | https://www.cosmos.esa.int/web/gaia-users/archive/programmatic-access | public official docs | gaia_tap_candidate | disabled | 30 | official | low | medium | high | medium | official_page_seen | Programmatic access candidate with strict caps only. | S10 |
| gaia_archive_endpoint | Gaia archive endpoint | gaia | heavy_archive_candidate | SYSTEM_SOLAR | https://gea.esac.esa.int/archive/ | public official archive | gaia_tap_candidate | disabled | 25 | official | low | medium | high | medium | heavy_archive_risk | Heavy archive source blocked by default. | S10 |
| astroquery_gaia | Astroquery Gaia docs | astroquery | manual_review_only | SYSTEM_SOLAR | https://astroquery.readthedocs.io/en/latest/gaia/gaia.html | public library docs | astroquery_candidate | disabled | 5 | third_party_docs | low | medium | medium | low | candidate_policy_sensitive | Dependency candidate only if later approved; do not add now. | S10 |
| astroquery_simbad | Astroquery SIMBAD docs | astroquery | manual_review_only | SYSTEM_SOLAR | https://astroquery.readthedocs.io/en/stable/simbad/simbad.html | public library docs | astroquery_candidate | disabled | 5 | third_party_docs | low | medium | medium | low | candidate_policy_sensitive | Dependency candidate only if later approved; do not add now. | S10 |
| astroquery_exoplanet_archive | Astroquery Exoplanet Archive docs | astroquery | manual_review_only | SYSTEM_SOLAR | https://astroquery.readthedocs.io/en/latest/ipac/nexsci/nasa_exoplanet_archive.html | public library docs | astroquery_candidate | disabled | 5 | third_party_docs | low | medium | medium | low | candidate_policy_sensitive | Avoid new dependency until explicit approval. | S10 |
| astroquery_tap | Astroquery TAP docs | astroquery | manual_review_only | SYSTEM_SOLAR | https://astroquery.readthedocs.io/en/latest/utils/tap.html | public library docs | astroquery_candidate | disabled | 5 | third_party_docs | low | medium | medium | low | candidate_policy_sensitive | Reference only; no package install. | S10 |
| ads_home | NASA ADS | ads | literature_metadata_candidate | SYSTEM_SOLAR | https://ui.adsabs.harvard.edu/ | public literature portal | source_health_probe_only | 24 h | 20 | official_candidate | low | medium | medium | low | candidate_policy_sensitive | Literature metadata reference, disabled by default. | S10 |
| ads_api_help | NASA ADS API help | ads | auth_required_candidate | SYSTEM_SOLAR | https://ui.adsabs.harvard.edu/help/api/ | public API help | ads_api_candidate | disabled | 25 | official_candidate | low | high | medium | low | auth_required | Token-required metadata candidate; no papers or secrets in repo. | S10 |
| ads_api_docs | NASA ADS API docs | ads | literature_metadata_candidate | SYSTEM_SOLAR | https://ui.adsabs.harvard.edu/help/api/api-docs.html | public API docs | ads_api_candidate | disabled | 25 | official_candidate | low | high | medium | low | auth_required | API docs for later literature metadata design. | S10 |
| science_space_topic | Science space topic | science_mag | science_news | SYSTEM_SOLAR | https://www.science.org/topic/category/space | public publisher page/feed candidate | rss_atom | 6 h | 30 | publisher | low | medium | medium | low | candidate_needs_verification | Science journalism convergence only. | S11 |
| nature_astronomy_subject | Nature astronomy subject | nature | science_news | SYSTEM_SOLAR | https://www.nature.com/subjects/astronomy-and-planetary-science | public publisher page | source_health_probe_only | 24 h | 20 | publisher | low | medium | medium | low | candidate_policy_sensitive | Paywall-sensitive publisher; metadata only. | S11 |
| nature_astronomy_rss | Nature astronomy RSS | nature | science_news | SYSTEM_SOLAR | https://www.nature.com/subjects/astronomy-and-planetary-science.rss | public RSS feed candidate | rss_atom | 6 h | 35 | publisher | low | medium | medium | low | candidate_needs_verification | Science news metadata only, not primary evidence. | S11 |
| scientific_american_space | Scientific American space | scientific_american | science_news | SYSTEM_SOLAR | https://www.scientificamerican.com/space/ | public publisher page/feed candidate | rss_atom | 6 h | 25 | publisher | low | medium | medium | low | candidate_needs_verification | Science journalism convergence only. | S11 |
| sky_telescope_news | Sky and Telescope news | sky_telescope | astronomy_news | SYSTEM_SOLAR | https://skyandtelescope.org/astronomy-news/ | public astronomy news page/feed candidate | rss_atom | 2 h | 35 | publisher | low | medium | medium | low | candidate_needs_verification | Astronomy-specialist news, not primary scientific evidence. | S11 |
| sky_telescope_feed | Sky and Telescope feed | sky_telescope | astronomy_news | SYSTEM_SOLAR | https://skyandtelescope.org/feed/ | public RSS feed | rss_atom | 2 h | 35 | publisher | low | medium | medium | low | candidate_needs_verification | RSS metadata candidate. | S11 |
| astronomy_com_feed | Astronomy.com feed | astronomy_com | astronomy_news | SYSTEM_SOLAR | https://www.astronomy.com/feed/ | public RSS feed | rss_atom | 2 h | 30 | publisher | low | medium | medium | low | candidate_needs_verification | Astronomy news echo only. | S11 |
| universe_today_feed | Universe Today feed | universe_today | astronomy_news | SYSTEM_SOLAR | https://www.universetoday.com/feed/ | public RSS feed | rss_atom | 2 h | 25 | publisher | low | medium | medium | low | candidate_needs_verification | Astronomy news echo only. | S11 |
| planetary_society_feed | Planetary Society RSS | planetary_society | astronomy_news | SYSTEM_SOLAR | https://www.planetary.org/rss.xml | public nonprofit RSS feed | rss_atom | 2 h | 35 | nonprofit | low | medium | medium | low | candidate_needs_verification | Planetary-science public-interest source. | S11 |
| space_com_astronomy | Space.com astronomy | space_com | astronomy_news | SYSTEM_SOLAR | https://www.space.com/astronomy | public publisher page/feed candidate | rss_atom | 2 h | 20 | publisher | low | medium | medium | low | unofficial_secondary | Broad astronomy news echo; hype penalty applies. | S11 |
| arstechnica_science_feed | Ars Technica science feed | ars_technica | science_news | SYSTEM_SOLAR | https://arstechnica.com/science/feed/ | public RSS feed | rss_atom | 2 h | 25 | publisher | low | medium | medium | low | candidate_needs_verification | Science journalism echo only. | S11 |
| bbc_science_rss | BBC science RSS | bbc | public_media_science | SYSTEM_SOLAR | https://feeds.bbci.co.uk/news/science_and_environment/rss.xml | public RSS feed | rss_atom | 2 h | 25 | public_media | low | medium | medium | low | candidate_needs_verification | Public media science convergence only. | S11 |
| npr_science_rss | NPR science RSS | npr | public_media_science | SYSTEM_SOLAR | https://feeds.npr.org/1007/rss.xml | public RSS feed | rss_atom | 2 h | 25 | public_media | low | medium | medium | low | candidate_needs_verification | Public media science convergence only. | S11 |
| pbs_science_rss | PBS science RSS | pbs | public_media_science | SYSTEM_SOLAR | https://www.pbs.org/newshour/feeds/rss/science | public RSS feed | rss_atom | 2 h | 25 | public_media | low | medium | medium | low | candidate_needs_verification | Public media science convergence only. | S11 |
| reddit_space | Reddit r/space | reddit | social_candidate | SYSTEM_SOLAR | https://www.reddit.com/r/space/ | platform community page/API candidate | manual_review_only | disabled | 5 | platform | high | high | high | high | candidate_policy_sensitive | Community echo only through compliant API access. | S12 |
| reddit_astronomy | Reddit r/astronomy | reddit | social_candidate | SYSTEM_SOLAR | https://www.reddit.com/r/astronomy/ | platform community page/API candidate | manual_review_only | disabled | 4 | platform | high | high | high | high | candidate_policy_sensitive | Community echo only through compliant API access. | S12 |
| reddit_spaceporn | Reddit r/spaceporn | reddit | social_candidate | SYSTEM_SOLAR | https://www.reddit.com/r/spaceporn/ | platform community image page/API candidate | manual_review_only | disabled | 0 | platform | high | high | high | high | reject_for_now | Image feed is low-value for this metadata dashboard. | S12 |
| x_nasa_universe | X NASA Universe account | x_api | social_candidate | SYSTEM_SOLAR | https://x.com/NASAUniverse | platform account/API candidate | manual_review_only | disabled | 5 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Official-account echo only if compliant API is configured. | S12 |
| x_nasa_exoplanets | X NASA Exoplanets account | x_api | social_candidate | SYSTEM_SOLAR | https://x.com/NASAExoplanets | platform account/API candidate | manual_review_only | disabled | 5 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Official-account echo only if compliant API is configured. | S12 |
| x_ligo | X LIGO account | x_api | social_candidate | SYSTEM_SOLAR | https://x.com/LIGO | platform account/API candidate | manual_review_only | disabled | 5 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Official-account echo only if compliant API is configured. | S12 |
| bluesky_jwst_exoplanet | Bluesky JWST exoplanet search | bluesky | social_candidate | SYSTEM_SOLAR | https://bsky.app/search?q=JWST%20exoplanet | platform search/API candidate | manual_review_only | disabled | 3 | platform | high | high | high | high | candidate_policy_sensitive | Broad social search is disabled and low-weight at most. | S12 |
| bluesky_supernova | Bluesky supernova search | bluesky | social_candidate | SYSTEM_SOLAR | https://bsky.app/search?q=supernova | platform search/API candidate | manual_review_only | disabled | 3 | platform | high | high | high | high | candidate_policy_sensitive | Social echo only after AT Protocol and retention review. | S12 |
| system_solar_fixture_pack | SYSTEM_SOLAR local fixture pack | local_fixture | manual_review_only | SYSTEM_SOLAR | tests/fixtures/system_solar/ | local repository fixtures | local_file_fixture | none | 0 | fixture | low | low | low | low | assistant_seeded | Fixture-only parser development target; must never fetch network. | S3 |
| rfc9309_robots | RFC 9309 Robots Exclusion Protocol | policy_reference | source_health_only | SYSTEM_SOLAR | https://www.rfc-editor.org/rfc/rfc9309.html | public standards reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | Policy reference for robots handling. | S2 |
| rss_specification | RSS specification | policy_reference | source_health_only | SYSTEM_SOLAR | https://www.rssboard.org/rss-specification | public standards reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | RSS parser reference. | S2 |
| schema_newsarticle | Schema.org NewsArticle | policy_reference | source_health_only | SYSTEM_SOLAR | https://schema.org/NewsArticle | public schema reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | Metadata vocabulary reference. | S2 |
| reddit_terms | Reddit developer/API terms | policy_reference | source_health_only | SYSTEM_SOLAR | https://redditinc.com/policies/data-api-terms | public platform policy | manual_review_only | none | 0 | reference | low | high | low | low | candidate_policy_sensitive | Must be reviewed before Reddit source enablement. | S12 |
| x_api_docs | X API docs | policy_reference | source_health_only | SYSTEM_SOLAR | https://docs.x.com/x-api/introduction | public platform API docs | manual_review_only | none | 0 | reference | low | high | low | low | candidate_policy_sensitive | Must be reviewed before X source enablement. | S12 |
| bluesky_atproto_docs | Bluesky AT Protocol docs | policy_reference | source_health_only | SYSTEM_SOLAR | https://docs.bsky.app/docs/api/at-protocol-xrpc-api | public platform API docs | manual_review_only | none | 0 | reference | low | medium | low | low | candidate_policy_sensitive | Reference for possible compliant Bluesky adapter. | S12 |

## SECTION 6: Source admission tiers

Tier 0 - local fixtures only:

- No network.
- Used for tests.
- Best for parser contracts, source-health states, ranking, scope-routing, hype suppression, and
  retention behavior.

Tier 1 - official agency RSS, official science news feeds, official mission updates, and small
official JSON APIs:

- Best first live candidates after fixtures and disabled-by-default config exist.
- Candidate sources: JPL RSS, NASA RSS, ESA RSS, Hubble/JWST RSS, STScI news, ESO RSS, NOIRLab RSS.
- Store headline metadata only.

Tier 2 - public astronomy alert feeds and official transient alert sources:

- Candidate sources: GCN notices, GCN circulars, ATel RSS, TNS, GraceDB/LIGO public alerts.
- Must be disabled by default until fixture parsing, preliminary/retraction handling, and
  sensitivity rules exist.

Tier 3 - official science archive APIs used only for small metadata checks:

- Candidate sources: Exoplanet Archive, MAST, HEASARC, PDS, MPC, JPL SSD.
- Must use strict allowlists, row caps, query caps, timeouts, and no bulk data downloads.

Tier 4 - scientific institution RSS and observatory news:

- Candidate sources: ESA, ESO, NOIRLab, NRAO, ALMA, STScI, JAXA, ISRO, CSA, NAOJ, SKAO.
- Store headline metadata only.

Tier 5 - science journalism and public media:

- Candidate sources: Science, Nature RSS, Scientific American, Sky and Telescope, Astronomy.com,
  Universe Today, Planetary Society, Space.com, Ars Technica, BBC, NPR, PBS.
- Store headline metadata only.
- No article-body archive.
- No paywall bypass.
- These sources are convergence/echo signals, not primary scientific evidence.

Tier 6 - heavy archive or catalog candidates:

- Candidate sources: Gaia, SIMBAD, VizieR, ESASky, ESO Archive, ADS, MAST bulk services, PDS bulk
  archives, HEASARC broad archive searches.
- Disabled by default.
- Fixture-only or source-health-only until a narrow use case exists.
- Do not ingest catalogs.

Tier 7 - auth-required sources:

- Candidate sources: ADS API, TNS API, some GraceDB or VO services, and any endpoint requiring
  account, token, API key, or special client.
- Disabled by default.
- Credentials must live outside the repo.
- Source health must report `auth_required`.

Tier 8 - social/community signals:

- Candidate sources: Reddit, X, Bluesky.
- Policy-sensitive and disabled by default.
- Reddit only through compliant official API or permitted feed access.
- X only through official API access if explicitly configured.
- Bluesky only through official AT Protocol later.
- No HTML scraping to bypass platform restrictions.

Tier 9 - manual-review-only sources:

- Anything with unclear terms, high parser risk, high volume, science hype risk, login walls,
  paywalls, bot controls, or ambiguous licensing.

## SECTION 7: Solar System and Beyond event model

The system should not only store news items. It should infer that multiple recent items refer to the
same cosmic, planetary, telescope, mission, or astronomy event. This can be implemented as a future
`solar_system_beyond_events` table or as a scope-specific extension of `news_clusters` if the common
recent-signal schema has already landed.

Candidate event fields:

| Field | Purpose |
| --- | --- |
| `cosmic_event_id` | Internal integer primary key. |
| `scope` | Working scope, initially `SYSTEM_SOLAR` or the chosen future label. |
| `proposed_scope_label` | User-facing label candidate, such as COSMIC or SOLAR. |
| `event_key` | Deterministic key from event ids, object ids, coordinates, source families, and title tokens. |
| `event_type` | Controlled event type. |
| `title` | Human-readable event title from representative item. |
| `representative_item_id` | Item used for primary display. |
| `severity` | `info`, `notice`, `attention`, or similar local enum. |
| `scientific_significance_score` | Source-backed scientific importance. |
| `public_interest_score` | User-facing interest without hype. |
| `source_diversity_score` | Independent source-family diversity. |
| `official_confirmation_score` | Official agency, observatory, archive, or alert-network confirmation. |
| `mission_relevance_score` | Mission/telescope/instrument relevance. |
| `discovery_score` | First detection, confirmation, or discovery basis. |
| `rarity_score` | Rarity basis for transients, exoplanets, discoveries, or data releases. |
| `transient_score` | GCN, ATel, TNS, GraceDB, FRB, GRB, supernova, or related signal. |
| `exoplanet_score` | Exoplanet discovery, atmosphere, catalog, or mission basis. |
| `planetary_science_score` | Solar-system mission or planetary-body basis. |
| `observatory_score` | Telescope/observatory science-release basis. |
| `peer_review_or_agency_score` | Agency or peer-review metadata basis if enabled. |
| `social_echo_score` | Low-weight social echo only if configured. |
| `news_echo_score` | Science journalism or public-media convergence. |
| `orbital_overlap_score` | ORBITAL relationship tag, not duplicate inflation. |
| `global_impact_score` | Terrestrial global impact tag when relevant. |
| `local_sky_interest_score` | Local/regional sky-viewing interest tag when relevant. |
| `first_seen_at` | First local observation time. |
| `last_seen_at` | Last local observation time. |
| `last_elevated_at` | Last time the event crossed attention threshold. |
| `expires_at` | Retention purge time. |
| `objects_json` | Stars, galaxies, planets, moons, asteroids, comets, or named sources. |
| `missions_json` | Mission names and spacecraft. |
| `instruments_json` | Instruments where source-provided. |
| `observatories_json` | Telescope or facility names. |
| `agencies_json` | NASA, ESA, STScI, ESO, LIGO, and other source agencies. |
| `sky_coordinates_json` | Source-provided coordinates, localizations, or sky regions. |
| `solar_system_body_json` | Planetary body, moon, asteroid, comet, or solar target metadata. |
| `exoplanet_system_json` | Planet, host star, system, method, and status metadata. |
| `transient_ids_json` | GCN ids, ATel numbers, TNS names, GraceDB superevent ids, or similar. |
| `source_ids_json` | Contributing source ids. |
| `item_ids_json` | Contributing normalized item ids. |
| `evidence_json` | Source and parser evidence. |
| `ranking_explanation_json` | Deterministic scoring features and penalties. |
| `status` | `candidate`, `active`, `confirmed`, `preliminary`, `retracted`, `stale`, or `suppressed`. |

Controlled event types should include at least:

- `planetary_mission_science`
- `planetary_body_update`
- `interplanetary_mission_milestone`
- `solar_science_discovery`
- `exoplanet_discovery`
- `exoplanet_atmosphere_result`
- `exoplanet_catalog_update`
- `major_telescope_release`
- `jwst_science_release`
- `hubble_science_release`
- `roman_mission_update`
- `tess_discovery_update`
- `gaia_data_release`
- `pds_data_release`
- `astronomy_archive_release`
- `gamma_ray_burst`
- `gravitational_wave_candidate`
- `gravitational_wave_confirmed`
- `supernova_candidate`
- `supernova_confirmed`
- `nova`
- `kilonova_candidate`
- `fast_radio_burst`
- `neutrino_candidate`
- `multi_messenger_event`
- `astronomical_transient`
- `comet_science_update`
- `minor_planet_science_update`
- `stellar_event`
- `galactic_center_event`
- `galaxy_discovery`
- `cosmology_result`
- `black_hole_result`
- `observatory_status_update`
- `major_science_publication`
- `source_health_problem`
- `community_signal`

Routine low-impact science news should not automatically become elevated. The event layer should
separate "seen and stored as metadata" from "ranked as worth attention."

## SECTION 8: Cross-source convergence ranking

Ranking must be deterministic and explainable. The core idea is that an item appearing in official
agency feeds, science archive metadata, transient alert networks, observatory feeds, science
journalism, and community/social signals within a short window is more likely to be important or
interesting than a lone generic article. "Frequency of appearance" means independent cross-source
convergence, not raw duplicate counts.

Required scoring factors:

1. Official or scientific provenance.

Examples include NASA/JPL/ESA/STScI official releases, mission blog updates, NASA Exoplanet Archive
metadata, GCN notices or circulars, ATel items, TNS items if configured, LIGO/Virgo/KAGRA public
alerts, PDS releases, MPC/MPEC items, peer-reviewed source metadata if allowed, and observatory
official releases.

2. Source diversity.

Independent source families count more than repeated mentions from the same family. Candidate
families include `nasa_science`, `nasa_jpl`, `nasa_blogs`, `nasa_exoplanet_archive`, `mast`,
`stsci`, `hubble`, `webb`, `roman`, `tess`, `pds`, `esa`, `jaxa`, `isro`, `csa`, `eso`, `noirlab`,
`nrao`, `alma`, `mpc`, `jpl_ssd`, `gcn`, `atel`, `tns`, `ligo`, `virgo`, `kagra`, `heasarc`,
`simbad`, `vizier`, `gaia`, `ads`, `science_journalism`, `public_media_science`, `reddit`,
`bluesky`, `x_api`, and `source_health`.

3. Temporal proximity.

Proposed matching windows:

| Source/event kind | Matching window |
| --- | --- |
| Agency science release | 0 to 7 days |
| Mission update | 0 to 14 days |
| Exoplanet discovery | 0 to 14 days |
| Exoplanet catalog update | 0 to 30 days if configured |
| GCN alert | 0 to 72 hours |
| GCN circular follow-up | 0 to 14 days |
| ATel transient | 0 to 14 days |
| TNS transient | 0 to 14 days |
| Gravitational-wave candidate | Alert time through 14 days |
| Major telescope data release | 0 to 30 days |
| PDS/archive release | 0 to 30 days |
| Science article or paper metadata | 0 to 14 days if enabled |
| Routine news | 0 to 7 days |

4. Object, mission, and coordinate proximity.

Match by mission name, telescope, instrument, source event id, transient name, TNS name, GCN event
id, GraceDB superevent id, ATel number, planet name, star name, exoplanet system, solar system
body, asteroid/comet designation, coordinates, sky localization, DOI or bibcode if enabled, archive
collection id, and dataset id.

5. Scientific significance.

Boost first detection or confirmation, official agency release, cross-observatory confirmation,
multi-messenger event, nearby supernova, gravitational-wave candidate with public alert, gamma-ray
burst with multiple follow-ups, exoplanet atmosphere detection, Earth-size or habitable-zone
exoplanet only if the source says so, solar system mission discovery, major telescope milestone,
major public data release, widely covered peer-reviewed discovery, and events with ORBITAL, GLOBAL,
NATIONAL, REGIONAL, or LOCAL impact tags.

6. Recency.

Recent items matter more, but major discoveries can stay elevated for a short configured period.

7. User-configured priority.

Future config can boost planetary science, exoplanets, JWST, Hubble, Roman, TESS, Gaia, Mars,
Europa, Titan, Enceladus, astrobiology, gravitational waves, gamma-ray bursts, supernovae, black
holes, cosmology, telescope data releases, NASA, ESA, JPL, STScI, ESO, LIGO, ATel, and GCN.

8. Low-public-value penalty.

De-emphasize generic astronomy explainers, low-significance press releases, routine archive
maintenance, routine catalog row changes, duplicate news rewrites, single-source hype, social-only
claims, alien-life speculation without credible source support, preliminary transients with no
follow-up, data-heavy sources outside allowlist, and old papers resurfaced as if new.

9. Hype and speculation penalty.

De-emphasize or block alien megastructure claims unless official or peer-reviewed and carefully
labeled, "life found" claims unless an official or peer-reviewed source says that, sensationalized
headlines not supported by source evidence, UFO conflation, social rumors, unreviewed preprint hype
if literature sources are ever enabled, and image-only clickbait.

Sample formula:

```text
score =
  recency_score
  + official_science_score
  + scientific_significance_score
  + source_diversity_score
  + mission_relevance_score
  + rarity_score
  + transient_score
  + public_interest_score
  + source_priority_score
  + cluster_size_score
  + local_or_global_impact_score
  - duplicate_family_penalty
  - stale_source_penalty
  - low_confidence_penalty
  - low_public_value_penalty
  - hype_penalty
  - out_of_scope_penalty
  - archive_firehose_penalty
```

Bad ranking:

- Thirty rewrites of the same generic "black holes are weird" article dominate.

Good ranking:

- GCN alert for a gamma-ray burst.
- Follow-up GCN circulars.
- Swift, Fermi, or other mission source.
- ATel follow-up.
- Observatory release or credible science outlet.
- All tied by event id, coordinates, and time.

## SECTION 9: Source category design

Every category must define why it exists, first safe sources, adapter class, refresh interval, risk,
source-health signals, sample fields, ranking contribution, and later phase.

| Category | Why it exists | First safe sources | Parser/adaptor class | Refresh interval | Risks | Source-health signals | Sample item fields | Ranking contribution | Phase |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Planetary science and solar system missions | Captures mission science and planetary-body discoveries beyond operational ORBITAL events. | JPL RSS, NASA Solar System news, mission pages as source-health only. | `rss_atom`, `static_html_headline_candidate`, `source_health_probe_only` | 60 min for RSS, 24 h for source health | Privacy low, policy low, parser medium | disabled, stale, parser_failed, policy_blocked | title, URL, body, mission, target body, instrument, published time | Strong official science and mission relevance boost. | S7 |
| Planetary data archives and mission data releases | Surfaces small metadata signals about official archive releases without downloading products. | PDS API fixtures, PDS subscription candidates. | `pds_api_candidate`, `source_health_probe_only`, `manual_review_only` | 24 h or disabled | Privacy low, policy medium, parser high | heavy_archive_disabled, needs_scope_filter, archive_firehose_blocked | collection id, release id, mission, target, no-products-downloaded flag | Moderate boost when tied to mission or agency release. | S8/S10 |
| Minor bodies, comet science, and small-body science context | Adds comet/asteroid science without duplicating ORBITAL close-approach alerts. | MPC MPEC API docs, JPL SSD SBDB, NASA comet/asteroid pages. | `mpc_api`, `jpl_ssd_api`, `source_health_probe_only` | 6 h to 24 h | Privacy low, policy low/medium, parser medium | needs_scope_filter, stale, parser_failed | designation, object type, event time, source id, ORBITAL overlap | Boosts science updates; ORBITAL owns hazard/operations. | S8 |
| Exoplanets and planetary systems | Tracks confirmed or agency-backed exoplanet discoveries and major updates. | NASA Exoplanet Archive tiny fixture, NASA/TESS/JWST releases. | `exoplanet_archive_api`, `tap_adql_candidate`, `rss_atom` | 6 h to 24 h | Privacy low, policy medium, parser high for TAP | heavy_archive_disabled, needs_scope_filter, stale | planet, host star, status, discovery method, source URL | High boost for confirmed, agency-backed, atmosphere, or high-interest source-provided terms. | S8/S10 |
| Space telescopes and observatory science releases | Covers JWST, Hubble, Roman, TESS, STScI, ESO, NOIRLab, NRAO, and ALMA releases. | Hubble RSS, Webb RSS, STScI news, ESO RSS, NOIRLab RSS. | `rss_atom`, `static_html_headline_candidate`, `mast_api_candidate` | 60 min for feeds, disabled for archives | Privacy low, policy low/medium, parser medium/high | disabled, stale, parser_failed, heavy_archive_disabled | observatory, telescope, instrument, release id, title, URL | Strong boost for official telescope science releases. | S7/S10 |
| High-energy astrophysics and GCN | Handles gamma-ray bursts and high-energy transient alerts. | GCN fixtures, Swift/Fermi source-health pages, HEASARC fixtures. | `gcn_notice_candidate`, `gcn_circular_candidate`, `heasarc_api_candidate` | 5 to 30 min if enabled | Privacy low, policy medium, parser high | preliminary, retracted, parser_failed, stale | notice id, event id, instrument, coordinates, alert status | Strong transient and rarity boost, with preliminary/retraction labels. | S9 |
| Gravitational-wave and multi-messenger astronomy | Captures LVK public alerts and follow-up convergence without downloading sky maps. | GraceDB fixtures, LIGO/Virgo/KAGRA news, GWOSC event API fixtures. | `gracedb_api_candidate`, `official_api_json`, `rss_atom` | 5 min to 24 h if enabled | Privacy low, policy medium/high, parser high | auth_required, policy_blocked, preliminary, retracted | superevent id, false alarm rate if source-provided, alert type, status | Very high rarity and multi-messenger boost when official and unretracted. | S9 |
| Transient astronomy, supernovae, novae, and ATel/TNS | Tracks astronomical transient reports with careful preliminary labeling. | ATel RSS fixture, TNS auth-required fixture, GCN circulars. | `astronomers_telegram_rss`, `tns_api_candidate`, `gcn_circular_candidate` | 30 to 60 min if enabled | Privacy low, policy medium/high, parser medium/high | auth_required, manual_review_only, stale, retracted | transient name, ATel number, TNS name, coordinates, classification | High boost when independent alert families converge. | S9 |
| Astronomy archive and catalog candidates | Supports narrow metadata lookups without becoming a catalog mirror. | SIMBAD, VizieR, Gaia, ESASky, ESO Archive as source-health/manual-review only. | `simbad_tap_candidate`, `vizier_tap_candidate`, `gaia_tap_candidate`, `tap_adql_candidate` | disabled | Privacy low, policy medium, parser high | heavy_archive_disabled, needs_scope_filter, archive_firehose_blocked | object id, catalog id, row cap, query bounds | Low boost; evidence enrichment only unless configured. | S10 |
| Literature metadata candidates | Optional later metadata about papers without paper downloads or review-engine behavior. | ADS API docs, Nature/Science RSS as journalism metadata. | `ads_api_candidate`, `rss_atom`, `manual_review_only` | disabled or 24 h | Privacy low, policy high for auth/paywalls, parser medium | auth_required, policy_blocked, manual_review_only | title, authors, bibcode, DOI, URL, no paper body | Peer-review metadata can boost only when enabled and bounded. | S10 |
| International observatory and agency feeds | Adds independent source-family diversity beyond NASA. | ESA RSS, JAXA, ISRO, CSA, ESO, NOIRLab, ALMA, NAOJ. | `rss_atom`, `static_html_headline_candidate` | 60 min to 6 h | Privacy low, policy low/medium, parser medium | disabled, stale, parser_failed | title, URL, agency, observatory, published time | Source-diversity and official-science boost. | S7 |
| Science journalism and public media | Gives public-interest echo without replacing official evidence. | BBC, NPR, PBS, Sky and Telescope, Planetary Society, Science, Nature RSS. | `rss_atom` | 2 to 6 h | Privacy low, policy medium, parser medium | stale, parser_failed, policy_blocked | title, URL, publisher, description, published time | News echo only; duplicate-family penalty prevents inflation. | S11 |
| Social/community echoes | Optional low-weight signal after policy review. | Reddit API candidates, X API candidates, Bluesky AT Protocol candidates. | `manual_review_only` initially | disabled | Privacy high, policy high, parser high | social_disabled, auth_required, policy_blocked | post/account/search metadata if allowed, no long archive | Very low weight; never primary evidence. | S12 |
| Source health and disabled states | Keeps the UI honest about unsupported, disabled, stale, auth-required, and heavy sources. | All configured and candidate sources. | `source_health_probe_only`, `local_file_fixture` | local only until enabled | Privacy low, policy low unless probes run | disabled, not_configured, naming_collision_unresolved, heavy_archive_disabled | source id, state, last success, message, evidence | Can lower ranking through stale or blocked source penalties. | S2/S3 |

## SECTION 10: Science, hype, and sensitivity posture

Rules:

- Store source-provided public metadata only.
- Do not store full article bodies.
- Do not download science data products.
- Do not bulk-ingest catalogs.
- Do not archive social posts long term.
- Do not treat social claims as verified fact.
- Do not invent scientific meaning.
- Do not interpret papers beyond metadata.
- Do not turn console-1706 into a literature review engine.
- Do not turn console-1706 into an observatory archive mirror.
- Do not amplify alien-life or UFO claims without strict source framing.
- Do not use "life found" unless an official or peer-reviewed source says it directly.
- Prefer official agency, observatory, mission, and recognized alert-network source labels.
- For transient alerts, label preliminary status clearly.
- For gravitational-wave candidates, preserve alert status and retraction status if provided.
- For exoplanets, distinguish candidate, confirmed, archive update, paper claim, and agency release.
- For telescope science, distinguish image release, data release, peer-reviewed result, mission
  update, and press release.
- For science journalism, treat it as news metadata, not primary scientific evidence.
- Preserve source links in evidence so the user can click official sources.

Hype handling:

- `hype_blocked` should suppress claims that conflate astronomy with UFO material.
- "Life found" language is blocked unless the exact source metadata or official headline supports
  that phrasing.
- Alien-life, biosignature, or technosignature language should be preserved only when source
  provided and should be displayed with source labels and confidence status.
- Social-only claims never promote an event above official or scientific sources.

## SECTION 11: Source freshness and retention

Solar System and Beyond is a short-retention recent-signal layer, not a permanent archive.

Default candidate retention:

| Data | Default retention |
| --- | --- |
| Raw fetch diagnostics | 7 days or less |
| Raw payload debug | Disabled by default; 6 hours max if enabled |
| Agency science release metadata | 7 days |
| Mission update metadata | 7 to 14 days |
| Planetary mission science metadata | 14 days |
| Exoplanet discovery metadata | 14 to 30 days |
| Exoplanet catalog-update metadata | 7 days unless configured |
| GCN notice metadata | 7 to 14 days |
| GCN circular metadata | 14 days |
| ATel metadata | 14 days |
| TNS metadata | 14 days if enabled |
| Gravitational-wave alert metadata | 14 to 30 days, with retraction/follow-up state |
| Telescope data release metadata | 14 to 30 days |
| PDS/archive release metadata | 14 to 30 days |
| Literature metadata | Disabled by default; 7 to 14 days if enabled |
| News headline metadata | 7 days |
| Event clusters | 7 to 14 days, 30 days for major confirmed discoveries if configured |
| Source health | 30 days |
| Ranking explanations | Same as event/item retention |
| Social metadata | 24 to 72 hours if ever enabled, unless terms require shorter or prohibit storage |

Every ingest run in later phases must purge expired data. There must be no article body archive, no
bulk astronomy data archive, and no permanent social archive.

## SECTION 12: Adapter design

Do not implement adapters in this task. Future adapters should be pure parser/normalizer units
against local fixtures before any live fetch exists.

`rss_atom`

- Targets: NASA RSS, JPL RSS, ESA RSS, STScI/Hubble/JWST feeds, ESO feeds, NOIRLab feeds, science
  journalism feeds.
- Must parse title, URL, published timestamp, source-provided description, and categories.
- Must bound description length.
- Must not fetch article bodies.

`nasa_api_json`

- Targets: NASA Open APIs only when a specific useful source is configured.
- Avoid imagery-heavy APIs unless needed.
- Respect API key handling.
- Do not store API keys in repo.

`pds_api_candidate`

- Targets: NASA PDS API.
- Use only for metadata-level recent data release checks.
- Do not download science products.
- Do not bulk mirror PDS.
- Require collection allowlists and row caps.

`exoplanet_archive_api`

- Targets: NASA Exoplanet Archive API or TAP-backed metadata queries.
- Use only allowlisted metadata queries.
- Distinguish candidate vs confirmed when source provides it.
- Do not run broad catalog downloads.

`mast_api_candidate`

- Targets: MAST API for mission metadata and configured small queries.
- Must not download science products.
- Must avoid broad catalog searches.
- Use fixture-only until a narrow query contract exists.

`heasarc_api_candidate`

- Targets: HEASARC source for high-energy mission metadata.
- Must verify current machine-readable endpoint.
- Use fixture-only until a narrow query contract exists.

`gcn_notice_candidate`

- Targets: NASA GCN notices.
- Must preserve notice type, event id, coordinates if provided, event time, instrument, alert
  status, and source URL.
- Must handle preliminary, update, and retraction states.
- Must not require Kafka dependency initially unless later approved.
- Fixture-first.

`gcn_circular_candidate`

- Targets: GCN Circulars.
- Use only if a machine-readable or policy-safe endpoint exists.
- Store metadata only.
- Do not scrape if not allowed.
- Fixture/manual-review first.

`astronomers_telegram_rss`

- Targets: Astronomers Telegram RSS.
- Store telegram metadata and URL.
- Do not store full body unless source allows and the user explicitly configures bounded storage.
- Treat as preliminary astronomy communication.

`tns_api_candidate`

- Targets: TNS API.
- Auth/account/policy-sensitive.
- Disabled by default.
- Must require credentials outside repo if needed.
- Preserve object name, type, discovery date, reporter, classification, and source URL when allowed.
- Do not bulk ingest.

`gracedb_api_candidate`

- Targets: GraceDB / LIGO public alert candidate.
- May require special client/dependency or API rules.
- Disabled by default.
- Preserve public alert id, event id, alert type, false-alarm rate if source provides it,
  retraction status, sky map URL metadata only, and source URL.
- Do not download sky maps by default.
- Fixture-first.

`tap_adql_candidate`

- Targets: Gaia, SIMBAD, VizieR, ESASky, ESO Archive, and other TAP/ADQL sources.
- Heavy-source risk.
- Disabled by default.
- Must require strict query allowlists, row limits, timeout, and no bulk downloads.

`simbad_tap_candidate`

- Targets: SIMBAD TAP.
- Use only for object-name cross-identification in event evidence if later needed.
- Do not bulk query.
- Cache only short metadata.

`vizier_tap_candidate`

- Targets: VizieR TAP.
- Use only for specific catalog metadata if later needed.
- Do not bulk query.

`gaia_tap_candidate`

- Targets: Gaia Archive TAP.
- Disabled by default.
- Use only for narrow configured science-release checks, if ever.
- Do not bulk query.

`ads_api_candidate`

- Targets: NASA ADS API.
- Auth token likely required.
- Disabled by default.
- Use only for literature metadata if explicitly configured.
- Do not download papers.
- Do not turn app into a literature-monitoring system.

`mpc_api`

- Targets: MPC MPECs, NEOCP, observations, orbits, and designation APIs.
- Must verify exact endpoints and usage guidance.
- Store metadata only.
- Avoid high-volume ingestion unless strictly filtered.

`jpl_ssd_api`

- Targets: JPL SSD/CNEOS APIs.
- Reuse from ORBITAL where useful for science context.
- Must avoid duplicate event inflation between ORBITAL and Solar System and Beyond.

`official_api_json`

- Targets: Other official JSON endpoints from observatories/agencies.
- Must use timeouts, response size caps, source-specific rate limits, and fail-soft source health.

`static_html_headline_candidate`

- Targets: official pages or science news pages with no RSS/API.
- Disabled unless homepage extractor support is explicitly allowed.
- Must use per-source selectors.
- No recursive crawling.
- No article-body fetch.
- Robots and policy review required.

`source_health_probe_only`

- Targets: dashboards and portals useful as human status references but not suitable for ingestion.
- Page loads must not run probes.

`local_file_fixture`

- Targets: fixture files under a future `tests/fixtures/system_solar/` path.
- Must never fetch the network.
- Must cover parser, ranking, source health, auth-required, heavy-archive, and hype-blocked states.

`manual_review_only`

- Targets: policy-sensitive, parser-risky, login-required, auth-required, account-required,
  paywalled, heavy-catalog, or unclear targets.
- These can exist in registry/docs but cannot produce live items.

## SECTION 13: Candidate source registry example

Do not edit `config.example.yml` for this design pass. A later implementation can add disabled
examples after the common recent-signal registry exists and the naming decision is made.

```yaml
solar_system_beyond_sources:
  enabled: false
  label: "Solar System and Beyond"
  final_scope_label: "TBD"
  naming_collision_with_system: true
  retention:
    agency_science_release_days: 7
    mission_update_days: 14
    planetary_science_days: 14
    exoplanet_days: 30
    transient_days: 14
    gravitational_wave_days: 30
    telescope_release_days: 14
    archive_release_days: 30
    headline_days: 7
    event_cluster_days: 14
    source_health_days: 30
    raw_payload_debug_enabled: false
    raw_payload_debug_ttl_hours: 6
  ranking:
    source_diversity_weight: 3.0
    official_science_weight: 3.25
    scientific_significance_weight: 3.0
    mission_relevance_weight: 2.5
    rarity_weight: 2.5
    transient_weight: 2.25
    public_interest_weight: 1.5
    recency_weight: 2.0
    social_echo_weight: 0.25
    low_public_value_penalty_weight: 3.0
    hype_penalty_weight: 4.0
    archive_firehose_penalty_weight: 4.0
  safety:
    no_bulk_catalog_ingest: true
    no_science_product_downloads: true
    no_article_body_archive: true
    suppress_alien_life_hype: true
    social_retention_hours: 48
    social_sources_disabled_by_default: true
    heavy_archive_sources_disabled_by_default: true
    auth_sources_disabled_by_default: true
  sources:
    - id: nasa_science_solar_system_news
      enabled: false
      source_family: nasa_science
      source_class: official_planetary_science
      adapter: rss_atom
      homepage_url: "https://science.nasa.gov/solar-system/news/"
      priority: 85
      interval_minutes: 60
      verification_status: candidate_needs_verification
      evidence_notes: "Prefer official NASA RSS if available. Store headline metadata only."
    - id: jpl_news
      enabled: false
      source_family: nasa_jpl
      source_class: official_planetary_science
      adapter: rss_atom
      homepage_url: "https://www.jpl.nasa.gov/news/"
      url: "https://www.jpl.nasa.gov/rss/"
      priority: 90
      interval_minutes: 60
      verification_status: official_page_seen
    - id: nasa_exoplanet_archive
      enabled: false
      source_family: nasa_exoplanet_archive
      source_class: official_exoplanet_archive
      adapter: exoplanet_archive_api
      homepage_url: "https://exoplanetarchive.ipac.caltech.edu/"
      url: "https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html"
      priority: 80
      interval_minutes: 360
      verification_status: official_page_seen
      filters:
        confirmed_only: true
        row_limit: 100
      notes: "No broad catalog downloads. Use only allowlisted metadata queries."
    - id: nasa_gcn_notices
      enabled: false
      source_family: gcn
      source_class: official_transient_alert
      adapter: gcn_notice_candidate
      homepage_url: "https://gcn.nasa.gov/"
      url: "https://gcn.nasa.gov/docs/notices"
      priority: 95
      interval_minutes: 5
      verification_status: official_page_seen
      notes: "Fixture-first. Preserve preliminary/update/retraction status."
    - id: astronomers_telegram_rss
      enabled: false
      source_family: atel
      source_class: official_transient_alert
      adapter: astronomers_telegram_rss
      homepage_url: "https://www.astronomerstelegram.org/"
      url: "https://www.astronomerstelegram.org/?rss"
      priority: 80
      interval_minutes: 30
      verification_status: official_page_seen
    - id: tns_transients
      enabled: false
      source_family: tns
      source_class: official_supernova_transient
      adapter: tns_api_candidate
      homepage_url: "https://www.wis-tns.org/"
      url: "https://www.wis-tns.org/content/tns-getting-started"
      priority: 75
      interval_minutes: 60
      verification_status: auth_required
      notes: "Disabled by default. Requires policy/auth review and credentials outside repo."
    - id: ligo_gracedb_public_alerts
      enabled: false
      source_family: ligo
      source_class: official_gravitational_wave
      adapter: gracedb_api_candidate
      homepage_url: "https://gracedb.ligo.org/"
      url: "https://rtd.igwn.org/projects/userguide/en/v3/index.html"
      priority: 90
      interval_minutes: 5
      verification_status: candidate_policy_sensitive
      notes: "Fixture-first. Preserve retraction/preliminary state. Do not download sky maps."
    - id: esa_science_rss
      enabled: false
      source_family: esa
      source_class: official_science_release
      adapter: rss_atom
      homepage_url: "https://www.esa.int/Services/RSS_Feeds"
      priority: 75
      interval_minutes: 60
      verification_status: official_page_seen
    - id: pds_api_metadata
      enabled: false
      source_family: pds
      source_class: official_planetary_data_archive
      adapter: pds_api_candidate
      homepage_url: "https://pds.nasa.gov/"
      url: "https://nasa-pds.github.io/pds-api/"
      priority: 60
      interval_minutes: 1440
      verification_status: official_page_seen
      notes: "Metadata-only, strict allowlists, no data product downloads."
    - id: ads_api_literature_metadata
      enabled: false
      source_family: ads
      source_class: literature_metadata_candidate
      adapter: ads_api_candidate
      homepage_url: "https://ui.adsabs.harvard.edu/"
      url: "https://ui.adsabs.harvard.edu/help/api/"
      priority: 35
      interval_minutes: 1440
      verification_status: auth_required
      notes: "Disabled by default. Metadata-only if enabled. No paper downloads."
```

## SECTION 14: UI architecture

Do not implement UI in this task. Because `SYSTEM` may already mean app-health, this section
describes a future candidate page only.

Candidate page goals:

- Use the same console-1706 dense local dashboard style.
- Show honest disabled/not-configured states.
- Preserve app-health SYSTEM until a naming decision is made.
- Never show fake headlines.

Proposed four bays:

| Bay | Name | Purpose |
| --- | --- | --- |
| 1 | Cosmic attention now | Highest-ranking events from solar system, exoplanet, transient, telescope, and astrophysics sources. Show ranking reasons, source-family badges, official/science/news/community convergence, observed time, and last seen. |
| 2 | Solar system and planetary science | NASA, JPL, ESA, JAXA, ISRO, PDS, MPC, JPL SSD, planetary missions, solar system bodies, mission science, planetary data releases, comet/asteroid science. |
| 3 | Beyond the solar system | Exoplanets, JWST, Hubble, Roman, TESS, Gaia, MAST, HEASARC, ESO, NOIRLab, NRAO, ALMA, SIMBAD/VizieR candidates, telescope science, galaxies, cosmology, and stellar events. |
| 4 | Transient alerts and source health | GCN, ATel, TNS, LIGO/GraceDB, transient candidates, source health, disabled auth-heavy sources, social/community signals only if configured and compliant. |

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
- Object, mission, telescope, or transient id where applicable.
- Preliminary/confirmed/retracted status where applicable.
- Scope-overlap tag where applicable.

Empty states:

- Solar System and Beyond layer disabled.
- Sources not configured.
- Sources configured but disabled.
- Sources configured but never scanned.
- Sources stale.
- Source policy blocked.
- Parser failed.
- Social sources disabled by policy.
- Heavy archive source disabled by policy.
- Auth-required source disabled by policy.
- Source requires token/account and is not configured.
- Source marked `manual_review_only`.
- SYSTEM naming collision unresolved.

## SECTION 15: Evidence model

Every item and event must trace back to source evidence.

For an event, evidence should include:

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
- Scientific significance basis.
- Object or mission match basis.
- Source diversity basis.
- Preliminary/confirmed/retracted status.
- Archive query bounds if any.
- Auth-required status if any.
- Retention expiration.
- Matching tokens.
- Event type.
- Event confidence.
- Policy notes.
- Low-public-value penalty if applied.
- Hype penalty if applied.
- Archive-firehose penalty if applied.
- Out-of-scope penalty if applied.

For planetary science and mission events, evidence must include, where available:

- Mission name.
- Spacecraft.
- Target body.
- Instrument.
- Agency.
- Publication date.
- Source URL.
- Mission phase or milestone.
- Whether it is science result, mission update, data release, or press release.

For exoplanet events, evidence must include, where available:

- Planet name.
- Host star.
- System name.
- Confirmed/candidate status.
- Discovery method.
- Archive row or source id.
- Publication or update date.
- Source URL.
- Whether the source says Earth-size, habitable-zone, atmosphere, biosignature, or another
  high-interest term.
- A rule that high-interest terms must not be inferred if the source does not say them.

For transient and multi-messenger events, evidence must include, where available:

- Event id.
- Transient name.
- Coordinates.
- Event time.
- Notice/circular id.
- Instrument.
- Preliminary/update/retraction status.
- Classification.
- Source URL.
- Follow-up count.
- Associated GCN/ATel/TNS/GraceDB ids.
- Whether the information is preliminary.

For telescope and archive events, evidence must include, where available:

- Observatory.
- Mission.
- Instrument.
- Dataset id.
- Release id.
- Data release date.
- Source URL.
- Whether data products were downloaded. This should normally say no data products downloaded.

For literature metadata events, if ever enabled, evidence must include:

- Title.
- Authors.
- Source.
- Bibcode or DOI.
- Publication date.
- Abstract URL if allowed.
- A no-full-paper-body flag.
- A no-paywall-bypass flag.
- Auth token status if ADS is used.

## SECTION 16: Source health

Source health must be visible in app-health SYSTEM later and summarized in this candidate scope's
Bay 4 or footer strip.

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
- `heavy_archive_disabled`
- `needs_terms_review`
- `needs_scope_filter`
- `naming_collision_unresolved`
- `hype_blocked`
- `archive_firehose_blocked`

Each source health row should have:

| Field | Purpose |
| --- | --- |
| `source_id` | Stable source id. |
| `state` | One of the required source-health states. |
| `last_attempt_at` | Last attempted fetch or fixture parse. |
| `last_success_at` | Last successful fetch or fixture parse. |
| `last_failure_at` | Last failure time. |
| `next_eligible_fetch_at` | Backoff/rate-limit marker. |
| `consecutive_failures` | Failure count. |
| `last_http_status` | Last HTTP status if applicable. |
| `item_count_last_success` | Count from last successful run. |
| `stale_after_minutes` | Per-source stale threshold. |
| `message` | Human-readable state explanation. |
| `evidence_json` | Policy, parser, timing, and config evidence. |

## SECTION 17: First implementation sequence

Phase S0: this design

- Create design doc.
- Update BACKLOG.
- No runtime behavior change.
- Document naming collision.

Phase S1: scope naming decision

- Resolve whether this layer becomes SYSTEM, COSMIC, SOLAR, DEEP, or another tab label.
- Do not implement before user decision.
- If app-health SYSTEM remains, create separate label and route plan.
- If SYSTEM is repurposed, design migration of app-health SYSTEM to CONSOLE or HEALTH.

Phase S2: source registry scaffolding

- Add disabled source config under the chosen scope name.
- Add source registry schema or tables if not already done by global architecture.
- Add tests proving disabled by default.
- No network.

Phase S3: local fixtures only

- Create fixture files for NASA/JPL RSS, ESA RSS, NASA Exoplanet Archive tiny metadata, MAST tiny
  metadata, PDS tiny metadata, GCN notice, GCN circular, ATel RSS, TNS auth-required source health,
  GraceDB auth/policy source health, LIGO public alert, JWST/Hubble RSS, and science news RSS.
- Parse fixtures only.
- Store normalized metadata.
- No live fetch.

Phase S4: event correlation

- Deterministic token/object/mission/time/source-family matching.
- No LLM.
- Tests for convergence, duplicate suppression, source-family diversity, transient id matching,
  object/mission matching, and Solar System and Beyond vs ORBITAL vs GLOBAL scope routing.

Phase S5: ranking

- Implement scoring model.
- Explain ranking in JSON.
- Test official science source, source diversity, recency, scientific significance, transient
  status, mission relevance, hype penalty, archive-firehose penalty, stale-source penalty, and
  out-of-scope penalty.

Phase S6: UI disabled and fixture-backed states

- Add candidate UI only after naming decision.
- Fixture-backed in tests only.
- No live fetch.
- No fake headlines.

Phase S7: official RSS live ingest, opt-in only

- Start with one safe official feed.
- Suggested first candidates are JPL RSS, ESA RSS, NASA RSS, Hubble/JWST RSS if verified, and ATel
  RSS if policy-safe.
- Must be disabled by default.
- Must use an explicit command.
- No page-load fetch.

Phase S8: official small API ingest, opt-in only

- Exoplanet Archive tiny allowlisted metadata query.
- GCN notice fixture-based parser, then live only after dependency and protocol review.
- PDS metadata-only query after row caps and no-download tests.
- MAST metadata-only query after row caps and no-download tests.
- No bulk archive queries.

Phase S9: transient and multi-messenger sources

- GCN notices/circulars.
- ATel.
- TNS only after auth/policy review.
- GraceDB/LIGO only after public-alert review.
- Preserve preliminary/update/retraction state.
- No sky-map downloads by default.

Phase S10: heavy archive and catalog candidates

- SIMBAD, VizieR, Gaia, ESASky, ESO Archive, ADS, MAST bulk, PDS bulk, and HEASARC broad searches.
- Disabled by default.
- Use only strict allowlists.
- Prefer source-health-only or metadata-only.
- No catalog ingestion.

Phase S11: science journalism RSS

- Publisher feeds only.
- Store metadata only.
- No article bodies.
- No paywall bypass.
- Do not let news-only clusters outrank official science/alert sources without convergence.

Phase S12: social/community

- Bluesky AT Protocol candidate.
- Reddit official API candidate.
- X official API only if explicitly configured.
- No HTML scraping.
- Short retention.
- Disabled by default.

## SECTION 18: Testing strategy

Config tests:

- Solar System and Beyond layer disabled by default.
- Source disabled by default.
- Invalid source class rejected.
- Invalid adapter rejected.
- Social source rejected unless `allow_social_sources` is true.
- Heavy archive source rejected unless `include_large_archive_queries` is true.
- Auth-required source marked `auth_required` unless credentials are explicitly configured outside
  repo.
- Literature metadata source rejected unless `include_literature_metadata` is true.
- Homepage extraction rejected unless `allow_homepage_extractors` is true.
- Source without URL rejected unless adapter supports no URL.
- Naming collision with SYSTEM is represented as unresolved until user decision.
- Secrets not allowed in `config.example.yml`.

Registry tests:

- Source keys unique.
- Source family valid.
- Source class valid.
- Verification status valid.
- Retention settings valid.
- Mission filters valid.
- Object filters valid.
- Archive row caps valid.
- Transient alert status values valid.
- Auth-required source flags valid.

Parser fixture tests:

- NASA/JPL RSS fixture parses.
- ESA RSS fixture parses.
- Hubble/JWST RSS fixture parses.
- Exoplanet Archive tiny fixture parses.
- MAST tiny metadata fixture parses.
- PDS tiny metadata fixture parses.
- GCN notice fixture parses.
- GCN circular fixture parses.
- ATel RSS fixture parses.
- TNS auth-required fixture returns `auth_required` without network.
- GraceDB auth/policy fixture returns disabled/auth-required without network unless configured.
- Science news RSS fixture parses.
- Malformed feed fails soft.
- Oversized payload blocked or truncated.

Safety and hype tests:

- No bulk archive source runs by default.
- No science data products are downloaded.
- No paper bodies are downloaded.
- No API credentials are stored in repo.
- Social-only claim does not outrank official science source.
- "Life found" wording is blocked unless source title or metadata directly says it.
- UFO content is out of scope.
- Generic astronomy explainer gets low-public-value penalty.
- Old paper resurfaced as new gets stale or low-confidence penalty.
- Preliminary transient is labeled preliminary.
- Retracted alert is displayed as retracted or suppressed, not live.

Correlation tests:

- GCN notice plus GCN circular plus ATel follow-up becomes one transient event.
- GraceDB alert plus GCN circular plus science news becomes one multi-messenger event.
- NASA/JPL mission release plus science journalism becomes one planetary science event.
- Exoplanet Archive update plus NASA release plus news becomes one exoplanet event.
- Same event from multiple news outlets counts as news-family convergence but not endless duplicate
  inflation.
- Same source repeated does not inflate source diversity.
- Different source families increase diversity.
- ORBITAL event without deeper science context stays ORBITAL.
- GLOBAL terrestrial event without astronomy cause does not appear in this scope.

Ranking tests:

- Official GCN transient alert outranks generic astronomy article.
- Confirmed exoplanet agency release outranks routine catalog update.
- JWST official science release outranks generic telescope image roundup.
- Multi-source gravitational-wave candidate outranks social rumor.
- PDS data release does not dominate unless configured as important.
- Heavy archive candidate is blocked unless explicitly enabled and scoped.
- Stale source lowers confidence.
- Source policy blocked item never displays as live.
- Auth-required source item never displays unless explicitly configured and policy-approved.

API design tests for later:

- GET routes read SQLite only.
- GET routes do not fetch network.
- Disabled, not configured, stale, failing, auth-required, and heavy-archive-disabled states are
  distinct.
- Naming collision state is visible until resolved.

UI tests for later:

- No fake headlines.
- Empty states clear.
- Evidence visible.
- Ranking reason visible.
- Source health visible.
- Object, mission, or transient label visible.
- Preliminary/confirmed/retracted status visible.
- Naming collision visible if unresolved.

Safety tests:

- No page-load external fetches.
- No hidden LLM calls.
- No telemetry.
- No package install.
- No sudo.
- No social fetch unless explicitly configured.
- No auth-required source fetch unless explicitly configured.
- No API-key source runs without key configuration.
- No bulk archive query.
- No data product download.

## SECTION 19: Backlog update requirements

`BACKLOG.md` must include a section named `Solar System and Beyond Recent Signal Layer`. Every
backlog item added for this design must say `Status: not implemented.` Future tasks should be
concrete enough for a later agent to implement without reading chat history.

Required backlog work areas:

- Resolve SYSTEM naming collision between app-health SYSTEM and Solar System and Beyond scope.
- Decide final UI label for Solar System and Beyond.
- Disabled-by-default Solar System and Beyond config.
- Solar System and Beyond source registry design implemented from document.
- Solar System and Beyond SQLite schema or extension.
- Solar System and Beyond fixture pack.
- NASA/JPL RSS parser.
- ESA RSS parser.
- Hubble/JWST RSS parser.
- NASA Exoplanet Archive tiny metadata parser.
- MAST tiny metadata parser.
- PDS metadata-only parser.
- GCN notice fixture parser.
- GCN circular source verification.
- ATel RSS parser.
- TNS auth/policy design.
- GraceDB/LIGO public alert policy design.
- Minor Planet Center science-context source verification.
- HEASARC metadata source verification.
- SIMBAD/VizieR/Gaia heavy-archive policy design.
- ADS literature metadata policy design, disabled and auth-required.
- Deterministic event correlation for transients, exoplanets, missions, and telescope releases.
- Deterministic ranking for official science, source diversity, rarity, transient status, and hype
  penalty.
- Hype and speculation suppression rules.
- Archive firehose blocking rules.
- UI disabled states after naming decision.
- Source health states.
- Evidence drawer contract.
- Official RSS live ingest phase, disabled by default.
- Official small API live ingest phase, disabled by default.
- Transient alert ingest phase, disabled by default.
- Heavy archive phase, disabled by default.
- Literature metadata phase, disabled by default.
- Social source policy review, disabled by default.
- Documentation for source verification.
- Tests for no page-load external fetches.
- Tests for no heavy archive source running without explicit config.
- Tests for no auth source running without config.
- Tests for no data product downloads.
- Tests for no alien-life or UFO hype leakage.

## SECTION 20: Non-goals

- No live fetch in this task.
- No collector implementation in this task.
- No UI implementation in this task.
- No tab rename in this task.
- No route rename in this task.
- No general crawler.
- No page-load fetch.
- No hidden LLM summarization.
- No full article archive.
- No permanent astronomy archive.
- No bulk science catalog ingestion.
- No telescope data product downloads.
- No paper downloads.
- No paywall bypass.
- No private data collection.
- No UFO dashboard.
- No alien-life hype feed.
- No science hype generator.
- No literature review engine.
- No observatory data mirror.
- No social surveillance.
- No scraping behind login.
- No bypassing Reddit, X, or API restrictions.
- No claiming social chatter is verified fact.
- No treating science journalism as primary scientific evidence.
- No treating duplicate articles as independent confirmation.
- No burying LOCAL, REGIONAL, NATIONAL, GLOBAL, ORBITAL, or app-health SYSTEM urgent items under
  deep-space headlines.
- No automatic API key discovery or secret storage.
- No broad SIMBAD, VizieR, Gaia, MAST, PDS, HEASARC, Exoplanet Archive, or ADS firehose ingestion.

## SECTION 21: Final response requirements

The final response for this task should include:

- Files changed.
- Confirmation that no application code was changed, unless it was.
- Confirmation that no external network fetches were added.
- Confirmation that no dependencies were added.
- Confirmation that no collectors were implemented.
- Confirmation that this Solar System and Beyond layer remains disabled by default.
- Confirmation that no tab rename or route rename was implemented.
- Confirmation that the SYSTEM naming collision was documented.
- Test commands run and exact results.
- `git diff --check` result.
- `git status --short`.
- BACKLOG entries added.
- Uncertainties and source targets needing later verification.

Do not commit. Do not push.
