Use this as `build_order/006_system.md`.

I am interpreting your `006_system.md` as **Solar System and Beyond**, not console app-health. The earlier architecture prompt reserved `SYSTEM` for console-1701 app/source health, so this prompt makes Codex document that naming collision instead of silently wrecking the existing scope model.

The source anchors here are real target families: NASA Exoplanet Archive API, MAST API, NASA GCN machine-readable notices, TNS as the IAU mechanism for astronomical transients, LIGO/Virgo/KAGRA public alerts through GraceDB, ESA RSS feeds, SIMBAD/TAP, VizieR TAP, ESA Gaia programmatic access, NASA PDS API, and NASA ADS API. ([NASA Exoplanet Archive][1])

Raw anchor URLs:

[https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html](https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html)
[https://mast.stsci.edu/api/v0/](https://mast.stsci.edu/api/v0/)
[https://gcn.nasa.gov/docs/notices](https://gcn.nasa.gov/docs/notices)
[https://www.wis-tns.org/content/tns-getting-started](https://www.wis-tns.org/content/tns-getting-started)
[https://rtd.igwn.org/projects/userguide/en/v3/index.html](https://rtd.igwn.org/projects/userguide/en/v3/index.html)
[https://www.esa.int/Services/RSS_Feeds](https://www.esa.int/Services/RSS_Feeds)
[https://simbad.u-strasbg.fr/Pages/guide/sim-q.htx](https://simbad.u-strasbg.fr/Pages/guide/sim-q.htx)
[https://tapvizier.cds.unistra.fr/adql/](https://tapvizier.cds.unistra.fr/adql/)
[https://www.cosmos.esa.int/web/gaia-users/archive/programmatic-access](https://www.cosmos.esa.int/web/gaia-users/archive/programmatic-access)
[https://nasa-pds.github.io/pds-api/](https://nasa-pds.github.io/pds-api/)
[https://ui.adsabs.harvard.edu/help/api/](https://ui.adsabs.harvard.edu/help/api/)

```text id="h4s1qf"
You are working in the console-1701 repository.

This task assumes the prior scoped recent-signal architecture prompt, LOCAL Seattle design prompt, REGIONAL Pacific Northwest design prompt, NATIONAL United States design prompt, GLOBAL World design prompt, and ORBITAL Space design prompt have either already been run, or will be pasted above this prompt.

This is a SOLAR SYSTEM AND BEYOND architecture, source-target inventory, and ranking design task only.

This task is being saved by the user as:

build_order/006_system.md

Important naming note:

The user currently wants the last design prompt to cover "solar system and beyond if found."

Earlier architecture may define SYSTEM as console-1701 application health, source health, ingest health, stale-source warnings, and configuration state.

Do not silently overwrite that meaning.

This task must explicitly document the naming collision and propose a safe path.

Use a working design scope label such as:

- SYSTEM_SOLAR
- SOLAR_SYSTEM
- COSMIC
- DEEP_SPACE
- SOLAR_SYSTEM_AND_BEYOND

Do not implement any tab rename.
Do not change the existing scope tabs.
Do not change runtime behavior.
Do not change templates.
Do not change CSS.
Do not change routes.

The design document must say that the final UI label is still a user decision.

Possible future naming choices to document:

Option A:
- Keep SYSTEM as console app-health.
- Add a future COSMIC or DEEP tab for solar system and beyond.

Option B:
- Rename console app-health to CONSOLE or HEALTH later.
- Use SYSTEM for Solar System and Beyond.

Option C:
- Keep ORBITAL for near-Earth space.
- Add SOLAR or COSMIC for solar system and beyond.

Recommendation should be conservative:
- Do not break current SYSTEM semantics in this task.
- Design the solar-system-and-beyond layer as a candidate future scope.
- Let the user choose final label later.

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

Your job is to design the Solar System and Beyond recent-signal layer in enough detail that later Codex passes can implement it safely, source by source, without guessing.

Before doing anything, inspect the current repo state and previous design outputs.

Required first checks:

pwd
git status --short
find docs/project -maxdepth 1 -type f -print | sort || true
grep -n "Recent Signal\|News Ingestion\|LOCAL\|REGIONAL\|NATIONAL\|GLOBAL\|ORBITAL\|SYSTEM\|COSMIC\|SOLAR" BACKLOG.md || true

If previous docs exist, read them first and extend them cleanly:

- docs/project/NEWS_SCOPE_INGESTION_ARCHITECTURE_DESIGN.md
- docs/project/LOCAL_SEATTLE_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md
- docs/project/REGIONAL_PNW_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md
- docs/project/NATIONAL_US_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md
- docs/project/GLOBAL_WORLD_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md
- docs/project/ORBITAL_SPACE_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md

Do not duplicate BACKLOG sections already added by previous tasks. Extend the relevant section cleanly or add a new Solar System and Beyond subsection.

The user intent:

console-1701 is a local-only home dashboard running at http://127.0.0.1:1701/.

The Solar System and Beyond layer should eventually answer:

"What is happening in the solar system, the wider galaxy, and the observable universe that may matter or be interesting right now?"

This is intentionally different from ORBITAL.

ORBITAL is near-Earth and operational:
- space weather
- aurora
- satellites
- launches
- reentries
- NEOs
- orbital debris
- ISS
- immediate spaceflight operations

Solar System and Beyond is deeper and broader:
- planetary science
- interplanetary missions
- solar system bodies
- exoplanets
- stellar astronomy
- deep-sky astronomy
- gravitational waves
- gamma-ray bursts
- supernovae
- novae
- kilonovae
- fast radio bursts
- neutrinos
- astronomical transients
- major observatory releases
- public science alerts
- major telescope mission updates
- peer-reviewed or agency-backed discoveries
- sky events that are not just near-Earth operational events
- credible astronomy and astrophysics news

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
- docs/project/ORBITAL_SPACE_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md, if it exists
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

   docs/project/SYSTEM_SOLAR_SYSTEM_BEYOND_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md

   Create docs/project if it does not exist.

2. Update BACKLOG.md with concrete future implementation tasks flowing from this design.

3. Do not touch application code unless absolutely necessary. This should normally be docs plus BACKLOG only.

4. Do not perform live source verification. The source links below are seed targets. Classify them as candidate links and design how they should be verified in a later phase.

5. The final response must prove what changed and what did not change.

The design document must include the following sections.

SECTION 1: Purpose

Explain the Solar System and Beyond layer in plain engineering language.

The Solar System and Beyond layer is the deep-space, planetary-science, astronomy, astrophysics, and cosmic-events recent-signal layer. It should tell the user what is happening beyond near-Earth operations, with source provenance, observed time, source kind, ranking reason, and evidence.

It is not:

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
- A replacement for app-health SYSTEM, unless the user later chooses to rename scopes.

It is:

- A local, short-retention metadata dashboard.
- A deterministic cross-source event detector for solar-system, exoplanet, transient, telescope, mission, and astrophysics signals.
- A source-health aware recent-signal system.
- A possible future scope in console-1701 that can surface official mission updates, planetary events, exoplanet discoveries, transient alerts, gravitational-wave alerts, gamma-ray bursts, supernovae, major telescope releases, agency news, astronomy news, and credible public science signals.
- A way to rank items by independent source convergence, official/scientific provenance, event rarity, public interest, scientific significance, freshness, and user-configured source priority.

Make clear that "solar system and beyond" means useful public, configured, lawful, recent signals that the user chooses to enable. It does not mean unbounded astronomy catalog ingestion, downloading huge archive products, scraping paper databases, or turning the app into a research data warehouse.

SECTION 2: Scope naming collision

This section is mandatory.

Document that earlier architecture may use SYSTEM for console app health.

This task is named 006_system.md by the user, but the user now describes the content as "solar system and beyond."

The design must not pretend this is already resolved.

Explain:

- SYSTEM as app-health is already useful for console-1701 source health, ingest health, stale-source warnings, config warnings, and database health.
- Solar System and Beyond is semantically unrelated to app-health.
- Using SYSTEM for both would confuse future code, docs, tests, UI labels, and source-health screens.
- This task should design the deep-space layer without implementing a tab change.
- The recommended future path should be stated clearly.

Recommended path:

- Keep existing SYSTEM app-health semantics untouched for now.
- Design this new layer under the working name SYSTEM_SOLAR or SOLAR_SYSTEM_BEYOND.
- Add a BACKLOG item for a later user-facing naming decision:
  "Resolve SYSTEM naming collision: app-health SYSTEM vs Solar System and Beyond scope."
- Possible UI labels:
  COSMIC
  SOLAR
  DEEP
  DEEP SPACE
  SYSTEM
  SKY
  BEYOND
- Do not change existing routes or tabs in this task.

SECTION 3: Relationship to ORBITAL and other scopes

Explain how this layer interacts with ORBITAL, GLOBAL, NATIONAL, REGIONAL, LOCAL, OVERVIEW, and app-health SYSTEM.

Rules:

- ORBITAL owns near-Earth operations and immediate space-environment effects:
  space weather, aurora, satellites, launches, NEOs, fireballs, reentries, debris, ISS, launch status, and operational spaceflight.

- Solar System and Beyond owns deeper scientific and observational signals:
  planetary science, interplanetary mission science, exoplanets, stars, galaxies, cosmology, supernovae, gamma-ray bursts, gravitational waves, neutrinos, transients, major telescope science, and credible astronomy discoveries.

- GLOBAL owns terrestrial world events unless the cause or primary signal is astronomical or space-science related.

- NATIONAL owns U.S. federal and domestic signals unless the primary signal is astronomy, planetary science, or astrophysics.

- REGIONAL and LOCAL own geographic impacts such as sky visibility, local observing, aurora visibility, meteor showers visible from Seattle, or regional observatory news only when relevant.

- OVERVIEW should select the highest-priority items from all scopes without burying urgent local/system issues.

- App-health SYSTEM should continue to exist as the place for source-health, ingest-health, stale-source warnings, config warnings, and database health unless the user later renames it.

Examples:

- SWPC G4 geomagnetic storm: ORBITAL.
- Aurora visible in Seattle: ORBITAL with LOCAL or REGIONAL impact.
- JPL CNEOS close approach: ORBITAL unless there is deeper science coverage, in which case this layer may link as science context.
- NASA planetary mission discovers active geology on a moon: Solar System and Beyond.
- JWST releases major exoplanet atmosphere result: Solar System and Beyond.
- New exoplanet catalog update: Solar System and Beyond, low priority unless major or multi-source.
- Routine telescope image of a nebula: low-priority Solar System and Beyond.
- Gamma-ray burst GCN alert with follow-up circulars: Solar System and Beyond.
- LIGO/Virgo/KAGRA gravitational-wave candidate alert: Solar System and Beyond.
- Supernova report in TNS plus ATel plus GCN follow-up: Solar System and Beyond.
- Launch of a telescope: ORBITAL during launch, Solar System and Beyond for science mission milestones.
- NASA budget story about science programs: NATIONAL unless directly tied to mission operation or telescope output.
- UFO story: out of scope unless the user later defines a separate explicit scope.

SECTION 4: Scope boundaries

Define the boundary.

Default Solar System and Beyond scope:

- Solar system science beyond immediate near-Earth operations.
- Planetary bodies, moons, comets, asteroids, Kuiper Belt objects, and interplanetary missions.
- Solar physics as science, but space-weather effects remain ORBITAL.
- Exoplanets and planetary systems.
- Stellar astronomy.
- Galactic astronomy.
- Extragalactic astronomy.
- Cosmology.
- Gravitational-wave astronomy.
- Gamma-ray bursts and high-energy transients.
- Supernovae, novae, kilonovae, tidal disruption events, fast radio bursts, neutrinos, and multi-messenger astronomy.
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
- Anything that turns console-1701 into an astronomy research platform rather than a recent-signal dashboard.

Design a later config escape hatch:

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

SECTION 5: Seed source target inventory

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

- official_planetary_science
- official_planetary_data_archive
- official_solar_system_mission
- official_solar_science
- official_exoplanet
- official_exoplanet_archive
- official_space_telescope
- official_astronomy_archive
- official_high_energy_astrophysics
- official_transient_alert
- official_gravitational_wave
- official_neutrino_candidate
- official_supernova_transient
- official_minor_body_science
- official_observatory_news
- official_science_release
- astronomy_catalog_candidate
- literature_metadata_candidate
- astronomy_news
- science_news
- public_media_science
- social_candidate
- heavy_archive_candidate
- auth_required_candidate
- source_health_only
- manual_review_only

Use these adapter types:

- rss_atom
- static_html_headline_candidate
- official_api_json
- tap_adql_candidate
- astroquery_candidate
- nasa_api_json
- pds_api_candidate
- exoplanet_archive_api
- mast_api_candidate
- heasarc_api_candidate
- gcn_notice_candidate
- gcn_circular_candidate
- tns_api_candidate
- gracedb_api_candidate
- astronomers_telegram_rss
- mpc_api
- jpl_ssd_api
- simbad_tap_candidate
- vizier_tap_candidate
- gaia_tap_candidate
- ads_api_candidate
- local_file_fixture
- source_health_probe_only
- manual_review_only

Use these verification_status values:

- user_seeded
- assistant_seeded
- official_page_seen
- candidate_needs_verification
- candidate_policy_sensitive
- auth_required
- heavy_archive_risk
- unofficial_secondary
- reject_for_now

Do not overstate verification. If a URL is only a likely feed endpoint, mark it candidate_needs_verification.

Seed source targets:

NASA planetary science, solar system, and mission science:

https://science.nasa.gov/solar-system/
https://science.nasa.gov/solar-system/news/
https://science.nasa.gov/mission/
https://science.nasa.gov/news/
https://www.nasa.gov/missions/
https://www.nasa.gov/news/
https://www.nasa.gov/rss-feeds/
https://www.jpl.nasa.gov/news/
https://www.jpl.nasa.gov/rss/
https://www.jpl.nasa.gov/missions/
https://solarsystem.nasa.gov/
https://science.nasa.gov/solar-system/planets/
https://science.nasa.gov/solar-system/moons/
https://science.nasa.gov/solar-system/comets/
https://science.nasa.gov/solar-system/asteroids/
https://science.nasa.gov/mission/voyager/
https://science.nasa.gov/mission/juno/
https://science.nasa.gov/mission/europa-clipper/
https://science.nasa.gov/mission/mars-2020-perseverance/
https://science.nasa.gov/mission/curiosity/
https://science.nasa.gov/mission/lucy/
https://science.nasa.gov/mission/osiris-apex/
https://science.nasa.gov/mission/parker-solar-probe/
https://science.nasa.gov/mission/solar-orbiter/

NASA Planetary Data System and planetary archives:

https://pds.nasa.gov/
https://pds.nasa.gov/datasearch/data-search/
https://nasa-pds.github.io/pds-api/
https://github.com/NASA-PDS/pds-api
https://pds.nasa.gov/about/
https://pds.nasa.gov/datasearch/subscription-service/
https://pds.nasa.gov/datasearch/metadata-search/
https://pds.nasa.gov/datasearch/tool-registry/

JPL SSD / CNEOS / minor bodies, reused as deep solar system context:

https://ssd-api.jpl.nasa.gov/
https://ssd-api.jpl.nasa.gov/doc/index.php
https://ssd-api.jpl.nasa.gov/doc/sbdb.html
https://ssd-api.jpl.nasa.gov/sbdb.api
https://ssd-api.jpl.nasa.gov/doc/cad.html
https://ssd-api.jpl.nasa.gov/cad.api
https://ssd-api.jpl.nasa.gov/doc/sentry.html
https://ssd-api.jpl.nasa.gov/sentry.api
https://ssd-api.jpl.nasa.gov/doc/scout.html
https://ssd-api.jpl.nasa.gov/scout.api
https://ssd-api.jpl.nasa.gov/doc/horizons.html
https://ssd.jpl.nasa.gov/api.html
https://cneos.jpl.nasa.gov/
https://cneos.jpl.nasa.gov/ca/
https://cneos.jpl.nasa.gov/sentry/
https://cneos.jpl.nasa.gov/scout/

Minor Planet Center:

https://www.minorplanetcenter.net/
https://www.minorplanetcenter.net/data
https://www.minorplanetcenter.net/mpec/RecentMPECs.html
https://www.minorplanetcenter.net/mpcops/documentation/
https://www.minorplanetcenter.net/mpcops/documentation/mpecs-api/
https://cgi.minorplanetcenter.net/mpcops/documentation/neocp-observations-api/
https://www.minorplanetcenter.net/neocp_obs
https://www.minorplanetcenter.net/mpcops/documentation/observations-api/
https://www.minorplanetcenter.net/mpcops/documentation/orbits-api/
https://www.minorplanetcenter.net/mpcops/documentation/designation-identifier-api/

NASA Exoplanet Archive, exoplanets, and MAST:

https://exoplanetarchive.ipac.caltech.edu/
https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html
https://exoplanetarchive.ipac.caltech.edu/docs/API_queries.html
https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html
https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html
https://exoplanetarchive.ipac.caltech.edu/docs/exonews_archive.html
https://exo.mast.stsci.edu/docs/
https://mast.stsci.edu/api/v0/
https://catalogs.mast.stsci.edu/docs/index.html
https://mast.stsci.edu/hapcut/
https://mast.stsci.edu/cassi/docs/index.html
https://jwst-docs.stsci.edu/accessing-jwst-data/mast-api-access
https://archive.stsci.edu/missions-and-data/jwst
https://archive.stsci.edu/missions-and-data/hubble
https://archive.stsci.edu/missions-and-data/tess
https://archive.stsci.edu/missions-and-data/kepler
https://archive.stsci.edu/missions-and-data/gaia

NASA, STScI, Hubble, JWST, Roman, TESS, and telescope science:

https://science.nasa.gov/mission/hubble/
https://science.nasa.gov/mission/jwst/
https://science.nasa.gov/mission/tess/
https://science.nasa.gov/mission/roman-space-telescope/
https://hubblesite.org/news
https://hubblesite.org/resource-gallery/rss-feeds
https://webbtelescope.org/news
https://webbtelescope.org/contents/news-releases
https://webbtelescope.org/resource-gallery/rss-feed
https://roman.gsfc.nasa.gov/news/
https://science.nasa.gov/universe/
https://science.nasa.gov/astrophysics/
https://science.nasa.gov/astrophysics/focus-areas/
https://www.stsci.edu/contents/news
https://www.stsci.edu/jwst
https://www.stsci.edu/hst
https://www.stsci.edu/roman

HEASARC, high-energy astrophysics, and NASA GCN:

https://heasarc.gsfc.nasa.gov/
https://heasarc.gsfc.nasa.gov/docs/archive.html
https://heasarc.gsfc.nasa.gov/docs/heasarc/missions.html
https://heasarc.gsfc.nasa.gov/docs/software/webservices/
https://gcn.nasa.gov/
https://gcn.nasa.gov/docs/notices
https://gcn.nasa.gov/docs/notices/schema
https://gcn.nasa.gov/docs/notices/archive
https://gcn.nasa.gov/docs/circulars
https://gcn.nasa.gov/circulars
https://gcn.nasa.gov/docs/sample
https://github.com/nasa-gcn/gcn-schema

Gravitational waves and multi-messenger astronomy:

https://rtd.igwn.org/projects/userguide/en/v3/index.html
https://emfollow.docs.ligo.org/userguide/quickstart.html
https://gracedb.ligo.org/
https://ligo-gracedb.readthedocs.io/
https://ligo-gracedb.readthedocs.io/en/latest/api.html
https://ligo-gracedb.readthedocs.io/en/latest/user_guide.html
https://www.ligo.caltech.edu/news
https://www.ligo.org/news.php
https://www.virgo-gw.eu/news/
https://gwcenter.icrr.u-tokyo.ac.jp/en/
https://www.gw-openscience.org/
https://www.gw-openscience.org/eventapi/

Astronomical transients, supernovae, ATel, TNS, GCN, and time-domain astronomy:

https://www.astronomerstelegram.org/
https://www.astronomerstelegram.org/?rss
https://www.wis-tns.org/
https://www.wis-tns.org/content/tns-getting-started
https://www.wis-tns.org/content/tns-news
https://www.wis-tns.org/sites/default/files/api/TNS_APIs_manual.pdf
https://gcn.nasa.gov/circulars
https://gcn.nasa.gov/docs/notices
https://gcn.nasa.gov/docs/notices/archive
https://www.swift.ac.uk/
https://swift.gsfc.nasa.gov/
https://fermi.gsfc.nasa.gov/
https://fermi.gsfc.nasa.gov/ssc/
https://www.lsst.org/news
https://rubinobservatory.org/news
https://www.ztf.caltech.edu/news.html
https://www.lco.global/news/

ESA, JAXA, ISRO, CSA, ESO, observatories, and international science feeds:

https://www.esa.int/Services/RSS_Feeds
https://www.esa.int/Science_Exploration
https://sci.esa.int/
https://sci.esa.int/web/services/rss
https://www.cosmos.esa.int/web/esdc
https://sky.esa.int/
https://www.cosmos.esa.int/web/esdc/esasky-javascript-api
https://global.jaxa.jp/press/
https://www.isro.gov.in/Press.html
https://www.asc-csa.gc.ca/eng/news/
https://www.eso.org/public/news/
https://www.eso.org/public/rss/
https://archive.eso.org/
https://archive.eso.org/programmatic/
https://noirlab.edu/public/news/
https://noirlab.edu/public/news/rss/
https://www.nrao.edu/news/
https://public.nrao.edu/news/
https://public.nrao.edu/feed/
https://www.almaobservatory.org/en/news/
https://www.almaobservatory.org/en/feed/
https://www.nao.ac.jp/en/news/
https://www.nao.ac.jp/en/news/rss.xml
https://www.naoj.org/
https://www.skao.int/en/news

Astronomy catalog and archive candidates:

https://simbad.u-strasbg.fr/
https://simbad.u-strasbg.fr/Pages/guide/sim-q.htx
https://simbad.u-strasbg.fr/simbad/sim-tap
https://tapvizier.cds.unistra.fr/adql/
https://vizier.cds.unistra.fr/
https://cds.unistra.fr/
https://www.cosmos.esa.int/web/gaia-users/archive
https://www.cosmos.esa.int/web/gaia-users/archive/programmatic-access
https://gea.esac.esa.int/archive/
https://astroquery.readthedocs.io/en/latest/gaia/gaia.html
https://astroquery.readthedocs.io/en/stable/simbad/simbad.html
https://astroquery.readthedocs.io/en/latest/ipac/nexsci/nasa_exoplanet_archive.html
https://astroquery.readthedocs.io/en/latest/utils/tap.html
https://astroquery.readthedocs.io/en/latest/esasky/esasky.html
https://archive.eso.org/
https://archive.eso.org/programmatic/
https://ui.adsabs.harvard.edu/
https://ui.adsabs.harvard.edu/help/api/
https://ui.adsabs.harvard.edu/help/api/api-docs.html

Science news, astronomy journalism, and public media:

https://www.science.org/topic/category/space
https://www.nature.com/subjects/astronomy-and-planetary-science
https://www.nature.com/subjects/astronomy-and-planetary-science.rss
https://www.scientificamerican.com/space/
https://www.scientificamerican.com/platform/syndication/rss/
https://skyandtelescope.org/astronomy-news/
https://skyandtelescope.org/feed/
https://www.astronomy.com/
https://www.astronomy.com/feed/
https://www.universetoday.com/
https://www.universetoday.com/feed/
https://www.planetary.org/articles
https://www.planetary.org/rss.xml
https://www.space.com/astronomy
https://www.space.com/feeds/all
https://arstechnica.com/science/
https://arstechnica.com/science/feed/
https://www.bbc.com/news/science_and_environment
https://feeds.bbci.co.uk/news/science_and_environment/rss.xml
https://www.npr.org/sections/science/
https://feeds.npr.org/1007/rss.xml
https://www.pbs.org/newshour/science
https://www.pbs.org/newshour/feeds/rss/science

Community and social candidates, policy-sensitive:

https://www.reddit.com/r/space/
https://www.reddit.com/r/astronomy/
https://www.reddit.com/r/Astronomy/
https://www.reddit.com/r/astrophysics/
https://www.reddit.com/r/exoplanets/
https://www.reddit.com/r/cosmology/
https://www.reddit.com/r/telescopes/
https://www.reddit.com/r/spaceporn/
https://x.com/NASAUniverse
https://x.com/NASAExoplanets
https://x.com/NASAHubble
https://x.com/NASAWebb
https://x.com/NASARoman
https://x.com/chandraxray
https://x.com/ESA_Hubble
https://x.com/ESA_Webb
https://x.com/ESO
https://x.com/NOIRLabAstro
https://x.com/LIGO
https://x.com/MinorPlanetCtr
https://x.com/astronomerstel
https://bsky.app/search?q=JWST%20exoplanet
https://bsky.app/search?q=supernova
https://bsky.app/search?q=gamma%20ray%20burst
https://bsky.app/search?q=gravitational%20wave
https://bsky.app/search?q=exoplanet%20discovery
https://bsky.app/search?q=astronomy%20transient
https://bsky.app/search?q=NASA%20universe

Source policy references:

https://www.rfc-editor.org/rfc/rfc9309.html
https://www.rssboard.org/rss-specification
https://www.sitemaps.org/protocol.html
https://schema.org/NewsArticle
https://redditinc.com/policies/developer-terms
https://redditinc.com/policies/data-api-terms
https://docs.x.com/x-api/introduction
https://docs.bsky.app/docs/api/at-protocol-xrpc-api

SECTION 6: Source admission tiers

Design source tiers.

Tier 0:
- Local fixtures only.
- No network.
- Used for tests.

Tier 1:
- Official agency RSS, official science news feeds, official mission updates, and small official JSON APIs.
- Best first live candidates.

Tier 2:
- Public astronomy alert feeds and official transient alert sources.
- GCN, ATel RSS, TNS candidates, and LIGO public alerts.
- Must be disabled by default until fixture parsing and sensitivity rules exist.

Tier 3:
- Official science archive APIs used only for small metadata checks.
- Exoplanet Archive, MAST, HEASARC, PDS, MPC, JPL SSD, and similar.
- Must use strict allowlists, row caps, query caps, and no bulk data downloads.

Tier 4:
- Scientific institution RSS and observatory news.
- ESA, ESO, NOIRLab, NRAO, ALMA, STScI, JAXA, ISRO, CSA, and similar.
- Store headline metadata only.

Tier 5:
- Science journalism and public media.
- Store headline metadata only.
- No article-body archive.
- No paywall bypass.

Tier 6:
- Heavy archive or catalog candidates.
- Gaia, SIMBAD, VizieR, ESASky, ESO Archive, ADS, MAST bulk services, PDS bulk archives.
- Disabled by default.
- Fixture-only or source-health-only until there is a narrow use case.
- Do not ingest catalogs.

Tier 7:
- Auth-required sources.
- ADS API, TNS API, some GraceDB or VO services, or other token/account endpoints if applicable.
- Disabled by default.
- Must require credentials outside repo.
- Must never store secrets in repo.
- Must expose auth_required source-health state.

Tier 8:
- Social/community signals.
- Policy-sensitive.
- Disabled by default.
- Reddit only through compliant official API or permitted feed access.
- X/Twitter only through official API access if explicitly configured.
- Bluesky may be explored through official AT Protocol later.
- No HTML scraping to bypass platform restrictions.

Tier 9:
- Manual-review-only sources.
- Anything with unclear terms, high parser risk, large data volume, or science hype risk.

SECTION 7: Solar System and Beyond event model

Design an event model that sits above raw items.

The system should not only store "news items." It should infer that multiple recent items refer to the same cosmic or astronomy event.

Propose a future solar_system_beyond_events table or explain how news_clusters should be extended.

A Solar System and Beyond event should have:

- cosmic_event_id
- scope
- proposed_scope_label
- event_key
- event_type
- title
- representative_item_id
- severity
- scientific_significance_score
- public_interest_score
- source_diversity_score
- official_confirmation_score
- mission_relevance_score
- discovery_score
- rarity_score
- transient_score
- exoplanet_score
- planetary_science_score
- observatory_score
- peer_review_or_agency_score
- social_echo_score
- news_echo_score
- orbital_overlap_score
- global_impact_score
- local_sky_interest_score
- first_seen_at
- last_seen_at
- last_elevated_at
- expires_at
- objects_json
- missions_json
- instruments_json
- observatories_json
- agencies_json
- sky_coordinates_json
- solar_system_body_json
- exoplanet_system_json
- transient_ids_json
- source_ids_json
- item_ids_json
- evidence_json
- ranking_explanation_json
- status

Event types should include at least:

- planetary_mission_science
- planetary_body_update
- interplanetary_mission_milestone
- solar_science_discovery
- exoplanet_discovery
- exoplanet_atmosphere_result
- exoplanet_catalog_update
- major_telescope_release
- jwst_science_release
- hubble_science_release
- roman_mission_update
- tess_discovery_update
- gaia_data_release
- pds_data_release
- astronomy_archive_release
- gamma_ray_burst
- gravitational_wave_candidate
- gravitational_wave_confirmed
- supernova_candidate
- supernova_confirmed
- nova
- kilonova_candidate
- fast_radio_burst
- neutrino_candidate
- multi_messenger_event
- astronomical_transient
- comet_science_update
- minor_planet_science_update
- stellar_event
- galactic_center_event
- galaxy_discovery
- cosmology_result
- black_hole_result
- observatory_status_update
- major_science_publication
- source_health_problem
- community_signal

Make clear that routine low-impact science news should not automatically become elevated.

SECTION 8: Cross-source convergence ranking

Design deterministic ranking around this idea:

If something appears in official agency feeds, science archive metadata, transient alert networks, observatory feeds, science journalism, and community/social signals within a short window, it is probably important or interesting.

Implement this as design only.

Do not design an LLM summarizer.

The scoring model must be explainable.

Required scoring factors:

1. Official or scientific provenance

Examples:

- NASA/JPL/ESA/STScI official release.
- Official mission blog update.
- NASA Exoplanet Archive confirmed dataset or catalog metadata.
- GCN notice or circular.
- ATel item.
- TNS item, if configured.
- LIGO/Virgo/KAGRA public alert or GraceDB record, if configured.
- PDS dataset release or official mission archive update.
- MPC/MPEC item.
- Peer-reviewed source metadata, only if later allowed through ADS or DOI metadata.
- Observatory official release.

2. Source diversity

Independent source families count more than repeated mentions from the same family.

Example families:

- nasa_science
- nasa_jpl
- nasa_blogs
- nasa_exoplanet_archive
- mast
- stsci
- hubble
- webb
- roman
- tess
- pds
- esa
- jaxa
- isro
- csa
- eso
- noirlab
- nrao
- alma
- mpc
- jpl_ssd
- gcn
- atel
- tns
- ligo
- virgo
- kagra
- heasarc
- simbad
- vizier
- gaia
- ads
- science_journalism
- public_media_science
- reddit
- bluesky
- x_api
- source_health

3. Temporal proximity

Items closer in time are more likely to be the same event.

Propose matching windows:

- Agency science release: 0 to 7 days.
- Mission update: 0 to 14 days.
- Exoplanet discovery: 0 to 14 days.
- Exoplanet catalog update: 0 to 30 days if configured.
- GCN alert: 0 to 72 hours.
- GCN circular follow-up: 0 to 14 days.
- ATel transient: 0 to 14 days.
- TNS transient: 0 to 14 days.
- Gravitational-wave candidate: alert time through 14 days.
- Major telescope data release: 0 to 30 days.
- PDS/archive release: 0 to 30 days.
- Science article or paper metadata: 0 to 14 days if enabled.
- Routine news: 0 to 7 days.

4. Object, mission, and coordinate proximity

Match by:

- mission name
- telescope
- instrument
- source event id
- transient name
- TNS name
- GCN event id
- GraceDB superevent id
- ATel number
- planet name
- star name
- exoplanet system
- solar system body
- asteroid/comet designation
- coordinates
- sky localization
- DOI or bibcode if enabled
- archive collection id
- dataset id

5. Scientific significance

Boost:

- first detection or confirmation
- official agency release
- cross-observatory confirmation
- multi-messenger event
- nearby supernova
- gravitational-wave candidate with public alert
- gamma-ray burst with multiple follow-ups
- exoplanet atmosphere detection
- Earth-size or habitable-zone exoplanet, only if source says so
- solar system mission discovery
- major telescope milestone
- major public data release
- widely covered peer-reviewed discovery
- event with ORBITAL, GLOBAL, NATIONAL, REGIONAL, or LOCAL impact tag

6. Recency

Recent items matter more, but major discoveries can stay elevated for a short configured period.

7. User-configured priority

Allow future config to boost:

- planetary science
- exoplanets
- JWST
- Hubble
- Roman
- TESS
- Gaia
- Mars
- Europa
- Titan
- Enceladus
- astrobiology
- gravitational waves
- gamma-ray bursts
- supernovae
- black holes
- cosmology
- telescope data releases
- NASA
- ESA
- JPL
- STScI
- ESO
- LIGO
- ATel
- GCN

8. Low-public-value penalty

De-emphasize:

- generic astronomy explainers
- low-significance press releases
- routine archive maintenance
- routine catalog row changes
- duplicate news rewrites
- single-source hype
- social-only claims
- alien-life speculation without credible source support
- preliminary transients with no follow-up
- data-heavy sources outside allowlist
- old papers resurfaced as if new

9. Hype and speculation penalty

De-emphasize or block:

- alien megastructure claims unless official/peer-reviewed and carefully labeled
- "life found" claims unless official source says that
- sensationalized headlines not supported by source evidence
- UFO conflation
- social rumors
- unreviewed preprint hype if literature sources are ever enabled
- image-only clickbait

The design must include a sample scoring formula.

Example:

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

The design must explain that "frequency of appearance" means independent cross-source convergence, not raw duplicate counts.

Bad ranking:

- 30 rewrites of the same generic "black holes are weird" article dominate.

Good ranking:

- GCN alert for gamma-ray burst.
- Follow-up GCN circulars.
- Swift/Fermi or other mission source.
- ATel follow-up.
- Observatory release or credible science outlet.
- All tied by event id, coordinates, and time.

SECTION 9: Source category design

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

1. Planetary science and solar system missions.

2. Planetary data archives and mission data releases.

3. Minor bodies, comet science, and small-body science context.

4. Exoplanets and planetary systems.

5. Space telescopes and observatory science releases.

6. High-energy astrophysics and GCN.

7. Gravitational-wave and multi-messenger astronomy.

8. Transient astronomy, supernovae, novae, and ATel/TNS.

9. Astronomy archive and catalog candidates.

10. Literature metadata candidates.

11. International observatory and agency feeds.

12. Science journalism and public media.

13. Social/community echoes.

14. Source health and disabled states.

SECTION 10: Science, hype, and sensitivity posture

Design this carefully.

Rules:

- Store source-provided public metadata only.
- Do not store full article bodies.
- Do not download science data products.
- Do not bulk-ingest catalogs.
- Do not archive social posts long term.
- Do not treat social claims as verified fact.
- Do not invent scientific meaning.
- Do not interpret papers beyond metadata.
- Do not turn console-1701 into a literature review engine.
- Do not turn it into an observatory archive mirror.
- Do not amplify alien-life or UFO claims without strict source framing.
- Do not use "life found" unless an official or peer-reviewed source says it directly.
- Prefer official agency, observatory, mission, and recognized alert-network source labels.
- For transient alerts, label preliminary status clearly.
- For gravitational-wave candidates, preserve alert status and retraction status if provided.
- For exoplanets, distinguish candidate, confirmed, archive update, paper claim, and agency release.
- For telescope science, distinguish image release, data release, peer-reviewed result, mission update, and press release.
- For science journalism, treat it as news metadata, not primary scientific evidence.
- Preserve source links in evidence so the user can click official sources.

SECTION 11: Source freshness and retention

Design short retention.

Default candidate retention:

- Raw fetch diagnostics: 7 days or less.
- Raw payload debug: disabled by default. If ever enabled, 6 hours max by default.
- Agency science release metadata: 7 days.
- Mission update metadata: 7 to 14 days.
- Planetary mission science metadata: 14 days.
- Exoplanet discovery metadata: 14 to 30 days.
- Exoplanet catalog-update metadata: 7 days unless configured.
- GCN notice metadata: 7 to 14 days.
- GCN circular metadata: 14 days.
- ATel metadata: 14 days.
- TNS metadata: 14 days if enabled.
- Gravitational-wave alert metadata: 14 to 30 days, with retraction/follow-up state.
- Telescope data release metadata: 14 to 30 days.
- PDS/archive release metadata: 14 to 30 days.
- Literature metadata: disabled by default. If enabled, 7 to 14 days.
- News headline metadata: 7 days.
- Event clusters: 7 to 14 days, 30 days for major confirmed discoveries if configured.
- Source health: 30 days.
- Ranking explanations: same as event/item retention.
- Social metadata, if ever enabled: 24 to 72 hours unless source terms require shorter or prohibit storage.

Every ingest run in later phases must purge expired data.

No article body archive.

No bulk astronomy data archive.

No permanent social archive.

SECTION 12: Adapter design

Design future adapter families.

Do not implement now.

Required adapter families:

rss_atom:
- NASA RSS.
- JPL RSS.
- ESA RSS.
- STScI/Hubble/JWST feeds.
- ESO feeds.
- NOIRLab feeds.
- science journalism feeds.
- Must parse title, URL, published timestamp, description, categories.
- Must bound description length.
- Must not fetch article bodies.

nasa_api_json:
- NASA Open APIs, only if a specific useful source is configured.
- Avoid imagery-heavy APIs unless needed.
- Respect API key handling.
- Do not store API keys in repo.

pds_api_candidate:
- NASA PDS API.
- Use only for metadata-level recent data release checks.
- Do not download science products.
- Do not bulk mirror PDS.
- Must use strict collection allowlists and row caps.

exoplanet_archive_api:
- NASA Exoplanet Archive API or TAP.
- Use only allowlisted metadata queries.
- Must distinguish candidate vs confirmed when source provides it.
- Do not run broad catalog downloads.

mast_api_candidate:
- MAST API for mission metadata and configured small queries.
- Must not download science products.
- Must avoid broad catalog searches.
- Use fixture-only until a narrow query contract exists.

heasarc_api_candidate:
- HEASARC source for high-energy mission metadata.
- Must verify current machine-readable endpoint.
- Use fixture-only until narrow query contract exists.

gcn_notice_candidate:
- NASA GCN notices.
- Must preserve notice type, event id, coordinates if provided, event time, instrument, alert status, and source URL.
- Must handle preliminary, update, and retraction states.
- Must not require Kafka dependency initially unless later approved.
- Fixture-first.

gcn_circular_candidate:
- GCN Circulars.
- Use only if machine-readable or policy-safe endpoint exists.
- Store metadata only.
- Do not scrape if not allowed.
- Fixture/manual-review first.

astronomers_telegram_rss:
- ATel RSS.
- Store telegram metadata and URL.
- Do not store full body unless source allows and user explicitly configures bounded storage.
- Treat as preliminary astronomy communication.

tns_api_candidate:
- TNS API.
- Auth/account/policy-sensitive.
- Disabled by default.
- Must require credentials outside repo if needed.
- Must preserve object name, type, discovery date, reporter, classification, and source URL when allowed.
- Do not bulk ingest.

gracedb_api_candidate:
- GraceDB / LIGO public alert candidate.
- May require special client/dependency or API rules.
- Disabled by default.
- Must preserve public alert id, event id, alert type, false-alarm rate if source provides it, retraction status, sky map URL metadata only, and source URL.
- Do not download sky maps by default.
- Fixture-first.

tap_adql_candidate:
- Generic TAP/ADQL sources.
- Examples: Gaia, SIMBAD, VizieR, ESASky, ESO Archive.
- Heavy-source risk.
- Disabled by default.
- Must require strict query allowlists, row limits, timeout, and no bulk downloads.

simbad_tap_candidate:
- SIMBAD TAP.
- Use only for object-name cross-identification in event evidence if later needed.
- Do not bulk query.
- Cache only short metadata.

vizier_tap_candidate:
- VizieR TAP.
- Use only for specific catalog metadata if later needed.
- Do not bulk query.

gaia_tap_candidate:
- Gaia Archive TAP.
- Disabled by default.
- Use only for narrow configured science release checks, if ever.
- Do not bulk query.

ads_api_candidate:
- NASA ADS API.
- Auth token likely required.
- Disabled by default.
- Use only literature metadata if explicitly configured.
- Do not download papers.
- Do not turn app into a literature-monitoring system.

mpc_api:
- MPC MPECs, NEOCP, observations, and orbits.
- Must verify exact endpoints and usage guidance.
- Store metadata only.
- Avoid high-volume ingestion unless strictly filtered.

jpl_ssd_api:
- JPL SSD/CNEOS APIs.
- Reuse from ORBITAL where useful for science context.
- Must avoid duplicate event inflation between ORBITAL and this layer.

official_api_json:
- Other official JSON endpoints from observatories/agencies.
- Must use timeout, response size caps, and source-specific rate limits.

static_html_headline_candidate:
- Only for official pages or science news pages with no RSS/API.
- Disabled unless homepage extractor support is explicitly allowed.
- Must use per-source selectors.
- No recursive crawling.
- No article-body fetch.
- Robots/policy review required.

source_health_probe_only:
- For dashboards and portals useful as human status references but not suitable for ingestion.

manual_review_only:
- For policy-sensitive, parser-risky, login-required, auth-required, account-required, paywalled, heavy-catalog, or unclear targets.

SECTION 13: Candidate source registry example

Include a YAML-like example in the design document.

Do not edit config.example.yml yet unless prior architecture already requires disabled examples.

The example must be disabled by default.

Example shape:

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
      notes: "Fixture-first. Preserve retraction/preliminary state. Do not download sky maps by default."

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
      notes: "Disabled by default. Metadata-only if ever enabled. No paper downloads."

SECTION 14: UI architecture

Design the eventual page, but do not implement it.

Because SYSTEM may already mean app-health, this section must describe UI only as future/candidate.

Candidate page should use the same console style.

Propose four bays.

Bay 1:
- "Cosmic attention now"
- Highest-ranking events from solar system, exoplanet, transient, telescope, and astrophysics sources.
- Must show why each item is ranked.
- Must show source-family badges.
- Must show official vs science alert vs news vs community convergence.
- Must show observed time and last seen.
- Must not dump generic science headlines.

Bay 2:
- "Solar system and planetary science"
- NASA, JPL, ESA, JAXA, ISRO, PDS, MPC, JPL SSD, planetary missions, solar system bodies.
- Mission science, planetary data releases, solar system object notices, comet/asteroid science.

Bay 3:
- "Beyond the solar system"
- Exoplanets, JWST, Hubble, Roman, TESS, Gaia, MAST, HEASARC, ESO, NOIRLab, NRAO, ALMA, SIMBAD/VizieR candidates.
- Exoplanet discoveries, stellar events, galaxy/cosmology releases, telescope science.

Bay 4:
- "Transient alerts and source health"
- GCN, ATel, TNS, LIGO/GraceDB, GCN circulars, transient candidates, source health, disabled auth-heavy sources.
- Social/community signals only if configured and compliant.
- No fake headlines.
- If disabled, show "Solar System and Beyond sources not configured."

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
- object, mission, telescope, or transient id where applicable
- preliminary/confirmed/retracted status where applicable
- scope-overlap tag where applicable

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
- Source marked manual_review_only.
- SYSTEM naming collision unresolved.

SECTION 15: Evidence model

Every item/event must trace back to source evidence.

For an event, evidence should include:

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
- scientific significance basis
- object or mission match basis
- source diversity basis
- preliminary/confirmed/retracted status
- archive query bounds if any
- auth-required status if any
- retention expiration
- matching tokens
- event type
- event confidence
- policy notes
- low-public-value penalty if applied
- hype penalty if applied
- archive-firehose penalty if applied
- out-of-scope penalty if applied

For planetary science and mission events, evidence must include, where available:

- mission name
- spacecraft
- target body
- instrument
- agency
- publication date
- source URL
- mission phase or milestone
- whether it is science result, mission update, data release, or press release

For exoplanet events, evidence must include, where available:

- planet name
- host star
- system name
- confirmed/candidate status
- discovery method
- archive row or source id
- publication or update date
- source URL
- whether the source says Earth-size, habitable-zone, atmosphere, biosignature, or other high-interest term
- do not infer those terms if source does not say them

For transient and multi-messenger events, evidence must include, where available:

- event id
- transient name
- coordinates
- event time
- notice/circular id
- instrument
- preliminary/update/retraction status
- classification
- source URL
- follow-up count
- associated GCN/ATel/TNS/GraceDB ids
- whether the information is preliminary

For telescope and archive events, evidence must include, where available:

- observatory
- mission
- instrument
- dataset id
- release id
- data release date
- source URL
- whether data products were downloaded
- this should normally say no data products downloaded

For literature metadata events, if ever enabled, evidence must include:

- title
- authors
- source
- bibcode or DOI
- publication date
- abstract URL if allowed
- no full paper body
- no paywall bypass
- auth token status if ADS is used

SECTION 16: Source health

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
- heavy_archive_disabled
- needs_terms_review
- needs_scope_filter
- naming_collision_unresolved
- hype_blocked
- archive_firehose_blocked

Source health must be visible in app-health SYSTEM later and summarized in this candidate scope's Bay 4 or footer strip.

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

SECTION 17: First implementation sequence

Design future phases.

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
- Create fixture files for:
  NASA/JPL RSS item.
  ESA RSS item.
  NASA Exoplanet Archive tiny metadata response.
  MAST tiny metadata response.
  PDS tiny metadata response.
  GCN notice fixture.
  GCN circular fixture.
  ATel RSS fixture.
  TNS fake auth-required source-health fixture, no real credentials.
  GraceDB fake or public-alert fixture, no real credentials.
  LIGO public alert fixture.
  JWST/Hubble release RSS fixture.
  Science news RSS fixture.
- Parse fixtures only.
- Store normalized metadata.
- No live fetch.

Phase S4: event correlation
- Deterministic token/object/mission/time/source-family matching.
- No LLM.
- Tests for convergence.
- Tests for duplicate suppression.
- Tests for source-family diversity.
- Tests for transient id matching.
- Tests for object/mission matching.
- Tests for solar-system-beyond vs ORBITAL vs GLOBAL scope routing.

Phase S5: ranking
- Implement scoring model.
- Explain ranking in JSON.
- Tests for official science source, source diversity, recency, scientific significance, transient status, mission relevance, hype penalty, archive-firehose penalty, stale-source penalty, and out-of-scope penalty.

Phase S6: UI disabled and fixture-backed states
- Add candidate UI only after naming decision.
- Fixture-backed in tests only.
- No live fetch.
- No fake headlines.

Phase S7: official RSS live ingest, opt-in only
- Start with one safe official feed.
- Suggested first candidates:
  JPL RSS.
  ESA RSS.
  NASA RSS.
  Hubble/JWST RSS if verified.
  ATel RSS if policy-safe.
- Must be disabled by default.
- Must use explicit command.
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
- Must preserve preliminary/update/retraction state.
- No sky-map downloads by default.

Phase S10: heavy archive and catalog candidates
- SIMBAD, VizieR, Gaia, ESASky, ESO Archive, ADS.
- Disabled by default.
- Use only strict allowlists.
- Prefer source_health_probe_only or metadata-only.
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

SECTION 18: Testing strategy

Design tests.

Required tests:

Config:
- Solar System and Beyond layer disabled by default.
- Source disabled by default.
- Invalid source class rejected.
- Invalid adapter rejected.
- Social source rejected unless allow_social_sources true.
- Heavy archive source rejected unless include_large_archive_queries true.
- Auth-required source marked auth_required unless credentials are explicitly configured outside repo.
- Literature metadata source rejected unless include_literature_metadata true.
- Homepage extraction rejected unless allow_homepage_extractors true.
- Source without URL rejected unless adapter supports no URL.
- Naming collision with SYSTEM is represented as unresolved until user decision.
- Secrets not allowed in config.example.yml.

Registry:
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
- TNS auth-required fixture returns auth_required without network.
- GraceDB auth/policy fixture returns disabled/auth_required without network unless configured.
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
- Same event from multiple news outlets counts as news-family convergence but not endless duplicate inflation.
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
- Disabled/not configured/stale/failing/auth_required/heavy_archive_disabled states distinct.
- Naming collision state is visible until resolved.

UI tests for later:
- No fake headlines.
- Empty states clear.
- Evidence visible.
- Ranking reason visible.
- Source health visible.
- Object/mission/transient label visible.
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

SECTION 19: Backlog update requirements

Update BACKLOG.md.

Add a section named:

Solar System and Beyond Recent Signal Layer

Add concrete backlog items with Status: not implemented.

Include at least:

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
- Deterministic ranking for official science, source diversity, rarity, transient status, and hype penalty.
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

SECTION 20: Non-goals

List non-goals.

Required:

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
- No bypassing Reddit/X/API restrictions.
- No claiming social chatter is verified fact.
- No treating science journalism as primary scientific evidence.
- No treating duplicate articles as independent confirmation.
- No burying LOCAL, REGIONAL, NATIONAL, GLOBAL, ORBITAL, or app-health SYSTEM urgent items under deep-space headlines.
- No automatic API key discovery or secret storage.
- No broad SIMBAD, VizieR, Gaia, MAST, PDS, HEASARC, Exoplanet Archive, or ADS firehose ingestion.

SECTION 21: Final response requirements

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
6. Confirmation that this Solar System and Beyond layer remains disabled by default.
7. Confirmation that no tab rename or route rename was implemented.
8. Confirmation that the SYSTEM naming collision was documented.
9. Test commands run and exact results.
10. git diff --check result.
11. git status --short.
12. BACKLOG entries added.
13. Uncertainties and source targets needing later verification.

Do not commit.

Do not push.

Do not install packages.

Do not run sudo.

Do not fetch live external sites.

Do not run curl against source targets for this task.
```

This is intentionally not a console-health `SYSTEM` prompt. It gives Codex a safe way to capture what you just asked for without letting it trample the earlier SYSTEM meaning.

[1]: https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html?utm_source=chatgpt.com "Using the Application Programming Interface (API)"
