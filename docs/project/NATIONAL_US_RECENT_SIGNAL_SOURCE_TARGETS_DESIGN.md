# NATIONAL United States Recent Signal Source Targets Design

## SECTION 1: Purpose

The NATIONAL scope is the United States recent-signal layer for console-1701. It should tell the
user what is happening at national scale, with source provenance, observed time, source kind,
ranking reason, freshness, and evidence. It is a deterministic metadata surface for public-impact
signals, not a crawler, not a cloud service, and not a runtime LLM summarizer.

The NATIONAL scope is not:

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

The NATIONAL scope is:

- A local, short-retention metadata dashboard.
- A deterministic cross-source event detector for U.S. public-impact signals.
- A source-health aware recent-signal system.
- A NATIONAL tab in console-1701 that can surface federal alerts, major hazards, transportation
  disruption, aviation disruption, recalls, public-health warnings, cybersecurity advisories,
  national emergency declarations, national news, economic releases, and compliant community echoes.
- A way to rank items by independent source convergence, official severity, public impact,
  freshness, user-configured source priority, and national relevance.

"National" means useful public, configured, lawful, recent signals that the user chooses to enable.
It does not mean unbounded crawling, political addiction, private data collection, investment
advice, or mass social monitoring.

## SECTION 2: National scope boundaries

Default NATIONAL scope:

- United States national scope.
- U.S. federal agencies.
- All U.S. states and territories only when the event has national public-impact value.
- Major national corridors, airports, ports, energy grids, cyber infrastructure, public-health
  systems, federal recalls, federal emergency declarations, national weather/hazard systems, and
  national government operations.
- U.S.-wide weather, disaster, wildfire, hurricane, earthquake, air-quality, aviation,
  transportation, cyber, recall, health, regulatory, court, congressional, and official economic
  signals.
- National news outlets and public media when they cover U.S. events with broad importance.
- State or regional events only when the event affects national systems or is receiving independent
  national coverage.

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
- Sources requiring login, payment, scraping around controls, or tokens not explicitly configured by
  the user.

Future disabled-by-default config escape hatch:

```yaml
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
```

## SECTION 3: Relationship to LOCAL, REGIONAL, GLOBAL, and OVERVIEW

NATIONAL should fit into the common scope model without stealing attention from urgent local or
system issues.

Rules:

- NATIONAL should not duplicate LOCAL Seattle unless the Seattle item has national impact.
- NATIONAL should not duplicate REGIONAL PNW unless the regional item has U.S.-wide impact or
  independent national coverage.
- NATIONAL should not duplicate GLOBAL unless the event is U.S.-specific or has direct U.S. national
  impact.
- GLOBAL owns non-U.S. world events unless U.S. national systems are directly involved.
- OVERVIEW should select the highest-priority items from LOCAL, REGIONAL, NATIONAL, GLOBAL, ORBITAL,
  and SYSTEM without burying urgent local/system issues.
- If a NATIONAL item directly affects Seattle or Washington, it can be tagged `LOCAL_IMPACT` or
  `REGIONAL_IMPACT` while canonical scope remains `NATIONAL`.
- If a LOCAL or REGIONAL item becomes nationally significant, it can be promoted or cross-listed into
  NATIONAL with evidence.

Examples:

- Routine SFD call in Seattle: LOCAL only or ignored.
- Major Seattle port shutdown affecting national freight: LOCAL, REGIONAL, NATIONAL.
- Snoqualmie Pass closure: REGIONAL unless national supply-chain impact exists.
- National FAA ground stop: NATIONAL and possibly LOCAL_IMPACT if SEA is affected.
- FDA Class I food recall distributed nationwide: NATIONAL.
- CDC Health Alert Network warning: NATIONAL.
- U.S. severe weather outbreak across several states: NATIONAL.
- Major hurricane landfall warning: NATIONAL.
- Federal Register routine notice: NATIONAL source pool but low priority unless public impact is high.
- Supreme Court decision with immediate national policy effect: NATIONAL, if court sources are enabled.
- Global earthquake outside the U.S. with no U.S. impact: GLOBAL.
- U.S. embassy warning abroad affecting U.S. travelers: NATIONAL and possibly GLOBAL depending on
  later GLOBAL design.

## SECTION 4: Seed source target inventory

This table is a candidate inventory, not a verification result. No live source verification was
performed in this task. `official_page_seen` means the source is a source-identifiable official
candidate from the prompt context, not that parser behavior has been tested. URLs that require
endpoint, feed, auth, or terms review remain `candidate_needs_verification` or
`candidate_policy_sensitive`.

Risk values use `low`, `medium`, or `high`. Future phases use `U0` through `U10` from the
implementation sequence.

| source_key | source_name | source_family | source_class | scope | raw_url | expected_access_kind | likely_adapter_type | likely_refresh_interval | initial_priority | official_status | privacy_risk | policy_risk | parser_risk | retention_sensitivity | verification_status | why_it_matters | future_phase |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fema_home | FEMA | fema | official_emergency | NATIONAL | https://www.fema.gov/ | public official webpage | source_health_probe_only | 24 h | 50 | official | low | low | low | low | official_page_seen | Federal emergency authority reference. | U7 |
| fema_newsroom | FEMA newsroom | fema | official_emergency | NATIONAL | https://www.fema.gov/about/newsroom | public official webpage | rss_atom | 60 min | 65 | official | low | low | medium | medium | candidate_needs_verification | FEMA response news can confirm national disasters. | U7 |
| fema_press_releases | FEMA press releases | fema | official_emergency | NATIONAL | https://www.fema.gov/about/news-multimedia/press-releases | public official webpage/feed candidate | rss_atom | 60 min | 70 | official | low | low | medium | medium | candidate_needs_verification | Official disaster response releases. | U7 |
| openfema_disaster_declarations | OpenFEMA Disaster Declarations Summaries v2 | fema | official_disaster | NATIONAL | https://www.fema.gov/openfema-data-page/disaster-declarations-summaries-v2 | public official dataset/API docs | official_api_json | 6 h | 90 | official | low | low | medium | medium | official_page_seen | Strong candidate for federal disaster declarations. | U7 |
| openfema_other_sources | OpenFEMA other data sources | fema | source_health_only | NATIONAL | https://www.fema.gov/about/openfema/other-data-sources | public official data index | data_gov_catalog_candidate | manual | 25 | official | low | low | medium | low | candidate_needs_verification | Discovery index only, not a harvest target. | U9 |
| disaster_assistance | DisasterAssistance.gov | fema | official_disaster | NATIONAL | https://www.disasterassistance.gov/ | public official webpage | source_health_probe_only | 24 h | 40 | official | medium | low | low | medium | official_page_seen | Human reference for assistance status after declarations. | U9 |
| dhs_ntas_home | DHS NTAS | dhs | official_alert | NATIONAL | https://www.dhs.gov/national-terrorism-advisory-system | public official webpage | static_html_headline_candidate | 30 min | 95 | official | low | low | medium | medium | official_page_seen | Homeland-security advisories are high-priority national alerts. | U9 |
| dhs_ntas_advisories | DHS NTAS advisories | dhs | official_alert | NATIONAL | https://www.dhs.gov/ntas/advisories | public official webpage | static_html_headline_candidate | 30 min | 95 | official | low | low | medium | medium | official_page_seen | Advisory list candidate after selector/policy review. | U9 |
| dhs_news | DHS news | dhs | official_federal_civic | NATIONAL | https://www.dhs.gov/news | public official webpage/feed candidate | rss_atom | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | DHS news can corroborate alerts and cyber/security actions. | U8 |
| dhs_press_releases | DHS press releases | dhs | official_federal_civic | NATIONAL | https://www.dhs.gov/news-releases/press-releases | public official webpage/feed candidate | rss_atom | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | Official civic source; usually low priority unless public-impact. | U8 |
| dhs_subscribe | DHS subscribe updates | dhs | source_health_only | NATIONAL | https://www.dhs.gov/subscribe-updates-dhs | public official webpage | source_health_probe_only | 24 h | 10 | official | low | low | low | low | official_page_seen | Human reference for feed/update channels. | U9 |
| ready_alerts | Ready.gov alerts | ready | official_alert | NATIONAL | https://www.ready.gov/alerts | public official webpage | source_health_probe_only | 24 h | 35 | official | low | low | low | low | official_page_seen | Federal alert education reference. | U9 |
| ready_home | Ready.gov | ready | source_health_only | NATIONAL | https://www.ready.gov/ | public official webpage | source_health_probe_only | 24 h | 20 | official | low | low | low | low | official_page_seen | Preparedness reference, not recent signal by default. | U9 |
| nws_alerts_home | NWS alerts | nws | official_weather_hazard | NATIONAL | https://www.weather.gov/alerts | public official webpage | cap_alerts | 10 min | 95 | official | low | low | medium | medium | official_page_seen | Official national weather alert entry point. | U6 |
| nws_active_alerts_api | NWS active alerts API | nws | official_weather_hazard | NATIONAL | https://api.weather.gov/alerts/active | documented official JSON API | official_api_json | 5 min | 100 | official | low | low | medium | medium | official_page_seen | Best first candidate for national active alerts. | U6 |
| nws_api_docs | NWS API docs | nws | source_health_only | NATIONAL | https://www.weather.gov/documentation/services-web-api | official API docs | manual_review_only | none | 10 | official | low | low | low | low | user_seeded | Reference for NWS API implementation. | U1 |
| nws_alerts_docs | NWS alert service docs | nws | source_health_only | NATIONAL | https://www.weather.gov/documentation/services-web-alerts | official API docs | manual_review_only | none | 10 | official | low | low | low | low | user_seeded | Reference for alert fields. | U1 |
| weather_home | National Weather Service | nws | official_weather_hazard | NATIONAL | https://www.weather.gov/ | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | official_page_seen | National weather authority reference. | U9 |
| spc_home | Storm Prediction Center | noaa_spc | official_weather_hazard | NATIONAL | https://www.spc.noaa.gov/ | public official webpage | static_html_headline_candidate | 15 min | 80 | official | low | low | medium | medium | official_page_seen | Severe storm authority and outbreak source. | U7 |
| spc_products | SPC products | noaa_spc | official_weather_hazard | NATIONAL | https://www.spc.noaa.gov/products/ | public official product index | source_health_probe_only | 30 min | 55 | official | low | low | medium | low | official_page_seen | Product index for watch/outlook verification. | U9 |
| spc_outlook | SPC convective outlooks | noaa_spc | official_weather_hazard | NATIONAL | https://www.spc.noaa.gov/products/outlook/ | public official webpage | static_html_headline_candidate | 30 min | 80 | official | low | low | medium | medium | official_page_seen | Severe-weather outbreak context. | U7 |
| spc_watch | SPC watches | noaa_spc | official_weather_hazard | NATIONAL | https://www.spc.noaa.gov/products/watch/ | public official webpage | static_html_headline_candidate | 10 min | 90 | official | low | low | medium | medium | official_page_seen | Tornado/severe thunderstorm watch signal. | U7 |
| spc_fire_weather | SPC fire weather | noaa_spc | official_weather_hazard | NATIONAL | https://www.spc.noaa.gov/products/fire_wx/ | public official webpage | static_html_headline_candidate | 30 min | 75 | official | low | low | medium | medium | official_page_seen | National fire weather signal. | U7 |
| wpc_home | Weather Prediction Center | noaa_wpc | official_weather_hazard | NATIONAL | https://www.wpc.ncep.noaa.gov/ | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | official_page_seen | WPC authority reference. | U9 |
| wpc_qpf | WPC QPF | noaa_wpc | official_water_flood | NATIONAL | https://www.wpc.ncep.noaa.gov/qpf/qpf2.shtml | public official webpage | static_html_headline_candidate | 6 h | 60 | official | low | low | medium | medium | candidate_needs_verification | Heavy-rain/flood risk input. | U7 |
| wpc_discussion | WPC discussion | noaa_wpc | official_weather_hazard | NATIONAL | https://www.wpc.ncep.noaa.gov/discussions/hpcdiscussions.php?disc=pmdspd | public official webpage | static_html_headline_candidate | 6 h | 50 | official | low | low | medium | low | candidate_needs_verification | National hazard discussion context. | U7 |
| nhc_home | National Hurricane Center | noaa_nhc | official_hurricane | NATIONAL | https://www.nhc.noaa.gov/ | public official webpage | source_health_probe_only | 30 min | 75 | official | low | low | low | low | official_page_seen | Hurricane authority reference. | U7 |
| nhc_gtwo | NHC tropical weather outlook | noaa_nhc | official_hurricane | NATIONAL | https://www.nhc.noaa.gov/gtwo.php | public official webpage | static_html_headline_candidate | 30 min | 85 | official | low | low | medium | medium | official_page_seen | Tropical development watch signal. | U7 |
| nhc_rss_info | NHC RSS information | noaa_nhc | source_health_only | NATIONAL | https://www.nhc.noaa.gov/aboutrss.shtml | public official feed docs | rss_atom | 10 min | 85 | official | low | low | medium | medium | candidate_needs_verification | Feed discovery for hurricane advisories. | U7 |
| nhc_gis | NHC GIS | noaa_nhc | official_hurricane | NATIONAL | https://www.nhc.noaa.gov/gis/ | public official GIS page | data_gov_catalog_candidate | 30 min | 65 | official | low | low | medium | medium | candidate_needs_verification | Possible official storm geospatial data. | U9 |
| nhc_data | NHC data | noaa_nhc | official_hurricane | NATIONAL | https://www.nhc.noaa.gov/data/ | public official data page | official_api_json | 10 min | 85 | official | low | low | medium | medium | candidate_needs_verification | Candidate advisory data source. | U7 |
| ncei_drought_monitor | NCEI drought monitor | noaa_ncei | official_weather_hazard | NATIONAL | https://www.ncei.noaa.gov/access/monitoring/us-drought-monitor/ | public official webpage | static_html_headline_candidate | daily | 45 | official | low | low | medium | low | candidate_needs_verification | National drought signal. | U9 |
| drought_monitor_unl | U.S. Drought Monitor | drought_monitor | official_weather_hazard | NATIONAL | https://droughtmonitor.unl.edu/ | public official partnership webpage | static_html_headline_candidate | daily | 45 | official_candidate | low | low | medium | low | candidate_needs_verification | Drought authority candidate. | U9 |
| drought_gov | Drought.gov | drought_gov | official_weather_hazard | NATIONAL | https://www.drought.gov/ | public official webpage | source_health_probe_only | daily | 40 | official | low | low | low | low | official_page_seen | Drought context and source discovery. | U9 |
| weather_fire | NWS fire weather | nws | official_weather_hazard | NATIONAL | https://www.weather.gov/fire/ | public official webpage | static_html_headline_candidate | 30 min | 65 | official | low | low | medium | medium | official_page_seen | Fire-weather conditions and alerts. | U7 |
| nwrfc_home_national | NWRFC | noaa_nwrfc | official_water_flood | NATIONAL | https://www.nwrfc.noaa.gov/ | public official webpage | source_health_probe_only | 30 min | 35 | official | low | low | medium | low | official_page_seen | Regional flood source with national architecture relevance. | U9 |
| water_noaa | NOAA Water Prediction | noaa_water | official_water_flood | NATIONAL | https://water.noaa.gov/ | public official webpage/API candidate | hydrology_api_json | 15 min | 70 | official | low | low | medium | medium | candidate_needs_verification | National water/flood candidate. | U7 |
| noaa_nwm | National Water Model | noaa_water | official_water_flood | NATIONAL | https://water.noaa.gov/about/nwm | public official documentation | source_health_probe_only | 24 h | 35 | official | low | low | low | low | official_page_seen | National water model reference. | U9 |
| usgs_water_services | USGS water services | usgs_water | official_water_flood | NATIONAL | https://waterservices.usgs.gov/ | official API docs | hydrology_api_json | 15 min | 70 | official | low | low | medium | medium | official_page_seen | National gauge/hydrology API candidate. | U7 |
| usgs_water_api | USGS water data API | usgs_water | official_water_flood | NATIONAL | https://api.waterdata.usgs.gov/ | official API endpoint/docs | hydrology_api_json | 15 min | 70 | official | low | low | medium | medium | official_page_seen | Machine-readable national water data. | U7 |
| usgs_water_mission | USGS Water Resources | usgs_water | source_health_only | NATIONAL | https://www.usgs.gov/mission-areas/water-resources | public official webpage | source_health_probe_only | 24 h | 20 | official | low | low | low | low | official_page_seen | Hydrology authority reference. | U9 |
| nifc_home | NIFC | nifc | official_wildfire | NATIONAL | https://www.nifc.gov/ | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | official_page_seen | National fire coordination authority. | U7 |
| nifc_nfn | NIFC National Fire News | nifc | official_wildfire | NATIONAL | https://www.nifc.gov/fire-information/nfn | public official webpage | static_html_headline_candidate | 60 min | 80 | official | low | low | medium | medium | official_page_seen | National wildfire coordination news. | U7 |
| nifc_stats | NIFC fire statistics | nifc | official_wildfire | NATIONAL | https://www.nifc.gov/fire-information/statistics | public official webpage | static_html_headline_candidate | daily | 35 | official | low | low | medium | low | official_page_seen | Fire context, not high-frequency alert. | U9 |
| inciweb | InciWeb | inciweb | official_wildfire | NATIONAL | https://inciweb.wildfire.gov/ | public official incident site | static_html_headline_candidate | 30 min | 70 | official | low | low | high | medium | candidate_needs_verification | Federal wildfire incident candidate; parser policy needed. | U9 |
| fire_weather_avalanche | Fire Weather Avalanche Center | fire_weather_avalanche | unofficial_aggregator | NATIONAL | https://www.fireweatheravalanche.org/fire/ | public unofficial aggregator | source_health_probe_only | manual | 10 | unofficial | low | high | high | low | unofficial_secondary | Human comparison only, not primary authority. | U9 |
| airnow_home | AirNow | airnow | official_air_quality | NATIONAL | https://www.airnow.gov/ | public official webpage | source_health_probe_only | 30 min | 55 | official | low | low | low | low | official_page_seen | National AQI authority reference. | U7 |
| airnow_api_docs | AirNow API docs | airnow | official_air_quality | NATIONAL | https://docs.airnowapi.org/ | public official API docs | official_api_json | 30 min | 70 | official | low | medium | medium | medium | candidate_needs_verification | Candidate API, may require key/config. | U7 |
| fire_airnow | Fire and Smoke Map | airnow | official_air_quality | NATIONAL | https://fire.airnow.gov/ | public official map | source_health_probe_only | 30 min | 45 | official | low | medium | high | low | candidate_needs_verification | Smoke map reference; avoid screen scraping. | U9 |
| epa_air_quality_data | EPA outdoor air quality data | epa | official_air_quality | NATIONAL | https://www.epa.gov/outdoor-air-quality-data | public official data page | data_gov_catalog_candidate | manual | 35 | official | low | low | medium | low | candidate_needs_verification | AQI data discovery. | U9 |
| epa_air_models | EPA air quality models | epa | source_health_only | NATIONAL | https://www.epa.gov/air-research/air-quality-models | public official webpage | source_health_probe_only | 24 h | 15 | official | low | low | low | low | official_page_seen | Reference, not recent signal by default. | U9 |
| usgs_eq_home | USGS earthquakes | usgs | official_seismic_volcano | NATIONAL | https://earthquake.usgs.gov/ | public official webpage | source_health_probe_only | 24 h | 40 | official | low | low | low | low | official_page_seen | Earthquake authority reference. | U6 |
| usgs_eq_feeds | USGS earthquake feeds | usgs | official_seismic_volcano | NATIONAL | https://earthquake.usgs.gov/earthquakes/feed/ | public official feed index | geojson_feed | 5 min | 85 | official | low | low | medium | medium | official_page_seen | Feed index for earthquake data. | U6 |
| usgs_eq_feed_v1 | USGS earthquake feed v1 | usgs | official_seismic_volcano | NATIONAL | https://earthquake.usgs.gov/earthquakes/feed/v1.0/ | public official feed docs | geojson_feed | 5 min | 85 | official | low | low | medium | medium | official_page_seen | Versioned earthquake feed docs. | U6 |
| usgs_eq_geojson | USGS earthquake GeoJSON | usgs | official_seismic_volcano | NATIONAL | https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php | public official GeoJSON feed docs | geojson_feed | 5 min | 90 | official | low | low | medium | medium | official_page_seen | Strong first live candidate for U.S. seismic events. | U6 |
| usgs_fdsn_event | USGS FDSN event service | usgs | official_seismic_volcano | NATIONAL | https://earthquake.usgs.gov/fdsnws/event/1/ | public official API docs | official_api_json | 5 min | 85 | official | low | low | medium | medium | official_page_seen | Structured earthquake query service. | U7 |
| usgs_vhp | USGS Volcano Hazards Program | usgs_vhp | official_seismic_volcano | NATIONAL | https://www.usgs.gov/programs/VHP | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | official_page_seen | Volcano authority reference. | U7 |
| volcanoes_usgs | USGS volcanoes | usgs_vhp | official_seismic_volcano | NATIONAL | https://volcanoes.usgs.gov/ | public official webpage | static_html_headline_candidate | 60 min | 65 | official | low | low | medium | medium | candidate_needs_verification | National volcano status candidate. | U7 |
| usgs_observatories | USGS observatories | usgs_vhp | source_health_only | NATIONAL | https://www.usgs.gov/observatories | public official index | source_health_probe_only | 24 h | 20 | official | low | low | low | low | official_page_seen | Observatory index. | U9 |
| usgs_hvo | USGS HVO | usgs_vhp | official_seismic_volcano | NATIONAL | https://www.usgs.gov/observatories/hvo | public official webpage | static_html_headline_candidate | 60 min | 45 | official | low | low | medium | low | candidate_needs_verification | Hawaii volcano source. | U7 |
| usgs_cvo | USGS CVO | usgs_vhp | official_seismic_volcano | NATIONAL | https://www.usgs.gov/observatories/cvo | public official webpage | static_html_headline_candidate | 60 min | 45 | official | low | low | medium | low | candidate_needs_verification | Cascades volcano source. | U7 |
| usgs_calvo | USGS CalVO | usgs_vhp | official_seismic_volcano | NATIONAL | https://www.usgs.gov/observatories/calvo | public official webpage | static_html_headline_candidate | 60 min | 40 | official | low | low | medium | low | candidate_needs_verification | California volcano source. | U7 |
| usgs_yvo | USGS YVO | usgs_vhp | official_seismic_volcano | NATIONAL | https://www.usgs.gov/observatories/yvo | public official webpage | static_html_headline_candidate | 60 min | 40 | official | low | low | medium | low | candidate_needs_verification | Yellowstone volcano source. | U7 |
| tsunami_gov | Tsunami.gov | noaa_tsunami | official_seismic_volcano | NATIONAL | https://www.tsunami.gov/ | public official webpage | static_html_headline_candidate | 10 min | 85 | official | low | low | medium | medium | official_page_seen | National tsunami alert source candidate. | U7 |
| weather_tsunami | NWS tsunami safety | noaa_tsunami | source_health_only | NATIONAL | https://www.weather.gov/tsunami/ | public official webpage | source_health_probe_only | 24 h | 20 | official | low | low | low | low | official_page_seen | Reference, not recent alert by default. | U9 |
| cdc_home | CDC | cdc | official_public_health | NATIONAL | https://www.cdc.gov/ | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | official_page_seen | Public-health authority reference. | U7 |
| cdc_han | CDC Health Alert Network | cdc | official_public_health | NATIONAL | https://www.cdc.gov/han/ | public official webpage/feed candidate | rss_atom | 60 min | 95 | official | low | low | medium | medium | official_page_seen | High-priority health alert source. | U7 |
| cdc_han_about | CDC HAN about | cdc | source_health_only | NATIONAL | https://www.cdc.gov/han/php/about/index.html | public official webpage | source_health_probe_only | 24 h | 10 | official | low | low | low | low | official_page_seen | Source context. | U9 |
| cdc_han_notices | CDC HAN notices | cdc | official_public_health | NATIONAL | https://www.cdc.gov/han/php/notices/index.html | public official webpage/feed candidate | rss_atom | 60 min | 95 | official | low | low | medium | medium | candidate_needs_verification | Candidate alert list for parser. | U7 |
| cdc_outbreaks | CDC outbreaks | cdc | official_public_health | NATIONAL | https://www.cdc.gov/outbreaks/ | public official webpage | static_html_headline_candidate | 2 h | 75 | official | medium | low | medium | medium | official_page_seen | Outbreak source candidate. | U7 |
| cdc_media | CDC media | cdc | official_public_health | NATIONAL | https://www.cdc.gov/media/ | public official webpage/feed candidate | rss_atom | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | Health news, usually lower than HAN. | U8 |
| cdc_releases | CDC releases | cdc | official_public_health | NATIONAL | https://www.cdc.gov/media/releases.html | public official webpage/feed candidate | rss_atom | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | Public-health releases can corroborate events. | U8 |
| fda_recalls | FDA recalls | fda | official_recall | NATIONAL | https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts | public official webpage/feed candidate | rss_atom | 60 min | 90 | official | low | low | medium | medium | official_page_seen | Product recall source. | U7 |
| fda_major_recalls | FDA major recalls | fda | official_recall | NATIONAL | https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts/major-product-recalls | public official webpage | static_html_headline_candidate | 60 min | 95 | official | low | low | medium | medium | official_page_seen | High-impact recall subset. | U7 |
| fda_enforcement_reports | FDA enforcement reports | fda | official_recall | NATIONAL | https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts/enforcement-reports | public official webpage/data candidate | official_api_json | daily | 65 | official | low | low | medium | medium | candidate_needs_verification | Recall enforcement data candidate. | U7 |
| fda_rss_feeds | FDA RSS feeds | fda | source_health_only | NATIONAL | https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds | public official feed index | rss_atom | manual | 30 | official | low | low | medium | low | official_page_seen | Feed discovery for FDA sources. | U7 |
| fsis_recalls | FSIS recalls | fsis | official_food_safety | NATIONAL | https://www.fsis.usda.gov/recalls | public official webpage | static_html_headline_candidate | 60 min | 85 | official | low | low | medium | medium | official_page_seen | USDA food recall source. | U7 |
| fsis_developer | FSIS developer resources | fsis | source_health_only | NATIONAL | https://www.fsis.usda.gov/science-data/developer-resources | public official docs | source_health_probe_only | 24 h | 15 | official | low | low | low | low | official_page_seen | API reference index. | U7 |
| fsis_recall_api | FSIS Recall API | fsis | official_food_safety | NATIONAL | https://www.fsis.usda.gov/science-data/developer-resources/recall-api | public official API docs | recall_api_json | 60 min | 90 | official | low | low | medium | medium | official_page_seen | Strong food safety API candidate. | U6 |
| cpsc_recalls | CPSC recalls | cpsc | official_recall | NATIONAL | https://www.cpsc.gov/Recalls | public official webpage | static_html_headline_candidate | 60 min | 85 | official | low | low | medium | medium | official_page_seen | Consumer product recall source. | U7 |
| cpsc_recalls_api | CPSC Recalls API | cpsc | official_recall | NATIONAL | https://www.cpsc.gov/Recalls/CPSC-Recalls-Application-Program-Interface-API-Information | public official API docs | recall_api_json | 60 min | 90 | official | low | low | medium | medium | official_page_seen | Strong recall API candidate. | U7 |
| cpsc_rss | CPSC RSS | cpsc | official_recall | NATIONAL | https://www.cpsc.gov/Newsroom/CPSC-RSS-Feed | public official feed docs | rss_atom | 60 min | 75 | official | low | low | medium | medium | official_page_seen | Feed path for CPSC notices. | U7 |
| recalls_gov | Recalls.gov | recalls_gov | unofficial_aggregator | NATIONAL | https://www.recalls.gov/ | public federal recall portal | source_health_probe_only | 24 h | 35 | official_candidate | low | medium | high | low | official_page_seen | Human aggregate reference; prefer source agencies. | U9 |
| nhtsa_recalls | NHTSA recalls | nhtsa | official_recall | NATIONAL | https://www.nhtsa.gov/recalls | public official webpage/API candidate | recall_api_json | 60 min | 90 | official | low | low | medium | medium | official_page_seen | Vehicle safety recall source. | U7 |
| nhtsa_data | NHTSA data | nhtsa | source_health_only | NATIONAL | https://www.nhtsa.gov/data | public official data index | data_gov_catalog_candidate | manual | 25 | official | low | low | medium | low | official_page_seen | Dataset discovery. | U9 |
| nhtsa_datasets_apis | NHTSA datasets and APIs | nhtsa | official_recall | NATIONAL | https://www.nhtsa.gov/nhtsa-datasets-and-apis | public official API index | recall_api_json | 60 min | 85 | official | low | low | medium | medium | official_page_seen | API source for recalls and safety. | U7 |
| osha_news | OSHA news releases | osha | official_public_health | NATIONAL | https://www.osha.gov/news/newsreleases | public official webpage/feed candidate | rss_atom | 2 h | 35 | official | low | low | medium | low | candidate_needs_verification | Workplace safety signals when public impact is high. | U8 |
| epa_news | EPA news releases | epa | official_regulatory | NATIONAL | https://www.epa.gov/newsreleases | public official webpage/feed candidate | rss_atom | 2 h | 35 | official | low | low | medium | low | candidate_needs_verification | Environmental health/regulatory signal. | U8 |
| epa_rss | EPA RSS news feeds | epa | source_health_only | NATIONAL | https://www.epa.gov/rss-news-feeds | public official feed index | rss_atom | manual | 20 | official | low | low | medium | low | official_page_seen | Feed discovery. | U8 |
| dot_home | U.S. DOT | dot | official_transport | NATIONAL | https://www.transportation.gov/ | public official webpage | source_health_probe_only | 24 h | 35 | official | low | low | low | low | official_page_seen | Transportation authority reference. | U7 |
| dot_newsroom | DOT newsroom | dot | official_transport | NATIONAL | https://www.transportation.gov/newsroom | public official webpage/feed candidate | rss_atom | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | National transportation releases. | U8 |
| faa_home | FAA | faa | official_aviation | NATIONAL | https://www.faa.gov/ | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | official_page_seen | Aviation authority reference. | U6 |
| faa_newsroom | FAA newsroom | faa | official_aviation | NATIONAL | https://www.faa.gov/newsroom | public official webpage/feed candidate | rss_atom | 60 min | 55 | official | low | low | medium | low | candidate_needs_verification | FAA official news and incident statements. | U8 |
| faa_statements | FAA general statements | faa | official_aviation | NATIONAL | https://www.faa.gov/newsroom/statements/general-statements | public official webpage | static_html_headline_candidate | 30 min | 70 | official | low | low | medium | medium | official_page_seen | Aviation operational statements. | U7 |
| faa_nasstatus_home | FAA NAS Status | faa | official_aviation | NATIONAL | https://nasstatus.faa.gov/ | public official status page | aviation_status_json_or_xml | 5 min | 95 | official | low | low | medium | medium | official_page_seen | National aviation disruption source. | U6 |
| faa_nasstatus_list | FAA NAS Status list | faa | official_aviation | NATIONAL | https://nasstatus.faa.gov/list | public official status page | aviation_status_json_or_xml | 5 min | 95 | official | low | low | medium | medium | candidate_needs_verification | Active NAS list candidate. | U6 |
| faa_nasstatus_api | FAA NAS airport status API | faa | official_aviation | NATIONAL | https://nasstatus.faa.gov/api/airport-status-information | public API candidate | aviation_status_json_or_xml | 5 min | 95 | official_candidate | low | low | medium | medium | candidate_needs_verification | Candidate API for airport delays/ground stops. | U6 |
| faa_airport_status | FAA airport status | faa | official_aviation | NATIONAL | https://www.faa.gov/airport-status | public official webpage | aviation_status_json_or_xml | 5 min | 90 | official | low | low | medium | medium | official_page_seen | Airport operational status source. | U6 |
| faa_ois_legacy | FAA OIS legacy | faa | official_aviation | NATIONAL | https://www.fly.faa.gov/ois/?legacy=true | public official status page | source_health_probe_only | 10 min | 45 | official | low | low | high | medium | candidate_needs_verification | Legacy status reference; avoid brittle scraping. | U9 |
| faa_api_gateway | FAA API portal | faa | source_health_only | NATIONAL | https://api.faa.gov/s/ | public API portal | manual_review_only | manual | 20 | official | low | medium | medium | low | candidate_needs_verification | API discovery, possible access controls. | U9 |
| faa_asws_repo | FAA ASWS GitHub | faa | source_health_only | NATIONAL | https://github.com/Federal-Aviation-Administration/ASWS | public source repository | manual_review_only | manual | 10 | official_candidate | low | medium | low | low | candidate_needs_verification | Documentation/reference only; do not add GitHub API calls. | U9 |
| fra_home | FRA | fra | official_rail | NATIONAL | https://www.fra.dot.gov/ | public official webpage | source_health_probe_only | 24 h | 30 | official | low | low | low | low | official_page_seen | Rail authority reference. | U9 |
| fra_newsroom | FRA newsroom | fra | official_rail | NATIONAL | https://railroads.dot.gov/newsroom | public official webpage/feed candidate | rss_atom | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | Rail disruption and safety news. | U8 |
| fra_accident_reporting | FRA accident reporting | fra | official_rail | NATIONAL | https://railroads.dot.gov/accident-and-incident-reporting | public official webpage/data candidate | csv_download_candidate | daily | 35 | official | medium | low | medium | medium | candidate_needs_verification | Rail data reference; not breaking alert by default. | U9 |
| amtrak_alert | Amtrak alert | amtrak | official_rail | NATIONAL | https://www.amtrak.com/alert | public official webpage | static_html_headline_candidate | 15 min | 65 | official_candidate | low | medium | medium | medium | candidate_needs_verification | Passenger rail disruption source. | U7 |
| amtrak_service_alerts | Amtrak service alerts | amtrak | official_rail | NATIONAL | https://www.amtrak.com/service-alerts-and-notices | public official webpage | static_html_headline_candidate | 15 min | 65 | official_candidate | low | medium | medium | medium | candidate_needs_verification | Service alert source candidate. | U7 |
| maritime_newsroom | Maritime Administration newsroom | maritime | official_transport | NATIONAL | https://www.maritime.dot.gov/newsroom | public official webpage/feed candidate | rss_atom | 2 h | 35 | official | low | low | medium | low | candidate_needs_verification | Maritime/port/freight signal. | U8 |
| maritime_press | Maritime press releases | maritime | official_transport | NATIONAL | https://www.maritime.dot.gov/outreach/newsroom/press-releases | public official webpage/feed candidate | rss_atom | 2 h | 35 | official | low | low | medium | low | candidate_needs_verification | Maritime official news. | U8 |
| fhwa_511 | FHWA 511 | fhwa | official_transport | NATIONAL | https://ops.fhwa.dot.gov/511/ | public official webpage | source_health_probe_only | 24 h | 20 | official | low | low | low | low | official_page_seen | Reference for 511 systems. | U9 |
| nhtsa_press_releases | NHTSA press releases | nhtsa | official_transport | NATIONAL | https://www.nhtsa.gov/press-releases | public official webpage/feed candidate | rss_atom | 2 h | 35 | official | low | low | medium | low | candidate_needs_verification | Vehicle safety news and recall corroboration. | U8 |
| cisa_home | CISA | cisa | official_cybersecurity | NATIONAL | https://www.cisa.gov/ | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | official_page_seen | Cybersecurity authority reference. | U6 |
| cisa_advisories | CISA cybersecurity advisories | cisa | official_cybersecurity | NATIONAL | https://www.cisa.gov/news-events/cybersecurity-advisories | public official webpage/feed candidate | rss_atom | 60 min | 95 | official | low | low | medium | medium | official_page_seen | High-priority cyber advisory source. | U6 |
| cisa_alerts | CISA alerts | cisa | official_cybersecurity | NATIONAL | https://www.cisa.gov/news-events/alerts | public official webpage/feed candidate | rss_atom | 60 min | 90 | official | low | low | medium | medium | official_page_seen | Official alert source. | U6 |
| cisa_ics_advisories | CISA ICS advisories | cisa | official_cybersecurity | NATIONAL | https://www.cisa.gov/news-events/ics-advisories | public official webpage/feed candidate | rss_atom | 60 min | 85 | official | low | low | medium | medium | official_page_seen | Infrastructure/security advisory source. | U6 |
| cisa_bulletins | CISA bulletins | cisa | official_cybersecurity | NATIONAL | https://www.cisa.gov/news-events/bulletins | public official webpage/feed candidate | rss_atom | 2 h | 65 | official | low | low | medium | medium | official_page_seen | Weekly/monthly cyber bulletin candidate. | U7 |
| cisa_kev | CISA KEV catalog | cisa | official_cybersecurity | NATIONAL | https://www.cisa.gov/known-exploited-vulnerabilities-catalog | public official catalog | official_api_json | 60 min | 95 | official | low | low | medium | medium | official_page_seen | Known exploited vulnerabilities are high-attention cyber signals. | U6 |
| cisa_subscribe | CISA subscribe | cisa | source_health_only | NATIONAL | https://www.cisa.gov/about/contact-us/subscribe-updates-cisa | public official webpage | source_health_probe_only | 24 h | 10 | official | low | low | low | low | official_page_seen | Feed/update discovery. | U9 |
| cisa_news | CISA news | cisa | official_cybersecurity | NATIONAL | https://www.cisa.gov/news-events/news | public official webpage/feed candidate | rss_atom | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | Corroborates cyber/emergency directives. | U8 |
| cisa_emergency_directives | CISA emergency directives | cisa | official_cybersecurity | NATIONAL | https://www.cisa.gov/news-events/emergency-directives | public official webpage | static_html_headline_candidate | 60 min | 95 | official | low | low | medium | medium | official_page_seen | High-impact directives. | U6 |
| fbi_news | FBI news | fbi | official_federal_civic | NATIONAL | https://www.fbi.gov/news | public official webpage/feed candidate | rss_atom | 2 h | 35 | official | medium | low | medium | medium | candidate_needs_verification | National public-safety/cyber corroboration only. | U8 |
| ic3_psa | IC3 PSA | ic3 | official_cybersecurity | NATIONAL | https://www.ic3.gov/Media/Y2026/PSA | public official webpage | static_html_headline_candidate | 2 h | 55 | official | low | low | medium | medium | candidate_needs_verification | Cyber/fraud PSA source; specific year path needs review. | U8 |
| nist_news | NIST news | nist | official_cybersecurity | NATIONAL | https://www.nist.gov/news-events/news | public official webpage/feed candidate | rss_atom | 6 h | 25 | official | low | low | medium | low | candidate_needs_verification | Standards/security context, low default. | U8 |
| nvd_home | NVD | nvd | official_cybersecurity | NATIONAL | https://nvd.nist.gov/ | public official webpage | source_health_probe_only | 24 h | 35 | official | low | low | low | low | official_page_seen | Vulnerability authority reference. | U7 |
| nvd_developers | NVD developer docs | nvd | official_cybersecurity | NATIONAL | https://nvd.nist.gov/developers/start-here | public official API docs | official_api_json | 60 min | 55 | official | low | low | medium | medium | candidate_needs_verification | API candidate, but KEV should outrank generic CVE firehose. | U7 |
| energy_home | DOE | doe | official_energy | NATIONAL | https://www.energy.gov/ | public official webpage | source_health_probe_only | 24 h | 30 | official | low | low | low | low | official_page_seen | Energy authority reference. | U9 |
| energy_newsroom | DOE newsroom | doe | official_energy | NATIONAL | https://www.energy.gov/newsroom | public official webpage/feed candidate | rss_atom | 2 h | 40 | official | low | low | medium | low | candidate_needs_verification | Energy/grid public-impact news. | U8 |
| doe_oe417 | DOE OE-417 annual summary | doe | official_energy | NATIONAL | https://www.oe.netl.doe.gov/OE417_annual_summary.aspx | public official webpage/data candidate | csv_download_candidate | daily | 55 | official | low | low | medium | medium | candidate_needs_verification | Electric emergency incident data candidate. | U9 |
| eia_home | EIA | eia | official_energy | NATIONAL | https://www.eia.gov/ | public official webpage | source_health_probe_only | 24 h | 35 | official | low | low | low | low | official_page_seen | Energy data authority reference. | U7 |
| eia_opendata | EIA Open Data | eia | official_energy | NATIONAL | https://www.eia.gov/opendata/ | public official API docs | economic_api_json | daily | 55 | official | low | low | medium | low | official_page_seen | Energy data API candidate. | U7 |
| eia_today | EIA Today in Energy | eia | official_energy | NATIONAL | https://www.eia.gov/todayinenergy/ | public official webpage/feed candidate | rss_atom | daily | 25 | official | low | low | medium | low | candidate_needs_verification | Context, not alert by default. | U8 |
| ferc_news | FERC news | ferc | official_energy | NATIONAL | https://www.ferc.gov/news-events/news | public official webpage/feed candidate | rss_atom | 2 h | 30 | official | low | low | medium | low | candidate_needs_verification | Energy regulatory actions. | U8 |
| nerc_news | NERC news | nerc | official_energy | NATIONAL | https://www.nerc.com/news/Pages/default.aspx | public official webpage | static_html_headline_candidate | 2 h | 30 | official_candidate | low | medium | medium | low | candidate_needs_verification | Grid reliability news. | U8 |
| bpa_home | BPA | bpa | official_energy | NATIONAL | https://www.bpa.gov/ | public official webpage | source_health_probe_only | 24 h | 20 | official | low | low | low | low | official_page_seen | PNW energy source can be national only if broader grid relevance exists. | U9 |
| whitehouse_news | White House news | whitehouse | official_federal_civic | NATIONAL | https://www.whitehouse.gov/news/ | public official webpage/feed candidate | rss_atom | 60 min | 45 | official | low | low | medium | low | candidate_needs_verification | Executive actions/news; filter heavily. | U8 |
| whitehouse_briefings | White House briefings/statements | whitehouse | official_federal_civic | NATIONAL | https://www.whitehouse.gov/briefings-statements/ | public official webpage/feed candidate | rss_atom | 60 min | 45 | official | low | low | medium | low | candidate_needs_verification | Federal civic source, low by default. | U8 |
| whitehouse_actions | White House presidential actions | whitehouse | official_federal_civic | NATIONAL | https://www.whitehouse.gov/presidential-actions/ | public official webpage/feed candidate | rss_atom | 60 min | 65 | official | low | low | medium | medium | candidate_needs_verification | Executive actions can have national public impact. | U8 |
| federal_register_home | Federal Register | federal_register | official_regulatory | NATIONAL | https://www.federalregister.gov/ | public official webpage | federal_register_api | 2 h | 45 | official | low | low | medium | low | official_page_seen | Regulatory authority reference. | U7 |
| federal_register_public_inspection | Federal Register public inspection | federal_register | official_regulatory | NATIONAL | https://www.federalregister.gov/public-inspection/current | public official webpage/API candidate | federal_register_api | 2 h | 65 | official | low | low | medium | medium | official_page_seen | Current rules/actions, must be filtered. | U7 |
| federal_register_api_docs | Federal Register API docs | federal_register | source_health_only | NATIONAL | https://www.federalregister.gov/developers/documentation/api/v1 | public official API docs | federal_register_api | none | 10 | official | low | low | low | low | user_seeded | API implementation reference. | U1 |
| federal_register_rest | Federal Register REST API resources | federal_register | source_health_only | NATIONAL | https://www.federalregister.gov/reader-aids/developer-resources/rest-api | public official API docs | federal_register_api | none | 10 | official | low | low | low | low | user_seeded | API implementation reference. | U1 |
| govinfo_home | GovInfo | govinfo | official_regulatory | NATIONAL | https://www.govinfo.gov/ | public official webpage | source_health_probe_only | 24 h | 30 | official | low | low | low | low | official_page_seen | Government publication reference. | U8 |
| govinfo_feeds | GovInfo feeds | govinfo | official_regulatory | NATIONAL | https://www.govinfo.gov/feeds | public official feeds | govinfo_rss | 2 h | 45 | official | low | low | medium | low | official_page_seen | Official publication feed candidate. | U8 |
| congress_home | Congress.gov | congress | official_federal_civic | NATIONAL | https://www.congress.gov/ | public official webpage | source_health_probe_only | 24 h | 25 | official | low | low | low | low | official_page_seen | Legislative source, disabled by default. | U9 |
| congress_api | Congress.gov API | congress | official_federal_civic | NATIONAL | https://api.congress.gov/ | API requiring key | congress_api_candidate | 6 h | 45 | official | low | medium | medium | low | candidate_policy_sensitive | Auth/key handling required. | U9 |
| congress_api_github | Congress.gov API GitHub | congress | source_health_only | NATIONAL | https://github.com/LibraryOfCongress/api.congress.gov/ | public documentation repo | manual_review_only | manual | 10 | official_candidate | low | medium | low | low | candidate_needs_verification | Reference only; do not add GitHub API calls. | U9 |
| loc_congress_api_docs | LOC Congress API docs | congress | source_health_only | NATIONAL | https://www.loc.gov/apis/additional-apis/congress-dot-gov-api/ | public official docs | manual_review_only | manual | 10 | official | low | low | low | low | official_page_seen | API docs and auth notes. | U9 |
| supreme_court_home | Supreme Court | supreme_court | official_court_legal | NATIONAL | https://www.supremecourt.gov/ | public official webpage | source_health_probe_only | 24 h | 35 | official | low | low | low | low | official_page_seen | Court authority reference. | U9 |
| supreme_court_slip_opinions | Supreme Court slip opinions | supreme_court | official_court_legal | NATIONAL | https://www.supremecourt.gov/opinions/slipopinion/25 | public official webpage | static_html_headline_candidate | 30 min | 65 | official | low | low | medium | medium | candidate_needs_verification | Court decisions only if enabled and high-impact. | U9 |
| uscourts_home | U.S. Courts | uscourts | official_court_legal | NATIONAL | https://www.uscourts.gov/ | public official webpage | source_health_probe_only | 24 h | 20 | official | low | low | low | low | official_page_seen | Federal court system reference. | U9 |
| uscourts_rss | U.S. Courts RSS feeds | uscourts | official_court_legal | NATIONAL | https://www.uscourts.gov/rss-feeds | public official feeds | rss_atom | 2 h | 30 | official | low | low | medium | low | official_page_seen | Court news feed candidate. | U9 |
| doj_news | DOJ news | doj | official_federal_civic | NATIONAL | https://www.justice.gov/news | public official webpage/feed candidate | rss_atom | 2 h | 35 | official | medium | low | medium | medium | candidate_needs_verification | Legal/civic source, filter heavily. | U8 |
| bls_home | BLS | bls | official_economic | NATIONAL | https://www.bls.gov/ | public official webpage | source_health_probe_only | 24 h | 35 | official | low | low | low | low | official_page_seen | Economic authority reference. | U7 |
| bls_news_releases | BLS news releases | bls | official_economic | NATIONAL | https://www.bls.gov/bls/newsrels.htm | public official release list | rss_atom | scheduled | 70 | official | low | low | medium | low | candidate_needs_verification | Scheduled economic releases. | U7 |
| bls_api_features | BLS API features | bls | source_health_only | NATIONAL | https://www.bls.gov/bls/api_features.htm | public official API docs | economic_api_json | none | 10 | official | low | low | low | low | user_seeded | API reference. | U1 |
| bls_developers | BLS developers | bls | source_health_only | NATIONAL | https://www.bls.gov/developers/home.htm | public official API docs | economic_api_json | none | 10 | official | low | low | low | low | user_seeded | API reference. | U1 |
| bea_home | BEA | bea | official_economic | NATIONAL | https://www.bea.gov/ | public official webpage | source_health_probe_only | 24 h | 30 | official | low | low | low | low | official_page_seen | Economic authority reference. | U7 |
| bea_news | BEA news | bea | official_economic | NATIONAL | https://www.bea.gov/news | public official release list | rss_atom | scheduled | 65 | official | low | low | medium | low | candidate_needs_verification | Scheduled economic releases. | U7 |
| bea_developers | BEA developers | bea | source_health_only | NATIONAL | https://www.bea.gov/resources/for-developers | public official API docs | economic_api_json | none | 10 | official | low | low | low | low | user_seeded | API docs. | U1 |
| bea_api_signup | BEA API signup | bea | source_health_only | NATIONAL | https://apps.bea.gov/API/signup/ | API key signup page | manual_review_only | manual | 5 | official | low | medium | low | low | candidate_policy_sensitive | Key handling reference only. | U9 |
| fred_home | FRED | fred | official_economic | NATIONAL | https://fred.stlouisfed.org/ | public official-ish data site | source_health_probe_only | 24 h | 30 | official_candidate | low | low | low | low | official_page_seen | Economic data reference. | U7 |
| fred_api_docs | FRED API docs | fred | official_economic | NATIONAL | https://fred.stlouisfed.org/docs/api/fred/ | public API docs | economic_api_json | daily | 45 | official_candidate | low | medium | medium | low | candidate_policy_sensitive | API may require key; allowlist series only. | U9 |
| fed_news | Federal Reserve news/events | federal_reserve | official_economic | NATIONAL | https://www.federalreserve.gov/newsevents.htm | public official webpage/feed candidate | rss_atom | scheduled | 65 | official | low | low | medium | low | candidate_needs_verification | High-salience national economic source. | U7 |
| fed_data | Federal Reserve data | federal_reserve | official_economic | NATIONAL | https://www.federalreserve.gov/data.htm | public official data index | source_health_probe_only | daily | 25 | official | low | low | low | low | official_page_seen | Data index, not dashboard feed by default. | U9 |
| fed_fred_info | Fed FRED download info | federal_reserve | source_health_only | NATIONAL | https://www.federalreserve.gov/data/data-download-fred-information.htm | public official docs | manual_review_only | manual | 10 | official | low | low | low | low | official_page_seen | Reference for data access. | U9 |
| treasury_releases | Treasury press releases | treasury | official_economic | NATIONAL | https://home.treasury.gov/news/press-releases | public official webpage/feed candidate | rss_atom | 2 h | 45 | official | low | low | medium | low | candidate_needs_verification | Treasury actions and sanctions context. | U8 |
| treasury_sanctions | Treasury sanctions recent actions | treasury | official_economic | NATIONAL | https://home.treasury.gov/policy-issues/financial-sanctions/recent-actions | public official webpage/feed candidate | rss_atom | 2 h | 60 | official | low | low | medium | low | candidate_needs_verification | Sanctions can be high-impact civic/economic signal. | U8 |
| fiscaldata_home | Treasury Fiscal Data | treasury | official_economic | NATIONAL | https://fiscaldata.treasury.gov/ | public official data site | source_health_probe_only | 24 h | 25 | official | low | low | low | low | official_page_seen | Fiscal data reference. | U9 |
| fiscaldata_api_docs | Fiscal Data API docs | treasury | official_economic | NATIONAL | https://fiscaldata.treasury.gov/api-documentation/ | public official API docs | economic_api_json | daily | 35 | official | low | low | medium | low | candidate_needs_verification | API candidate with allowlisted datasets only. | U9 |
| census_developers | Census developers | census | official_economic | NATIONAL | https://www.census.gov/data/developers.html | public official API docs | economic_api_json | scheduled | 30 | official | low | low | medium | low | candidate_needs_verification | Census API candidate; allowlist only. | U9 |
| census_newsroom | Census newsroom | census | official_economic | NATIONAL | https://www.census.gov/newsroom.html | public official webpage/feed candidate | rss_atom | 6 h | 30 | official | low | low | medium | low | candidate_needs_verification | Scheduled releases and census news. | U8 |
| ap_us_news | AP U.S. News | ap | wire_service | NATIONAL | https://apnews.com/hub/us-news | public publisher webpage/feed candidate | rss_atom | 30 min | 45 | national_media | medium | medium | medium | low | candidate_needs_verification | Wire/source-family news convergence. | U8 |
| reuters_us | Reuters U.S. | reuters | wire_service | NATIONAL | https://www.reuters.com/world/us/ | public publisher webpage/feed candidate | rss_atom | 30 min | 45 | national_media | medium | medium | medium | low | candidate_needs_verification | Independent national news convergence. | U8 |
| npr_home | NPR | npr | public_media | NATIONAL | https://www.npr.org/ | public media webpage/feed candidate | rss_atom | 30 min | 40 | public_media | low | medium | medium | low | candidate_needs_verification | Public-media national context. | U8 |
| npr_rss | NPR RSS | npr | public_media | NATIONAL | https://www.npr.org/rss/ | public feed index | rss_atom | 30 min | 45 | public_media | low | medium | medium | low | candidate_needs_verification | Preferred NPR metadata path. | U8 |
| pbs_newshour | PBS NewsHour | pbs | public_media | NATIONAL | https://www.pbs.org/newshour/ | public media webpage/feed candidate | rss_atom | 60 min | 35 | public_media | low | medium | medium | low | candidate_needs_verification | Public-media national context. | U8 |
| pbs_newshour_rss | PBS NewsHour RSS | pbs | public_media | NATIONAL | https://www.pbs.org/newshour/feeds/rss/headlines | public RSS feed | rss_atom | 60 min | 40 | public_media | low | medium | medium | low | candidate_needs_verification | Preferred PBS metadata path. | U8 |
| cbs_rss | CBS latest RSS | cbs | local_tv_radio_national | NATIONAL | https://www.cbsnews.com/latest/rss/main | public RSS feed | rss_atom | 30 min | 30 | national_media | medium | medium | medium | low | candidate_needs_verification | Broadcaster metadata candidate. | U8 |
| abc_us | ABC U.S. | abc | local_tv_radio_national | NATIONAL | https://abcnews.go.com/US | public publisher webpage | static_html_headline_candidate | 30 min | 25 | national_media | medium | medium | high | low | candidate_needs_verification | Prefer feed if valid; avoid homepage extraction early. | U8 |
| abc_us_rss | ABC U.S. headlines | abc | local_tv_radio_national | NATIONAL | https://abcnews.go.com/abcnews/usheadlines | candidate feed | rss_atom | 30 min | 30 | national_media | medium | medium | medium | low | candidate_needs_verification | Candidate metadata path. | U8 |
| nbc_home | NBC News | nbc | local_tv_radio_national | NATIONAL | https://www.nbcnews.com/ | public publisher webpage | static_html_headline_candidate | 30 min | 25 | national_media | medium | medium | high | low | candidate_needs_verification | Prefer feed. | U8 |
| nbc_feed | NBC public feed | nbc | local_tv_radio_national | NATIONAL | https://feeds.nbcnews.com/nbcnews/public/news | public RSS feed | rss_atom | 30 min | 30 | national_media | medium | medium | medium | low | candidate_needs_verification | Candidate metadata path. | U8 |
| cnn_home | CNN | cnn | national_news | NATIONAL | https://www.cnn.com/ | public publisher webpage | static_html_headline_candidate | 30 min | 20 | national_media | medium | medium | high | low | candidate_needs_verification | Prefer feed; avoid homepage extraction early. | U8 |
| cnn_rss | CNN RSS | cnn | national_news | NATIONAL | https://www.cnn.com/services/rss/ | public feed index | rss_atom | 30 min | 25 | national_media | medium | medium | medium | low | candidate_needs_verification | Candidate metadata path. | U8 |
| fox_home | Fox News | fox | national_news | NATIONAL | https://www.foxnews.com/ | public publisher webpage | static_html_headline_candidate | 30 min | 20 | national_media | medium | medium | high | low | candidate_needs_verification | Prefer feed; avoid homepage extraction early. | U8 |
| fox_latest_feed | Fox latest feed | fox | national_news | NATIONAL | https://moxie.foxnews.com/google-publisher/latest.xml | candidate XML feed | rss_atom | 30 min | 25 | national_media | medium | medium | medium | low | candidate_needs_verification | Candidate metadata path. | U8 |
| usa_today_news | USA Today news | usatoday | national_news | NATIONAL | https://www.usatoday.com/news/ | public publisher webpage | static_html_headline_candidate | 30 min | 20 | national_media | medium | medium | high | low | candidate_needs_verification | Prefer feed. | U8 |
| usa_today_feed | USA Today top stories feed | usatoday | national_news | NATIONAL | https://rssfeeds.usatoday.com/usatoday-NewsTopStories | candidate RSS feed | rss_atom | 30 min | 25 | national_media | medium | medium | medium | low | candidate_needs_verification | Candidate metadata path. | U8 |
| propublica_home | ProPublica | propublica | nonprofit_news | NATIONAL | https://www.propublica.org/ | public nonprofit webpage | rss_atom | 60 min | 30 | nonprofit_media | low | medium | medium | low | candidate_needs_verification | Investigative context, not breaking feed by default. | U8 |
| propublica_feeds | ProPublica feeds | propublica | nonprofit_news | NATIONAL | https://www.propublica.org/feeds | public feed index | rss_atom | 60 min | 30 | nonprofit_media | low | medium | medium | low | candidate_needs_verification | Preferred ProPublica metadata path. | U8 |
| guardian_us | Guardian U.S. | guardian | national_news | NATIONAL | https://www.theguardian.com/us-news | public publisher webpage/feed candidate | rss_atom | 60 min | 25 | national_media | medium | medium | medium | low | candidate_needs_verification | National news convergence, not official. | U8 |
| guardian_us_rss | Guardian U.S. RSS | guardian | national_news | NATIONAL | https://www.theguardian.com/us-news/rss | public RSS feed | rss_atom | 60 min | 25 | national_media | medium | medium | medium | low | candidate_needs_verification | Candidate metadata path. | U8 |
| bbc_us_canada | BBC U.S. and Canada | bbc | national_news | NATIONAL | https://www.bbc.com/news/world/us_and_canada | public publisher webpage/feed candidate | rss_atom | 60 min | 25 | national_media | medium | medium | medium | low | candidate_needs_verification | Outside-U.S. publisher; U.S. news convergence only. | U8 |
| bbc_us_canada_rss | BBC U.S. and Canada RSS | bbc | national_news | NATIONAL | https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml | public RSS feed | rss_atom | 60 min | 25 | national_media | medium | medium | medium | low | candidate_needs_verification | Candidate metadata path. | U8 |
| reddit_news | Reddit r/news | reddit | social_candidate | NATIONAL | https://www.reddit.com/r/news/ | platform community page/API candidate | manual_review_only | disabled | 10 | platform | high | high | high | high | candidate_policy_sensitive | Disabled community echo only through compliant API access. | U10 |
| reddit_politics | Reddit r/politics | reddit | social_candidate | NATIONAL | https://www.reddit.com/r/politics/ | platform community page/API candidate | manual_review_only | disabled | 5 | platform | high | high | high | high | candidate_policy_sensitive | High risk of outrage feed; disabled by default. | U10 |
| reddit_weather | Reddit r/weather | reddit | social_candidate | NATIONAL | https://www.reddit.com/r/weather/ | platform community page/API candidate | manual_review_only | disabled | 8 | platform | high | high | high | high | candidate_policy_sensitive | Community weather echo only if compliant. | U10 |
| reddit_tropical_weather | Reddit r/TropicalWeather | reddit | social_candidate | NATIONAL | https://www.reddit.com/r/TropicalWeather/ | platform community page/API candidate | manual_review_only | disabled | 8 | platform | high | high | high | high | candidate_policy_sensitive | Hurricane community echo only if compliant. | U10 |
| reddit_aviation | Reddit r/aviation | reddit | social_candidate | NATIONAL | https://www.reddit.com/r/aviation/ | platform community page/API candidate | manual_review_only | disabled | 6 | platform | high | high | high | high | candidate_policy_sensitive | Aviation echo, never primary evidence. | U10 |
| reddit_sysadmin | Reddit r/sysadmin | reddit | social_candidate | NATIONAL | https://www.reddit.com/r/sysadmin/ | platform community page/API candidate | manual_review_only | disabled | 6 | platform | high | high | high | high | candidate_policy_sensitive | Cyber/infrastructure chatter only after policy review. | U10 |
| reddit_cybersecurity | Reddit r/cybersecurity | reddit | social_candidate | NATIONAL | https://www.reddit.com/r/cybersecurity/ | platform community page/API candidate | manual_review_only | disabled | 6 | platform | high | high | high | high | candidate_policy_sensitive | Cyber echo only if compliant. | U10 |
| reddit_economics | Reddit r/economics | reddit | social_candidate | NATIONAL | https://www.reddit.com/r/economics/ | platform community page/API candidate | manual_review_only | disabled | 3 | platform | high | high | high | high | candidate_policy_sensitive | Low value; disabled by default. | U10 |
| x_nws | X NWS account | x_api | social_candidate | NATIONAL | https://x.com/NWS | platform account/API candidate | manual_review_only | disabled | 10 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Official agency social echo only through official API. | U10 |
| x_nhc_atlantic | X NHC Atlantic account | x_api | social_candidate | NATIONAL | https://x.com/NHC_Atlantic | platform account/API candidate | manual_review_only | disabled | 10 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Hurricane social echo only through official API. | U10 |
| x_fema | X FEMA account | x_api | social_candidate | NATIONAL | https://x.com/fema | platform account/API candidate | manual_review_only | disabled | 10 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Emergency social echo only through official API. | U10 |
| x_cdc | X CDC account | x_api | social_candidate | NATIONAL | https://x.com/CDCgov | platform account/API candidate | manual_review_only | disabled | 10 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Health social echo only through official API. | U10 |
| x_fda | X FDA account | x_api | social_candidate | NATIONAL | https://x.com/US_FDA | platform account/API candidate | manual_review_only | disabled | 10 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Recall/health social echo only through official API. | U10 |
| x_cpsc | X CPSC account | x_api | social_candidate | NATIONAL | https://x.com/USCPSC | platform account/API candidate | manual_review_only | disabled | 10 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Consumer recall echo only through official API. | U10 |
| x_nhtsa | X NHTSA account | x_api | social_candidate | NATIONAL | https://x.com/NHTSAgov | platform account/API candidate | manual_review_only | disabled | 10 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Vehicle recall echo only through official API. | U10 |
| x_cisa | X CISA account | x_api | social_candidate | NATIONAL | https://x.com/CISAgov | platform account/API candidate | manual_review_only | disabled | 10 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Cyber social echo only through official API. | U10 |
| x_faa | X FAA News account | x_api | social_candidate | NATIONAL | https://x.com/FAANews | platform account/API candidate | manual_review_only | disabled | 10 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Aviation social echo only through official API. | U10 |
| x_usgs_quakes | X USGS Quakes account | x_api | social_candidate | NATIONAL | https://x.com/USGS_Quakes | platform account/API candidate | manual_review_only | disabled | 10 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Seismic social echo only through official API. | U10 |
| x_whitehouse | X White House account | x_api | social_candidate | NATIONAL | https://x.com/WhiteHouse | platform account/API candidate | manual_review_only | disabled | 5 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Civic social source; low default and policy-sensitive. | U10 |
| x_federal_register | X Federal Register account | x_api | social_candidate | NATIONAL | https://x.com/FederalRegister | platform account/API candidate | manual_review_only | disabled | 5 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Regulatory social echo only through official API. | U10 |
| bluesky_us_breaking | Bluesky U.S. breaking news search | bluesky | social_candidate | NATIONAL | https://bsky.app/search?q=United%20States%20breaking%20news | platform search/API candidate | manual_review_only | disabled | 4 | platform | high | high | high | high | candidate_policy_sensitive | Broad social search is disabled and high risk. | U10 |
| bluesky_nws_warning | Bluesky NWS warning search | bluesky | social_candidate | NATIONAL | https://bsky.app/search?q=NWS%20warning | platform search/API candidate | manual_review_only | disabled | 5 | platform | high | high | high | high | candidate_policy_sensitive | Weather echo candidate only after AT Protocol review. | U10 |
| bluesky_faa_ground_stop | Bluesky FAA ground stop search | bluesky | social_candidate | NATIONAL | https://bsky.app/search?q=FAA%20ground%20stop | platform search/API candidate | manual_review_only | disabled | 5 | platform | high | high | high | high | candidate_policy_sensitive | Aviation echo only after policy review. | U10 |
| bluesky_fda_recall | Bluesky FDA recall search | bluesky | social_candidate | NATIONAL | https://bsky.app/search?q=FDA%20recall | platform search/API candidate | manual_review_only | disabled | 5 | platform | high | high | high | high | candidate_policy_sensitive | Recall echo only after policy review. | U10 |
| bluesky_cisa_advisory | Bluesky CISA advisory search | bluesky | social_candidate | NATIONAL | https://bsky.app/search?q=CISA%20advisory | platform search/API candidate | manual_review_only | disabled | 5 | platform | high | high | high | high | candidate_policy_sensitive | Cyber echo only after policy review. | U10 |
| bluesky_usgs_earthquake | Bluesky USGS earthquake search | bluesky | social_candidate | NATIONAL | https://bsky.app/search?q=USGS%20earthquake | platform search/API candidate | manual_review_only | disabled | 5 | platform | high | high | high | high | candidate_policy_sensitive | Seismic echo only after policy review. | U10 |
| rfc9309_robots | RFC 9309 Robots Exclusion Protocol | policy_reference | source_health_only | NATIONAL | https://www.rfc-editor.org/rfc/rfc9309.html | public standards reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | Policy reference for robots handling. | U1 |
| rss_specification | RSS specification | policy_reference | source_health_only | NATIONAL | https://www.rssboard.org/rss-specification | public standards reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | RSS parser reference. | U1 |
| sitemap_protocol | Sitemaps protocol | policy_reference | source_health_only | NATIONAL | https://www.sitemaps.org/protocol.html | public standards reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | Reference only; no sitemap crawling early. | U1 |
| schema_newsarticle | Schema.org NewsArticle | policy_reference | source_health_only | NATIONAL | https://schema.org/NewsArticle | public schema reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | Metadata reference for publisher markup review. | U8 |
| reddit_developer_terms | Reddit Developer Terms | policy_reference | source_health_only | NATIONAL | https://redditinc.com/policies/developer-terms | public platform policy | manual_review_only | none | 0 | reference | low | high | low | low | candidate_policy_sensitive | Must be reviewed before Reddit access. | U10 |
| reddit_data_api_terms | Reddit Data API Terms | policy_reference | source_health_only | NATIONAL | https://redditinc.com/policies/data-api-terms | public platform policy | manual_review_only | none | 0 | reference | low | high | low | low | candidate_policy_sensitive | Must be reviewed before Reddit API use. | U10 |
| x_api_docs | X API introduction | policy_reference | source_health_only | NATIONAL | https://docs.x.com/x-api/introduction | public platform API docs | manual_review_only | none | 0 | reference | low | high | low | low | candidate_policy_sensitive | Must be reviewed before X source enablement. | U10 |
| bluesky_atproto_docs | Bluesky AT Protocol XRPC API docs | policy_reference | source_health_only | NATIONAL | https://docs.bsky.app/docs/api/at-protocol-xrpc-api | public platform API docs | manual_review_only | none | 0 | reference | low | medium | low | low | candidate_policy_sensitive | Reference for possible compliant Bluesky adapter. | U10 |

## SECTION 5: Source admission tiers

Tier 0 - local fixtures only:

- No network.
- Used for parser, storage, ranking, privacy, and UI tests.
- Fixture adapters must produce the same normalized shapes as later live adapters.

Tier 1 - official APIs, official open data, RSS/Atom, CAP feeds, GeoJSON feeds, hydrology APIs,
recall APIs, Federal Register APIs, official agency JSON endpoints, and official government RSS:

- Best first live candidates.
- Examples: NWS active alerts, USGS earthquake GeoJSON, FSIS Recall API, CPSC Recalls API, FAA NAS
  status if endpoint behavior is verified, CISA advisory/KEV feeds if machine-readable, and Federal
  Register API with filters.
- Must be disabled by default and opt-in.

Tier 2 - official pages with stable public operational data but no obvious feed/API:

- Candidate only after source-policy review.
- Prefer source-health checks and manual review before parser implementation.
- Must use per-source selectors if extraction is ever allowed.
- No recursive crawling and no article-body fetch.

Tier 3 - national news RSS or publisher-provided feeds:

- Store headline metadata only.
- No article-body archive.
- No paywall bypass.
- Repeated syndicated headlines should not create fake source diversity.

Tier 4 - public media, nonprofit outlets, and specialist topic outlets:

- Prefer RSS/Atom.
- Store headline metadata only.
- Respect robots, terms, and source policy.
- Rank by public-impact relevance, not general interest alone.

Tier 5 - social/community signals:

- Policy-sensitive.
- Disabled by default.
- Reddit only through compliant official API or permitted feed access.
- X/Twitter only through official API access if explicitly configured.
- Bluesky may be explored through official AT Protocol later.
- No HTML scraping to bypass platform restrictions.
- No long-term social archive.

Tier 6 - unofficial aggregators and dashboards:

- Useful as human comparison or source-health reference.
- Do not treat as primary authority over official sources.
- Do not clone their work or scrape aggressively.
- If used later, source-health-only or manual-review-only unless policy review supports more.

## SECTION 6: NATIONAL event model

The system should not only store "news items." It should infer that multiple recent items refer to
the same national event. A future `national_events` table is clearer than forcing all national
state into generic clusters, though it can share the same storage and evidence conventions used by
the broader news architecture.

Candidate future `national_events` table:

| Column | Purpose |
| --- | --- |
| `national_event_id` | Internal integer primary key. |
| `scope` | Always `NATIONAL` initially. |
| `event_key` | Deterministic key from event type, source families, agency/state/sector/product/time tokens, and normalized title tokens. |
| `event_type` | Controlled NATIONAL event type. |
| `title` | Representative bounded title, not an LLM summary. |
| `representative_item_id` | Best item to display as primary evidence. |
| `severity` | Deterministic severity bucket such as `info`, `notice`, `elevated`, `major`, or `critical`. |
| `public_impact_score` | Direct national impact component. |
| `source_diversity_score` | Independent source-family convergence component. |
| `official_confirmation_score` | Official-source strength component. |
| `social_echo_score` | Optional compliant social echo component. |
| `news_echo_score` | National news/public media convergence component. |
| `emergency_score` | FEMA/DHS/federal alert component. |
| `weather_hazard_score` | NWS/SPC/WPC severe weather component. |
| `disaster_score` | FEMA declaration and disaster signal component. |
| `public_health_score` | CDC/FDA/FSIS/CPSC/NHTSA/OSHA/EPA public health and safety component. |
| `recall_score` | Recall severity, class, distribution, and hazard component. |
| `transport_impact_score` | DOT/FRA/Amtrak/maritime transport component. |
| `aviation_impact_score` | FAA/NAS/airport ground stop or delay component. |
| `cyber_impact_score` | CISA/NVD/NIST/FBI/IC3 cyber component. |
| `economic_impact_score` | Scheduled official economic release component. |
| `regulatory_impact_score` | Federal Register and regulatory action component. |
| `federal_civic_score` | Executive, congressional, court, and agency action component. |
| `first_seen_at` | First local observation. |
| `last_seen_at` | Most recent matching observation. |
| `last_elevated_at` | Most recent time the event crossed display/ranking threshold. |
| `expires_at` | Purge cutoff. |
| `geography_json` | Bounded geography such as national, multi-state, affected states, territories, FEMA region, storm basin, or airport list. |
| `states_json` | Normalized affected states/territories. |
| `agencies_json` | Federal agencies represented in evidence. |
| `corridors_json` | Airports, routes, national corridors, ports, rail, sectors, or systems. |
| `source_ids_json` | Source ids represented in the event. |
| `item_ids_json` | Item ids represented in the event. |
| `evidence_json` | Source, parser, matching, ranking, policy, and scope evidence. |
| `ranking_explanation_json` | Score factors and deterministic reason strings. |
| `status` | `active`, `monitoring`, `expired`, `hidden`, `policy_blocked`, or `resolved`. |

Required event types:

- `national_emergency_alert`
- `federal_disaster_declaration`
- `severe_weather_outbreak`
- `hurricane_watch_warning`
- `tornado_outbreak`
- `wildfire_national`
- `smoke_air_quality_national`
- `flood_national`
- `drought_national`
- `earthquake_national`
- `tsunami_national`
- `volcano_unrest`
- `public_health_alert`
- `disease_outbreak`
- `food_recall`
- `drug_device_recall`
- `consumer_product_recall`
- `vehicle_recall`
- `aviation_ground_stop`
- `airport_national_disruption`
- `rail_disruption`
- `major_transport_disruption`
- `cyber_advisory`
- `known_exploited_vulnerability`
- `emergency_directive`
- `energy_grid_disruption`
- `federal_regulatory_action`
- `executive_action`
- `congressional_action`
- `court_decision`
- `economic_release`
- `sanctions_action`
- `major_national_news`
- `community_signal`
- `source_health_problem`

Routine low-impact national news should not automatically become elevated NATIONAL events. Ordinary
agency press releases, political churn, punditry, personnel announcements, grant announcements,
routine court filings, and market commentary remain hidden, low-priority, or background pulse unless
official severity, immediate public impact, or independent cross-source convergence justifies
elevation.

## SECTION 7: Cross-source convergence ranking

The ranking model should implement this idea deterministically: if something appears in official
sources, national news, agency feeds, transport feeds, public-health feeds, cyber feeds, recall
sources, and compliant community/social signals within a short window, it is probably important or
interesting.

This is not an LLM summarizer. The system should compute features, scores, and explanations from
stored metadata only.

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

Independent source families count more than repeated mentions from the same family. Candidate
families:

- `fema`
- `dhs`
- `nws`
- `noaa_spc`
- `noaa_nhc`
- `noaa_wpc`
- `noaa_nwm`
- `usgs`
- `cdc`
- `fda`
- `fsis`
- `cpsc`
- `nhtsa`
- `faa`
- `dot`
- `cisa`
- `nist`
- `fbi`
- `doe`
- `eia`
- `ferc`
- `treasury`
- `federal_reserve`
- `bls`
- `bea`
- `census`
- `federal_register`
- `congress`
- `govinfo`
- `supreme_court`
- `national_wire`
- `public_media`
- `national_tv`
- `nonprofit_news`
- `reddit`
- `bluesky`
- `x_api`
- `source_health`

3. Temporal proximity

Items closer in time are more likely to refer to the same event. Initial matching windows:

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
- Federal regulatory/civic action: 0 to 72 hours unless active public comment or immediate public
  impact exists.

4. Geographic proximity and reach

Match by:

- United States national flag.
- State.
- Territory.
- Region.
- FEMA region.
- NWS region.
- Storm basin.
- Affected airports.
- Affected states.
- Affected product distribution area.
- Affected industry.
- Affected federal agency.
- Affected infrastructure sector.
- Affected population group.
- Court/federal jurisdiction.
- National or multi-state label.

5. Public impact

Boost:

- Official emergency alerts.
- Disaster declarations.
- Hurricane/tornado/severe weather warnings.
- Nationwide or multi-state aviation disruption.
- High-risk recalls.
- Public health warnings.
- Widespread cyber threats.
- Energy/grid disruptions.
- Major transport closures.
- Federal rules with immediate public effect.
- Supreme Court/court decisions with immediate national effect.
- Economic releases with broad public salience.
- Sanctions or foreign policy actions with direct domestic impact.
- National security advisories.
- Multi-source national news convergence.

6. Recency

Recent items matter more, but older active hazards can stay elevated while still active. Evidence
must show whether an item is fresh, active-but-older, stale, or retained only for source-health/debug
evidence.

7. User-configured priority

Future config should allow boosts for:

- Weather.
- Hurricane.
- Aviation.
- Cyber.
- Recalls.
- Public health.
- FDA.
- CDC.
- CISA.
- NWS.
- FAA.
- Transportation.
- Energy.
- Economy.
- Courts.
- Congress.
- Federal regulations.
- Pacific Northwest impact.
- Seattle impact.
- Washington impact.

8. Low-public-value penalty

De-emphasize:

- Routine agency press releases.
- Generic political messaging.
- Minor personnel announcements.
- Single-source punditry.
- Duplicate syndicated stories.
- Local stories with no national impact.
- Vague social-only reports.
- Economic data releases not on the configured attention list.
- Routine court filings with no public impact.
- Press releases that only announce grants unless tied to emergency/disaster response.

Sample scoring formula:

```text
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
```

Possible normalization:

```text
recency_score = 0..20
official_severity_score = 0..45
source_diversity_score = min(35, independent_family_count * 6 + official_family_count * 4)
public_impact_score = 0..35
geographic_reach_score = 0..30
active_alert_score = 0 or 20
source_priority_score = configured_priority / 10
cluster_size_score = min(10, unique_item_count)
local_or_regional_impact_score = 0..15
duplicate_family_penalty = max(0, duplicate_mentions_same_family - 1) * 2
stale_source_penalty = 0..25
low_confidence_penalty = 0..30
low_public_value_penalty = 0..50
out_of_scope_penalty = 0..60
```

The exact constants can change in implementation, but the score must stay explainable in JSON and
visible in evidence. A display row should be able to say:

```json
{
  "reason": "Elevated by FAA national ground stop, NAS status evidence, airport impact, and independent AP/NPR coverage within 45 minutes.",
  "features": {
    "official_severity_score": 40,
    "source_diversity_score": 22,
    "public_impact_score": 32,
    "geographic_reach_score": 30,
    "low_public_value_penalty": 0
  }
}
```

"Frequency of appearance" means independent cross-source convergence, not raw duplicate counts.

Bad ranking:

- 30 syndicated versions of the same political article dominate.

Good ranking:

- FAA national ground stop.
- FAA/NAS official status confirms.
- Major airports show active events.
- National news and local airport feeds converge.
- Social chatter appears only as a low-weight echo if compliant.
- All within a plausible time window.

## SECTION 8: NATIONAL source category design

NATIONAL sources should be grouped by operational purpose. The category controls parser family,
retention, privacy rules, source-health expectations, and ranking contribution.

### 1. National emergency and disaster

- Why it exists: Federal emergency, disaster, and homeland-security alerts can matter nationally and
  can anchor cross-source convergence.
- First safe sources: FEMA/OpenFEMA disaster declarations, DHS NTAS, Ready.gov, FEMA press releases.
- Parser/adaptor class: `official_api_json`, `rss_atom`, `static_html_headline_candidate`, and
  `source_health_probe_only`.
- Likely refresh interval: 30 to 60 minutes for active alert pages, 6 hours for disaster
  declarations, 24 hours for reference pages.
- Privacy risk: low to medium.
- Policy risk: low for official APIs/feeds, medium for HTML-only pages.
- Source-health signals: last successful parse, active declaration count, advisory timestamp,
  stale threshold, parser error, policy state.
- Sample item fields: `declaration_id`, `incident_type`, `state`, `fema_region`, `effective_at`,
  `published_at`, `source_url`, `assistance_programs`.
- Ranking contribution: high official severity for declarations, NTAS alerts, emergency assistance,
  and multi-state disaster response.
- Later phase: U6/U7 for official API/feed candidates; U9 for HTML-only sources.

### 2. Weather, hurricane, flood, fire weather, and drought

- Why it exists: Weather hazards are among the most actionable national signals and often drive
  disaster, transport, power, and public-health impacts.
- First safe sources: NWS active alerts, SPC watches/outlooks, NHC advisories, WPC rainfall/flood
  products, NOAA water candidates, USGS water services.
- Parser/adaptor class: `official_api_json`, `cap_alerts`, `rss_atom`, `hydrology_api_json`,
  `static_html_headline_candidate`.
- Likely refresh interval: 5 to 10 minutes for active alerts, 10 to 30 minutes for hurricane and
  severe weather products, 15 to 60 minutes for hydrology/drought products.
- Privacy risk: low.
- Policy risk: low to medium.
- Source-health signals: alert count, advisory number, product issue time, gauge staleness, parser
  failure, stale source warning.
- Sample item fields: `event`, `severity`, `urgency`, `certainty`, `affected_states`,
  `storm_name`, `watch_number`, `effective_at`, `expires_at`, `source_url`.
- Ranking contribution: warnings, active hurricane watches/warnings, multi-state severe weather,
  flooding, and fire weather elevate strongly.
- Later phase: U2 fixtures, U6 first live candidates, U7 additional NOAA/water sources.

### 3. Wildfire, smoke, and national air quality

- Why it exists: Large fires and smoke impacts cross state lines and can affect travel, public
  health, power, and federal response.
- First safe sources: NIFC, InciWeb, AirNow, EPA air quality data, NWS fire weather.
- Parser/adaptor class: `rss_atom`, `official_api_json`, `static_html_headline_candidate`,
  `source_health_probe_only`, `arcgis_feature_service_candidate` only after verified.
- Likely refresh interval: 15 to 60 minutes during active events, daily for statistics.
- Privacy risk: low to medium.
- Policy risk: medium until endpoint shapes are verified.
- Source-health signals: incident update time, fire count, AQI station freshness, endpoint
  verification status.
- Sample item fields: `fire_name`, `incident_id`, `states`, `acres`, `containment_percent`,
  `evacuation_level`, `aqi_region`, `source_url`.
- Ranking contribution: large fires, evacuations, multi-state smoke, AQI above threshold, and
  convergent weather/news signals elevate.
- Later phase: U2 fixtures, U7 endpoint verification, U9 dashboard/feature-service research.

### 4. Earthquake, tsunami, and volcano

- Why it exists: Low-frequency/high-impact national hazards require official-only handling and clear
  thresholds.
- First safe sources: USGS GeoJSON/FDSN, USGS VHP/observatories, Tsunami.gov.
- Parser/adaptor class: `geojson_feed`, `official_api_json`, `static_html_headline_candidate`,
  `source_health_probe_only`.
- Likely refresh interval: 5 minutes for earthquake feeds, 10 to 60 minutes for tsunami/volcano
  pages during active events, 24 hours for references.
- Privacy risk: low.
- Policy risk: low to medium.
- Source-health signals: feed age, latest event timestamp, GeoJSON validity, magnitude threshold
  coverage, official alert level.
- Sample item fields: `event_id`, `magnitude`, `depth_km`, `place`, `time`, `felt_count`, `mmi`,
  `volcano_name`, `alert_level`, `tsunami_status`.
- Ranking contribution: earthquakes above threshold, tsunami warnings, and official volcano unrest
  get high severity.
- Later phase: U2 fixtures, U6 USGS live candidate, U7 volcano/tsunami sources.

### 5. Public health, disease, food safety, recalls, and consumer safety

- Why it exists: Health alerts and recalls have direct national public-impact value and should rank
  above generic health news.
- First safe sources: CDC HAN/outbreaks, FDA recalls, FSIS Recall API, CPSC Recalls API, NHTSA
  recalls, OSHA/EPA releases when public-impact.
- Parser/adaptor class: `rss_atom`, `official_api_json`, `recall_api_json`,
  `static_html_headline_candidate`.
- Likely refresh interval: 60 minutes for recall/alert feeds, 2 to 6 hours for release pages.
- Privacy risk: low to medium depending on outbreak detail.
- Policy risk: low to medium.
- Source-health signals: latest recall/update timestamp, active recall count, API schema validity,
  parser failure, source stale state.
- Sample item fields: `agency`, `alert_type`, `product`, `firm`, `recall_class`, `hazard`,
  `distribution_geography`, `public_instruction_url`, `effective_at`, `updated_at`.
- Ranking contribution: CDC HAN, Class I/high-risk recalls, public health alerts, and multi-source
  recall/news convergence elevate.
- Later phase: U2 fixtures, U6 FSIS first live candidate, U7 FDA/CPSC/NHTSA.

### 6. Transportation, aviation, rail, ports, and national travel

- Why it exists: FAA/NAS and national transportation disruptions can immediately affect daily plans,
  logistics, and regional/local scopes.
- First safe sources: FAA NAS status, FAA airport status, FAA statements, DOT/FRA/Amtrak/Maritime
  pages.
- Parser/adaptor class: `aviation_status_json_or_xml`, `rss_atom`, `static_html_headline_candidate`,
  `source_health_probe_only`.
- Likely refresh interval: 5 minutes for active aviation status, 15 to 60 minutes for transit/rail,
  2 hours for lower-priority official releases.
- Privacy risk: low.
- Policy risk: low to medium.
- Source-health signals: active airport event count, status update time, endpoint behavior, parser
  state, auth/rate-limit state if any.
- Sample item fields: `airport`, `system`, `event_type`, `delay_minutes`, `ground_stop`,
  `ground_delay`, `closure_status`, `start_time`, `end_time`, `source_update_time`.
- Ranking contribution: nationwide or multi-airport ground stops, major rail disruption, and
  freight/port disruption elevate strongly.
- Later phase: U2 fixtures, U6 FAA live candidate, U7/U8 additional DOT/FRA/Amtrak sources.

### 7. Cybersecurity and critical infrastructure

- Why it exists: Known exploited vulnerabilities, emergency directives, and infrastructure security
  advisories can require immediate user action.
- First safe sources: CISA advisories, alerts, ICS advisories, KEV catalog, emergency directives,
  NVD/NIST docs, IC3/FBI as corroboration.
- Parser/adaptor class: `rss_atom`, `official_api_json`, `csv_download_candidate`,
  `static_html_headline_candidate`.
- Likely refresh interval: 60 minutes for CISA/KEV/advisories, 2 to 6 hours for lower-priority
  sources.
- Privacy risk: low.
- Policy risk: low to medium.
- Source-health signals: advisory id continuity, KEV due-date parsing, feed timestamp, API/CSV
  schema validity, parser failure.
- Sample item fields: `advisory_id`, `cve_ids`, `vendor`, `product`, `kev_due_date`, `severity`,
  `exploited_in_the_wild`, `mitigation_url`, `emergency_directive`.
- Ranking contribution: KEV additions, emergency directives, high-impact advisories, and
  convergence with official/news/security sources elevate.
- Later phase: U2 fixtures, U6/U7 CISA/KEV endpoint research and parsing.

### 8. Energy, grid, fuels, and infrastructure

- Why it exists: Grid/fuel/energy disruptions can affect national systems, transportation, and
  public safety.
- First safe sources: DOE, EIA Open Data, FERC, NERC, DOE OE-417 candidates.
- Parser/adaptor class: `rss_atom`, `economic_api_json`, `csv_download_candidate`,
  `source_health_probe_only`.
- Likely refresh interval: daily for data series, 2 hours for official releases, faster only for
  verified operational outage sources.
- Privacy risk: low.
- Policy risk: low to medium.
- Source-health signals: release timestamp, dataset freshness, parser schema validity, source
  stale state.
- Sample item fields: `agency`, `sector`, `region`, `incident_type`, `release_id`, `metric`,
  `published_at`, `source_url`.
- Ranking contribution: confirmed energy emergency, grid reliability issue, fuel disruption, or
  multi-source infrastructure impact elevates. Routine data releases remain low.
- Later phase: U7/U8 for official sources, U9 for dataset research.

### 9. Federal government, regulatory, courts, Congress, and executive actions

- Why it exists: Federal actions can matter nationally, but this category must not become a
  politics feed.
- First safe sources: White House presidential actions, Federal Register API, GovInfo feeds,
  Congress.gov API candidate, Supreme Court slip opinions, U.S. Courts RSS, DOJ news.
- Parser/adaptor class: `federal_register_api`, `govinfo_rss`, `congress_api_candidate`,
  `rss_atom`, `static_html_headline_candidate`.
- Likely refresh interval: 2 hours for Federal Register/public inspection, 30 to 60 minutes for
  court opinions when enabled, 6 hours for Congress/govinfo.
- Privacy risk: low to medium for legal items.
- Policy risk: low to medium, with auth/key risk for Congress.gov.
- Source-health signals: API availability, auth-required state, feed timestamp, filter hit count,
  parser status.
- Sample item fields: `agency`, `document_type`, `docket`, `action`, `publication_date`,
  `comment_close_date`, `court`, `opinion_id`, `bill_id`, `source_url`.
- Ranking contribution: high-impact rules, emergency actions, executive actions, court decisions,
  sanctions, and official actions with immediate public effect can elevate; routine notices sink.
- Later phase: U7/U9 after filters/auth design.

### 10. Economic releases and national indicators

- Why it exists: Official economic releases can be high-salience public facts but must not turn into
  investment advice or a market dashboard.
- First safe sources: BLS, BEA, Federal Reserve, Treasury, Fiscal Data, Census, FRED candidates.
- Parser/adaptor class: `economic_api_json`, `rss_atom`, `csv_download_candidate`,
  `source_health_probe_only`.
- Likely refresh interval: scheduled release windows, daily otherwise.
- Privacy risk: low.
- Policy risk: medium when API keys are required.
- Source-health signals: release schedule match, series allowlist, API key state, stale dataset
  state, parser schema validity.
- Sample item fields: `agency`, `release_name`, `series_id`, `period`, `value`, `unit`,
  `release_time`, `source_url`.
- Ranking contribution: configured high-salience releases elevate on release day; the system must
  not provide trading or investment advice.
- Later phase: U7/U9 after allowlist design.

### 11. National news, public media, wires, and nonprofit journalism

- Why it exists: Journalism can explain official signals and provide convergence, but it must not
  dominate official alerts or become an archive.
- First safe sources: AP, Reuters, NPR, PBS, CBS, ABC, NBC, CNN, Fox, USA Today, ProPublica,
  Guardian, BBC U.S./Canada feeds where verified.
- Parser/adaptor class: `rss_atom` preferred; `static_html_headline_candidate` only after explicit
  policy review.
- Likely refresh interval: 30 to 60 minutes.
- Privacy risk: medium for crime/victim/health details.
- Policy risk: medium because publisher terms, paywalls, and syndication require caution.
- Source-health signals: feed parse status, latest item time, duplicate/syndication fingerprint
  rate, policy-blocked status.
- Sample item fields: `headline`, `url`, `canonical_url`, `published_at`, `description_bounded`,
  `publisher`, `tags`, `syndication_hint`.
- Ranking contribution: Adds independent news echo to official events. Multiple publishers increase
  convergence only when source families are independent, not duplicate wire copies.
- Later phase: U2 fixtures, U8 live RSS after source verification.

### 12. Social/community echoes

- Why it exists: Community signals can add weak echo, but they are policy-sensitive and should never
  become primary evidence.
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
- Ranking contribution: Weak echo only after official or news evidence exists. Social-only reports
  must not outrank official sources or be presented as verified fact.
- Later phase: U10 only.

### 13. Source health and disabled states

- Why it exists: NATIONAL must distinguish nothing known from disabled, stale, unsupported,
  auth-required, rate-limited, policy blocked, or parser failed.
- First safe sources: All configured NATIONAL sources, including disabled and manual-review-only
  entries.
- Parser/adaptor class: `source_health_probe_only`, registry validation, and stored health rows.
- Likely refresh interval: computed from config/SQLite on page load; explicit ingest/source-health
  commands update health rows later.
- Privacy risk: low.
- Policy risk: low unless later probes perform network. Page loads must never do that.
- Source-health signals: state, last success/failure, stale threshold, parser support, auth status,
  policy status, disabled reason.
- Sample item fields: `source_id`, `state`, `last_attempt_at`, `last_success_at`,
  `consecutive_failures`, `message`, `evidence_json`.
- Ranking contribution: stale/failing sources lower confidence. Source-health problems appear as
  maintenance items, not public events.
- Later phase: U1/U2 for registry and fixture health, U5 for UI.

## SECTION 9: NATIONAL public-safety and privacy posture

NATIONAL is a public-impact metadata layer. It should prefer official, public, bounded fields and
should avoid amplifying private distress, outrage, or speculative claims.

Rules:

- Store source-provided public metadata only.
- Do not store full narratives beyond bounded descriptions.
- Do not archive social posts long term.
- Do not surface private individual data.
- Preserve source links in evidence so the user can click official sources.
- For major incidents, show public operational facts: event type, source, source family, affected
  states/agencies/sectors, public impact, observed time, and source link.
- Treat early official reports as preliminary where applicable.
- Do not turn NATIONAL into a fear dashboard.
- Do not turn NATIONAL into a partisan outrage dashboard.
- Low-public-value political churn should be background pulse or ignored unless it has official,
  legal, emergency, economic, or public-impact significance.
- Social-only national claims should never outrank official alerts.
- Do not infer medical, legal, investment, victim, suspect, or private-person advice from source
  metadata.
- Do not present economic releases as trading signals.
- Do not use LLMs to summarize sensitive national incident narratives in runtime behavior.

Default display posture:

| Source shape | Display location | Retention posture | Elevation rule |
| --- | --- | --- | --- |
| Official federal alert | National/state/agency/sector | Expiration plus 24 hours | Elevate by severity. |
| Weather/hurricane hazard | State/multi-state/storm basin | Expiration plus 24 to 48 hours, hurricane active storm plus 7 days | Elevate by warning/watch and reach. |
| Public health alert | Agency/affected population/states | 14 to 30 days | Elevate by official action guidance and severity. |
| Recall | Product/agency/distribution area | 14 to 30 days | Elevate high-risk and broad distribution. |
| Cyber advisory | Advisory/CVE/vendor/product | 14 to 30 days | Elevate KEV, emergency directives, high-impact advisories. |
| Aviation/transport disruption | Airport/system/route | 3 to 7 days | Elevate ground stops, closures, national disruption. |
| Economic release | Agency/release/period | 3 to 7 days | Elevate only configured high-salience releases; no advice. |
| News headline | Publisher headline metadata | 7 days | Elevate only with public impact or convergence. |
| Social/community echo | Platform/link only if allowed | 24 to 72 hours max | Never primary; weak echo only. |

## SECTION 10: NATIONAL source freshness and retention

NATIONAL is a short-retention recent-signal layer. It is not an archive. Every future ingest run
must purge expired data before or after writing new rows, and purge evidence must be visible in
source-health or SYSTEM evidence.

Default candidate retention:

| Data class | Candidate retention | Notes |
| --- | --- | --- |
| Raw fetch diagnostics | 7 days or less | Status, timing, byte counts, and parser outcome only. |
| Raw payload debug | Disabled by default; 6 hours max if enabled | Must never be enabled in `config.example.yml`. |
| Official alert metadata | Expiration plus 24 hours | If no expiration exists, use 7 days max. |
| Weather/hazard metadata | Expiration plus 24 to 48 hours | Active hazards stay until expiration plus grace window. |
| Hurricane/advisory metadata | Active storm plus 7 days | Preserve advisory cycle evidence while active. |
| Wildfire/smoke metadata | 7 to 14 days while active, then expire | Keep active incident evidence bounded. |
| Earthquake metadata | 7 days for significant U.S. events, 14 days for major events | Threshold-driven. |
| Volcano unrest metadata | 14 days while active, official-only | No stale unofficial chatter. |
| Recall metadata | 14 to 30 days | High-severity recalls may remain visible as active if source says active. |
| Public health alert metadata | 14 to 30 days | Depends on source expiration and severity. |
| Cyber advisory metadata | 14 to 30 days | KEV items can follow due date or configured active window. |
| FAA/transport disruption metadata | 3 to 7 days | Longer only for unresolved disruptions. |
| Economic release metadata | 3 to 7 days | Scheduled-release metadata only. |
| Federal Register/civic metadata | 7 days | Longer only if active public-comment/action window is explicitly tracked. |
| News headline metadata | 7 days | Metadata only, no article body archive. |
| National event clusters | 7 to 14 days | Same or slightly longer than member items. |
| Source health | 30 days | Enough for local troubleshooting. |
| Ranking explanations | Same as item/event retention | Ranking evidence expires with item/event. |
| Social metadata, if ever enabled | 24 to 72 hours unless terms require shorter or prohibit storage | Disabled by default. |

Freshness classes:

| Class | Meaning | Display behavior |
| --- | --- | --- |
| `fresh` | Source item is inside normal update window. | Eligible for normal ranking. |
| `active_but_older` | Item is older but source says it is still active or unexpired. | Eligible with active-alert score and age disclosure. |
| `scheduled_release` | Item is a configured official release on its release day. | Eligible only if configured. |
| `stale_source` | Source has not updated within `stale_after_minutes`. | Lower confidence and show warning. |
| `expired` | Item passed expiration/retention cutoff. | Purge or hide. |
| `debug_only` | Retained only for source-health/debug evidence. | Never show as live public event. |

No article body archive, no permanent national incident archive, and no permanent social archive are
allowed.

## SECTION 11: Adapter design for NATIONAL

The adapter layer should normalize source-specific records into a shared item/event input shape
without fetching article bodies, crawling, or making page-load network requests. Adapters should be
pure parser/normalizer units in early phases and should run against local fixtures before any live
source is enabled.

Shared adapter output fields:

```yaml
normalized_item:
  source_id: "cisa_kev"
  source_family: "cisa"
  source_class: "official_cybersecurity"
  scope: "NATIONAL"
  title: "Known exploited vulnerability added"
  url: "https://..."
  canonical_url: "https://..."
  published_at: "2026-01-01T12:00:00Z"
  observed_at: "2026-01-01T12:01:00Z"
  expires_at: "2026-01-31T12:00:00Z"
  description_bounded: "Short source-provided description."
  event_type_hint: "known_exploited_vulnerability"
  national_relevance:
    affected_states: []
    affected_sectors: ["technology"]
    affected_agencies: ["CISA"]
    national_scope: true
  severity:
    source_severity: "known_exploited"
    normalized: "major"
  policy:
    body_fetched: false
    source_terms_reviewed: false
    homepage_extractor_used: false
  evidence:
    parser: "cisa_kev_fixture_v1"
    fixture: true
```

Adapter families:

`rss_atom`

- Targets: federal agency RSS feeds, national news/public media feeds, CPSC RSS, FDA RSS if
  verified, GovInfo feeds, and court/agency feeds where available.
- Must parse title, URL, canonical URL where available, published timestamp, bounded description,
  categories, tags, and source.
- Must bound description length.
- Must not fetch article bodies.
- Must fail soft on malformed feeds.
- Must produce duplicate fingerprints for syndicated articles.

`official_api_json`

- Targets: NWS active alerts, FDA/CISA/FAA/EIA/NHTSA/FEMA/OpenFEMA and other official JSON endpoints
  where verified.
- Must support timeouts, response size caps, source-specific rate limits, conditional requests when
  available, schema validation, and per-source fail-soft behavior.
- Must preserve official IDs, issue/update times, expiration times, status, severity, and source
  URLs.

`cap_alerts`

- Targets: NWS CAP/API alert records if useful.
- Must preserve severity, urgency, certainty, effective time, expiration, affected area, source
  instruction URL, and alert ID.

`geojson_feed`

- Targets: USGS earthquake GeoJSON and possible wildfire/federal geospatial feeds if verified.
- Must support region filters, magnitude filters, hazard filters, feature IDs, geometry handling,
  source-provided update times, and provenance.

`hydrology_api_json`

- Targets: USGS water services and NOAA water candidates if verified.
- Must support gauge allowlists, national/regional filters, stage category mapping, stale gauge
  detection, and flood-stage evidence.

`recall_api_json`

- Targets: FSIS Recall API, CPSC Recalls API, NHTSA recall APIs, and FDA recall data only after
  endpoint verification.
- Must preserve recall class, product, firm, hazard, distribution scope, date, official URL,
  active status, and public instructions.

`federal_register_api`

- Targets: Federal Register API and public inspection documents.
- Must support agency allowlist, document type allowlist, high-impact filters, and public-comment
  window fields.
- Must not flood the dashboard with routine notices.

`congress_api_candidate`

- Congress.gov API requires an API key.
- Disabled by default.
- Must treat auth/key handling carefully.
- Must support bill/action filters and avoid becoming a general legislative firehose.

`govinfo_rss`

- Targets: GovInfo RSS feeds for allowlisted collections.
- Must be allowlisted and filtered.
- Must not ingest every federal publication by default.

`economic_api_json`

- Targets: BLS API, BEA API, FRED/Federal Reserve candidates, Treasury Fiscal Data API, and Census
  candidates.
- Must support scheduled-release awareness and configured series allowlists.
- Must not provide investment advice.

`aviation_status_json_or_xml`

- Targets: FAA NAS Status and airport status candidates.
- Must preserve active event type, airport, delay, ground stop/ground delay/closure, and observed
  time.

`csv_download_candidate`

- Only for official CSV data with stable schema.
- Disabled by default until fixture tests exist.
- Must cap rows and support updated-since or short retention.

`data_gov_catalog_candidate`

- Data.gov and agency catalogs are discovery surfaces, not live dashboard ingestion.
- Manual review only unless a specific dataset is promoted.

`arcgis_feature_service_candidate`

- Only if official federal/state feature services are discovered.
- Do not screen scrape dashboards.
- Must record service URL, layer ID, field mapping, geometry policy, paging limits, query filters,
  and source ownership evidence.

`static_html_headline_candidate`

- Only for official pages or national news pages with no RSS/API.
- Disabled unless homepage extractor support is explicitly allowed in future config.
- Must use per-source selectors, no recursive crawling, no article-body fetch, payload size caps,
  robots/policy review, and source-health evidence.

`source_health_probe_only`

- For dashboards and portals useful as human status references but not suitable for ingestion.
- Page loads must not run probes.

`manual_review_only`

- For policy-sensitive, parser-risky, login-required, auth-required, unclear, social, or
  source-terms-sensitive sources.
- These sources can exist in registry and docs but cannot produce live items.

## SECTION 12: Candidate national source registry example

Do not edit `config.example.yml` for this design pass. A later implementation can add disabled
examples after the common news/registry configuration exists. The candidate shape below is
intentionally disabled by default.

```yaml
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
```

Config validation rules for later:

- `national_sources.enabled` defaults to `false`.
- Every source defaults to `enabled: false`.
- Unknown source classes, adapters, verification statuses, and source families are rejected.
- Social source IDs are rejected unless `allow_social_sources` is explicitly true.
- Homepage extraction is rejected unless a future `allow_homepage_extractors` flag is true.
- Congress.gov, BEA, FRED, and any keyed API source must be `auth_required` unless local key config
  exists.
- Economic sources must use allowlisted series/releases and must not provide trading advice.
- Secrets must not appear in `config.example.yml`.

## SECTION 13: NATIONAL UI architecture

Do not implement the UI in this task. The eventual NATIONAL page should use the existing
console-1701 style and template conventions, but it should show honest source-backed states rather
than placeholders or fake headlines.

Proposed bays:

### Bay 1: National attention now

- Highest-ranking NATIONAL events.
- Must show why each item is ranked.
- Must show source-family badges.
- Must show official vs news vs community convergence.
- Must show observed time and last seen.
- Must not dump low-impact political churn.

Required row content:

- Title.
- Event type.
- Representative source.
- Source-family badges.
- Confidence/convergence count.
- Observed time.
- Last seen time.
- Ranking reason.
- Evidence affordance.
- Geographic label, such as national, state, multi-state, affected airport, agency, sector, or
  region.

### Bay 2: Official alerts and hazards

- FEMA, DHS, NWS, NOAA, NHC, SPC, USGS, CDC, FDA, FSIS, CPSC, NHTSA, CISA, FAA, and similar.
- Show active official alerts first.
- Show source freshness.
- Show active severe weather, hurricane, recall, cyber, public-health, aviation, and emergency
  alerts.

### Bay 3: Systems and infrastructure

- Aviation, cyber, transportation, energy, economic releases, Federal Register, Congress/courts if
  enabled.
- Useful for "will this affect national systems, travel, services, software/security, markets, or
  government operations?"
- Must identify auth-required or disabled API sources honestly.

### Bay 4: National press and civic pulse

- AP, Reuters, NPR, PBS, major national broadcasters, nonprofit journalism, and future configured
  sources.
- Social/community signals only if configured and compliant.
- No fake headlines.
- If disabled, show "NATIONAL news sources not configured."

Shared empty states:

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

## SECTION 14: Evidence model for NATIONAL

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
- Retention expiration.
- Matching tokens.
- Event type.
- Event confidence.
- Policy notes.
- Low-public-value penalty if applied.
- Out-of-scope penalty if applied.

Hazard-specific evidence should include where available:

- Alert severity.
- Urgency.
- Certainty.
- Effective time.
- Expiration time.
- Affected zones.
- Affected states.
- Storm name.
- Hurricane advisory number.
- Tornado/severe weather watch number.
- Wildfire name.
- Fire size.
- Containment.
- Evacuation level.
- AQI station or region.
- Drought category.
- Earthquake magnitude.
- Earthquake depth.
- Tsunami status.
- Volcano alert level.
- Source instructions URL.

Public health and recall evidence should include where available:

- Alert type.
- Issuing agency.
- Product.
- Firm.
- Recall class.
- Hazard.
- Affected distribution geography.
- Public instruction URL.
- Outbreak name or pathogen if source provides it.
- Effective/update date.
- Expiration or active status.
- Whether the source says the information is preliminary.

Cyber evidence should include where available:

- Advisory id.
- CVE ids.
- Product/vendor.
- KEV due date if applicable.
- Severity if provided.
- Exploited-in-the-wild flag if provided.
- Mitigation URL.
- Emergency directive flag if applicable.

Transport/aviation evidence should include where available:

- Airport.
- Route.
- System.
- Event type.
- Delay estimate.
- Closure status.
- Ground stop or ground delay status.
- Start time.
- End time.
- Source update time.

Candidate evidence shape:

```json
{
  "event_type": "aviation_ground_stop",
  "event_confidence": "high",
  "source_ids": ["faa_nas_status", "faa_airport_status", "ap_us_news"],
  "source_families": ["faa", "national_wire"],
  "source_classes": ["official_aviation", "wire_service"],
  "official_source_count": 2,
  "news_echo_count": 1,
  "community_echo_count": 0,
  "geographic_reach_basis": {
    "label": "United States",
    "affected_airports": ["SEA", "LAX", "ORD"],
    "affected_states": ["WA", "CA", "IL"]
  },
  "ranking_features": {
    "recency_score": 19,
    "official_severity_score": 40,
    "source_diversity_score": 18,
    "public_impact_score": 32,
    "geographic_reach_score": 28,
    "low_public_value_penalty": 0,
    "out_of_scope_penalty": 0
  },
  "retention": {
    "expires_at": "2026-01-08T00:00:00Z"
  },
  "policy_notes": [
    "No article bodies fetched.",
    "No social sources used.",
    "Page render reads stored SQLite state only."
  ]
}
```

## SECTION 15: Source health for NATIONAL

Source health is part of the feature. The UI and SYSTEM evidence must tell the user when NATIONAL is
disabled, stale, unsupported, auth-required, rate-limited, or policy blocked.

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
| `evidence_json` | Parser, policy, config, auth, and source-health details. |

Health rules:

- Disabled sources are not failures.
- Manual-review-only sources are not failures.
- Auth-required sources must not prompt for secrets in the UI.
- Rate-limited sources back off and preserve the last known source health.
- Parser failures should never crash unrelated sources.
- Page rendering must read stored health only and must not fetch.
- SYSTEM should eventually summarize stale, failing, disabled, policy-blocked, auth-required, and
  manual-review source counts.

## SECTION 16: First implementation sequence for NATIONAL

Phase U0: this design

- Create this design doc.
- Update BACKLOG.
- No runtime behavior change.
- No network.
- No collectors.

Phase U1: source registry scaffolding

- Add disabled NATIONAL source config.
- Add source registry schema or shared news source tables if not already provided by global
  architecture work.
- Add tests proving NATIONAL is disabled by default.
- Add enum validation for source class, adapter, verification status, and source health state.
- No network.

Phase U2: local fixtures only

- Create fixture files for NWS active alert JSON.
- Create NHC RSS/advisory fixture.
- Create USGS earthquake GeoJSON fixture.
- Create CDC HAN fixture.
- Create FDA recall fixture.
- Create FSIS Recall API fixture.
- Create CPSC recall API fixture.
- Create NHTSA recall fixture.
- Create CISA advisory fixture.
- Create CISA KEV fixture.
- Create FAA NAS status fixture.
- Create Federal Register API fixture.
- Create BLS release fixture.
- Create AP/NPR/PBS RSS fixture.
- Parse fixtures only.
- Store normalized metadata.
- Update fixture source health.
- No live fetch.

Phase U3: NATIONAL event correlation

- Implement deterministic token/location/time/source-family matching.
- No LLM.
- Tests for convergence.
- Tests for duplicate suppression.
- Tests for source-family diversity.
- Tests for national vs regional vs local scope routing.

Phase U4: NATIONAL ranking

- Implement the scoring model.
- Explain ranking in JSON.
- Tests for official severity, source diversity, recency, public impact, low-public-value penalty,
  stale-source penalty, duplicate-family penalty, and out-of-scope penalty.

Phase U5: NATIONAL UI disabled and fixture-backed states

- Replace NATIONAL placeholders with honest disabled/not-configured/source-health states.
- Fixture-backed rows can be used in tests only.
- No live fetch.
- No fake headlines.

Phase U6: official API/RSS live fetch, opt-in only

- Start with one safe official source at a time.
- Suggested first candidates: NWS active alerts, USGS earthquake GeoJSON, CISA advisories or KEV if
  machine-readable endpoint is verified, FSIS Recall API, and FAA NAS status if endpoint behavior is
  verified.
- Must be disabled by default.
- Must run through an explicit ingest command or separate disabled timer, not page load.
- Must use timeouts, size caps, source intervals, conditional requests when available, and fail-soft
  behavior.

Phase U7: additional official sources

- FDA recall feed/API after endpoint verification.
- CPSC recalls API.
- NHTSA recalls API.
- FEMA/OpenFEMA disaster declarations.
- Federal Register API with filters.
- BLS/BEA/FRED/Treasury only after indicator allowlists are designed.

Phase U8: national news RSS

- Publisher feeds only.
- Store metadata only.
- No article bodies.
- No paywall bypass.
- Detect duplicate/syndicated stories.
- Keep disabled by default.

Phase U9: official dashboards and HTML research

- DHS/NTAS, FEMA, NIFC, FAA, and other official pages only through official feeds/APIs if found.
- Homepage extraction only after explicit policy review.
- No broad page scraping.
- If no official data endpoint is found, keep `source_health_probe_only` or `manual_review_only`.

Phase U10: social/community

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

- NATIONAL disabled by default.
- Source disabled by default.
- Invalid source class rejected.
- Invalid adapter rejected.
- Invalid verification status rejected.
- Social source rejected unless `allow_social_sources` is true.
- Homepage extraction rejected unless `allow_homepage_extractors` is true.
- Congress.gov API source marked `auth_required` unless key source configured.
- BEA/FRED keyed sources marked `auth_required` unless key source configured.
- Source without URL rejected unless adapter supports no URL.
- Secrets not allowed in `config.example.yml`.

Registry tests:

- Source keys unique.
- Source family valid.
- Source class valid.
- Verification status valid.
- Retention settings valid.
- Geography filters valid.
- Agency filters valid.
- Sector filters valid.
- Source priority bounded.
- Refresh intervals bounded.

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
- Timestamps normalize deterministically.
- Descriptions are bounded.

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
- Same event from multiple news outlets counts as news-family convergence but not endless duplicate
  inflation.
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
- Duplicate syndicated articles do not create fake independent confirmation.

API design tests for later:

- GET routes read SQLite only.
- GET routes do not fetch network.
- Disabled, not-configured, stale, failing, auth-required, policy-blocked, parser-failed, and
  manual-review-only states remain distinct.

UI tests for later:

- No fake headlines.
- Empty states clear.
- Evidence visible.
- Ranking reason visible.
- Source health visible.
- National/state/agency/sector label visible.
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
- No API-key source runs without key configuration.
- No source target curl/live verification in fixture tests.

## SECTION 18: Backlog update requirements

`BACKLOG.md` must include a section named `NATIONAL United States Recent Signal Layer`. Every
NATIONAL backlog item added for this design must say `Status: not implemented.` Future tasks should
be concrete enough for a later agent to implement without reading chat history.

The required backlog work areas are:

- NATIONAL source registry design implemented from this document.
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
- No stock trading advice.
- No investment advice.
- No medical advice.
- No legal advice.
- No political outrage feed.
- No scraping behind login.
- No bypassing Reddit, X, API, auth, rate-limit, paywall, or bot-control restrictions.
- No claiming social chatter is verified fact.
- No treating unofficial aggregators as official.
- No treating duplicate articles as independent confirmation.
- No burying LOCAL or SYSTEM urgent items under NATIONAL headlines.
- No importing GLOBAL content unless U.S. national relevance rules allow it.
- No automatic API key discovery or secret storage.
- No adding dependencies.
- No API keys or secrets in the repo.
- No scheduled NATIONAL ingest until a separate disabled-by-default timer/command is designed.

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
6. Confirmation that NATIONAL remains disabled by default.
7. Test commands run and exact results.
8. `git diff --check` result.
9. `git status --short`.
10. BACKLOG entries added.
11. Uncertainties and source targets needing later verification.

Do not commit, push, install packages, run sudo, fetch live external sites, or curl source targets
for this task.
