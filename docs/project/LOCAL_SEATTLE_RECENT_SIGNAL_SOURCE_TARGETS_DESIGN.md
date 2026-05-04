# LOCAL Seattle Recent Signal Source Targets Design

## SECTION 1: Purpose

The LOCAL scope is the Seattle recent-signal layer for console-1701. It should tell the user what is
happening locally with source provenance, observed time, source kind, ranking reason, and evidence.
The target is a short-retention, deterministic, local metadata dashboard that can answer "what is
going on near Seattle right now?" without turning the app into a crawler, archive, scanner clone,
or cloud service.

The LOCAL scope is not:

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

The LOCAL scope is:

- A local, short-retention metadata dashboard.
- A deterministic cross-source event detector.
- A source-health aware recent-signal system.
- A LOCAL tab in console-1701 that can surface official alerts, incidents, travel disruptions,
  outages, hazards, airport/port operations, local news, and compliant community signals.
- A way to rank items by independent source convergence, official severity, local impact,
  freshness, and user-configured source priority.

"All there is to know about Seattle" means all useful public, configured, lawful, recent signals
that the user chooses to enable. It does not mean unbounded crawling, private data collection,
login bypass, paywall bypass, recursive discovery, browser automation, social media archiving, or
storing large article bodies.

Normal daily runtime must not require LLM calls. LLMs can help during development to inspect
fixture structure, draft adapters, or write tests, but the app itself must use deterministic
parsing, matching, ranking, and evidence records.

## SECTION 2: Local scope boundaries

Default LOCAL geography:

- Seattle city proper.
- SEA Airport because it is regionally critical and operationally tied to Seattle life.
- Port of Seattle because port, airport, and maritime disruptions matter locally.
- King County Metro and Sound Transit only as they affect Seattle service.
- WSDOT and Washington State Ferries only as they affect Seattle corridors, ferries, bridges,
  passes, routes, or regional access.
- Weather and hazard feeds only for Seattle, King County, Puget Sound, and immediate surrounding
  hazard zones.
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
- Sources requiring login, payment, scraping around controls, or access tokens not explicitly
  configured by the user.

Future config escape hatch, disabled by default:

```yaml
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
```

## SECTION 3: Seed source target inventory

No live verification was performed for this design. The URLs below are seed targets only. Future
work must verify each source's current endpoint, access rules, terms, parser stability, rate-limit
expectations, robots controls where relevant, and operational suitability before implementation.

Risk vocabulary:

- `privacy_risk`: whether source metadata may expose private distress, exact addresses, or personal
  situations.
- `policy_risk`: whether source terms, auth, robots controls, platform policy, or paywalls need
  careful review.
- `parser_risk`: whether the likely parser is stable and bounded.
- `retention_sensitivity`: how aggressively retained metadata should expire.

| source_key | source_name | source_family | source_class | scope | raw_url | expected_access_kind | likely_adapter_type | likely_refresh_interval | initial_priority | official_status | privacy_risk | policy_risk | parser_risk | retention_sensitivity | verification_status | why_it_matters | future_phase |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| alertseattle_home | AlertSeattle homepage | alertseattle | official_alert | LOCAL | https://alert.seattle.gov/ | public official webpage | static_html_headline_candidate | 10 min | 100 | official | low | medium | medium | medium | candidate_needs_verification | Primary city emergency alert surface. | L6 |
| seattle_em_alert_signup | Seattle Emergency Management AlertSeattle page | alertseattle | official_alert | LOCAL | https://www.seattle.gov/emergency-management/prepare/alert-seattle | public official webpage | source_health_probe_only | 24 h | 70 | official | low | low | low | low | candidate_needs_verification | Human reference for official alert enrollment and source provenance. | L7 |
| alertseattle_feed | AlertSeattle RSS feed candidate | alertseattle | official_alert | LOCAL | https://alert.seattle.gov/feed/ | candidate RSS feed | rss_atom | 10 min | 100 | official | low | medium | low | medium | candidate_needs_verification | Best candidate for city emergency alert metadata if valid. | L6 |
| sfd_realtime_911_page | Seattle Fire Realtime 911 page | sfd | official_incident | LOCAL | https://web.seattle.gov/sfd/realtime911/ | public official webpage | static_html_headline_candidate | 5 min | 85 | official | high | medium | high | high | candidate_needs_verification | Official current fire incident page, but privacy rules must constrain display. | L7 |
| sfd_realtime_911_today_endpoint | Seattle Fire Realtime 911 today endpoint candidate | sfd | official_incident | LOCAL | https://web.seattle.gov/sfd/realtime911/getRecsForDatePub.asp?action=Today&incDate=&rad1=des | candidate official HTML endpoint | static_html_headline_candidate | 5 min | 85 | official | high | medium | high | high | candidate_needs_verification | Possible structured-ish current incident source if policy and parser review pass. | L7 |
| sfd_fire_911_dataset | Seattle Real-Time Fire 911 Calls dataset | sfd | official_open_data | LOCAL | https://data.seattle.gov/Public-Safety/Seattle-Real-Time-Fire-911-Calls/kzjm-xkqj | Socrata dataset page | socrata_json | 5 min | 90 | official | high | low | low | high | candidate_needs_verification | Strong official source for SFD public call metadata and event correlation. | L6 |
| sfd_fire_911_socrata_api | Seattle Real-Time Fire 911 Socrata API docs | sfd | official_open_data | LOCAL | https://dev.socrata.com/foundry/data.seattle.gov/kzjm-xkqj | Socrata API documentation | socrata_json | 5 min | 90 | official | high | low | low | high | candidate_needs_verification | Documents fields and API access for the SFD dataset. | L6 |
| sfdlive_unofficial | SFD Live unofficial aggregator | sfd_live | unofficial_aggregator | LOCAL | https://sfdlive.com/ | public unofficial webpage | source_health_probe_only | manual | 20 | unofficial | high | high | high | high | unofficial_secondary | Human comparison only; must not outrank official SFD data or be cloned. | L6 |
| spd_online_crime_maps | SPD Online Crime Maps page | spd | official_incident | LOCAL | https://www.seattle.gov/police/information-and-data/data/online-crime-maps | public official webpage | source_health_probe_only | 24 h | 55 | official | high | medium | medium | high | candidate_needs_verification | Source context for SPD mapping and public data limitations. | L7 |
| spd_arcgis_dashboard | SPD ArcGIS dashboard candidate | spd | official_incident | LOCAL | https://www.arcgis.com/apps/dashboards/3556b79ef2494b8c9bd7eeddaabea68f | public ArcGIS dashboard | arcgis_dashboard_research | manual | 55 | official_candidate | high | medium | high | high | candidate_needs_verification | May expose official SPD public call/map data through underlying services. | L7 |
| spd_call_data_dataset | SPD Call Data dataset | spd | official_open_data | LOCAL | https://data.seattle.gov/Public-Safety/Call-Data/33kz-ixgy | Socrata dataset page | socrata_json | 10 min | 75 | official | high | low | low | high | candidate_needs_verification | Official SPD call data candidate, requiring privacy review before display. | L7 |
| spd_call_data_socrata_api | SPD Call Data Socrata API docs | spd | official_open_data | LOCAL | https://dev.socrata.com/foundry/data.seattle.gov/33kz-ixgy | Socrata API documentation | socrata_json | 10 min | 75 | official | high | low | low | high | candidate_needs_verification | Documents fields and API access for the SPD call dataset. | L7 |
| spd_blotter_home | SPD Blotter homepage | spd | official_incident | LOCAL | https://spdblotter.seattle.gov/ | public official publisher page | wordpress_feed_candidate | 15 min | 80 | official | high | medium | medium | high | candidate_needs_verification | Official narrative posts and public safety updates. | L7 |
| spd_blotter_significant_incidents | SPD Significant Incident Reports | spd | official_incident | LOCAL | https://spdblotter.seattle.gov/significant-incident-reports/ | public official publisher page | wordpress_feed_candidate | 15 min | 85 | official | high | medium | medium | high | candidate_needs_verification | Significant incidents can elevate beyond routine call data. | L7 |
| spd_blotter_incident_category | SPD Blotter incident reports category | spd | official_incident | LOCAL | https://spdblotter.seattle.gov/category/incident-reports/ | public official category page | wordpress_feed_candidate | 15 min | 80 | official | high | medium | medium | high | candidate_needs_verification | Category-level incident report metadata. | L7 |
| spd_blotter_news_releases_category | SPD Blotter news releases category | spd | official_alert | LOCAL | https://spdblotter.seattle.gov/category/statements-and-news-releases/news-releases/ | public official category page | wordpress_feed_candidate | 30 min | 70 | official | medium | medium | medium | medium | candidate_needs_verification | Official SPD statements and public notices. | L7 |
| spd_blotter_feed | SPD Blotter RSS feed candidate | spd | official_incident | LOCAL | https://spdblotter.seattle.gov/feed/ | candidate RSS feed | rss_atom | 15 min | 85 | official | high | medium | low | high | candidate_needs_verification | Likely best metadata path for SPD official posts if valid. | L7 |
| seattle_open_data_home | Seattle Open Data portal | seattle_open_data | official_open_data | LOCAL | https://data.seattle.gov/ | public open data portal | source_health_probe_only | 24 h | 50 | official | medium | low | low | low | candidate_needs_verification | Parent portal for explicit configured datasets, not a harvest target. | L1 |
| seattle_open_data_getting_started | Seattle Open Data getting started | seattle_open_data | source_health_only | LOCAL | https://data.seattle.gov/stories/s/Getting-Started-on-the-Open-Data-Portal/feq8-x3ti/ | public documentation | manual_review_only | none | 10 | official | low | low | low | low | user_seeded | Documentation for future Socrata use and source verification. | L1 |
| socrata_dev_home | Socrata developer portal | socrata | source_health_only | LOCAL | https://dev.socrata.com/ | public documentation | manual_review_only | none | 10 | reference | low | low | low | low | user_seeded | Reference for Socrata adapter behavior. | L1 |
| socrata_endpoints_docs | Socrata endpoint docs | socrata | source_health_only | LOCAL | https://dev.socrata.com/docs/endpoints.html | public documentation | manual_review_only | none | 10 | reference | low | low | low | low | user_seeded | Reference for dataset endpoint conventions. | L1 |
| sdot_travelers_map | SDOT Travelers map | sdot | official_transport | LOCAL | https://web.seattle.gov/travelers/ | public official map webpage | arcgis_dashboard_research | 10 min | 80 | official | low | medium | high | medium | candidate_needs_verification | City traffic, camera, and road condition surface. | L7 |
| sdot_interactive_maps | SDOT interactive maps page | sdot | official_transport | LOCAL | https://www.seattle.gov/transportation/permits-and-services/interactive-maps | public official webpage | source_health_probe_only | 24 h | 55 | official | low | low | low | low | candidate_needs_verification | Human index of SDOT map products and official context. | L7 |
| sdot_blog_home | SDOT Blog homepage | sdot | official_transport | LOCAL | https://sdotblog.seattle.gov/ | public official publisher page | wordpress_feed_candidate | 30 min | 65 | official | low | medium | medium | medium | candidate_needs_verification | Official SDOT notices, construction, and major travel impacts. | L7 |
| sdot_blog_feed | SDOT Blog RSS feed candidate | sdot | official_transport | LOCAL | https://sdotblog.seattle.gov/feed/ | candidate RSS feed | rss_atom | 30 min | 70 | official | low | medium | low | medium | candidate_needs_verification | Metadata path for SDOT official posts if valid. | L7 |
| sdot_gis_datasets | SDOT GIS Datasets | sdot | official_open_data | LOCAL | https://data.seattle.gov/Transportation/SDOT-GIS-Datasets/jyjy-n3ap | Socrata dataset page | socrata_json | 24 h | 45 | official | low | low | medium | low | candidate_needs_verification | Index or dataset reference for SDOT GIS assets. | L7 |
| seattle_traffic_cameras_dataset | Traffic Cameras dataset | sdot | official_transport | LOCAL | https://data.seattle.gov/dataset/Traffic-Cameras/mvth-ptq3 | open data dataset page | arcgis_feature_service_candidate | 30 min | 55 | official | low | low | medium | low | candidate_needs_verification | Camera locations can support route/facility matching, not incident proof. | L7 |
| seattle_traffic_cameras_arcgis_api | Traffic Cameras ArcGIS API candidate | sdot | official_transport | LOCAL | https://data-seattlecitygis.opendata.arcgis.com/datasets/traffic-cameras/api | candidate ArcGIS API page | arcgis_feature_service_candidate | 30 min | 55 | official_candidate | low | low | medium | low | candidate_needs_verification | Possible stable feature service for traffic camera metadata. | L7 |
| wsdot_traffic_api | WSDOT traffic API page | wsdot | official_transport | LOCAL | https://wsdot.wa.gov/traffic/api/ | public official API documentation | official_api_json | 10 min | 85 | official | low | low | medium | medium | candidate_needs_verification | Official state traveler data for Seattle corridors and regional access. | L6 |
| wsdot_realtime_home | WSDOT real-time travel page | wsdot | official_transport | LOCAL | https://wsdot.com/travel/real-time/ | public official webpage | source_health_probe_only | 15 min | 60 | official | low | low | medium | medium | candidate_needs_verification | Human real-time travel reference. | L7 |
| wsdot_realtime_map | WSDOT real-time travel map | wsdot | official_transport | LOCAL | https://wsdot.com/travel/real-time/map/ | public official map webpage | source_health_probe_only | 15 min | 60 | official | low | low | high | medium | candidate_needs_verification | Map reference; avoid screen scraping. | L7 |
| wsdot_travel_home | WSDOT travel homepage | wsdot | official_transport | LOCAL | https://wsdot.wa.gov/travel | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | candidate_needs_verification | Parent travel source context. | L7 |
| wsf_schedule_bulletins | WSF schedule bulletins | wsdot_ferries | official_transport | LOCAL | https://wsdot.com/ferries/schedule/bulletin.aspx | public official webpage | static_html_headline_candidate | 10 min | 85 | official | low | low | medium | medium | candidate_needs_verification | Ferry cancellations and terminal disruptions affect Seattle travel. | L6 |
| wsf_home | Washington State Ferries travel page | wsdot_ferries | official_transport | LOCAL | https://wsdot.wa.gov/travel/washington-state-ferries | public official webpage | source_health_probe_only | 24 h | 55 | official | low | low | low | low | candidate_needs_verification | Official ferry service context. | L7 |
| wsdot_alert_signup | WSDOT travel alerts signup | wsdot | official_transport | LOCAL | https://wsdot.wa.gov/travel/sign-wsdot-travel-alerts | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | candidate_needs_verification | Human reference for official alert channels. | L7 |
| metro_service_advisories | King County Metro service advisories | metro | official_transport | LOCAL | https://kingcounty.gov/en/dept/metro/rider-tools/service-advisories | public official webpage | static_html_headline_candidate | 10 min | 80 | official | low | low | medium | medium | candidate_needs_verification | Transit disruptions affecting Seattle routes. | L6 |
| metro_service_advisories_rss | King County Metro service advisories RSS | metro | official_transport | LOCAL | https://kingcounty.gov/en/dept/metro/rider-tools/service-advisories/rss | candidate RSS feed | rss_atom | 10 min | 85 | official | low | low | low | medium | candidate_needs_verification | Best candidate for Metro alert metadata if valid. | L6 |
| metro_blog_home | King County Metro blog | metro | official_transport | LOCAL | https://kingcountymetro.blog/ | public official publisher page | wordpress_feed_candidate | 30 min | 55 | official | low | medium | medium | low | candidate_needs_verification | Official Metro service and operations posts. | L8 |
| metro_blog_feed | King County Metro blog feed | metro | official_transport | LOCAL | https://kingcountymetro.blog/feed/ | candidate RSS feed | rss_atom | 30 min | 60 | official | low | medium | low | low | candidate_needs_verification | Metadata path for Metro blog posts if valid. | L8 |
| sound_transit_service_alerts | Sound Transit service alerts | sound_transit | official_transport | LOCAL | https://www.soundtransit.org/ride-with-us/service-alerts | public official webpage | static_html_headline_candidate | 10 min | 80 | official | low | low | medium | medium | candidate_needs_verification | Link and regional rail/bus disruptions affecting Seattle. | L7 |
| sound_transit_otd_downloads | Sound Transit open transit data | sound_transit | official_transport | LOCAL | https://www.soundtransit.org/help-contacts/business-information/open-transit-data-otd/otd-downloads | official open data page | gtfs_realtime_alerts | 10 min | 75 | official | low | low | high | medium | candidate_needs_verification | Candidate GTFS realtime alert source, dependency review needed. | L7 |
| city_light_outages_home | Seattle City Light outages page | city_light | official_utility | LOCAL | https://www.seattle.gov/city-light/outages | public official webpage | source_health_probe_only | 10 min | 85 | official | low | low | medium | medium | candidate_needs_verification | Official outage landing page. | L7 |
| city_light_datacapable_map | Seattle City Light DataCapable outage map | city_light | official_utility | LOCAL | https://scl.datacapable.com/map/ | public outage map webpage | arcgis_dashboard_research | manual | 80 | official_candidate | low | medium | high | medium | candidate_needs_verification | Outage map candidate; underlying endpoint must be verified. | L7 |
| city_light_arcgis_experience | Seattle City Light ArcGIS outage experience | city_light | official_utility | LOCAL | https://experience.arcgis.com/experience/66636c38766c4fb4aca16976d79b0527/page/Energy-Page---Seattle-Light-Outage-Map | public ArcGIS experience | arcgis_dashboard_research | manual | 80 | official_candidate | low | medium | high | medium | candidate_needs_verification | Outage map candidate; no dashboard scraping. | L7 |
| city_light_outage_alerts | Seattle City Light outage alerts | city_light | official_utility | LOCAL | https://www.seattle.gov/city-light/outages/outage-alerts | public official webpage | source_health_probe_only | 24 h | 55 | official | low | low | low | low | candidate_needs_verification | Human reference for outage alert channels. | L7 |
| alertseattle_poweroutage | AlertSeattle power outage page | city_light | official_utility | LOCAL | https://alert.seattle.gov/poweroutage/ | public official alert webpage | static_html_headline_candidate | 10 min | 80 | official | low | medium | medium | medium | candidate_needs_verification | Official alert page for power outage incidents. | L7 |
| spu_home | Seattle Public Utilities homepage | seattle_utilities | official_utility | LOCAL | https://www.seattle.gov/utilities | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | candidate_needs_verification | Parent source for utility disruptions beyond power. | L7 |
| spu_data_resources | Seattle Utilities data resources | seattle_utilities | official_open_data | LOCAL | https://www.seattle.gov/utilities/construction-resources/records-vault/data-resources | public official webpage | manual_review_only | manual | 35 | official | low | low | medium | low | candidate_needs_verification | Candidate utility data reference after source review. | L7 |
| port_seattle_home | Port of Seattle homepage | port_sea | official_airport_port | LOCAL | https://www.portseattle.org/ | public official webpage | source_health_probe_only | 24 h | 50 | official | low | low | low | low | candidate_needs_verification | Parent source for port and SEA operations. | L7 |
| port_seattle_news | Port of Seattle news | port_sea | official_airport_port | LOCAL | https://www.portseattle.org/news | public official publisher page | static_html_headline_candidate | 30 min | 65 | official | low | low | medium | low | candidate_needs_verification | Official port news and operations context. | L7 |
| port_seattle_newsroom | Port of Seattle newsroom | port_sea | official_airport_port | LOCAL | https://www.portseattle.org/newsroom | public official publisher page | static_html_headline_candidate | 30 min | 65 | official | low | low | medium | low | candidate_needs_verification | Official press and operational notices. | L7 |
| sea_airport_home | SEA Airport homepage | port_sea | official_airport_port | LOCAL | https://www.portseattle.org/sea | public official webpage | source_health_probe_only | 15 min | 70 | official | low | low | medium | medium | candidate_needs_verification | Airport operating context and notices. | L7 |
| sea_flight_status | SEA flight status page | port_sea | official_airport_port | LOCAL | https://www.portseattle.org/sea/flight-status | public official webpage | airport_status_json_or_xml | 15 min | 75 | official | low | medium | high | low | candidate_needs_verification | Flight status context; normal flight boards should not dominate ranking. | L7 |
| sea_airport_traveler_updates_actions | SEA airport traveler updates action page | port_sea | official_airport_port | LOCAL | https://www.portseattle.org/actions/airport-traveler-updates | public official webpage | static_html_headline_candidate | 15 min | 80 | official | low | low | medium | medium | candidate_needs_verification | Official airport operational updates. | L7 |
| sea_traveler_updates_tips | SEA traveler updates and tips | port_sea | official_airport_port | LOCAL | https://www.portseattle.org/page/traveler-updates-and-tips | public official webpage | static_html_headline_candidate | 30 min | 65 | official | low | low | medium | low | candidate_needs_verification | Traveler disruption context and operational tips. | L7 |
| sea_checkpoint_wait_times | SEA checkpoint wait times | port_sea | official_airport_port | LOCAL | https://www.portseattle.org/page/live-estimated-checkpoint-wait-times | public official webpage | airport_status_json_or_xml | 10 min | 70 | official | low | medium | high | low | candidate_needs_verification | Airport operations pulse, but only major anomalies should elevate. | L7 |
| sea_this_week | This Week at SEA | port_sea | official_airport_port | LOCAL | https://www.portseattle.org/ThisWeekatSEA | public official webpage | static_html_headline_candidate | 24 h | 45 | official | low | low | medium | low | candidate_needs_verification | Planned airport events and construction context. | L8 |
| faa_fly_sea | FAA fly.faa.gov SEA status | faa | official_airport_port | LOCAL | https://www.fly.faa.gov/fly/flyfaa/flyfaaindex?ARPT=SEA&p=1 | public official webpage | airport_status_json_or_xml | 10 min | 90 | official | low | low | medium | medium | candidate_needs_verification | FAA operational status for SEA disruptions. | L6 |
| faa_nasstatus_home | FAA NAS Status homepage | faa | official_airport_port | LOCAL | https://nasstatus.faa.gov/ | public official webpage | source_health_probe_only | 15 min | 70 | official | low | low | medium | low | candidate_needs_verification | Parent FAA national airspace status source. | L7 |
| faa_nasstatus_api | FAA NAS airport status API candidate | faa | official_airport_port | LOCAL | https://nasstatus.faa.gov/api/airport-status-information | candidate official JSON API | official_api_json | 10 min | 90 | official | low | low | medium | medium | candidate_needs_verification | Candidate machine-readable FAA airport status source. | L6 |
| faa_airport_status_sea | FAA airport status SEA page | faa | official_airport_port | LOCAL | https://www.faa.gov/airport-status/SEA | public official webpage | airport_status_json_or_xml | 10 min | 90 | official | low | low | medium | medium | candidate_needs_verification | FAA SEA-specific operational status. | L6 |
| faa_asws_github | FAA ASWS GitHub reference | faa | source_health_only | LOCAL | https://github.com/Federal-Aviation-Administration/ASWS | public code/docs reference | manual_review_only | none | 10 | official_reference_candidate | low | medium | low | low | candidate_needs_verification | Research reference only; no GitHub API calls or automatic fetches. | L7 |
| nws_seattle_home | NWS Seattle office | nws | official_weather_hazard | LOCAL | https://www.weather.gov/sew/ | public official webpage | source_health_probe_only | 15 min | 75 | official | low | low | medium | medium | candidate_needs_verification | Official weather office context for Seattle. | L6 |
| nws_api_docs | NWS API documentation | nws | source_health_only | LOCAL | https://www.weather.gov/documentation/services-web-api | public official API docs | manual_review_only | none | 10 | official | low | low | low | low | user_seeded | Reference for NWS API implementation. | L2 |
| nws_alerts_docs | NWS alerts service docs | nws | source_health_only | LOCAL | https://www.weather.gov/documentation/services-web-alerts | public official API docs | manual_review_only | none | 10 | official | low | low | low | low | user_seeded | Reference for weather alert adapter. | L2 |
| nws_active_alerts_api | NWS active alerts API | nws | official_weather_hazard | LOCAL | https://api.weather.gov/alerts/active | documented official JSON API | official_api_json | 10 min | 95 | official | low | low | medium | medium | candidate_needs_verification | Strong official source for active hazard alerts, filtered by zone/area. | L6 |
| nws_alerts_home | NWS alerts page | nws | official_weather_hazard | LOCAL | https://www.weather.gov/alerts | public official webpage | source_health_probe_only | 30 min | 55 | official | low | low | low | low | candidate_needs_verification | Human reference for alert status and docs. | L6 |
| airnow_home | AirNow homepage | air_quality | official_air_quality | LOCAL | https://www.airnow.gov/ | public official webpage | source_health_probe_only | 30 min | 70 | official | low | low | medium | low | candidate_needs_verification | Official national AQI context. | L7 |
| airnow_api_docs | AirNow API docs | air_quality | official_air_quality | LOCAL | https://docs.airnowapi.org/ | official API documentation | official_api_json | 30 min | 75 | official | low | medium | medium | low | candidate_needs_verification | Candidate AQI API if explicitly configured and key rules allow. | L7 |
| pscleanair_air_quality | Puget Sound Clean Air air quality | air_quality | official_air_quality | LOCAL | https://pscleanair.gov/27/Air-Quality | public official webpage | source_health_probe_only | 30 min | 80 | official | low | low | medium | low | candidate_needs_verification | Local AQI and smoke authority for Puget Sound. | L7 |
| pscleanair_rss | Puget Sound Clean Air RSS candidate | air_quality | official_air_quality | LOCAL | https://pscleanair.gov/rss.aspx | candidate RSS feed | rss_atom | 30 min | 80 | official | low | low | low | low | candidate_needs_verification | Best metadata path for local air quality notices if valid. | L7 |
| pscleanair_sensormap | Puget Sound Clean Air sensor map | air_quality | official_air_quality | LOCAL | https://pscleanair.gov/sensormap | public official map webpage | source_health_probe_only | 30 min | 55 | official | low | low | high | low | candidate_needs_verification | Map reference only unless an official API is found. | L7 |
| seattle_wildfire_smoke_safety | Seattle wildfire smoke safety | air_quality | official_air_quality | LOCAL | https://www.seattle.gov/wildfire-smoke-safety | public official webpage | static_html_headline_candidate | 6 h | 65 | official | low | low | medium | low | candidate_needs_verification | City smoke guidance and public safety reference. | L7 |
| wasmoke_blog | Washington Smoke Blog | air_quality | official_air_quality | LOCAL | https://wasmoke.blogspot.com/ | public multi-agency blog | rss_atom | 30 min | 75 | official_candidate | low | medium | medium | medium | candidate_needs_verification | Regional smoke conditions can directly affect Seattle. | L7 |
| usgs_earthquake_home | USGS Earthquake Hazards | usgs | official_weather_hazard | LOCAL | https://earthquake.usgs.gov/ | public official webpage | source_health_probe_only | 30 min | 70 | official | low | low | low | low | candidate_needs_verification | Parent earthquake source. | L7 |
| usgs_earthquake_geojson | USGS earthquake GeoJSON feeds | usgs | official_weather_hazard | LOCAL | https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php | official GeoJSON feed docs | official_api_json | 5 min | 90 | official | low | low | low | medium | candidate_needs_verification | Earthquakes within radius or above magnitude should elevate. | L6 |
| seattle_schools_alerts | Seattle Public Schools alerts | seattle_schools | official_school_civic | LOCAL | https://www.seattleschools.org/alerts/ | public official webpage | static_html_headline_candidate | 15 min | 70 | official | medium | low | medium | medium | candidate_needs_verification | School closures and safety notices affect local life. | L7 |
| seattle_schools_inclement_weather_transport | SPS inclement weather transportation plan | seattle_schools | official_school_civic | LOCAL | https://www.seattleschools.org/departments/transportation/inclement-weather-transportation-plan/ | public official webpage | source_health_probe_only | 24 h | 40 | official | low | low | low | low | candidate_needs_verification | Static reference for snow/weather transportation policy. | L7 |
| seattle_schools_safety_faq | SPS safety and security FAQ | seattle_schools | official_school_civic | LOCAL | https://www.seattleschools.org/departments/safety-security/faq/ | public official webpage | source_health_probe_only | 24 h | 25 | official | low | low | low | low | candidate_needs_verification | Context only, not a recent alert source. | L7 |
| seattle_center_events | Seattle Center events | seattle_center | official_school_civic | LOCAL | https://www.seattlecenter.com/events | public official webpage | static_html_headline_candidate | 6 h | 45 | official | low | low | medium | low | candidate_needs_verification | Major events can explain local congestion and crowds. | L8 |
| seattle_center_calendar | Seattle Center event calendar | seattle_center | official_school_civic | LOCAL | https://www.seattlecenter.com/events/event-calendar | public official webpage | static_html_headline_candidate | 6 h | 45 | official | low | low | medium | low | candidate_needs_verification | Calendar context for public impact. | L8 |
| seattle_center_featured_events | Seattle Center featured events | seattle_center | official_school_civic | LOCAL | https://www.seattlecenter.com/events/featured-events | public official webpage | static_html_headline_candidate | 6 h | 45 | official | low | low | medium | low | candidate_needs_verification | Featured events can affect nearby movement. | L8 |
| parkways_home | Seattle Parks Parkways blog | seattle_parks | official_school_civic | LOCAL | https://parkways.seattle.gov/ | public official publisher page | wordpress_feed_candidate | 60 min | 45 | official | low | medium | medium | low | candidate_needs_verification | Parks closures and civic notices. | L8 |
| parkways_feed | Seattle Parks Parkways RSS feed | seattle_parks | official_school_civic | LOCAL | https://parkways.seattle.gov/feed/ | candidate RSS feed | rss_atom | 60 min | 50 | official | low | medium | low | low | candidate_needs_verification | Metadata path for parks notices if valid. | L8 |
| west_seattle_blog_home | West Seattle Blog homepage | west_seattle_blog | neighborhood_blog | LOCAL | https://westseattleblog.com/ | public publisher webpage | wordpress_feed_candidate | 15 min | 55 | independent_local | medium | medium | medium | medium | candidate_needs_verification | Hyperlocal West Seattle reporting often catches local disruptions early. | L9 |
| west_seattle_blog_feed | West Seattle Blog feed | west_seattle_blog | neighborhood_blog | LOCAL | https://westseattleblog.com/feed/ | candidate RSS feed | rss_atom | 15 min | 60 | independent_local | medium | medium | low | medium | candidate_needs_verification | Preferred metadata path for West Seattle headlines if valid. | L9 |
| west_seattle_blog_rss2 | West Seattle Blog rss-2 feed | west_seattle_blog | neighborhood_blog | LOCAL | https://westseattleblog.com/rss-2/ | candidate RSS feed | rss_atom | 15 min | 55 | independent_local | medium | medium | low | medium | candidate_needs_verification | Alternate feed candidate to verify. | L9 |
| capitol_hill_seattle_home | Capitol Hill Seattle homepage | capitol_hill_seattle | neighborhood_blog | LOCAL | https://www.capitolhillseattle.com/ | public publisher webpage | wordpress_feed_candidate | 15 min | 55 | independent_local | medium | medium | medium | medium | candidate_needs_verification | Hyperlocal Capitol Hill and central Seattle reporting. | L9 |
| capitol_hill_seattle_feed | Capitol Hill Seattle feed | capitol_hill_seattle | neighborhood_blog | LOCAL | https://www.capitolhillseattle.com/feed/ | candidate RSS feed | rss_atom | 15 min | 60 | independent_local | medium | medium | low | medium | candidate_needs_verification | Preferred metadata path for CHS if valid. | L9 |
| capitol_hill_seattle_about | Capitol Hill Seattle about page | capitol_hill_seattle | source_health_only | LOCAL | https://www.capitolhillseattle.com/about-chs/ | public publisher policy/about page | manual_review_only | none | 10 | independent_local | low | medium | low | low | candidate_needs_verification | Source identity and policy context for future review. | L9 |
| kuow_home | KUOW homepage | kuow | local_news | LOCAL | https://www.kuow.org/ | public publisher webpage | rss_atom | 30 min | 55 | local_media | low | medium | medium | low | candidate_needs_verification | Local public radio news and civic context. | L8 |
| kuow_seattle_now | KUOW Seattle Now podcast | kuow | local_news | LOCAL | https://www.kuow.org/podcasts/seattlenow | public publisher webpage/feed candidate | rss_atom | 60 min | 35 | local_media | low | medium | medium | low | candidate_needs_verification | Local context, probably less urgent than official alerts. | L8 |
| king5_rss | KING 5 RSS page | king5 | local_news | LOCAL | https://www.king5.com/rss | public publisher feed index | rss_atom | 15 min | 55 | local_media | medium | medium | medium | medium | candidate_needs_verification | Local TV headlines can corroborate major incidents. | L8 |
| kiro7_home | KIRO 7 homepage | kiro7 | local_news | LOCAL | https://www.kiro7.com/homepage | public publisher webpage | static_html_headline_candidate | 15 min | 45 | local_media | medium | medium | high | medium | candidate_needs_verification | Local TV source, prefer feed over homepage extraction. | L8 |
| kiro7_rss_snd | KIRO 7 RSS candidate | kiro7 | local_news | LOCAL | https://www.kiro7.com/rss-snd/ | candidate RSS feed | rss_atom | 15 min | 55 | local_media | medium | medium | medium | medium | candidate_needs_verification | Candidate metadata feed for local TV headlines. | L8 |
| komo_home | KOMO News homepage | komo | local_news | LOCAL | https://komonews.com/ | public publisher webpage | static_html_headline_candidate | 15 min | 45 | local_media | medium | medium | high | medium | candidate_needs_verification | Local TV news; avoid homepage extraction unless reviewed. | L8 |
| komo_local | KOMO local news page | komo | local_news | LOCAL | https://komonews.com/news/local | public publisher webpage | static_html_headline_candidate | 15 min | 50 | local_media | medium | medium | high | medium | candidate_needs_verification | Local headlines candidate if feed unavailable and policy allows. | L8 |
| fox13_home | FOX 13 Seattle homepage | fox13 | local_news | LOCAL | https://www.fox13seattle.com/ | public publisher webpage | static_html_headline_candidate | 15 min | 45 | local_media | medium | medium | high | medium | candidate_needs_verification | Local TV source; prefer publisher feed if found later. | L8 |
| cascadepbs_news | Cascade PBS news | cascadepbs | local_news | LOCAL | https://www.cascadepbs.org/news/ | public publisher webpage/feed candidate | rss_atom | 30 min | 45 | local_media | low | medium | medium | low | candidate_needs_verification | Local civic and regional journalism. | L8 |
| the_urbanist_home | The Urbanist | the_urbanist | local_news | LOCAL | https://www.theurbanist.org/ | public publisher webpage/feed candidate | wordpress_feed_candidate | 60 min | 35 | independent_local | low | medium | medium | low | candidate_needs_verification | Transportation, housing, and civic context, usually not urgent. | L8 |
| seattle_bike_blog_home | Seattle Bike Blog | seattle_bike_blog | neighborhood_blog | LOCAL | https://www.seattlebikeblog.com/ | public publisher webpage/feed candidate | wordpress_feed_candidate | 60 min | 35 | independent_local | low | medium | medium | low | candidate_needs_verification | Bike/transportation impacts and street safety context. | L9 |
| reddit_seattle | Reddit r/Seattle | reddit | social_candidate | LOCAL | https://www.reddit.com/r/Seattle/ | platform community page/API candidate | manual_review_only | disabled | 20 | platform | high | high | high | high | candidate_policy_sensitive | Community signal only through compliant configured access. | L10 |
| reddit_seattlewa | Reddit r/SeattleWA | reddit | social_candidate | LOCAL | https://www.reddit.com/r/SeattleWA/ | platform community page/API candidate | manual_review_only | disabled | 15 | platform | high | high | high | high | candidate_policy_sensitive | Community signal candidate, disabled by default. | L10 |
| reddit_askseattle | Reddit r/AskSeattle | reddit | social_candidate | LOCAL | https://www.reddit.com/r/AskSeattle/ | platform community page/API candidate | manual_review_only | disabled | 10 | platform | high | high | high | high | candidate_policy_sensitive | Lower-signal community question source, disabled by default. | L10 |
| x_seattledot | X SeattleDOT account | x_api | social_candidate | LOCAL | https://x.com/seattledot | platform account/API candidate | manual_review_only | disabled | 25 | platform_official_account | medium | high | high | high | candidate_policy_sensitive | Official agency social echo only if official API is configured. | L10 |
| x_seattlepd | X SeattlePD account | x_api | social_candidate | LOCAL | https://x.com/SeattlePD | platform account/API candidate | manual_review_only | disabled | 25 | platform_official_account | high | high | high | high | candidate_policy_sensitive | Official police social echo only if compliant API access exists. | L10 |
| x_alertseattle | X AlertSeattle account | x_api | social_candidate | LOCAL | https://x.com/AlertSeattle | platform account/API candidate | manual_review_only | disabled | 30 | platform_official_account | low | high | high | medium | candidate_policy_sensitive | Alert social echo only if compliant API access exists. | L10 |
| x_flysea | X flySEA account | x_api | social_candidate | LOCAL | https://x.com/flySEA | platform account/API candidate | manual_review_only | disabled | 25 | platform_official_account | low | high | high | medium | candidate_policy_sensitive | Airport operations social echo only if compliant API access exists. | L10 |
| x_kcmetroalerts | X KC Metro Alerts account | x_api | social_candidate | LOCAL | https://x.com/kcmetroalerts | platform account/API candidate | manual_review_only | disabled | 25 | platform_official_account | low | high | high | medium | candidate_policy_sensitive | Metro social echo only if compliant API access exists. | L10 |
| x_wsferries | X WSFerries account | x_api | social_candidate | LOCAL | https://x.com/wsferries | platform account/API candidate | manual_review_only | disabled | 25 | platform_official_account | low | high | high | medium | candidate_policy_sensitive | Ferry social echo only if compliant API access exists. | L10 |
| bluesky_seattle_search | Bluesky Seattle search | bluesky | social_candidate | LOCAL | https://bsky.app/search?q=Seattle | platform search page/API candidate | manual_review_only | disabled | 15 | platform | high | high | high | high | candidate_policy_sensitive | Possible AT Protocol exploration later; no HTML scraping. | L10 |
| rfc9309_robots | RFC 9309 Robots Exclusion Protocol | policy_reference | source_health_only | LOCAL | https://www.rfc-editor.org/rfc/rfc9309.html | public standards reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | Policy reference for future robots handling. | L1 |
| rss_specification | RSS specification | policy_reference | source_health_only | LOCAL | https://www.rssboard.org/rss-specification | public standards reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | Reference for feed parser expectations. | L2 |
| sitemap_protocol | Sitemaps protocol | policy_reference | source_health_only | LOCAL | https://www.sitemaps.org/protocol.html | public standards reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | Reference only; no sitemap crawling in early LOCAL phases. | L9 |
| schema_newsarticle | Schema.org NewsArticle | policy_reference | source_health_only | LOCAL | https://schema.org/NewsArticle | public schema reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | Metadata reference for possible publisher markup review. | L9 |
| reddit_developer_terms | Reddit Developer Terms | policy_reference | source_health_only | LOCAL | https://redditinc.com/policies/developer-terms | public platform policy | manual_review_only | none | 0 | reference | low | high | low | low | candidate_policy_sensitive | Must be reviewed before any Reddit source is enabled. | L10 |
| reddit_data_api_terms | Reddit Data API Terms | policy_reference | source_health_only | LOCAL | https://redditinc.com/policies/data-api-terms | public platform policy | manual_review_only | none | 0 | reference | low | high | low | low | candidate_policy_sensitive | Must be reviewed before any Reddit API use. | L10 |
| x_api_docs | X API introduction | policy_reference | source_health_only | LOCAL | https://docs.x.com/x-api/introduction | public platform API docs | manual_review_only | none | 0 | reference | low | high | low | low | candidate_policy_sensitive | Must be reviewed before any X source is enabled. | L10 |
| bluesky_atproto_docs | Bluesky AT Protocol XRPC API docs | policy_reference | source_health_only | LOCAL | https://docs.bsky.app/docs/api/at-protocol-xrpc-api | public platform API docs | manual_review_only | none | 0 | reference | low | medium | low | low | candidate_policy_sensitive | Reference for possible compliant Bluesky adapter. | L10 |

## SECTION 4: Source admission tiers

Tier 0 - local fixtures only:

- No network.
- Used for tests.
- Best initial implementation target.
- Fixture adapters must produce the same normalized shape as later live adapters.

Tier 1 - official APIs, official open data, and official RSS/Atom:

- Best first live candidates.
- Examples: SFD Socrata, SPD Socrata after privacy review, AlertSeattle RSS if valid, NWS API,
  Metro RSS if valid, WSDOT API, FAA/NAS API if valid.
- Must be disabled by default and opt-in.

Tier 2 - official HTML pages with stable public data but no obvious feed/API:

- Candidate only after source-policy review.
- Prefer source-health checks and manual review before parser implementation.
- Must use per-source selectors if extraction is ever allowed.
- No recursive crawling and no article-body fetch.

Tier 3 - local news RSS or publisher-provided feeds:

- Store headline metadata only.
- No article-body archive.
- No paywall bypass.
- Repeated syndicated headlines should not create fake source diversity.

Tier 4 - neighborhood blogs:

- Valuable because they often beat large outlets for hyperlocal events.
- Prefer RSS/Atom.
- Store headline metadata only.
- Respect robots, terms, and source policy.

Tier 5 - social/community signals:

- Policy-sensitive.
- Disabled by default.
- Reddit only through compliant official API or permitted feed access.
- X/Twitter only through official API access if explicitly configured.
- Bluesky may be explored through official AT Protocol later.
- No HTML scraping to bypass platform restrictions.
- No long-term social archive.

Tier 6 - unofficial aggregators:

- Example: SFD Live.
- Useful as a human comparison or secondary source-health reference.
- Do not treat as primary authority over official sources.
- Do not clone their work or scrape aggressively.
- If used later, source-health-only or manual-review-only unless policy review supports more.

## SECTION 5: LOCAL event model

The system should not only store "news items." It should infer when multiple recent items refer to
the same local event. The existing global architecture proposes `news_clusters`; LOCAL can either
extend `news_clusters` or add a dedicated `local_events` table. A dedicated `local_events` table is
clearer because LOCAL event ranking needs geography, privacy, official severity, transport impact,
utility impact, airport/port impact, and public-safety redaction decisions that are more specific
than generic headline clustering.

Candidate future `local_events` table:

| Column | Purpose |
| --- | --- |
| `local_event_id` | Internal integer primary key. |
| `scope` | Always `LOCAL` initially, but stored for consistency. |
| `event_key` | Deterministic key from source families, type, time bucket, geography tokens, and normalized title/location tokens. |
| `event_type` | One of the controlled LOCAL event types. |
| `title` | Representative bounded title, not an LLM summary. |
| `representative_item_id` | Best item to display as the primary evidence row. |
| `severity` | Deterministic severity bucket such as `info`, `notice`, `elevated`, `major`, `critical`. |
| `public_impact_score` | Score component for direct local impact. |
| `source_diversity_score` | Independent source-family convergence component. |
| `official_confirmation_score` | Official source strength component. |
| `social_echo_score` | Optional compliant social echo component. |
| `news_echo_score` | Local news/blog convergence component. |
| `transport_impact_score` | Movement, route, bridge, transit, ferry, or road component. |
| `utility_impact_score` | Power, water, utility disruption component. |
| `hazard_score` | Weather, smoke, earthquake, flood, or hazard component. |
| `airport_port_score` | SEA Airport or Port of Seattle operational component. |
| `first_seen_at` | First local observation. |
| `last_seen_at` | Most recent matching observation. |
| `last_elevated_at` | Most recent time the event crossed display/ranking threshold. |
| `expires_at` | Purge cutoff. |
| `geography_json` | Bounded structured geography such as neighborhood, route, facility, weather zone, or redacted location. |
| `neighborhoods_json` | Normalized neighborhood labels. |
| `source_ids_json` | Source ids represented in the event. |
| `item_ids_json` | Item ids represented in the event. |
| `evidence_json` | Source, parser, matching, ranking, policy, and redaction evidence. |
| `ranking_explanation_json` | Score factors and human-readable deterministic reason strings. |
| `status` | `active`, `monitoring`, `expired`, `hidden`, `policy_blocked`, or `resolved`. |

Required event types:

- `fire`
- `rescue`
- `medical_public_impact`
- `police_public_safety`
- `traffic_collision`
- `road_closure`
- `bridge_disruption`
- `transit_disruption`
- `ferry_disruption`
- `airport_disruption`
- `port_disruption`
- `power_outage`
- `utility_disruption`
- `weather_alert`
- `smoke_air_quality`
- `earthquake`
- `flood`
- `school_closure`
- `civic_alert`
- `major_event`
- `news_story`
- `community_signal`
- `source_health_problem`

Raw low-acuity calls should not automatically become elevated LOCAL events. Routine medical aid,
ordinary single-source minor police calls, vague social reports, and private residential distress
should remain hidden or aggregated into background pulse counts unless official severity,
public-impact rules, or independent cross-source convergence justify elevation.

## SECTION 6: Cross-source convergence ranking

The ranking model should implement the user's intuition deterministically: if the same event appears
in official sources, local news, neighborhood blogs, transit/traffic feeds, and compliant
community/social signals within a short window, it is probably important or interesting.

This is not an LLM summarizer. The system should compute features, scores, and explanations from
stored metadata only.

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

Independent source families count more than repeated mentions from the same family. Candidate
families:

- `sfd`
- `spd`
- `alertseattle`
- `sdot`
- `wsdot`
- `metro`
- `sound_transit`
- `city_light`
- `port_sea`
- `nws`
- `usgs`
- `air_quality`
- `local_tv`
- `local_radio`
- `local_newspaper`
- `neighborhood_blog`
- `reddit`
- `bluesky`
- `x_api`
- `source_health`

3. Temporal proximity

Items closer in time are more likely to refer to the same event. Initial matching windows:

- SFD/SPD/traffic: 0 to 6 hours.
- Breaking news: 0 to 24 hours.
- Weather/hazard/outage: active alert duration or 0 to 48 hours.
- Airport/port: 0 to 24 hours.
- Major civic story: 0 to 72 hours.

4. Geographic proximity

Match by:

- Exact location, if safe and appropriate.
- Street intersection.
- Neighborhood.
- Facility, such as SEA Airport, Port of Seattle, West Seattle Bridge, I-5, SR 99, or ferry terminal.
- Route ID.
- Utility outage area.
- Weather zone.
- Citywide or countywide flag.

5. Public impact

Boost:

- Port.
- Airport.
- Bridges.
- Ferries.
- I-5.
- SR 99.
- West Seattle Bridge.
- Hospitals.
- Schools.
- Downtown.
- Major transit stations.
- Major power outages.
- Major public events.
- Official emergency alerts.
- Citywide impacts.

6. Recency

Recent items matter more, but older active hazards can stay elevated while still active. The ranking
explanation must show whether an item is fresh, active-but-older, stale, or retained only for source
health/debug evidence.

7. User-configured priority

Future config should allow boosts for:

- Seattle proper.
- Nearby neighborhood.
- SEA Airport.
- Port.
- West Seattle.
- Capitol Hill.
- Traffic.
- Power.
- Weather.
- Fire.
- Transit.
- Major civic alerts.

8. Privacy and low-public-value penalty

De-emphasize:

- Ordinary medical aid calls.
- Overdose calls.
- Low-acuity response.
- Private residential calls with no broader public impact.
- Single-source minor police calls.
- Noisy social-only posts.
- Vague reports with no official confirmation.

Sample scoring formula:

```text
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
```

Possible normalization:

```text
recency_score = 0..20
official_severity_score = 0..35
source_diversity_score = min(30, independent_family_count * 6 + official_family_count * 3)
public_impact_score = 0..25
source_priority_score = configured_priority / 10
active_alert_score = 0 or 15
cluster_size_score = min(10, unique_item_count)
privacy_penalty = 0..40
duplicate_family_penalty = max(0, duplicate_mentions_same_family - 1) * 2
stale_source_penalty = 0..20
low_confidence_penalty = 0..25
```

The exact constants can change in implementation, but the score must stay explainable in JSON and
visible in evidence. A display row should be able to say:

```json
{
  "reason": "Elevated by official SFD severity, SDOT route impact, Port facility match, and two independent local-news families within 4 hours.",
  "features": {
    "official_severity_score": 26,
    "source_diversity_score": 18,
    "public_impact_score": 20,
    "privacy_penalty": 0
  }
}
```

"Frequency of appearance" means independent cross-source convergence, not raw duplicate counts.

Bad ranking:

- 20 syndicated copies of the same article dominate.

Good ranking:

- SFD 10-unit incident at Port of Seattle.
- SDOT or WSDOT nearby road impact.
- SEA or Port notice.
- West Seattle Blog or local TV report.
- Reddit/Bluesky chatter, only if compliant.
- All within a short time window.

## SECTION 7: Public safety privacy posture

The source data may be public, but the dashboard should not amplify private distress by default.

Rules:

- Store source-provided public metadata only.
- Do not store full narratives from police/fire articles beyond bounded descriptions.
- Do not archive social posts long term.
- Do not surface exact addresses for low-acuity medical or private residential aid calls unless an
  official source clearly frames it as a public-impact incident.
- Prefer neighborhood or intersection-level display for sensitive calls.
- Preserve source links in evidence so the user can click official sources.
- For major incidents, show the public operational facts: incident type, source, unit count if
  available, neighborhood, public impact, observed time, and source link.
- For SPD Significant Incident Reports, evidence should note that early incident reports can differ
  from final reports and should be treated as preliminary.
- Do not turn LOCAL into a fear dashboard or crime ticker.
- The UI should group low-acuity public safety data into "background pulse" counts unless elevated
  by severity or cross-source convergence.

Privacy redaction evidence should be explicit:

```json
{
  "exact_location_suppressed": true,
  "suppression_reason": "low_acuity_medical_or_private_residential_call",
  "display_geography": "neighborhood",
  "elevated": false
}
```

## SECTION 8: LOCAL source freshness and retention

Default candidate retention:

- Raw fetch diagnostics: 7 days or less.
- Raw payload debug: disabled by default. If ever enabled, 6 hours max by default.
- Official incident metadata: 3 to 7 days.
- Active alerts: until expiration plus 24 hours.
- News headline metadata: 7 days.
- Local event clusters: 7 to 14 days.
- Source health: 30 days.
- Ranking explanations: same as event/item retention.
- Social metadata, if ever enabled: 24 to 72 hours unless source terms require shorter or prohibit
  storage.

Every ingest run in later phases must purge expired data. This must be deterministic and testable.

Hard retention boundaries:

- No article body archive.
- No permanent local news archive.
- No permanent social archive.
- No large raw payload storage by default.
- No hidden long-term incident archive.

## SECTION 9: Adapter design for LOCAL

Do not implement these adapters in this design phase.

### `socrata_json`

- Seattle Open Data Fire 911.
- SPD Call Data.
- Other future `data.seattle.gov` datasets.
- Must support app token later but must run without secrets for public low-volume usage if permitted.
- Must support SoQL fields, ordering, limits, and updated-since queries.
- Must cap rows per run.
- Must preserve dataset ID and row ID.
- Must record dataset URL, API URL, selected fields, limit, order, and source health.

### `rss_atom`

- AlertSeattle feed if verified.
- SPD Blotter feed if verified.
- SDOT Blog feed if verified.
- King County Metro RSS.
- Local news/blog feeds.
- Must parse title, URL, published timestamp, description, and categories.
- Must bound description length.
- Must not fetch article bodies.
- Must fail soft on malformed feeds.

### `official_api_json`

- NWS alerts.
- FAA/NAS airport status, if verified.
- Air quality APIs if configured.
- USGS GeoJSON.
- WSDOT Traveler Information API.
- Must support ETag/Last-Modified if available.
- Must use timeouts and response size caps.
- Must preserve query parameters in evidence, especially area/zone/radius filters.

### `gtfs_realtime_alerts`

- Sound Transit service alerts.
- Possibly transit feeds later.
- Must be optional because protobuf support may need dependency review.
- If dependency is needed, backlog it instead of adding it.
- Initial phase can use local binary/text fixtures only if parser dependency is not approved.

### `arcgis_dashboard_research`

- SPD dashboard.
- City Light outage ArcGIS/Experience pages.
- Traffic cameras / ArcGIS feature services.
- Must not screen scrape dashboard HTML.
- Later work should identify underlying feature services or official APIs.
- If no official data endpoint is found, mark `manual_review_only` or `source_health_probe_only`.

### `static_html_headline_candidate`

- Only for official pages or local news pages with no RSS/API.
- Disabled unless homepage extractor support is explicitly allowed.
- Must use per-source selectors.
- No recursive crawling.
- No article-body fetch.
- Robots/policy review required.
- Store only bounded metadata.

### `wordpress_feed_candidate`

- WordPress-style `/feed/` endpoints.
- Must be verified before implementation.
- Treat as RSS/Atom if valid.
- Store headline metadata only.

### `source_health_probe_only`

- For pages useful as human status references but not suitable for ingestion.
- Examples: maps, dashboards, unofficial aggregators.
- Probe only when explicitly configured and enabled in a future phase.
- Probe result should be source health, not displayed content.

### `manual_review_only`

- For policy-sensitive or parser-risky targets.
- Does not fetch or parse in normal operation.
- Provides a registry state and evidence that a human review is required.

## SECTION 10: Candidate source registry example

This is a future config sketch only. Do not edit `config.example.yml` in this phase. The example is
disabled by default.

```yaml
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
```

## SECTION 11: LOCAL UI architecture

Do not implement UI changes in this phase. The eventual LOCAL page should use the same dense
console style and should not show fake headlines or demo content.

Bay 1 - Attention now:

- Highest-ranking LOCAL events.
- Must show why each item is ranked.
- Must show source-family badges.
- Must show official vs news vs community convergence.
- Must show observed time and last seen.
- Must avoid dumping raw low-acuity incidents.

Bay 2 - Official operations:

- AlertSeattle, SFD, SPD, SDOT, WSDOT, City Light, Port/SEA, NWS.
- Show active official alerts first.
- Show major public-safety incidents only when elevated.
- Show source freshness.

Bay 3 - Movement and utilities:

- Traffic, bridges, transit, ferries, airport, port, power, weather/air.
- Useful for "will this affect getting around or staying functional?"

Bay 4 - Local press and neighborhood pulse:

- West Seattle Blog, Capitol Hill Seattle, KUOW, KING5, KIRO, KOMO, FOX 13, Cascade PBS,
  The Urbanist, Seattle Bike Blog, and future configured sources.
- Social/community signals only if configured and compliant.
- No fake headlines.
- If disabled, show "LOCAL news sources not configured."

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

## SECTION 12: Evidence model for LOCAL

Every item/event must trace back to source evidence.

For a LOCAL event, evidence should include:

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
- Privacy redaction decision.
- Retention expiration.
- Matching tokens.
- Geographic match basis.
- Event type.
- Event confidence.
- Policy notes.

For public safety events, evidence must also include:

- Whether exact location was suppressed.
- Why it was elevated.
- Whether it was official-only, news-only, social-only, or cross-source.
- Whether the source describes the data as preliminary, delayed, or otherwise limited.

Candidate evidence shape:

```json
{
  "event_type": "fire",
  "event_confidence": "high",
  "source_families": ["sfd", "sdot", "neighborhood_blog"],
  "source_classes": ["official_incident", "official_transport", "neighborhood_blog"],
  "official_confirmation_score": 22,
  "source_diversity_score": 18,
  "geographic_match_basis": ["facility", "street_intersection", "neighborhood"],
  "matching_tokens": ["west seattle bridge", "fire", "lane blocked"],
  "privacy": {
    "exact_location_suppressed": false,
    "redaction_reason": "public facility and public traffic impact"
  },
  "retention": {
    "expires_at": "2026-05-10T12:00:00-07:00"
  }
}
```

## SECTION 13: Source health for LOCAL

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

Source health must be visible in SYSTEM later and summarized in LOCAL Bay 4 or a footer strip.

Each source health row should have:

- `source_id`
- `state`
- `last_attempt_at`
- `last_success_at`
- `last_failure_at`
- `next_eligible_fetch_at`
- `consecutive_failures`
- `last_http_status`
- `item_count_last_success`
- `stale_after_minutes`
- `message`
- `evidence_json`

Source health evidence should include policy state, parser name, adapter type, configured interval,
source URL, last response size if available, conditional request metadata if used, and whether the
source is intentionally disabled.

## SECTION 14: First implementation sequence for LOCAL

Phase L0 - this design:

- Create design doc.
- Update BACKLOG.
- No runtime behavior change.

Phase L1 - source registry scaffolding:

- Add disabled source config.
- Add source registry schema or tables if not already done by global architecture.
- Add tests proving LOCAL disabled by default.
- No network.

Phase L2 - local fixtures only:

- Create fixture files for SFD Socrata JSON, AlertSeattle RSS, Metro RSS, NWS alert JSON, WSDOT
  alert JSON, local blog RSS, City Light outage fixture, and FAA airport status fixture.
- Parse fixtures only.
- Store normalized metadata.
- No live fetch.

Phase L3 - LOCAL event correlation:

- Deterministic token/location/time matching.
- No LLM.
- Tests for convergence.
- Tests for duplicate suppression.
- Tests for source-family diversity.

Phase L4 - LOCAL ranking:

- Implement scoring model.
- Explain ranking in JSON.
- Tests for official severity, source diversity, recency, public impact, privacy penalty.

Phase L5 - LOCAL UI disabled and fixture-backed states:

- Replace LOCAL placeholders with honest states.
- Fixture-backed in tests only.
- No live fetch.
- No fake headlines.

Phase L6 - official API/RSS live fetch, opt-in only:

- Start with one safe official source.
- Suggested first candidates: Seattle SFD Fire 911 Socrata, NWS alerts, King County Metro RSS,
  WSDOT API.
- Must be disabled by default.
- Must use explicit command.
- No page-load fetch.

Phase L7 - additional official sources:

- City Light outage source only after endpoint verification.
- SEA/FAA status after endpoint verification.
- SPD Call Data after privacy posture is tested.
- Sound Transit GTFS alerts after dependency review.

Phase L8 - local news RSS:

- Publisher feeds only.
- Store metadata only.
- No article bodies.
- No paywall bypass.

Phase L9 - neighborhood blogs:

- RSS first.
- Homepage extraction only if explicitly allowed and reviewed.

Phase L10 - social/community:

- Bluesky AT Protocol candidate.
- Reddit official API candidate.
- X official API only if explicitly configured.
- No HTML scraping.
- Short retention.
- Disabled by default.

## SECTION 15: Testing strategy

Config tests:

- LOCAL disabled by default.
- Source disabled by default.
- Invalid source class rejected.
- Invalid adapter rejected.
- Social source rejected unless `allow_social_sources` is true.
- Homepage extraction rejected unless `allow_homepage_extractors` is true.
- Source without URL rejected unless adapter supports no URL.
- Secrets not allowed in `config.example.yml`.

Registry tests:

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
- Same event from multiple news outlets counts as news family convergence but not endless duplicate
  inflation.
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

## SECTION 16: Backlog update requirements

`BACKLOG.md` must include a section named `LOCAL Seattle Recent Signal Layer` with concrete future
implementation tasks flowing from this design. Each item should be marked `Status: not implemented`
until completed. Required backlog themes:

- LOCAL source registry design implemented from this document.
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

## SECTION 17: Non-goals

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

## SECTION 18: Final response requirements

Before final response for the design task, run:

```bash
pwd
git status --short
git diff --name-only
git diff --check
.venv/bin/python -m pytest -q
```

The final response must include:

- Files changed.
- Confirmation that no application code was changed, unless it was.
- Confirmation that no external network fetches were added.
- Confirmation that no dependencies were added.
- Confirmation that no collectors were implemented.
- Confirmation that LOCAL remains disabled by default.
- Test commands run and exact results.
- `git diff --check` result.
- `git status --short`.
- BACKLOG entries added.
- Uncertainties and source targets needing later verification.

Do not commit. Do not push. Do not install packages. Do not run sudo. Do not fetch live external
sites. Do not run curl against source targets for this task.
