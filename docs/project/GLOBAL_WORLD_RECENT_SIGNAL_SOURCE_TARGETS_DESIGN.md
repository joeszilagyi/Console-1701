# GLOBAL World Recent Signal Source Targets Design

## SECTION 1: Purpose

The GLOBAL scope is the world recent-signal layer for console-1706. It should tell the user what is
happening globally, with source provenance, observed time, source kind, ranking reason, freshness,
and evidence. It is a local, deterministic metadata surface for public-impact world signals, not a
crawler, not a runtime LLM summarizer, and not a geopolitical analysis product.

The GLOBAL scope is not:

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

The GLOBAL scope is:

- A local, short-retention metadata dashboard.
- A deterministic cross-source event detector for global public-impact signals.
- A source-health aware recent-signal system.
- A GLOBAL tab in console-1706 that can surface disasters, humanitarian crises, disease outbreaks,
  severe weather, tropical cyclones, earthquakes, volcanoes, air quality, international
  public-health alerts, geopolitical crises, supply-chain disruption, global cyber risk,
  international institutional actions, and global news.
- A way to rank items by independent source convergence, official severity, global reach, U.S. or
  local relevance, freshness, and user-configured source priority.

"Global" means useful public, configured, lawful, recent signals that the user chooses to enable.
It does not mean unbounded crawling, private data collection, global social surveillance, automated
geopolitical analysis, or broad open-data firehose ingestion.

## SECTION 2: Global scope boundaries

Default GLOBAL scope:

- World events outside the United States.
- International events that affect multiple countries.
- International organizations and global systems.
- Global disaster, humanitarian, health, weather, hazard, conflict, infrastructure, economy,
  transport, and cyber signals.
- U.S. events only when they are part of a global event or directly affect global systems.
- Washington or Seattle events only when they are part of a global signal, such as port logistics,
  aviation systems, international health, major earthquake/tsunami basin impacts, or global supply
  chain.
- Global news outlets and international public media when they cover events with broad world
  importance.
- Country-level official signals only when they are strong enough to matter globally or when
  configured by the user.

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
- Sources requiring login, payment, scraping around controls, or tokens not explicitly configured by
  the user.

Future disabled-by-default config escape hatch:

```yaml
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
```

## SECTION 3: Relationship to NATIONAL, REGIONAL, LOCAL, ORBITAL, and OVERVIEW

GLOBAL should complement the other scopes rather than duplicate them.

Rules:

- GLOBAL should not duplicate NATIONAL unless the U.S. item has direct international or
  global-system impact.
- GLOBAL should not duplicate REGIONAL or LOCAL unless the regional/local item is part of a global
  event or has global impact.
- NATIONAL owns U.S. federal, domestic, regulatory, recall, national weather, U.S. aviation, U.S.
  cyber, and U.S. official public-impact signals.
- REGIONAL owns Washington / PNW hazards, transit, state emergency, wildfire, smoke, and regional
  news.
- LOCAL owns Seattle-level signals.
- ORBITAL owns space, astronomy, satellites, solar weather, launch, NEO, NASA/JPL sky signals, and
  orbital infrastructure signals.
- GLOBAL may link to ORBITAL only when a space-weather or satellite disruption has global human
  impact, but canonical space telemetry stays ORBITAL.
- OVERVIEW should select the highest-priority items from LOCAL, REGIONAL, NATIONAL, GLOBAL, ORBITAL,
  and SYSTEM without burying urgent local/system issues.
- If a GLOBAL item directly affects Seattle, Washington, or the United States, it can be tagged
  `LOCAL_IMPACT`, `REGIONAL_IMPACT`, or `NATIONAL_IMPACT` while canonical scope remains `GLOBAL`.
- If a NATIONAL item becomes global, such as a U.S. policy action causing international market or
  diplomatic effects, it can be promoted or cross-listed into GLOBAL with evidence.

Examples:

- Major earthquake in Japan with tsunami watch across the Pacific: GLOBAL, possible REGIONAL_IMPACT
  or LOCAL_IMPACT.
- Global WHO Disease Outbreak News item: GLOBAL.
- CDC domestic health alert: NATIONAL unless WHO/ECDC/other international sources also show global
  spread.
- Seattle port issue: LOCAL and REGIONAL, GLOBAL only if international shipping impact is clear.
- Russia/Ukraine diplomatic development from UN plus Reuters/BBC: GLOBAL.
- U.S. FAA ground stop: NATIONAL, GLOBAL only if international aviation impact is clear.
- Solar storm warning affecting satellites and grids: ORBITAL canonical, GLOBAL impact tag if
  widespread infrastructure relevance exists.
- GDACS orange/red cyclone alert: GLOBAL.
- Routine foreign election story: GLOBAL only if configured or major public-impact threshold is met.
- Routine UN speech: low priority unless tied to an active crisis, sanction, resolution,
  humanitarian emergency, or global event.

## SECTION 4: Seed source target inventory

This table is a candidate inventory, not a verification result. No live source verification was
performed in this task. `official_page_seen` means the source is a source-identifiable official
candidate from the prompt context, not that parser behavior has been tested. URLs that require
endpoint, feed, auth, account, token, data licensing, terms, or selector review remain
`candidate_needs_verification` or `candidate_policy_sensitive`.

Risk values use `low`, `medium`, or `high`. Future phases use `G0` through `G10` from the
implementation sequence.

| source_key | source_name | source_family | source_class | scope | raw_url | expected_access_kind | likely_adapter_type | likely_refresh_interval | initial_priority | official_status | privacy_risk | policy_risk | parser_risk | retention_sensitivity | verification_status | why_it_matters | future_phase |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gdacs_home | GDACS | gdacs | official_global_alert | GLOBAL | https://www.gdacs.org/ | public official webpage | source_health_probe_only | 24 h | 70 | official | low | low | low | low | official_page_seen | Global disaster alert authority reference. | G6 |
| gdacs_feed_reference | GDACS feed reference | gdacs | official_global_alert | GLOBAL | https://www.gdacs.org/feed_reference.aspx | official feed reference | gdacs_feed | 10 min | 100 | official | low | low | medium | medium | official_page_seen | Best first candidate for global disaster alert feed discovery. | G6 |
| gdacs_api_swagger | GDACS API Swagger | gdacs | official_global_alert | GLOBAL | https://www.gdacs.org/gdacsapi/swagger/index.html | official API docs | gdacs_api | 10 min | 95 | official | low | low | medium | medium | official_page_seen | Candidate API for disaster events after fixture tests. | G6 |
| gdacs_api_quickstart | GDACS API quickstart PDF | gdacs | source_health_only | GLOBAL | https://www.gdacs.org/Documents/2025/GDACS_API_quickstart_v1.pdf | official PDF docs | manual_review_only | manual | 10 | official | low | low | low | low | user_seeded | Implementation reference, not an ingest source. | G1 |
| reliefweb_home | ReliefWeb | reliefweb | official_humanitarian | GLOBAL | https://reliefweb.int/ | public official-ish humanitarian portal | source_health_probe_only | 24 h | 50 | official_candidate | low | low | low | low | official_page_seen | Humanitarian source authority reference. | G6 |
| reliefweb_disasters | ReliefWeb disasters | reliefweb | official_humanitarian | GLOBAL | https://reliefweb.int/disasters | public disaster page/API candidate | reliefweb_api | 30 min | 95 | official_candidate | medium | low | medium | medium | official_page_seen | Strong disaster/humanitarian metadata source. | G6 |
| reliefweb_updates | ReliefWeb updates | reliefweb | official_humanitarian | GLOBAL | https://reliefweb.int/updates | public updates page/API candidate | reliefweb_api | 30 min | 80 | official_candidate | medium | low | medium | medium | official_page_seen | Humanitarian report metadata source. | G6 |
| reliefweb_api_help | ReliefWeb API help | reliefweb | source_health_only | GLOBAL | https://reliefweb.int/help/api | public API help | manual_review_only | manual | 10 | official_candidate | low | low | low | low | user_seeded | API implementation reference. | G1 |
| reliefweb_api_docs | ReliefWeb API docs | reliefweb | source_health_only | GLOBAL | https://apidoc.reliefweb.int/ | public API docs | reliefweb_api | none | 10 | official_candidate | low | low | low | low | user_seeded | API implementation reference. | G1 |
| reliefweb_api_endpoints | ReliefWeb API endpoints | reliefweb | official_humanitarian | GLOBAL | https://apidoc.reliefweb.int/endpoints | public API endpoint docs | reliefweb_api | 30 min | 95 | official_candidate | low | low | medium | medium | official_page_seen | Endpoint docs for reports/disasters. | G6 |
| hdx_home | HDX | hdx | heavy_open_data_candidate | GLOBAL | https://data.humdata.org/ | humanitarian data catalog | data_catalog_candidate | manual | 30 | official_candidate | medium | medium | high | medium | candidate_policy_sensitive | Catalog only until scoped datasets are promoted. | G9 |
| hdx_hapi_page | HDX HAPI | hdx | official_humanitarian | GLOBAL | https://data.humdata.org/hapi | public API docs | hdx_hapi_json | 6 h | 65 | official_candidate | medium | medium | medium | medium | candidate_policy_sensitive | Humanitarian indicator candidate requiring strict filters. | G7 |
| hapi_service | HAPI service | hdx | official_humanitarian | GLOBAL | https://hapi.humdata.org/ | public API service | hdx_hapi_json | 6 h | 65 | official_candidate | medium | medium | medium | medium | candidate_policy_sensitive | API endpoint candidate, disabled by default. | G7 |
| hdx_devs | HDX developer FAQ | hdx | source_health_only | GLOBAL | https://data.humdata.org/faqs/devs | public developer docs | manual_review_only | manual | 10 | official_candidate | low | medium | low | low | user_seeded | Terms/API reference. | G1 |
| unocha_home | UN OCHA | unocha | official_humanitarian | GLOBAL | https://www.unocha.org/ | public official webpage | source_health_probe_only | 24 h | 50 | official | low | low | low | low | official_page_seen | Humanitarian coordination authority reference. | G7 |
| unocha_news | UN OCHA news | unocha | official_humanitarian | GLOBAL | https://www.unocha.org/news-and-stories | public official webpage/feed candidate | rss_atom | 60 min | 70 | official | medium | low | medium | medium | candidate_needs_verification | OCHA crisis updates and humanitarian context. | G7 |
| unocha_reports | OCHA reports | unocha | official_humanitarian | GLOBAL | https://reports.unocha.org/ | public official reports site | humanitarian_api_json | 60 min | 75 | official | medium | low | medium | medium | candidate_needs_verification | Situation report candidate. | G7 |
| cerf_home | CERF | cerf | official_humanitarian | GLOBAL | https://cerf.un.org/ | public official webpage | source_health_probe_only | 24 h | 25 | official | low | low | low | low | official_page_seen | Humanitarian financing context, low priority by default. | G9 |
| ifrc_emergencies | IFRC emergencies | ifrc | official_humanitarian | GLOBAL | https://www.ifrc.org/emergencies | public official webpage/feed candidate | rss_atom | 60 min | 75 | official | medium | low | medium | medium | candidate_needs_verification | Emergency response source. | G7 |
| ifrc_go | IFRC GO | ifrc | official_humanitarian | GLOBAL | https://go.ifrc.org/ | public dashboard/API candidate | humanitarian_api_json | 60 min | 65 | official_candidate | medium | medium | high | medium | candidate_needs_verification | Operational humanitarian data candidate; no dashboard scraping. | G7 |
| icrc_news | ICRC news | icrc | official_humanitarian | GLOBAL | https://www.icrc.org/en/news-and-events | public official webpage/feed candidate | rss_atom | 2 h | 55 | official | medium | low | medium | medium | candidate_needs_verification | Humanitarian/conflict source with careful labeling. | G8 |
| ifrc_rss | IFRC RSS | ifrc | official_humanitarian | GLOBAL | https://www.ifrc.org/rss.xml | public RSS feed | rss_atom | 60 min | 65 | official | medium | low | medium | medium | candidate_needs_verification | Feed candidate for IFRC updates. | G7 |
| un_news | UN News | un_news | official_diplomacy | GLOBAL | https://news.un.org/en/ | public official webpage | rss_atom | 60 min | 70 | official | low | low | medium | low | candidate_needs_verification | UN global news and institution signal. | G6 |
| un_news_rss | UN News RSS | un_news | official_diplomacy | GLOBAL | https://news.un.org/en/rss.xml | public RSS feed | rss_atom | 60 min | 75 | official | low | low | medium | low | candidate_needs_verification | Preferred UN News metadata path. | G6 |
| un_press | UN Press | un_press | official_diplomacy | GLOBAL | https://press.un.org/en | public official webpage | rss_atom | 60 min | 55 | official | low | low | medium | low | candidate_needs_verification | Official UN press source. | G7 |
| un_press_rss | UN Press RSS | un_press | official_diplomacy | GLOBAL | https://press.un.org/en/rss.xml | public RSS feed | rss_atom | 60 min | 60 | official | low | low | medium | low | candidate_needs_verification | Preferred UN press metadata path. | G7 |
| un_security_council | UN Security Council | un_security_council | official_diplomacy | GLOBAL | https://www.un.org/securitycouncil/ | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | official_page_seen | Security Council authority reference. | G7 |
| un_security_council_news | UN Security Council news | un_security_council | official_diplomacy | GLOBAL | https://www.un.org/securitycouncil/content/news | public official webpage | static_html_headline_candidate | 60 min | 65 | official | low | low | medium | low | candidate_needs_verification | Institution action tied to active crises. | G7 |
| un_ga_rss | UN General Assembly RSS | un_ga | official_diplomacy | GLOBAL | https://www.un.org/en/ga/rss/index.shtml | public RSS index | rss_atom | 2 h | 35 | official | low | low | medium | low | candidate_needs_verification | GA feed source, filter heavily. | G8 |
| ungeneva_rss | UN Geneva RSS | un_geneva | official_diplomacy | GLOBAL | https://www.ungeneva.org/en/news-media/rss | public RSS feed | rss_atom | 2 h | 35 | official | low | low | medium | low | candidate_needs_verification | Geneva institution source. | G8 |
| ohchr_press | OHCHR press releases | ohchr | official_human_rights | GLOBAL | https://www.ohchr.org/en/press-releases | public official webpage/feed candidate | rss_atom | 2 h | 45 | official | medium | low | medium | medium | candidate_needs_verification | Human-rights alerts need source labeling. | G8 |
| ohchr_rss | OHCHR RSS | ohchr | official_human_rights | GLOBAL | https://www.ohchr.org/en/rss.xml | public RSS feed | rss_atom | 2 h | 45 | official | medium | low | medium | medium | candidate_needs_verification | Preferred OHCHR metadata path. | G8 |
| undp_news | UNDP news | undp | official_development | GLOBAL | https://www.undp.org/news-centre | public official webpage/feed candidate | rss_atom | 6 h | 20 | official | low | low | medium | low | candidate_needs_verification | Development source, low priority unless crisis-linked. | G8 |
| unhcr_news | UNHCR news | unhcr | official_humanitarian | GLOBAL | https://www.unhcr.org/news | public official webpage/feed candidate | rss_atom | 2 h | 55 | official | medium | low | medium | medium | candidate_needs_verification | Refugee/displacement source. | G8 |
| unhcr_rss | UNHCR RSS | unhcr | official_humanitarian | GLOBAL | https://www.unhcr.org/rss.xml | public RSS feed | rss_atom | 2 h | 55 | official | medium | low | medium | medium | candidate_needs_verification | Preferred UNHCR metadata path. | G8 |
| unicef_press | UNICEF press releases | unicef | official_humanitarian | GLOBAL | https://www.unicef.org/press-releases | public official webpage/feed candidate | rss_atom | 2 h | 45 | official | medium | low | medium | medium | candidate_needs_verification | Child/humanitarian source, careful labeling. | G8 |
| unicef_rss | UNICEF RSS feeds | unicef | official_humanitarian | GLOBAL | https://www.unicef.org/rss-feeds | public RSS index | rss_atom | 2 h | 45 | official | medium | low | medium | medium | candidate_needs_verification | Feed discovery. | G8 |
| wfp_news | WFP news | wfp | official_humanitarian | GLOBAL | https://www.wfp.org/news | public official webpage/feed candidate | rss_atom | 2 h | 55 | official | medium | low | medium | medium | candidate_needs_verification | Food security/humanitarian source. | G8 |
| fao_news | FAO newsroom | fao | official_development | GLOBAL | https://www.fao.org/newsroom/en | public official webpage/feed candidate | rss_atom | 6 h | 35 | official | low | low | medium | low | candidate_needs_verification | Food/agriculture institution signal. | G8 |
| fao_news_rss | FAO news RSS | fao | official_development | GLOBAL | https://www.fao.org/news/rss | public RSS feed | rss_atom | 6 h | 35 | official | low | low | medium | low | candidate_needs_verification | Preferred FAO metadata path. | G8 |
| iaea_news | IAEA news | iaea | official_nuclear_safety | GLOBAL | https://www.iaea.org/news | public official webpage/feed candidate | rss_atom | 60 min | 65 | official | low | low | medium | medium | candidate_needs_verification | Nuclear safety/institution source. | G7 |
| iaea_feeds | IAEA feeds | iaea | official_nuclear_safety | GLOBAL | https://www.iaea.org/feeds | public official feed index | rss_atom | 60 min | 65 | official | low | low | medium | medium | candidate_needs_verification | Preferred feed discovery for IAEA. | G7 |
| iaea_news_alt | IAEA news alternate | iaea | official_nuclear_safety | GLOBAL | https://www-news.iaea.org/ | public official candidate | source_health_probe_only | 24 h | 35 | official_candidate | low | medium | medium | low | candidate_needs_verification | Alternate/legacy source; verify before use. | G9 |
| nato_news | NATO news | nato | official_diplomacy | GLOBAL | https://www.nato.int/cps/en/natohq/news.htm | public official webpage/feed candidate | rss_atom | 2 h | 35 | official | low | low | medium | low | candidate_needs_verification | Security institution context, filter heavily. | G8 |
| osce_press | OSCE press releases | osce | official_diplomacy | GLOBAL | https://www.osce.org/press-releases | public official webpage/feed candidate | rss_atom | 2 h | 35 | official | low | low | medium | low | candidate_needs_verification | Institution context, filter heavily. | G8 |
| who_home | WHO | who | official_public_health | GLOBAL | https://www.who.int/ | public official webpage | source_health_probe_only | 24 h | 50 | official | low | low | low | low | official_page_seen | Global health authority reference. | G6 |
| who_don | WHO Disease Outbreak News | who | official_public_health | GLOBAL | https://www.who.int/emergencies/disease-outbreak-news | public official webpage/API candidate | who_api_json | 60 min | 100 | official | medium | low | medium | medium | official_page_seen | Strong first candidate for global outbreak events. | G6 |
| who_don_api | WHO DON API help | who | official_public_health | GLOBAL | https://www.who.int/api/news/diseaseoutbreaknews/sfhelp | public official API help | who_api_json | 60 min | 100 | official | medium | low | medium | medium | official_page_seen | Candidate API shape for Disease Outbreak News. | G6 |
| who_outbreaks_api | WHO outbreaks API help | who | official_public_health | GLOBAL | https://www.who.int/api/news/outbreaks/sfhelp | public official API help | who_api_json | 60 min | 90 | official | medium | low | medium | medium | candidate_needs_verification | Outbreak API candidate. | G6 |
| who_newsroom | WHO newsroom | who | official_public_health | GLOBAL | https://www.who.int/news-room | public official webpage | rss_atom | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | Health news, lower than DON. | G8 |
| who_rss_feeds | WHO RSS feeds | who | official_public_health | GLOBAL | https://www.who.int/news-room/rss-feeds | public official feed index | rss_atom | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | Feed discovery. | G8 |
| who_emro_rss | WHO EMRO RSS | who_emro | official_public_health | GLOBAL | https://www.emro.who.int/rss-feeds.html | public official feed index | rss_atom | 2 h | 40 | official | medium | low | medium | medium | candidate_needs_verification | Regional health signal. | G8 |
| who_afro_rss | WHO AFRO RSS | who_afro | official_public_health | GLOBAL | https://www.afro.who.int/rss-feeds | public official feed index | rss_atom | 2 h | 40 | official | medium | low | medium | medium | candidate_needs_verification | Regional health signal. | G8 |
| paho_news | PAHO news | paho | official_public_health | GLOBAL | https://www.paho.org/en/news | public official webpage/feed candidate | rss_atom | 2 h | 45 | official | medium | low | medium | medium | candidate_needs_verification | Americas health signal. | G8 |
| paho_rss | PAHO RSS | paho | official_public_health | GLOBAL | https://www.paho.org/en/rss.xml | public RSS feed | rss_atom | 2 h | 45 | official | medium | low | medium | medium | candidate_needs_verification | Preferred PAHO metadata path. | G8 |
| ecdc_news | ECDC news | ecdc | official_public_health | GLOBAL | https://www.ecdc.europa.eu/en/news-events | public official webpage/feed candidate | ecdc_rss | 2 h | 50 | official | medium | low | medium | medium | candidate_needs_verification | Europe public-health signal. | G7 |
| ecdc_rss | ECDC RSS feeds | ecdc | official_public_health | GLOBAL | https://www.ecdc.europa.eu/en/rss-feeds | public RSS index | ecdc_rss | 2 h | 50 | official | medium | low | medium | medium | candidate_needs_verification | Preferred ECDC metadata path. | G7 |
| africa_cdc_news | Africa CDC news | africa_cdc | official_public_health | GLOBAL | https://africacdc.org/news/ | public official webpage/feed candidate | rss_atom | 2 h | 45 | official | medium | low | medium | medium | candidate_needs_verification | Africa health signal. | G8 |
| africa_cdc_rss | Africa CDC RSS | africa_cdc | official_public_health | GLOBAL | https://africacdc.org/rss-feed/ | public RSS feed | rss_atom | 2 h | 45 | official | medium | low | medium | medium | candidate_needs_verification | Preferred Africa CDC metadata path. | G8 |
| cdc_travel_notices | CDC travel notices | cdc_travel | official_public_health | GLOBAL | https://www.cdc.gov/travel/notices | public official webpage/feed candidate | rss_atom | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | U.S. travel-health global impact source. | G8 |
| cdc_travel_rss | CDC travel RSS | cdc_travel | official_public_health | GLOBAL | https://www.cdc.gov/travel/rss | public RSS feed | rss_atom | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | Preferred CDC travel metadata path. | G8 |
| woah_wahis_info | WOAH WAHIS information | woah | official_public_health | GLOBAL | https://www.woah.org/en/what-we-do/animal-health-and-welfare/disease-data-collection/world-animal-health-information-system/ | public official webpage | source_health_probe_only | 24 h | 30 | official | low | low | medium | low | official_page_seen | Animal-health source discovery. | G9 |
| wahis | WAHIS | woah | official_public_health | GLOBAL | https://wahis.woah.org/ | public dashboard/API candidate | official_api_json | 6 h | 45 | official_candidate | low | medium | high | medium | candidate_needs_verification | Animal disease data candidate; no dashboard scraping. | G9 |
| fao_animal_health | FAO animal health | fao | official_public_health | GLOBAL | https://www.fao.org/animal-health/en | public official webpage | source_health_probe_only | 24 h | 25 | official | low | low | low | low | official_page_seen | Animal-health reference. | G9 |
| fao_plant_health | FAO plant health | fao | official_environment | GLOBAL | https://www.fao.org/plant-health/en | public official webpage | source_health_probe_only | 24 h | 25 | official | low | low | low | low | official_page_seen | Plant-health reference. | G9 |
| wmo_sww | WMO severe weather | wmo | official_weather_hazard | GLOBAL | https://severeweather.wmo.int/ | public official webpage | cap_alerts | 15 min | 90 | official | low | low | medium | medium | official_page_seen | Global severe weather warning source candidate. | G7 |
| wmo_sources | WMO warning sources | wmo | official_weather_hazard | GLOBAL | https://severeweather.wmo.int/sources.html | public official source index | cap_alerts | 15 min | 90 | official | low | low | medium | medium | official_page_seen | CAP/source discovery for WMO warnings. | G7 |
| wmo_public | WMO public site | wmo | official_weather_hazard | GLOBAL | https://public.wmo.int/ | public official webpage | source_health_probe_only | 24 h | 35 | official | low | low | low | low | official_page_seen | WMO authority reference. | G9 |
| wmo_news | WMO news | wmo | official_weather_hazard | GLOBAL | https://wmo.int/news | public official webpage/feed candidate | rss_atom | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | Global weather institution news. | G8 |
| wmo_rss | WMO RSS | wmo | official_weather_hazard | GLOBAL | https://wmo.int/rss.xml | public RSS feed | rss_atom | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | Preferred WMO metadata path. | G8 |
| nhc_global_home | NHC | noaa_nhc | official_tropical_cyclone | GLOBAL | https://www.nhc.noaa.gov/ | public official webpage | source_health_probe_only | 30 min | 60 | official | low | low | low | low | official_page_seen | Atlantic/Eastern Pacific tropical cyclone source. | G7 |
| nhc_rss | NHC RSS info | noaa_nhc | official_tropical_cyclone | GLOBAL | https://www.nhc.noaa.gov/aboutrss.shtml | official feed docs | rss_atom | 10 min | 85 | official | low | low | medium | medium | candidate_needs_verification | Feed discovery for advisories. | G7 |
| nhc_data | NHC data | noaa_nhc | official_tropical_cyclone | GLOBAL | https://www.nhc.noaa.gov/data/ | official data page | official_api_json | 10 min | 85 | official | low | low | medium | medium | candidate_needs_verification | Advisory data candidate. | G7 |
| nhc_gis | NHC GIS | noaa_nhc | official_tropical_cyclone | GLOBAL | https://www.nhc.noaa.gov/gis/ | official GIS page | geojson_feed | 10 min | 75 | official | low | low | medium | medium | candidate_needs_verification | Storm geospatial source candidate. | G7 |
| metoffice_world_warnings | Met Office world warnings | metoffice | official_weather_hazard | GLOBAL | https://www.metoffice.gov.uk/weather/warnings-and-advice/world-warnings | public official webpage | source_health_probe_only | 6 h | 25 | official | low | low | medium | low | candidate_needs_verification | Human reference for world warnings. | G9 |
| cyclocane_home | Cyclocane | cyclocane | unofficial_aggregator | GLOBAL | https://www.cyclocane.com/ | public unofficial webpage | source_health_probe_only | manual | 10 | unofficial | low | high | high | low | unofficial_secondary | Human comparison only; not official. | G9 |
| cyclocane_rss | Cyclocane RSS | cyclocane | unofficial_aggregator | GLOBAL | https://www.cyclocane.com/rss/ | public unofficial RSS | manual_review_only | disabled | 10 | unofficial | low | high | medium | low | unofficial_secondary | Disabled unless policy review supports. | G9 |
| jtwc_home | Joint Typhoon Warning Center | jtwc | official_tropical_cyclone | GLOBAL | https://www.cnmoc.usff.navy.mil/Our-Commands/Fleet-Weather-Center-San-Diego/Joint-Typhoon-Warning-Center/ | public official webpage | static_html_headline_candidate | 30 min | 75 | official | low | low | medium | medium | candidate_needs_verification | Typhoon source candidate. | G7 |
| tsr_home | Tropical Storm Risk | tsr | official_tropical_cyclone | GLOBAL | https://www.tropicalstormrisk.com/ | public forecast candidate | source_health_probe_only | 6 h | 25 | official_candidate | low | medium | medium | low | candidate_needs_verification | Specialist source, not first live target. | G9 |
| tsr_tracker | Tropical Storm Risk tracker | tsr | official_tropical_cyclone | GLOBAL | https://www.tropicalstormrisk.com/tracker/dynamic/main_.html | public tracker | source_health_probe_only | 6 h | 25 | official_candidate | low | medium | high | low | candidate_needs_verification | Avoid tracker scraping. | G9 |
| nws_alerts_global_relevance | NWS alerts global relevance | nws | official_weather_hazard | GLOBAL | https://www.weather.gov/alerts | public official webpage | cap_alerts | 10 min | 25 | official | low | low | medium | low | official_page_seen | NATIONAL canonical; GLOBAL only with global-system impact. | G9 |
| nws_active_alerts_global_relevance | NWS active alerts global relevance | nws | official_weather_hazard | GLOBAL | https://api.weather.gov/alerts/active | documented official API | official_api_json | 10 min | 25 | official | low | low | medium | low | official_page_seen | NATIONAL canonical; GLOBAL only if international impact. | G9 |
| usgs_eq_geojson_global | USGS global earthquake GeoJSON | usgs | official_seismic_volcano | GLOBAL | https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php | official GeoJSON docs | geojson_feed | 5 min | 95 | official | low | low | medium | medium | official_page_seen | Strong first live candidate for global earthquakes. | G6 |
| tsunami_gov_global | Tsunami.gov | tsunami_gov | official_tsunami | GLOBAL | https://www.tsunami.gov/ | public official webpage | static_html_headline_candidate | 10 min | 85 | official | low | low | medium | medium | official_page_seen | Tsunami watch/warning candidate. | G7 |
| glofas_home | Copernicus Global Flood Awareness System | glofas | official_water_flood | GLOBAL | https://global-flood.emergency.copernicus.eu/ | public official flood portal/API candidate | disaster_api_json | 6 h | 70 | official_candidate | low | medium | medium | medium | assistant_seeded | Global flood awareness candidate; verify endpoint/API before parser work. | G7 |
| smithsonian_gvp | Smithsonian Global Volcanism Program | smithsonian_gvp | official_seismic_volcano | GLOBAL | https://volcano.si.edu/ | public specialist official-ish webpage | source_health_probe_only | 24 h | 45 | official_candidate | low | low | low | low | official_page_seen | Volcano authority reference. | G7 |
| smithsonian_weekly | Smithsonian Weekly Volcanic Activity Report | smithsonian_gvp | official_seismic_volcano | GLOBAL | https://volcano.si.edu/reports_weekly.cfm | public specialist report | static_html_headline_candidate | weekly | 70 | official_candidate | low | low | medium | medium | candidate_needs_verification | Weekly volcano activity parser candidate. | G7 |
| nasa_firms_home | NASA FIRMS | nasa_firms | official_wildfire | GLOBAL | https://firms.modaps.eosdis.nasa.gov/ | public official webpage | source_health_probe_only | 24 h | 45 | official | low | medium | low | low | official_page_seen | Global fire source reference. | G7 |
| nasa_firms_api | NASA FIRMS API | nasa_firms | official_wildfire | GLOBAL | https://firms.modaps.eosdis.nasa.gov/api/ | API docs/access candidate | nasa_firms_api_candidate | 60 min | 80 | official | low | medium | medium | medium | candidate_policy_sensitive | Key/config and strict filters required. | G7 |
| nasa_firms_web_services | NASA FIRMS web services | nasa_firms | official_wildfire | GLOBAL | https://firms.modaps.eosdis.nasa.gov/web-services/ | API docs | nasa_firms_api_candidate | 60 min | 80 | official | low | medium | medium | medium | candidate_policy_sensitive | Web service docs, no firehose ingestion. | G7 |
| airnow_global | AirNow global relevance | airnow | official_air_quality | GLOBAL | https://www.airnow.gov/ | public official webpage | source_health_probe_only | 24 h | 25 | official | low | low | low | low | official_page_seen | U.S.-centric; GLOBAL only when useful as smoke/AQI reference. | G9 |
| eea_home | European Environment Agency | eea | official_environment | GLOBAL | https://www.eea.europa.eu/en | public official webpage | source_health_probe_only | 24 h | 25 | official | low | low | low | low | official_page_seen | Europe environment source reference. | G8 |
| eea_news | EEA newsroom | eea | official_environment | GLOBAL | https://www.eea.europa.eu/en/newsroom | public official webpage/feed candidate | rss_atom | 6 h | 30 | official | low | low | medium | low | candidate_needs_verification | Environment news, low default. | G8 |
| copernicus_home | Copernicus | copernicus | official_environment | GLOBAL | https://www.copernicus.eu/en | public official webpage | source_health_probe_only | 24 h | 35 | official | low | low | low | low | official_page_seen | EU Earth observation reference. | G9 |
| copernicus_atmosphere | Copernicus Atmosphere | copernicus | official_air_quality | GLOBAL | https://atmosphere.copernicus.eu/ | public official webpage/feed candidate | rss_atom | 6 h | 45 | official | low | low | medium | low | candidate_needs_verification | Smoke/air-quality/climate context. | G8 |
| copernicus_climate | Copernicus Climate | copernicus | official_environment | GLOBAL | https://climate.copernicus.eu/ | public official webpage/feed candidate | rss_atom | 6 h | 25 | official | low | low | medium | low | candidate_needs_verification | Climate context, low recent-signal priority. | G8 |
| copernicus_emergency | Copernicus Emergency | copernicus | official_disaster | GLOBAL | https://emergency.copernicus.eu/ | public official webpage | data_catalog_candidate | 6 h | 55 | official | low | low | medium | medium | candidate_needs_verification | Emergency mapping source. | G9 |
| copernicus_emsr | Copernicus EMSR list | copernicus | official_disaster | GLOBAL | https://emergency.copernicus.eu/mapping/list-of-components/EMSR | public official list | static_html_headline_candidate | 6 h | 55 | official | low | low | medium | medium | candidate_needs_verification | Emergency mapping activation candidate. | G9 |
| copernicus_ems_feature_candidate | Copernicus EMS feature-service candidate | copernicus | official_disaster | GLOBAL | https://emergency.copernicus.eu/mapping | possible official feature service behind EMS products | arcgis_feature_service_candidate | disabled | 20 | official | low | medium | high | medium | assistant_seeded | Only if an official machine-readable feature service is later verified; do not scrape dashboards. | G9 |
| acled_home | ACLED | acled | heavy_open_data_candidate | GLOBAL | https://acleddata.com/ | public/account data source | acled_api_candidate | disabled | 25 | nonprofit_data | high | high | high | high | candidate_policy_sensitive | Conflict data candidate only after terms/auth/attribution review. | G9 |
| acled_api_docs | ACLED API docs | acled | heavy_open_data_candidate | GLOBAL | https://acleddata.com/acled-api-documentation | API docs | acled_api_candidate | disabled | 25 | nonprofit_data | high | high | high | high | candidate_policy_sensitive | Auth/terms-sensitive source. | G9 |
| acled_terms | ACLED terms | acled | source_health_only | GLOBAL | https://acleddata.com/terms-and-conditions | terms page | manual_review_only | none | 0 | nonprofit_data | low | high | low | low | candidate_policy_sensitive | Required before ACLED use. | G9 |
| crisisgroup_updates | Crisis Group updates | crisisgroup | nonprofit_news | GLOBAL | https://www.crisisgroup.org/latest-updates | public nonprofit page/feed candidate | rss_atom | 2 h | 35 | nonprofit | medium | medium | medium | medium | candidate_needs_verification | Conflict analysis source, not official. | G8 |
| crisisgroup_rss | Crisis Group RSS | crisisgroup | nonprofit_news | GLOBAL | https://www.crisisgroup.org/rss.xml | public RSS feed | rss_atom | 2 h | 35 | nonprofit | medium | medium | medium | medium | candidate_needs_verification | Preferred metadata path if policy allows. | G8 |
| sipri_rss | SIPRI RSS | sipri | nonprofit_news | GLOBAL | https://www.sipri.org/rss.xml | public RSS feed | rss_atom | 6 h | 20 | nonprofit | low | medium | medium | low | candidate_needs_verification | Arms/conflict research, low default. | G8 |
| gtd_home | Global Terrorism Database | gtd | heavy_open_data_candidate | GLOBAL | https://www.start.umd.edu/data-tools/GTD | public dataset info | manual_review_only | disabled | 5 | academic_data | high | high | high | high | candidate_policy_sensitive | Not a recent-signal source by default. | G9 |
| undss_home | UNDSS | undss | official_diplomacy | GLOBAL | https://www.undss.org/ | public official webpage | source_health_probe_only | 24 h | 20 | official | low | low | low | low | official_page_seen | UN safety/security reference. | G9 |
| unocha_conflict_reports | OCHA conflict humanitarian reports | unocha | official_conflict_humanitarian | GLOBAL | https://reports.unocha.org/ | public official conflict/humanitarian reports | humanitarian_api_json | 60 min | 70 | official | medium | low | medium | medium | candidate_needs_verification | Conflict-affected humanitarian reporting with cautious labels and short retention. | G8 |
| peacekeeping_news | UN Peacekeeping news | peacekeeping | official_diplomacy | GLOBAL | https://peacekeeping.un.org/en/news | public official webpage/feed candidate | rss_atom | 2 h | 35 | official | medium | low | medium | medium | candidate_needs_verification | Peacekeeping updates tied to active crises. | G8 |
| msf_latest | MSF latest | msf | nonprofit_news | GLOBAL | https://www.msf.org/latest | public NGO webpage/feed candidate | rss_atom | 2 h | 45 | NGO | medium | medium | medium | medium | candidate_needs_verification | Humanitarian medical NGO source with careful labeling. | G8 |
| msf_rss | MSF RSS | msf | nonprofit_news | GLOBAL | https://www.msf.org/rss.xml | public RSS feed | rss_atom | 2 h | 45 | NGO | medium | medium | medium | medium | candidate_needs_verification | Preferred MSF metadata path. | G8 |
| amnesty_news | Amnesty latest news | amnesty | nonprofit_news | GLOBAL | https://www.amnesty.org/en/latest/news/ | public NGO webpage/feed candidate | rss_atom | 6 h | 25 | NGO | medium | medium | medium | medium | candidate_needs_verification | Human-rights advocacy source, not official. | G8 |
| hrw_news | Human Rights Watch news | hrw | nonprofit_news | GLOBAL | https://www.hrw.org/news | public NGO webpage/feed candidate | rss_atom | 6 h | 25 | NGO | medium | medium | medium | medium | candidate_needs_verification | Human-rights advocacy source, not official. | G8 |
| hrw_rss | Human Rights Watch RSS | hrw | nonprofit_news | GLOBAL | https://www.hrw.org/rss.xml | public RSS feed | rss_atom | 6 h | 25 | NGO | medium | medium | medium | medium | candidate_needs_verification | Preferred HRW metadata path. | G8 |
| cisa_global_advisories | CISA global-relevance advisories | cisa | official_cybersecurity | GLOBAL | https://www.cisa.gov/news-events/cybersecurity-advisories | public official webpage/feed candidate | rss_atom | 60 min | 60 | official | low | low | medium | medium | official_page_seen | NATIONAL canonical, GLOBAL if global exploitation/relevance exists. | G8 |
| cert_eu_advisories | CERT-EU advisories | cert_eu | official_cybersecurity | GLOBAL | https://www.cert.europa.eu/publications/security-advisories | public official webpage/feed candidate | rss_atom | 60 min | 55 | official | low | low | medium | medium | candidate_needs_verification | EU cyber advisory source. | G8 |
| enisa_news | ENISA news | enisa | official_cybersecurity | GLOBAL | https://www.enisa.europa.eu/news | public official webpage/feed candidate | rss_atom | 2 h | 35 | official | low | low | medium | low | candidate_needs_verification | EU cyber institution source. | G8 |
| ncsc_uk_feed | UK NCSC feed | ncsc_uk | official_cybersecurity | GLOBAL | https://www.ncsc.gov.uk/api/1/services/v1/news-rss-feed.xml | public RSS feed | rss_atom | 60 min | 45 | official | low | low | medium | medium | candidate_needs_verification | UK cyber feed; global only when impact is broad. | G8 |
| circl_misp | CIRCL MISP OSINT feed | circl | heavy_open_data_candidate | GLOBAL | https://www.circl.lu/doc/misp/feed-osint/ | public docs/feed candidate | manual_review_only | disabled | 15 | official_candidate | low | high | high | medium | candidate_policy_sensitive | Threat-intel-like source; manual review only. | G9 |
| shadowserver_news | Shadowserver news | shadowserver | nonprofit_news | GLOBAL | https://www.shadowserver.org/news/ | public nonprofit webpage/feed candidate | rss_atom | 2 h | 25 | nonprofit | low | medium | medium | low | candidate_needs_verification | Security nonprofit context. | G8 |
| icao_news | ICAO newsroom | icao | official_aviation | GLOBAL | https://www.icao.int/Newsroom/Pages/default.aspx | public official webpage/feed candidate | rss_atom | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | Global aviation institution source. | G8 |
| iata_press | IATA pressroom | iata | official_aviation | GLOBAL | https://www.iata.org/en/pressroom/ | public association webpage/feed candidate | rss_atom | 2 h | 35 | industry_association | low | medium | medium | low | candidate_needs_verification | Airline industry source, not official regulator. | G8 |
| itf_oecd_news | International Transport Forum news | itf_oecd | official_transport | GLOBAL | https://www.itf-oecd.org/news | public intergovernmental transport page/feed candidate | rss_atom | 6 h | 25 | official_candidate | low | low | medium | low | assistant_seeded | Global transport policy context, low priority unless disruption-linked. | G8 |
| eurocontrol_ops | Eurocontrol network operations | eurocontrol | official_aviation | GLOBAL | https://www.eurocontrol.int/network-operations | public official webpage/feed candidate | rss_atom | 30 min | 55 | official | low | medium | medium | medium | candidate_needs_verification | Europe aviation/network disruption source. | G8 |
| eurocontrol_rss | Eurocontrol RSS | eurocontrol | official_aviation | GLOBAL | https://www.eurocontrol.int/rss.xml | public RSS feed | rss_atom | 60 min | 45 | official | low | medium | medium | low | candidate_needs_verification | Preferred Eurocontrol metadata path. | G8 |
| imo_press | IMO press briefings | imo | official_maritime | GLOBAL | https://www.imo.org/en/MediaCentre/PressBriefings | public official webpage/feed candidate | rss_atom | 2 h | 35 | official | low | low | medium | low | candidate_needs_verification | Maritime institution source. | G8 |
| marinetraffic_api | MarineTraffic API services | marinetraffic | manual_review_only | GLOBAL | https://www.marinetraffic.com/en/ais-api-services | commercial API info | manual_review_only | disabled | 5 | commercial | low | high | high | medium | candidate_policy_sensitive | Likely account/paid API; not early candidate. | G9 |
| supplychaindive_feed | Supply Chain Dive feed | supplychaindive | regional_global_news | GLOBAL | https://www.supplychaindive.com/feeds/news/ | public RSS feed | rss_atom | 60 min | 20 | publisher | low | medium | medium | low | candidate_needs_verification | Industry news echo only. | G8 |
| fmc_news | FMC news | fmc | official_maritime | GLOBAL | https://www.fmc.gov/news/ | public official webpage/feed candidate | rss_atom | 2 h | 25 | official | low | low | medium | low | candidate_needs_verification | U.S. maritime regulator, GLOBAL only if global shipping impact. | G8 |
| imf_news_rss | IMF news RSS | imf | official_economic | GLOBAL | https://www.imf.org/en/News/RSS | public official RSS | rss_atom | 6 h | 35 | official | low | low | medium | low | candidate_needs_verification | Global economy institution signal, low by default. | G8 |
| imf_data_api_candidate | IMF data API candidate | imf | official_economic | GLOBAL | https://data.imf.org/ | public official data/API candidate | imf_api_candidate | scheduled | 20 | official | low | medium | medium | low | candidate_needs_verification | Configured-indicator candidate only after API and terms verification. | G9 |
| worldbank_api | World Bank API | worldbank | official_development | GLOBAL | https://api.worldbank.org/v2 | public API endpoint | worldbank_api_json | scheduled | 30 | official | low | low | medium | low | candidate_needs_verification | Configured-indicator only, no firehose. | G9 |
| oecd_data | OECD data | oecd | official_economic | GLOBAL | https://www.oecd.org/en/about/data.html | public official data page | data_catalog_candidate | manual | 20 | official | low | low | medium | low | candidate_needs_verification | Data discovery only. | G9 |
| wto_news | WTO news | wto | official_economic | GLOBAL | https://www.wto.org/english/news_e/news_e.htm | public official webpage/feed candidate | rss_atom | 6 h | 30 | official | low | low | medium | low | candidate_needs_verification | Trade institution signal. | G8 |
| unctad_news | UNCTAD news | unctad | official_development | GLOBAL | https://unctad.org/news | public official webpage/feed candidate | rss_atom | 6 h | 25 | official | low | low | medium | low | candidate_needs_verification | Trade/development source. | G8 |
| iea_news | IEA news | iea | official_economic | GLOBAL | https://www.iea.org/news | public official webpage/feed candidate | rss_atom | 6 h | 25 | official_candidate | low | low | medium | low | candidate_needs_verification | Energy institution signal, not advice. | G8 |
| fao_food_price_index | FAO Food Price Index | fao | official_economic | GLOBAL | https://www.fao.org/worldfoodsituation/foodpricesindex/en/ | public official webpage/data candidate | csv_download_candidate | monthly | 40 | official | low | low | medium | low | candidate_needs_verification | Food price signal if configured. | G9 |
| fsin_food_crises | Global Report on Food Crises | fsin | official_humanitarian | GLOBAL | https://www.fsinplatform.org/global-report-food-crises | public official report page | source_health_probe_only | 24 h | 30 | official_candidate | medium | low | low | low | official_page_seen | Food security reference. | G9 |
| gdelt_home | GDELT | gdelt | heavy_open_data_candidate | GLOBAL | https://www.gdeltproject.org/ | public open-data source | gdelt_api_candidate | disabled | 20 | open_data | high | high | high | high | candidate_policy_sensitive | Heavy media-trend candidate; no firehose ingestion. | G9 |
| gdelt_docs | GDELT docs | gdelt | heavy_open_data_candidate | GLOBAL | https://gdelt.github.io/ | public docs | gdelt_api_candidate | disabled | 20 | open_data | high | high | high | high | candidate_policy_sensitive | Docs for strict allowlist design. | G9 |
| gdelt_doc_api | GDELT DOC API | gdelt | heavy_open_data_candidate | GLOBAL | https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/ | public docs/blog | gdelt_api_candidate | disabled | 20 | open_data | high | high | high | high | candidate_policy_sensitive | API candidate, low-weight trend echo only. | G9 |
| owid_api_docs | OWID chart API docs | owid | heavy_open_data_candidate | GLOBAL | https://docs.owid.io/projects/etl/api/chart-api/ | public docs | official_api_json | scheduled | 15 | nonprofit_data | low | medium | medium | low | candidate_policy_sensitive | Configured indicator only. | G9 |
| data_un | UN Data | un_data | heavy_open_data_candidate | GLOBAL | https://data.un.org/ | public data catalog | data_catalog_candidate | manual | 10 | official | low | low | high | low | candidate_needs_verification | Catalog only. | G9 |
| google_crisismap | Google Crisis Map | google_crisis | unofficial_aggregator | GLOBAL | https://www.google.org/crisismap/weather_and_events | public dashboard | source_health_probe_only | manual | 5 | unofficial | low | high | high | low | unofficial_secondary | Human comparison only; do not scrape. | G9 |
| reuters_world | Reuters world | reuters | wire_service | GLOBAL | https://www.reuters.com/world/ | public publisher webpage/feed candidate | rss_atom | 30 min | 45 | media | medium | medium | medium | low | candidate_needs_verification | Global news convergence. | G8 |
| bbc_world_rss | BBC World RSS | bbc | public_media | GLOBAL | https://feeds.bbci.co.uk/news/world/rss.xml | public RSS feed | rss_atom | 30 min | 45 | public_media | medium | medium | medium | low | candidate_needs_verification | Global public-media convergence. | G8 |
| aljazeera_rss | Al Jazeera RSS | al_jazeera | global_news | GLOBAL | https://www.aljazeera.com/xml/rss/all.xml | public RSS feed | rss_atom | 30 min | 40 | media | medium | medium | medium | low | candidate_needs_verification | Non-U.S./global news convergence. | G8 |
| guardian_world_rss | Guardian World RSS | guardian | global_news | GLOBAL | https://www.theguardian.com/world/rss | public RSS feed | rss_atom | 60 min | 35 | media | medium | medium | medium | low | candidate_needs_verification | Global news convergence. | G8 |
| france24_rss | France 24 RSS | france24 | public_media | GLOBAL | https://www.france24.com/en/rss | public RSS feed | rss_atom | 60 min | 35 | public_media | medium | medium | medium | low | candidate_needs_verification | Global public-media source. | G8 |
| dw_rss | DW RSS | dw | public_media | GLOBAL | https://rss.dw.com/xml/rss-en-all | public RSS feed | rss_atom | 60 min | 35 | public_media | medium | medium | medium | low | candidate_needs_verification | Global public-media source. | G8 |
| npr_world_rss | NPR World RSS | npr_world | public_media | GLOBAL | https://feeds.npr.org/1004/rss.xml | public RSS feed | rss_atom | 60 min | 30 | public_media | medium | medium | medium | low | candidate_needs_verification | U.S. public-media world section. | G8 |
| pbs_world_rss | PBS World RSS | pbs_world | public_media | GLOBAL | https://www.pbs.org/newshour/feeds/rss/world | public RSS feed | rss_atom | 60 min | 30 | public_media | medium | medium | medium | low | candidate_needs_verification | U.S. public-media world section. | G8 |
| nhk_world_news | NHK World news | nhk | public_media | GLOBAL | https://www3.nhk.or.jp/nhkworld/en/news/ | public media webpage/feed candidate | rss_atom | 60 min | 35 | public_media | medium | medium | medium | low | candidate_needs_verification | Asia/Pacific public-media source. | G8 |
| euronews_rss | Euronews RSS | euronews | global_news | GLOBAL | https://www.euronews.com/rss?level=theme&name=news | public RSS feed | rss_atom | 60 min | 30 | media | medium | medium | medium | low | candidate_needs_verification | Europe/global news convergence. | G8 |
| lemonde_en_rss | Le Monde English RSS | lemonde | global_news | GLOBAL | https://www.lemonde.fr/en/rss/ | public RSS feed | rss_atom | 60 min | 25 | media | medium | medium | medium | low | candidate_needs_verification | Europe/global news convergence. | G8 |
| bellingcat_feed | Bellingcat feed | bellingcat | nonprofit_news | GLOBAL | https://www.bellingcat.com/feed/ | public nonprofit feed | rss_atom | 6 h | 20 | nonprofit | medium | medium | medium | low | candidate_needs_verification | Investigative source, not official. | G8 |
| occrp_rss | OCCRP RSS | occrp | nonprofit_news | GLOBAL | https://www.occrp.org/en/rss | public nonprofit feed | rss_atom | 6 h | 20 | nonprofit | medium | medium | medium | low | candidate_needs_verification | Investigative source, not official. | G8 |
| globalvoices_feed | Global Voices feed | globalvoices | nonprofit_news | GLOBAL | https://globalvoices.org/feed/ | public nonprofit feed | rss_atom | 6 h | 20 | nonprofit | medium | medium | medium | low | candidate_needs_verification | Civil-society news source, not official. | G8 |
| reddit_worldnews | Reddit r/worldnews | reddit | social_candidate | GLOBAL | https://www.reddit.com/r/worldnews/ | platform community page/API candidate | manual_review_only | disabled | 8 | platform | high | high | high | high | candidate_policy_sensitive | Community echo only through compliant API access. | G10 |
| reddit_geopolitics | Reddit r/geopolitics | reddit | social_candidate | GLOBAL | https://www.reddit.com/r/geopolitics/ | platform community page/API candidate | manual_review_only | disabled | 3 | platform | high | high | high | high | candidate_policy_sensitive | High risk of punditry/rumor; disabled. | G10 |
| x_un | X UN account | x_api | social_candidate | GLOBAL | https://x.com/UN | platform account/API candidate | manual_review_only | disabled | 8 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Official-account echo only through compliant API. | G10 |
| x_who | X WHO account | x_api | social_candidate | GLOBAL | https://x.com/WHO | platform account/API candidate | manual_review_only | disabled | 8 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Health echo only through compliant API. | G10 |
| x_gdacs | X GDACS account | x_api | social_candidate | GLOBAL | https://x.com/GDACS | platform account/API candidate | manual_review_only | disabled | 8 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Disaster echo only through compliant API. | G10 |
| x_reuters_world | X Reuters World account | x_api | social_candidate | GLOBAL | https://x.com/ReutersWorld | platform account/API candidate | manual_review_only | disabled | 4 | platform_media_account | medium | high | high | high | candidate_policy_sensitive | Media social echo, never primary evidence. | G10 |
| bluesky_global_breaking | Bluesky global breaking search | bluesky | social_candidate | GLOBAL | https://bsky.app/search?q=global%20breaking%20news | platform search/API candidate | manual_review_only | disabled | 3 | platform | high | high | high | high | reject_for_now | Broad social search is too noisy and high risk for current design. | G10 |
| bluesky_who_outbreak | Bluesky WHO outbreak search | bluesky | social_candidate | GLOBAL | https://bsky.app/search?q=WHO%20outbreak | platform search/API candidate | manual_review_only | disabled | 4 | platform | high | high | high | high | candidate_policy_sensitive | Public-health echo only after AT Protocol review. | G10 |
| global_fixture_pack_local | GLOBAL local fixture pack | local_fixture | manual_review_only | GLOBAL | tests/fixtures/global/ | local repository fixtures | local_file_fixture | none | 0 | fixture | low | low | low | low | assistant_seeded | Fixture-only parser development target; it must never fetch the network. | G2 |
| rfc9309_robots | RFC 9309 Robots Exclusion Protocol | policy_reference | source_health_only | GLOBAL | https://www.rfc-editor.org/rfc/rfc9309.html | public standards reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | Policy reference for robots handling. | G1 |
| rss_specification | RSS specification | policy_reference | source_health_only | GLOBAL | https://www.rssboard.org/rss-specification | public standards reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | RSS parser reference. | G1 |
| reddit_data_api_terms | Reddit Data API Terms | policy_reference | source_health_only | GLOBAL | https://redditinc.com/policies/data-api-terms | public platform policy | manual_review_only | none | 0 | reference | low | high | low | low | candidate_policy_sensitive | Must be reviewed before Reddit API use. | G10 |
| x_api_docs | X API introduction | policy_reference | source_health_only | GLOBAL | https://docs.x.com/x-api/introduction | public platform API docs | manual_review_only | none | 0 | reference | low | high | low | low | candidate_policy_sensitive | Must be reviewed before X source enablement. | G10 |
| bluesky_atproto_docs | Bluesky AT Protocol XRPC API docs | policy_reference | source_health_only | GLOBAL | https://docs.bsky.app/docs/api/at-protocol-xrpc-api | public platform API docs | manual_review_only | none | 0 | reference | low | medium | low | low | candidate_policy_sensitive | Reference for possible compliant Bluesky adapter. | G10 |

## SECTION 5: Source admission tiers

Tier 0 - local fixtures only:

- No network.
- Used for parser, storage, ranking, privacy/sensitivity, and UI tests.
- Fixture adapters must produce the same normalized shapes as later live adapters.

Tier 1 - official APIs, official open data, RSS/Atom, CAP feeds, GeoJSON feeds, disaster APIs,
humanitarian APIs, WHO APIs, GDACS feeds, ReliefWeb API, WMO CAP source links, official UN feeds,
and official international organization feeds:

- Best first live candidates.
- Examples: GDACS feed/API, ReliefWeb disasters/reports API, WHO Disease Outbreak News API, USGS
  global earthquake GeoJSON, UN News RSS, and ECDC RSS.
- Must be disabled by default and opt-in.

Tier 2 - official pages with stable public operational data but no obvious feed/API:

- Candidate only after source-policy review.
- Prefer source-health checks and manual review before parser implementation.
- Must use per-source selectors if extraction is ever allowed.
- No recursive crawling and no article-body fetch.

Tier 3 - global news RSS or publisher-provided feeds:

- Store headline metadata only.
- No article-body archive.
- No paywall bypass.
- Repeated syndicated headlines should not create fake source diversity.

Tier 4 - public media, nonprofit outlets, humanitarian organizations, and specialist topic outlets:

- Prefer RSS/Atom or documented APIs.
- Store headline metadata only.
- Respect robots, terms, attribution, and source policy.
- Rank by public-impact relevance, not general interest alone.

Tier 5 - social/community signals:

- Policy-sensitive.
- Disabled by default.
- Reddit only through compliant official API or permitted feed access.
- X/Twitter only through official API access if explicitly configured.
- Bluesky may be explored through official AT Protocol later.
- No HTML scraping to bypass platform restrictions.
- No long-term social archive.

Tier 6 - heavy open-data aggregators:

- Examples: GDELT, ACLED, Our World in Data, World Bank, HDX/HAPI, large humanitarian catalogs.
- Useful, but must be scoped, filtered, rate-limited, and carefully documented.
- Do not ingest firehoses.
- Do not let heavy sources dominate the dashboard.
- Some may require accounts, attribution, terms review, strict result caps, or credentials.
- Prefer manual review or fixture-only exploration first.

Tier 7 - unofficial aggregators and dashboards:

- Useful as human comparison or source-health reference.
- Do not treat as primary authority over official sources.
- Do not clone their work or scrape aggressively.
- If used later, source-health-only or manual-review-only unless policy review supports more.

## SECTION 6: GLOBAL event model

The system should not only store "news items." It should infer that multiple recent items refer to
the same global event. A future `global_events` table is clearer than forcing all global state into
generic clusters, though it can share the same storage and evidence conventions used by the broader
news architecture.

Candidate future `global_events` table:

| Column | Purpose |
| --- | --- |
| `global_event_id` | Internal integer primary key. |
| `scope` | Always `GLOBAL` initially. |
| `event_key` | Deterministic key from event type, source families, event IDs, countries, regions, organizations, hazard IDs, and normalized title tokens. |
| `event_type` | Controlled GLOBAL event type. |
| `title` | Representative bounded title, not an LLM summary. |
| `representative_item_id` | Best item to display as primary evidence. |
| `severity` | Deterministic severity bucket such as `info`, `notice`, `elevated`, `major`, or `critical`. |
| `public_impact_score` | Direct global public-impact component. |
| `source_diversity_score` | Independent source-family convergence component. |
| `official_confirmation_score` | Official-source strength component. |
| `humanitarian_impact_score` | OCHA/ReliefWeb/UNHCR/WFP/IFRC/ICRC/MSF and displacement/food-security component. |
| `health_impact_score` | WHO/ECDC/PAHO/Africa CDC/WOAH public-health component. |
| `disaster_score` | GDACS/ReliefWeb/disaster component. |
| `weather_hazard_score` | WMO/NHC/JTWC/severe weather component. |
| `conflict_humanitarian_score` | Conflict-humanitarian, peacekeeping, human-rights, and protection component. |
| `diplomacy_institution_score` | UN, IAEA, NATO, OSCE, and institution action component. |
| `transport_supply_chain_score` | Aviation, maritime, port, sea lane, and supply chain component. |
| `cyber_impact_score` | Global cybersecurity advisory and infrastructure risk component. |
| `economic_impact_score` | Configured international economy/trade/food/energy release component. |
| `social_echo_score` | Optional compliant social echo component. |
| `news_echo_score` | Global news/public media convergence component. |
| `us_impact_score` | Direct U.S. impact tag component. |
| `regional_impact_score` | Direct Washington/PNW impact tag component. |
| `local_impact_score` | Direct Seattle/local impact tag component. |
| `first_seen_at` | First local observation. |
| `last_seen_at` | Most recent matching observation. |
| `last_elevated_at` | Most recent time the event crossed display/ranking threshold. |
| `expires_at` | Purge cutoff. |
| `geography_json` | Countries, regions, basins, coordinates if safe, organizations, ports, routes, or affected systems. |
| `countries_json` | Normalized affected country labels/codes. |
| `regions_json` | Normalized UN/WHO/ocean/continent/regional labels. |
| `organizations_json` | Organizations represented in evidence. |
| `source_ids_json` | Source ids represented in the event. |
| `item_ids_json` | Item ids represented in the event. |
| `evidence_json` | Source, parser, matching, ranking, policy, sensitivity, and scope evidence. |
| `ranking_explanation_json` | Score factors and deterministic reason strings. |
| `status` | `active`, `monitoring`, `expired`, `hidden`, `policy_blocked`, or `resolved`. |

Required event types:

- `global_disaster_alert`
- `earthquake_global`
- `tsunami_global`
- `tropical_cyclone`
- `flood_global`
- `wildfire_global`
- `smoke_air_quality_global`
- `volcano_unrest_global`
- `drought_food_security`
- `disease_outbreak`
- `public_health_emergency`
- `humanitarian_crisis`
- `displacement_crisis`
- `famine_food_security`
- `conflict_humanitarian`
- `ceasefire_peacekeeping`
- `sanctions_diplomacy`
- `international_institution_action`
- `human_rights_alert`
- `nuclear_safety_event`
- `aviation_global_disruption`
- `maritime_port_disruption`
- `supply_chain_disruption`
- `cyber_global_advisory`
- `global_economic_release`
- `commodity_food_energy_shock`
- `major_global_news`
- `community_signal`
- `source_health_problem`

Routine low-impact global news should not automatically become elevated GLOBAL events. Routine
diplomatic remarks, generic summit coverage, punditry, conflict rumor, commodity speculation,
single-source social claims, and old humanitarian updates without material change remain hidden,
low-priority, or background pulse unless official severity, immediate public impact, or independent
cross-source convergence justifies elevation.

## SECTION 7: Cross-source convergence ranking

The ranking model should implement this idea deterministically: if something appears in official
international sources, disaster feeds, humanitarian feeds, health feeds, hazard feeds, global news,
and compliant community/social signals within a short window, it is probably important or
interesting.

This is not an LLM summarizer. The system should compute features, scores, and explanations from
stored metadata only.

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

Independent source families count more than repeated mentions from the same family. Candidate
families:

- `gdacs`
- `reliefweb`
- `unocha`
- `hdx`
- `who`
- `ecdc`
- `paho`
- `africa_cdc`
- `woah`
- `wmo`
- `noaa_nhc`
- `usgs`
- `tsunami_gov`
- `smithsonian_gvp`
- `nasa_firms`
- `copernicus`
- `iaea`
- `un_news`
- `un_press`
- `un_security_council`
- `unhcr`
- `wfp`
- `fao`
- `ifrc`
- `icrc`
- `msf`
- `ohchr`
- `acled`
- `gdelt`
- `reuters`
- `ap`
- `bbc`
- `al_jazeera`
- `guardian`
- `france24`
- `dw`
- `npr_world`
- `public_media`
- `nonprofit_investigative`
- `reddit`
- `bluesky`
- `x_api`
- `source_health`

3. Temporal proximity

Items closer in time are more likely to refer to the same event. Initial matching windows:

- Breaking global news: 0 to 24 hours.
- Disaster alert: active alert duration or 0 to 72 hours.
- Earthquake/tsunami: 0 to 24 hours, with aftershock clustering.
- Tropical cyclone: active advisory cycle or 0 to 7 days.
- Flood/wildfire/smoke: 0 to 72 hours, longer only if active.
- Volcano unrest: 0 to 7 days, official sources preferred.
- Disease outbreak: 0 to 14 days, with active event extension.
- Humanitarian crisis: 0 to 14 days, with active event extension.
- Conflict humanitarian event: 0 to 72 hours for breaking events, 0 to 14 days for official
  situation reports.
- International institution action: 0 to 72 hours unless tied to active crisis.
- Supply-chain/transport disruption: 0 to 48 hours.
- Cyber advisory: 0 to 14 days.
- Economic release: release day plus 24 hours unless follow-up coverage converges.

4. Geographic proximity and reach

Match by:

- Country.
- Region.
- Continent.
- Ocean basin.
- Disaster id.
- Storm id.
- Earthquake id.
- Volcano name.
- Humanitarian operation id.
- UN region.
- WHO region.
- Affected border.
- Affected airspace.
- Affected sea lane.
- Affected port.
- Affected agency.
- Affected population group.
- Affected disease/outbreak name.
- Affected infrastructure sector.

5. Public impact

Boost:

- Official global disaster alerts.
- Large earthquakes.
- Tsunami warnings.
- Tropical cyclone watches/warnings.
- Major floods.
- Major wildfires or smoke events.
- Disease outbreaks.
- Humanitarian crises.
- Evacuation/displacement.
- Famine/food insecurity.
- Nuclear safety incidents.
- Major aviation or maritime disruption.
- Major cyber advisories with global exploitation.
- International institutional action tied to active crises.
- Global supply-chain disruption.
- Events with U.S., PNW, or Seattle impact tags.
- Multi-source news convergence from independent regions or source families.

6. Recency

Recent items matter more, but older active hazards can stay elevated while still active. Evidence
must show whether an item is fresh, active-but-older, stale, or retained only for source-health/debug
evidence.

7. User-configured priority

Future config should allow boosts for:

- Global disasters.
- Humanitarian crises.
- Disease outbreaks.
- Earthquakes.
- Tsunami.
- Volcanoes.
- Tropical cyclones.
- Aviation.
- Maritime.
- Cyber.
- Nuclear safety.
- Food security.
- Europe.
- Middle East.
- East Asia.
- Pacific.
- Latin America.
- Africa.
- Arctic.
- U.S. impact.
- Seattle impact.
- Washington impact.
- Specific countries.
- Specific organizations.
- Specific source families.

8. Low-public-value penalty

De-emphasize:

- Routine diplomatic remarks.
- Generic summit coverage.
- Single-source political opinion.
- Minor foreign domestic politics with no wider impact.
- Conflict rumor without official or trusted reporting.
- Social-only claims.
- Duplicate syndicated stories.
- Old humanitarian updates that do not change the situation.
- Data releases not on the configured attention list.
- Commodity speculation.
- Content that lacks source provenance.

Sample scoring formula:

```text
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
```

Possible normalization:

```text
recency_score = 0..20
official_severity_score = 0..50
source_diversity_score = min(40, independent_family_count * 6 + official_family_count * 5)
public_impact_score = 0..35
geographic_reach_score = 0..30
active_alert_score = 0 or 20
humanitarian_impact_score = 0..35
us_or_local_impact_score = 0..20
source_priority_score = configured_priority / 10
cluster_size_score = min(10, unique_item_count)
duplicate_family_penalty = max(0, duplicate_mentions_same_family - 1) * 2
stale_source_penalty = 0..25
low_confidence_penalty = 0..35
low_public_value_penalty = 0..50
out_of_scope_penalty = 0..60
rumor_penalty = 0..70
```

"Frequency of appearance" means independent cross-source convergence, not raw duplicate counts.

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

## SECTION 8: GLOBAL source category design

GLOBAL sources should be grouped by operational purpose. The category controls parser family,
retention, sensitivity rules, source-health expectations, and ranking contribution.

### 1. Global disaster alerts

- Why it exists: Global disaster alert sources provide the strongest official trigger for immediate
  world-scope events.
- First safe sources: GDACS feed/API, ReliefWeb disasters, Copernicus EMS activation candidates.
- Parser/adaptor class: `gdacs_feed`, `gdacs_api`, `reliefweb_api`, `static_html_headline_candidate`.
- Likely refresh interval: 10 to 30 minutes for active disaster feeds, 6 hours for mapping lists.
- Privacy risk: low to medium.
- Policy risk: low for official feeds, medium for dashboard/list extraction.
- Source-health signals: last event update, alert level parse, event id continuity, feed/API stale
  state, parser failure.
- Sample item fields: `event_id`, `event_type`, `alert_level`, `country`, `region`, `coordinates`,
  `started_at`, `updated_at`, `source_url`.
- Ranking contribution: GDACS orange/red alerts and matching official/news/humanitarian reports
  strongly elevate.
- Later phase: G2 fixtures, G6 first live candidate.

### 2. Humanitarian crises and response

- Why it exists: Relief operations, displacement, food insecurity, and emergency response can matter
  globally and need careful source labeling.
- First safe sources: ReliefWeb reports/disasters, OCHA reports, IFRC, ICRC, UNHCR, WFP, MSF.
- Parser/adaptor class: `reliefweb_api`, `humanitarian_api_json`, `rss_atom`, `hdx_hapi_json`.
- Likely refresh interval: 30 to 120 minutes.
- Privacy risk: medium.
- Policy risk: low to medium; high for broad catalogs.
- Source-health signals: report count, disaster id, latest situation report date, source labels,
  parser failure, heavy-source gate state.
- Sample item fields: `disaster_id`, `report_id`, `country`, `organization`, `format`,
  `theme`, `published_at`, `affected_population`, `source_url`.
- Ranking contribution: official/NGO humanitarian reports elevate only with crisis relevance,
  active updates, and source labels preserved.
- Later phase: G2/G6/G7.

### 3. Global public health and outbreaks

- Why it exists: WHO, ECDC, PAHO, Africa CDC, WOAH, and FAO signals can identify world-scale health
  and animal/plant disease events.
- First safe sources: WHO Disease Outbreak News API, WHO RSS, ECDC RSS, PAHO RSS, Africa CDC RSS,
  CDC travel notices, WOAH/WAHIS candidates.
- Parser/adaptor class: `who_api_json`, `ecdc_rss`, `rss_atom`, `official_api_json`.
- Likely refresh interval: 60 minutes for WHO DON, 2 to 6 hours for regional feeds.
- Privacy risk: medium.
- Policy risk: low to medium.
- Source-health signals: latest outbreak date, disease/country parse, WHO region parse, feed/API
  stale state, parser failure.
- Sample item fields: `disease`, `outbreak_name`, `countries`, `who_region`, `published_at`,
  `risk_framing`, `official_advice_url`.
- Ranking contribution: WHO DON and corroborating ECDC/PAHO/news reports rank above generic health
  articles.
- Later phase: G2/G6/G7.

### 4. Weather, tropical cyclones, flood, drought, and severe hazards

- Why it exists: Severe weather and tropical cyclones are high-impact global hazards that can affect
  travel, shipping, supply chains, and humanitarian response.
- First safe sources: WMO severe weather sources, NHC RSS/data, JTWC page, WPC/NWS only when global
  relevance exists, drought/food-security sources.
- Parser/adaptor class: `cap_alerts`, `rss_atom`, `official_api_json`, `static_html_headline_candidate`.
- Likely refresh interval: 10 to 30 minutes for active warnings/advisories, 6 hours for lower
  priority sources.
- Privacy risk: low.
- Policy risk: low to medium.
- Source-health signals: advisory number, storm id, basin, warning level, issue time, stale source.
- Sample item fields: `storm_name`, `basin`, `advisory_number`, `watch_warning`,
  `affected_countries`, `issued_at`, `expires_at`, `source_url`.
- Ranking contribution: tropical cyclone watches/warnings, severe weather CAP alerts, flood/drought
  alerts, and convergence with GDACS/news elevate.
- Later phase: G2/G7.

### 5. Earthquake, tsunami, volcano, fire, smoke, and environmental emergencies

- Why it exists: Earthquakes, tsunami warnings, volcano unrest, major fires, smoke, and environment
  emergencies have strong public-impact value and often cross borders.
- First safe sources: USGS GeoJSON/FDSN, Tsunami.gov, Smithsonian GVP, USGS VHP, NASA FIRMS,
  Copernicus, AirNow/EEA/EPA references where relevant.
- Parser/adaptor class: `geojson_feed`, `nasa_firms_api_candidate`, `rss_atom`,
  `static_html_headline_candidate`, `source_health_probe_only`.
- Likely refresh interval: 5 minutes for earthquakes, 10 minutes for tsunami, 60 minutes for
  FIRMS/volcano updates.
- Privacy risk: low.
- Policy risk: low to medium; NASA FIRMS may require key/config.
- Source-health signals: event id, magnitude, tsunami flag, volcano report date, FIRMS filter state,
  stale source.
- Sample item fields: `event_id`, `magnitude`, `depth_km`, `place`, `tsunami_status`,
  `volcano_name`, `fire_cluster`, `smoke_region`, `source_url`.
- Ranking contribution: magnitude/tsunami/alert-level thresholds and cross-source convergence
  drive ranking.
- Later phase: G2/G6/G7.

### 6. Conflict-humanitarian and human-rights sources

- Why it exists: Conflict and rights sources can matter globally but are sensitivity- and
  policy-heavy. The system should frame these as humanitarian/public-impact signals, not a war
  ticker.
- First safe sources: OCHA, ICRC, IFRC, UNHCR, WFP, OHCHR, UN Peacekeeping, MSF, Amnesty, HRW,
  Crisis Group, ACLED only after policy review.
- Parser/adaptor class: `rss_atom`, `humanitarian_api_json`, `acled_api_candidate`,
  `manual_review_only`.
- Likely refresh interval: 2 to 6 hours, disabled for heavy/conflict data until reviewed.
- Privacy risk: high.
- Policy risk: medium to high.
- Source-health signals: source label, official/NGO/media/open-data class, policy gate, report date,
  parser failure.
- Sample item fields: `country`, `region`, `organization`, `report_type`, `themes`,
  `affected_population`, `preliminary_flag`, `source_url`.
- Ranking contribution: humanitarian impact and official/multi-source convergence can elevate;
  rumor/social-only/conflict firehose data is penalized.
- Later phase: G8/G9.

### 7. United Nations, diplomacy, and international institutions

- Why it exists: UN, IAEA, OSCE, NATO, and institution actions can confirm global crises and formal
  responses but should not become routine diplomatic churn.
- First safe sources: UN News RSS, UN Press RSS, Security Council news, OHCHR, IAEA feeds, OSCE,
  NATO.
- Parser/adaptor class: `rss_atom`, `static_html_headline_candidate`, `source_health_probe_only`.
- Likely refresh interval: 60 minutes to 6 hours.
- Privacy risk: low to medium.
- Policy risk: low.
- Source-health signals: feed timestamp, document/action type, crisis tag, policy state, stale
  source.
- Sample item fields: `organization`, `body`, `action_type`, `country`, `region`, `published_at`,
  `source_url`.
- Ranking contribution: formal action tied to active crises elevates; routine remarks sink.
- Later phase: G6/G7/G8.

### 8. Cybersecurity and global technology risk

- Why it exists: Global exploitation, cross-border infrastructure risk, and international cyber
  advisories can require attention.
- First safe sources: CISA global-relevance advisories, NVD/CVE references, CERT-EU, ENISA, UK NCSC,
  FIRST, CIRCL/Shadowserver only after review.
- Parser/adaptor class: `rss_atom`, `official_api_json`, `manual_review_only`.
- Likely refresh interval: 60 minutes to 6 hours.
- Privacy risk: low.
- Policy risk: medium to high for threat-intel feeds.
- Source-health signals: advisory id, CVE parse, source jurisdiction, feed timestamp, policy gate.
- Sample item fields: `advisory_id`, `cve_ids`, `vendor`, `product`, `severity`,
  `mitigation_url`, `global_impact_basis`.
- Ranking contribution: globally exploited vulnerabilities or official cross-border advisories
  elevate; generic security news does not.
- Later phase: G8/G9.

### 9. Transport, aviation, maritime, ports, and supply chain

- Why it exists: Global aviation, maritime, ports, and supply-chain disruptions can affect travel,
  logistics, and local/regional impacts.
- First safe sources: ICAO, IATA, Eurocontrol, IMO, FMC global-impact items, maritime/port industry
  feeds, FAA/NAS only when global impact exists.
- Parser/adaptor class: `rss_atom`, `static_html_headline_candidate`, `manual_review_only`.
- Likely refresh interval: 30 minutes to 2 hours.
- Privacy risk: low.
- Policy risk: medium for commercial APIs.
- Source-health signals: route/airspace/port parse, active disruption state, feed timestamp,
  commercial/account gate.
- Sample item fields: `airport`, `port`, `airspace`, `sea_lane`, `system`, `event_type`,
  `start_time`, `end_time`, `affected_countries`.
- Ranking contribution: major global aviation/maritime disruption, port closures, supply-chain
  impacts, and convergence with official/news sources elevate.
- Later phase: G8/G9.

### 10. Global economy, finance, trade, food, energy, and development

- Why it exists: Global institutional releases can contextualize food security, energy, trade, and
  development, but must not become investment advice or commodity speculation.
- First safe sources: IMF RSS, World Bank Indicators API, WTO, UNCTAD, IEA, FAO Food Price Index,
  FSIN reports.
- Parser/adaptor class: `rss_atom`, `worldbank_api_json`, `imf_api_candidate`,
  `csv_download_candidate`, `data_catalog_candidate`.
- Likely refresh interval: scheduled releases or daily/monthly; not high-frequency.
- Privacy risk: low.
- Policy risk: medium for APIs and data licensing.
- Source-health signals: indicator allowlist, release date, dataset freshness, auth state, parser
  schema validity.
- Sample item fields: `organization`, `indicator`, `country_or_region`, `period`, `value`,
  `release_date`, `source_url`.
- Ranking contribution: configured food/security/development indicators can support crises; the
  system must not generate trading/investment advice.
- Later phase: G9.

### 11. Global open-data and trend candidates

- Why it exists: Heavy open-data sources can support trend detection but can also swamp the system,
  amplify bias, or create pseudo-intelligence behavior.
- First safe sources: GDELT, ACLED, OWID, World Bank, HDX, UN Data only as fixture/manual-review
  candidates.
- Parser/adaptor class: `gdelt_api_candidate`, `acled_api_candidate`, `worldbank_api_json`,
  `data_catalog_candidate`, `manual_review_only`.
- Likely refresh interval: disabled by default; configured queries only.
- Privacy risk: medium to high.
- Policy risk: high.
- Source-health signals: heavy-source disabled state, terms review, query allowlist, result cap,
  attribution notes, rate-limit state.
- Sample item fields: `query_id`, `dataset`, `indicator`, `country`, `time_window`,
  `result_count`, `source_url`.
- Ranking contribution: low-weight trend echo only, never primary fact.
- Later phase: G9 only.

### 12. Global news, wires, public media, and nonprofit journalism

- Why it exists: Journalism can corroborate official signals and provide context, but must not
  dominate official alerts or become a world-news archive.
- First safe sources: Reuters, AP, BBC, Al Jazeera, Guardian, France 24, DW, NPR World, PBS World,
  CBC, ABC Australia, NHK, Euronews, Le Monde English, Bellingcat, OCCRP, Global Voices.
- Parser/adaptor class: `rss_atom` preferred; `static_html_headline_candidate` only after explicit
  policy review.
- Likely refresh interval: 30 to 60 minutes for feeds, 6 hours for investigative/nonprofit sources.
- Privacy risk: medium.
- Policy risk: medium.
- Source-health signals: feed parse status, latest item time, duplicate/syndication fingerprint
  rate, policy-blocked status.
- Sample item fields: `headline`, `url`, `canonical_url`, `published_at`, `description_bounded`,
  `publisher`, `tags`, `syndication_hint`.
- Ranking contribution: Adds independent news echo to official events. Multiple publishers increase
  convergence only when source families are independent.
- Later phase: G2 fixtures, G8 live RSS after source verification.

### 13. Social/community echoes

- Why it exists: Community signals can add weak echo, but they are policy-sensitive and should never
  become primary evidence or global surveillance.
- First safe sources: Bluesky AT Protocol candidate, Reddit official API/permitted feed access, X
  official API only if explicitly configured.
- Parser/adaptor class: `manual_review_only` in this design; future compliant API adapters only.
- Likely refresh interval: disabled by default; if ever enabled, 15 to 60 minutes depending on
  source terms and rate limits.
- Privacy risk: high.
- Policy risk: high.
- Source-health signals: policy review state, auth configured state, rate-limit state, storage
  allowed state, retention rule.
- Sample item fields: `platform`, `post_id`, `author_display_policy`, `bounded_text`, `created_at`,
  `url`, `matched_tokens`, `retention_expires_at`.
- Ranking contribution: Weak echo only after official or trusted news evidence exists. Social-only
  reports must not outrank official sources or be presented as verified fact.
- Later phase: G10 only.

### 14. Source health and disabled states

- Why it exists: GLOBAL must distinguish nothing known from disabled, stale, unsupported,
  auth-required, heavy-source disabled, needs-terms-review, needs-scope-filter, policy-blocked, or
  parser failed.
- First safe sources: All configured GLOBAL sources, including disabled and manual-review-only
  entries.
- Parser/adaptor class: `source_health_probe_only`, registry validation, and stored health rows.
- Likely refresh interval: computed from config/SQLite on page load; explicit ingest/source-health
  commands update health rows later.
- Privacy risk: low.
- Policy risk: low unless later probes perform network. Page loads must never do that.
- Source-health signals: state, last success/failure, stale threshold, parser support, auth status,
  policy status, disabled reason, heavy-source gate.
- Sample item fields: `source_id`, `state`, `last_attempt_at`, `last_success_at`,
  `consecutive_failures`, `message`, `evidence_json`.
- Ranking contribution: stale/failing sources lower confidence. Source-health problems appear as
  maintenance items, not public events.
- Later phase: G1/G2 for registry and fixture health, G5 for UI.

## SECTION 9: GLOBAL conflict, health, and humanitarian sensitivity posture

GLOBAL is a public-impact metadata layer. It should prefer official, public, bounded fields and
should avoid amplifying private distress, graphic content, conflict rumor, or speculative claims.

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
- For major incidents, show public operational facts: event type, source, source family, affected
  country/region, public impact, observed time, and source link.
- Treat early official reports as preliminary where applicable.
- For public-health events, show official source and action URL, not invented advice.
- For conflict-humanitarian events, prefer humanitarian impact framing over sensational framing.
- For human-rights or conflict sources, use extra caution around advocacy-source vs official-source
  labeling.
- For ACLED, GDELT, Crisis Group, human-rights NGOs, and similar sources, preserve source-family
  labels and policy notes.
- Social-only global claims should never outrank official alerts or trusted news.
- Do not use LLMs to summarize sensitive global incident narratives in runtime behavior.

Default display posture:

| Source shape | Display location | Retention posture | Elevation rule |
| --- | --- | --- | --- |
| GDACS/official disaster alert | Country/region/basin/event id | Expiration plus 24 to 72 hours | Elevate by alert level. |
| Humanitarian report | Country/region/organization | 14 days with active extension | Elevate by active crisis and source convergence. |
| Public-health outbreak | Disease/country/WHO region | 14 to 30 days | Elevate WHO DON and official action guidance. |
| Earthquake/tsunami/volcano | Event/country/basin/volcano | 7 to 14 days | Elevate by magnitude, tsunami status, or official volcano status. |
| Conflict-humanitarian item | Country/region/source label | 7 to 14 days | Elevate humanitarian impact, not rumor or spectacle. |
| Global news headline | Publisher headline metadata | 7 days | Elevate only with public impact or convergence. |
| Heavy open-data candidate | Query/dataset only | Disabled by default | Never primary; low-weight echo after policy gates. |
| Social/community echo | Platform/link only if allowed | 24 to 72 hours max | Never primary; weak echo only. |

## SECTION 10: GLOBAL source freshness and retention

GLOBAL is a short-retention recent-signal layer. It is not an archive. Every future ingest run must
purge expired data before or after writing new rows, and purge evidence must be visible in
source-health or SYSTEM evidence.

Default candidate retention:

| Data class | Candidate retention | Notes |
| --- | --- | --- |
| Raw fetch diagnostics | 7 days or less | Status, timing, byte counts, and parser outcome only. |
| Raw payload debug | Disabled by default; 6 hours max if enabled | Must never be enabled in `config.example.yml`. |
| Official disaster alert metadata | Expiration plus 24 to 72 hours | Use source expiration when present. |
| Humanitarian crisis metadata | 14 days | Extend only while source updates continue. |
| Public health outbreak metadata | 14 to 30 days | Depends on source expiration and severity. |
| Tropical cyclone/advisory metadata | Active storm plus 7 days | Preserve advisory cycle evidence while active. |
| Weather/hazard metadata | Expiration plus 24 to 48 hours | Active hazards stay until expiration plus grace. |
| Earthquake metadata | 7 days for significant global events, 14 days for major events | Threshold-driven. |
| Tsunami metadata | Expiration plus 48 hours | Hide stale tsunami notices. |
| Volcano unrest metadata | 14 days while active | Official or specialist sources preferred. |
| Fire/smoke metadata | 7 to 14 days while active, then expire | Avoid global firehose storage. |
| Conflict-humanitarian metadata | 7 to 14 days | Preserve source labels and preliminary notes. |
| Global cyber advisory metadata | 14 to 30 days | Depends on advisory active window. |
| Transport/supply-chain disruption metadata | 3 to 7 days | Longer only for unresolved disruptions. |
| Economic release metadata | 3 to 7 days | Configured releases only. |
| Global news headline metadata | 7 days | Metadata only, no article body archive. |
| Global event clusters | 7 to 14 days | Same or slightly longer than member items. |
| Source health | 30 days | Enough for local troubleshooting. |
| Ranking explanations | Same as item/event retention | Ranking evidence expires with item/event. |
| Social metadata, if ever enabled | 24 to 72 hours unless terms require shorter or prohibit storage | Disabled by default. |

No article body archive, no permanent global incident archive, and no permanent social archive are
allowed.

## SECTION 11: Adapter design for GLOBAL

The adapter layer should normalize source-specific records into a shared item/event input shape
without fetching article bodies, crawling, or making page-load network requests. Adapters should be
pure parser/normalizer units in early phases and should run against local fixtures before any live
source is enabled.

Shared adapter output fields:

```yaml
normalized_item:
  source_id: "gdacs_all_events"
  source_family: "gdacs"
  source_class: "official_global_alert"
  scope: "GLOBAL"
  title: "GDACS red earthquake alert"
  url: "https://..."
  canonical_url: "https://..."
  published_at: "2026-01-01T12:00:00Z"
  observed_at: "2026-01-01T12:01:00Z"
  expires_at: "2026-01-04T12:00:00Z"
  description_bounded: "Short source-provided description."
  event_type_hint: "earthquake_global"
  global_relevance:
    countries: ["Japan"]
    regions: ["Pacific"]
    ocean_basins: ["Pacific"]
    us_impact_possible: true
  severity:
    source_severity: "red"
    normalized: "critical"
  sensitivity:
    graphic_content_stored: false
    identifiable_victim_details_stored: false
    preliminary: true
  policy:
    body_fetched: false
    source_terms_reviewed: false
    homepage_extractor_used: false
  evidence:
    parser: "gdacs_feed_fixture_v1"
    fixture: true
```

Adapter families:

`rss_atom`

- Targets: UN News RSS, UN Press RSS, WHO regional RSS where useful, ECDC RSS, IAEA feeds, global
  news feeds, nonprofit feeds, and public-media feeds.
- Must parse title, URL, canonical URL where available, published timestamp, bounded description,
  categories, tags, and source.
- Must bound description length.
- Must not fetch article bodies.
- Must fail soft on malformed feeds.
- Must produce duplicate fingerprints for syndicated articles.

`gdacs_feed`

- Targets: GDACS RSS/XML feeds after exact feed endpoints are verified.
- Must preserve alert level, event id, event type, countries, coordinates if available, event
  start/update times, severity, official URL, and feed source.
- Must avoid duplicate feed/API inflation.

`gdacs_api`

- Targets: GDACS API candidate.
- Must be disabled by default until fixture tests exist.
- Must preserve event id and avoid duplicate feed/API inflation.
- Must use source-specific rate limits, size caps, and deterministic filters.

`reliefweb_api`

- Targets: ReliefWeb API for reports and disasters.
- Must preserve disaster id, report id, source, country, date, format, theme, and official
  ReliefWeb URL.
- Must not store full report bodies by default.

`humanitarian_api_json`

- Targets: OCHA, IFRC, and other humanitarian candidates after verification.
- Must preserve source organization, situation id if available, country, affected population
  metadata if source provides it, source URL, and source labels.
- Must not infer casualty or displacement numbers beyond source metadata.

`hdx_hapi_json`

- Targets: HDX HAPI candidate.
- Useful for curated humanitarian indicators.
- Disabled by default until scoped query rules exist.
- Must not ingest broad catalogs into the dashboard.

`who_api_json`

- Targets: WHO Disease Outbreak News and outbreak API candidates.
- Must preserve disease/outbreak name, country, WHO region, publication date, summary metadata, and
  official URL.
- Must not invent medical advice.

`ecdc_rss`

- Targets: ECDC RSS feeds.
- Must preserve feed category, source URL, publication timestamp, and European regional scope.

`cap_alerts`

- Targets: WMO SWIC / CAP warning sources where machine-readable CAP links are verified.
- Must preserve severity, urgency, certainty, effective time, expiration, affected area, issuing
  authority, and instruction URL.
- Must not treat every national weather warning as global. Use threshold filters.

`geojson_feed`

- Targets: USGS earthquake GeoJSON and tsunami/hazard geospatial feeds if verified.
- Must support magnitude, region, depth, tsunami flag, distance, and bounding filters.

`nasa_firms_api_candidate`

- Targets: NASA FIRMS API candidate for global active fire data.
- Requires map key handling if needed.
- Must be disabled by default.
- Must use strict geographic and severity filters.
- Must not ingest global firehose data.

`official_api_json`

- Targets: WHO, UN, ECDC, World Bank, IMF, OECD, IEA, CISA, NVD, or other official JSON endpoints
  where verified.
- Must support timeouts, response size caps, source-specific rate limits, conditional requests when
  available, schema validation, and per-source fail-soft behavior.

`worldbank_api_json`

- Targets: World Bank Indicators API.
- Must be allowlisted by indicator and country/region.
- Must not become a general economic database.
- Dashboard use should focus on scheduled release or specific configured indicators, not constant
  polling.

`imf_api_candidate`

- IMF data source candidate.
- Must verify current API and usage terms before implementation.
- Disabled by default.

`acled_api_candidate`

- Policy-sensitive.
- Must require explicit configuration, terms review, credentials if required, attribution notes,
  strict filters, and short retention.
- Do not implement in early phases.

`gdelt_api_candidate`

- Heavy open-data firehose.
- Must be disabled by default.
- Must use strict query allowlists, time windows, and result caps.
- Treat as low-weight media-trend echo, not authoritative fact.

`csv_download_candidate`

- Only for official CSV data with stable schema.
- Disabled by default until fixture tests exist.
- Must cap rows and support updated-since or short retention.

`data_catalog_candidate`

- Data catalogs are discovery surfaces, not live dashboard feeds.
- Manual review only unless a specific dataset is promoted.

`arcgis_feature_service_candidate`

- Only if official global feature services are discovered.
- Do not screen scrape dashboards.

`static_html_headline_candidate`

- Only for official pages or global news pages with no RSS/API.
- Disabled unless homepage extractor support is explicitly allowed.
- Must use per-source selectors, no recursive crawling, no article-body fetch, payload size caps,
  robots/policy review, and source-health evidence.

`source_health_probe_only`

- For dashboards and portals useful as human status references but not suitable for ingestion.
- Page loads must not run probes.

`manual_review_only`

- For policy-sensitive, parser-risky, login-required, auth-required, account-required, paywalled, or
  unclear targets.
- These sources can exist in registry and docs but cannot produce live items.

## SECTION 12: Candidate global source registry example

Do not edit `config.example.yml` for this design pass. A later implementation can add disabled
examples after the common news/registry configuration exists. The candidate shape below is
intentionally disabled by default.

```yaml
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
```

Config validation rules for later:

- `global_sources.enabled` defaults to `false`.
- Every source defaults to `enabled: false`.
- Unknown source classes, adapters, verification statuses, and source families are rejected.
- Social source IDs are rejected unless `allow_social_sources` is explicitly true.
- Heavy open-data source IDs are rejected unless `allow_heavy_open_data_sources` is explicitly true.
- Conflict-heavy sources are rejected unless terms/policy review is recorded.
- Homepage extraction is rejected unless a future `allow_homepage_extractors` flag is true.
- Token/account sources such as NASA FIRMS, ACLED, or commercial maritime APIs must be
  `auth_required` unless local key config exists.
- Secrets must not appear in `config.example.yml`.

## SECTION 13: GLOBAL UI architecture

Do not implement the UI in this task. The eventual GLOBAL page should use the existing console-1706
style and template conventions, but it should show honest source-backed states rather than
placeholders or fake headlines.

Proposed bays:

### Bay 1: Global attention now

- Highest-ranking GLOBAL events.
- Must show why each item is ranked.
- Must show source-family badges.
- Must show official vs news vs community convergence.
- Must show observed time and last seen.
- Must show country/region label.
- Must not dump low-impact international churn.

Each row should show title, event type, representative source, source-family badges,
confidence/convergence count, observed time, last seen, ranking reason, evidence affordance,
geographic label, and U.S./regional/local impact tag where applicable.

### Bay 2: Disasters, health, and hazards

- GDACS, ReliefWeb, OCHA, WHO, ECDC, WMO, USGS, tsunami, volcano, NASA FIRMS, Copernicus, and
  AirNow where useful.
- Show active official alerts first.
- Show source freshness.
- Show disaster, humanitarian, disease outbreak, cyclone, earthquake, tsunami, wildfire, smoke,
  flood, and volcano signals.

### Bay 3: World systems and institutions

- UN, IAEA, ICRC, IFRC, FAO, WFP, UNHCR, global aviation/maritime, cyber, economy, trade,
  development, diplomacy.
- Useful for "will this affect global systems, international travel, supply chains, health,
  security, economy, or institutions?"
- Must identify token/account-required or heavy-source-disabled states honestly.

### Bay 4: Global press and civic pulse

- Reuters, AP, BBC, Al Jazeera, Guardian, France 24, DW, NPR World, PBS World, NHK, Euronews,
  Le Monde English, Global Voices, OCCRP, Bellingcat, and future configured sources.
- Social/community signals only if configured and compliant.
- No fake headlines.
- If disabled, show "GLOBAL news sources not configured."

Shared empty states:

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

## SECTION 14: Evidence model for GLOBAL

Every item and event must trace back to source evidence. Evidence should be plain JSON that the UI
can show without interpretation by a hidden service or LLM.

Required event evidence fields:

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
- Geographic reach basis.
- Public impact basis.
- Source diversity basis.
- Humanitarian impact basis.
- U.S. or local impact basis.
- Retention expiration.
- Matching tokens.
- Event type.
- Event confidence.
- Policy notes.
- Low-public-value penalty if applied.
- Rumor penalty if applied.
- Out-of-scope penalty if applied.

Disaster and hazard evidence should include where available:

- Alert source.
- Alert level.
- Event id.
- Event type.
- Affected countries.
- Affected regions.
- Coordinates if available and safe to store.
- Magnitude.
- Depth.
- Storm name.
- Basin.
- Advisory number.
- Tsunami status.
- Volcano name.
- Fire/smoke indicator.
- Affected population if source provides it.
- Effective time.
- Expiration time.
- Source instructions URL.

Humanitarian and conflict-humanitarian evidence should include where available:

- Issuing organization.
- Country.
- Region.
- Crisis/disaster id.
- Report type.
- Situation report date.
- Affected population metadata if source provides it.
- Source labels/themes.
- Whether the source is official, NGO, media, or open-data.
- Whether numbers are preliminary.
- Official URL.

Public health evidence should include where available:

- Issuing organization.
- Disease/outbreak name.
- Countries or WHO region.
- Publication date.
- Source-provided risk framing.
- Official advice URL.
- Whether the information is preliminary.
- No invented medical advice.

Cyber evidence should include where available:

- Advisory id.
- CVE ids.
- Product/vendor.
- Severity if provided.
- Exploited-in-the-wild flag if provided.
- Mitigation URL.
- Issuing organization.
- Global impact basis.

Transport, aviation, maritime, and supply-chain evidence should include where available:

- Airport.
- Port.
- Route.
- Airspace.
- Sea lane.
- System.
- Event type.
- Delay estimate.
- Closure status.
- Start time.
- End time.
- Source update time.
- Affected countries or regions.

Candidate evidence shape:

```json
{
  "event_type": "earthquake_global",
  "event_confidence": "high",
  "source_ids": ["gdacs_all_events", "usgs_global_earthquake_geojson", "reuters_world"],
  "source_families": ["gdacs", "usgs", "reuters"],
  "source_classes": ["official_global_alert", "official_seismic_volcano", "wire_service"],
  "official_source_count": 2,
  "news_echo_count": 1,
  "community_echo_count": 0,
  "geographic_reach_basis": {
    "countries": ["Japan"],
    "regions": ["Pacific"],
    "ocean_basins": ["Pacific"],
    "regional_impact_possible": true
  },
  "ranking_features": {
    "recency_score": 19,
    "official_severity_score": 48,
    "source_diversity_score": 22,
    "public_impact_score": 34,
    "humanitarian_impact_score": 14,
    "rumor_penalty": 0,
    "out_of_scope_penalty": 0
  },
  "sensitivity": {
    "graphic_content_stored": false,
    "identifiable_victim_details_stored": false,
    "preliminary": true
  },
  "retention": {
    "expires_at": "2026-01-15T00:00:00Z"
  },
  "policy_notes": [
    "No article bodies fetched.",
    "No social sources used.",
    "Page render reads stored SQLite state only."
  ]
}
```

## SECTION 15: Source health for GLOBAL

Source health is part of the feature. The UI and SYSTEM evidence must tell the user when GLOBAL is
disabled, stale, unsupported, auth-required, rate-limited, heavy-source-disabled, needs-terms-review,
needs-scope-filter, or policy blocked.

Required source health states:

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
- `heavy_source_disabled`
- `needs_terms_review`
- `needs_scope_filter`

Each source health row should have:

| Field | Purpose |
| --- | --- |
| `source_id` | Registry source id. |
| `state` | One of the required health states. |
| `last_attempt_at` | Last attempted fetch or fixture parse. |
| `last_success_at` | Last successful fetch or fixture parse. |
| `last_failure_at` | Last failed attempt. |
| `next_eligible_fetch_at` | Backoff/rate-limit gate. |
| `consecutive_failures` | Failure count for confidence and backoff. |
| `last_http_status` | Later live fetch HTTP status, if any. |
| `item_count_last_success` | Normalized items from last success. |
| `stale_after_minutes` | Per-source staleness threshold. |
| `message` | Human-readable local diagnostic. |
| `evidence_json` | Parser, policy, config, auth, heavy-source, and source-health details. |

Health rules:

- Disabled sources are not failures.
- Manual-review-only sources are not failures.
- Heavy-source-disabled sources are not failures.
- Auth-required sources must not prompt for secrets in the UI.
- Rate-limited sources back off and preserve the last known source health.
- Parser failures should never crash unrelated sources.
- Page rendering must read stored health only and must not fetch.
- SYSTEM should eventually summarize stale, failing, disabled, policy-blocked, auth-required,
  heavy-source-disabled, needs-terms-review, needs-scope-filter, and manual-review source counts.

## SECTION 16: First implementation sequence for GLOBAL

Phase G0: this design

- Create this design doc.
- Update BACKLOG.
- No runtime behavior change.
- No network.
- No collectors.

Phase G1: source registry scaffolding

- Add disabled GLOBAL source config.
- Add source registry schema or shared news source tables if not already provided by global
  architecture work.
- Add tests proving GLOBAL is disabled by default.
- Add enum validation for source class, adapter, verification status, and source health state.
- No network.

Phase G2: local fixtures only

- Create fixture files for GDACS RSS/XML feed.
- Create GDACS API response fixture.
- Create ReliefWeb disasters API response fixture.
- Create ReliefWeb reports API response fixture.
- Create WHO Disease Outbreak News API response fixture.
- Create ECDC RSS feed fixture.
- Create WMO CAP warning fixture.
- Create USGS earthquake GeoJSON fixture.
- Create NHC RSS fixture.
- Create Smithsonian GVP weekly report fixture.
- Create NASA FIRMS small filtered response fixture.
- Create UN News RSS fixture.
- Create IAEA RSS fixture.
- Create Reuters/BBC/Al Jazeera RSS fixture.
- Create GDELT tiny fixture only if policy review allows fixture-only exploration.
- Parse fixtures only.
- Store normalized metadata.
- Update fixture source health.
- No live fetch.

Phase G3: GLOBAL event correlation

- Implement deterministic token/location/time/source-family matching.
- No LLM.
- Tests for convergence.
- Tests for duplicate suppression.
- Tests for source-family diversity.
- Tests for country, region, basin, event-id, disease, and organization matching.
- Tests for global vs national vs regional vs local scope routing.

Phase G4: GLOBAL ranking

- Implement the scoring model.
- Explain ranking in JSON.
- Tests for official severity, source diversity, recency, public impact, humanitarian impact, U.S. or
  local impact tag, low-public-value penalty, rumor penalty, stale-source penalty, duplicate-family
  penalty, and out-of-scope penalty.

Phase G5: GLOBAL UI disabled and fixture-backed states

- Replace GLOBAL placeholders with honest disabled/not-configured/source-health states.
- Fixture-backed rows can be used in tests only.
- No live fetch.
- No fake headlines.

Phase G6: official API/RSS live fetch, opt-in only

- Start with one safe official source at a time.
- Suggested first candidates: GDACS feed, ReliefWeb disasters API, WHO Disease Outbreak News API,
  USGS earthquake GeoJSON, and UN News RSS.
- Must be disabled by default.
- Must run through an explicit ingest command or separate disabled timer, not page load.
- Must use timeouts, size caps, source intervals, conditional requests when available, and fail-soft
  behavior.

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
- Detect duplicate/syndicated stories.
- Do not let news-only clusters outrank official alerts without convergence.
- Keep disabled by default.

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
- Social echo is never primary evidence.

## SECTION 17: Testing strategy

Tests should start with config and fixtures. Live-source tests must use mocked HTTP or local test
servers only. No test should require network access.

Config tests:

- GLOBAL disabled by default.
- Source disabled by default.
- Invalid source class rejected.
- Invalid adapter rejected.
- Invalid verification status rejected.
- Social source rejected unless `allow_social_sources` is true.
- Heavy open-data source rejected unless `allow_heavy_open_data_sources` is true.
- Homepage extraction rejected unless `allow_homepage_extractors` is true.
- Conflict source rejected unless `conflict_sources_require_policy_review` is satisfied.
- Source without URL rejected unless adapter supports no URL.
- Secrets not allowed in `config.example.yml`.

Registry tests:

- Source keys unique.
- Source family valid.
- Source class valid.
- Verification status valid.
- Retention settings valid.
- Country filters valid.
- Region filters valid.
- Organization filters valid.
- Heavy-source filters required.
- Source priority bounded.
- Refresh intervals bounded.

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
- Timestamps normalize deterministically.
- Descriptions are bounded.

Sensitivity and low-public-value tests:

- Routine diplomatic statement does not elevate to GLOBAL attention.
- Social-only vague report does not outrank official alert.
- Conflict rumor gets rumor penalty.
- Public-health event shows official source and action URL, not invented advice.
- Humanitarian report preserves source labels and does not invent numbers.
- Graphic or victim-identifying content is not stored.
- Economic data release does not become advice.
- Global news-only event does not outrank official GDACS/WHO/USGS alert unless convergence and
  public-impact rules justify it.

Correlation tests:

- GDACS earthquake plus USGS earthquake plus Reuters/BBC coverage becomes one event.
- WHO DON plus ECDC/PAHO/Reuters coverage becomes one outbreak event.
- Tropical cyclone NHC/JTWC/GDACS plus news coverage becomes one event.
- ReliefWeb disaster plus OCHA/IFRC report plus news coverage becomes one humanitarian event.
- Same event from multiple news outlets counts as news-family convergence but not endless duplicate
  inflation.
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
- Disabled, not-configured, stale, failing, auth-required, heavy-source-disabled, needs-terms-review,
  needs-scope-filter, policy-blocked, parser-failed, and manual-review-only states remain distinct.

UI tests for later:

- No fake headlines.
- Empty states clear.
- Evidence visible.
- Ranking reason visible.
- Source health visible.
- Country/region/organization label visible.
- U.S., regional, and local impact tags visible when applicable.
- Heavy source disabled state visible.
- Auth-required source state visible.
- Social disabled state visible.
- Homepage extraction disabled state visible.

Safety tests:

- No page-load external fetches.
- No hidden LLM calls.
- No telemetry.
- No package install.
- No sudo.
- No social fetch unless explicitly configured.
- No heavy open-data source fetch unless explicitly configured.
- No token/account source runs without key configuration.
- No source target curl/live verification in fixture tests.

## SECTION 18: Backlog update requirements

`BACKLOG.md` must include a section named `GLOBAL World Recent Signal Layer`. Every GLOBAL backlog
item added for this design must say `Status: not implemented.` Future tasks should be concrete
enough for a later agent to implement without reading chat history.

The required backlog work areas are:

- GLOBAL source registry design implemented from this document.
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

## SECTION 19: Non-goals

- No live fetch in this task.
- No collector implementation in this task.
- No UI implementation in this task.
- No application runtime behavior change in this task.
- No route, template, CSS, JavaScript, Python app code, schema, or test changes in this task.
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
- No bypassing Reddit, X, API, auth, rate-limit, paywall, or bot-control restrictions.
- No claiming social chatter is verified fact.
- No treating advocacy sources as official.
- No treating unofficial aggregators as official.
- No treating duplicate articles as independent confirmation.
- No burying LOCAL, REGIONAL, NATIONAL, SYSTEM, or ORBITAL urgent items under GLOBAL headlines.
- No importing NATIONAL content unless global relevance rules allow it.
- No importing ORBITAL content unless global human-impact rules allow it.
- No automatic API key discovery or secret storage.
- No broad GDELT, ACLED, HDX, World Bank, or OWID firehose ingestion.
- No adding dependencies.
- No API keys or secrets in the repo.
- No scheduled GLOBAL ingest until a separate disabled-by-default timer/command is designed.

## SECTION 20: Final response requirements

Before final response, run the project-local verification commands:

```bash
pwd
git status --short
git diff --name-only
git diff --check
.venv/bin/python -m pytest -q
```

Use the project virtualenv for pytest. Do not run bare `pytest` for this repository workflow.

The final response must include:

1. Files changed.
2. Confirmation that no application code was changed, unless it was.
3. Confirmation that no external network fetches were added.
4. Confirmation that no dependencies were added.
5. Confirmation that no collectors were implemented.
6. Confirmation that GLOBAL remains disabled by default.
7. Test commands run and exact results.
8. `git diff --check` result.
9. `git status --short`.
10. BACKLOG entries added.
11. Uncertainties and source targets needing later verification.

Do not commit, push, install packages, run sudo, fetch live external sites, or curl source targets
for this task.
