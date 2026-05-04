# REGIONAL Pacific Northwest Recent Signal Source Targets Design

## SECTION 1: Purpose

The REGIONAL scope is the Washington, Puget Sound, Pacific Northwest, and nearby Cascadia
recent-signal layer for console-1701. It should tell the user what is happening regionally with
source provenance, observed time, source kind, ranking reason, geographic basis, public-impact
basis, source health, and evidence.

The target is a short-retention, deterministic, local metadata dashboard that can answer "what is
happening around Washington and the PNW that may matter to me?" without turning console-1701 into a
crawler, archive, social monitor, cloud service, or general news product.

The REGIONAL scope is not:

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

The REGIONAL scope is:

- A local, short-retention metadata dashboard.
- A deterministic cross-source event detector for regional public-impact signals.
- A source-health aware recent-signal system.
- A REGIONAL tab in console-1701 that can surface official alerts, hazards, transportation
  disruption, wildfire, smoke, weather, seismic activity, ferry and pass problems, public-health
  alerts, major regional civic news, local journalism, and compliant community echoes.
- A way to rank items by independent source convergence, official severity, geographic relevance,
  public impact, freshness, and user-configured source priority.

"Regional" means useful public, configured, lawful, recent signals that the user chooses to enable.
It does not mean unbounded crawling, private data collection, paywall bypass, login bypass,
platform-policy bypass, browser automation, social-media archiving, or storing large article bodies.

Normal daily runtime must not require LLM calls. LLMs can help during development to inspect fixture
structure, draft adapters, or write tests, but the app itself must use deterministic parsing,
matching, ranking, and evidence records.

## SECTION 2: Regional scope boundaries

Default REGIONAL geography:

- Washington state.
- Puget Sound outside Seattle proper.
- King, Snohomish, Pierce, Kitsap, Thurston, Skagit, Whatcom, Island, Mason, Lewis, Kittitas,
  Yakima, Chelan, Clallam, Jefferson, and San Juan counties when events have regional public impact.
- Major Washington corridors: I-5, I-90, SR 99, SR 520, SR 167, SR 18, US 2, US 101, US 97, SR 20,
  ferry routes, mountain passes, and border crossings.
- The Cascades and Olympic Peninsula for weather, wildfire, smoke, seismic, landslide, avalanche,
  flood, pass, and recreation-access impacts.
- Oregon and British Columbia only when the event plausibly affects Washington, Puget Sound,
  regional transportation, smoke, wildfire, weather systems, earthquakes, ports, ferries, airports,
  or cross-border travel.
- Pacific Northwest and Cascadia only for hazards, infrastructure, and news with plausible regional
  relevance.

Out of REGIONAL by default:

- Generic Seattle neighborhood items. Those belong in LOCAL unless they create wider impact.
- Generic national politics unless it directly affects Washington or the PNW.
- Generic global stories.
- Routine county press releases with no broader public impact.
- Single-source social chatter.
- Crime blotter noise.
- Full police scanner streams.
- Private medical or residential distress.
- Sources requiring login, payment, scraping around controls, or tokens not explicitly configured by
  the user.

Future config escape hatch, disabled by default:

```yaml
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
```

## SECTION 3: Relationship to LOCAL and OVERVIEW

REGIONAL should complement LOCAL and OVERVIEW rather than duplicate them.

Rules:

- REGIONAL should not duplicate LOCAL Seattle unless the Seattle item has broader regional impact.
- LOCAL should own Seattle fire, local roads, local utility outages, neighborhood blogs, and
  immediate city services.
- REGIONAL should own statewide and PNW hazards, highways, ferries, mountain passes, wildfires,
  smoke, floods, air quality, earthquakes, public-health alerts, and regional travel disruption.
- OVERVIEW should select the highest-priority items from LOCAL and REGIONAL without burying urgent
  local/system issues under broad regional headlines.
- If a regional item directly affects Seattle or the user's configured local interests, it can be
  tagged both `REGIONAL` and `LOCAL_IMPACT`, but the canonical scope remains `REGIONAL`.
- If a local Seattle item becomes regionally significant, such as port disruption, airport
  disruption, major I-5 closure, bridge failure, regional protest/event, or widespread outage, it
  can be promoted to REGIONAL with evidence.

Examples:

- SFD 1-unit medical aid in Seattle: LOCAL background or ignored.
- Major Port of Seattle fire affecting regional freight: LOCAL and REGIONAL.
- WSDOT closes Snoqualmie Pass: REGIONAL.
- Smoke plume from Cascades wildfire degrading Puget Sound AQI: REGIONAL.
- AlertSeattle city warming center update: LOCAL.
- WA EMD tsunami warning affecting the coast and Puget Sound: REGIONAL and OVERVIEW.
- King County flood warning affecting major rivers: REGIONAL.
- Seattle Times statewide election story: REGIONAL only if immediate public impact is high,
  otherwise lower-priority news.

## SECTION 4: Seed source target inventory

No live source verification was performed for this design. The URLs below are seed targets only.
Future work must verify each source's endpoint ownership, current access method, terms, parser
stability, robots/policy notes where applicable, rate limits, auth requirements, source-health
behavior, and operational suitability before implementation.

Risk vocabulary:

- `privacy_risk`: whether source metadata may expose private distress, exact addresses, or personal
  situations.
- `policy_risk`: whether source terms, auth, robots controls, platform policy, paywalls, or API
  restrictions need careful review.
- `parser_risk`: whether the likely parser is stable and bounded.
- `retention_sensitivity`: how aggressively retained metadata should expire.

| source_key | source_name | source_family | source_class | scope | raw_url | expected_access_kind | likely_adapter_type | likely_refresh_interval | initial_priority | official_status | privacy_risk | policy_risk | parser_risk | retention_sensitivity | verification_status | why_it_matters | future_phase |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wa_emd_alerts | WA Emergency Management alerts | wa_emd | official_alert | REGIONAL | https://mil.wa.gov/alerts | public official webpage | static_html_headline_candidate | 10 min | 100 | official | low | low | medium | medium | candidate_needs_verification | Statewide emergency alerts and declarations can affect all REGIONAL ranking. | R6 |
| wa_emd_division | WA Emergency Management Division | wa_emd | official_emergency | REGIONAL | https://mil.wa.gov/emergency-management-division | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | candidate_needs_verification | Human reference for WA EMD authority and source provenance. | R7 |
| wa_emd_eas | WA Emergency Alert System | wa_emd | official_alert | REGIONAL | https://mil.wa.gov/emergency-alert-system | public official webpage | source_health_probe_only | 24 h | 35 | official | low | low | low | low | candidate_needs_verification | Reference for statewide alert channels. | R7 |
| wa_emd_tsunami | WA EMD tsunami page | wa_emd | official_weather_hazard | REGIONAL | https://mil.wa.gov/tsunami | public official webpage | static_html_headline_candidate | 30 min | 85 | official | low | low | medium | medium | candidate_needs_verification | Tsunami hazards can affect coastal Washington and Puget Sound. | R7 |
| wa_emd_preparedness | WA EMD preparedness | wa_emd | source_health_only | REGIONAL | https://mil.wa.gov/preparedness | public official webpage | source_health_probe_only | 24 h | 20 | official | low | low | low | low | candidate_needs_verification | Preparedness reference, not a high-frequency recent signal. | R7 |
| wa_emd_news | WA EMD news | wa_emd | official_state_civic | REGIONAL | https://mil.wa.gov/news | public official webpage | static_html_headline_candidate | 60 min | 55 | official | low | low | medium | low | candidate_needs_verification | Official emergency-management news can confirm regional hazard state. | R7 |
| nws_alerts_home | NWS alerts page | nws | official_weather_hazard | REGIONAL | https://www.weather.gov/alerts | public official webpage | source_health_probe_only | 30 min | 65 | official | low | low | low | low | candidate_needs_verification | Human reference for weather alert coverage. | R6 |
| nws_active_alerts_api | NWS active alerts API | nws | official_weather_hazard | REGIONAL | https://api.weather.gov/alerts/active | documented official JSON API | official_api_json | 10 min | 100 | official | low | low | medium | medium | official_page_seen | Strong first live candidate for WA weather and hazard alerts. | R6 |
| nws_api_docs | NWS API documentation | nws | source_health_only | REGIONAL | https://www.weather.gov/documentation/services-web-api | public official API docs | manual_review_only | none | 10 | official | low | low | low | low | user_seeded | Reference for NWS API implementation and limits. | R1 |
| nws_alerts_docs | NWS alerts service docs | nws | source_health_only | REGIONAL | https://www.weather.gov/documentation/services-web-alerts | public official API docs | manual_review_only | none | 10 | official | low | low | low | low | user_seeded | Reference for alert fields, severity, urgency, and certainty. | R1 |
| king_county_emergency_home | King County Emergency News | county_emergency | county_emergency | REGIONAL | https://kcemergency.com/ | public official WordPress site | wordpress_feed_candidate | 10 min | 90 | official_candidate | low | medium | medium | medium | official_page_seen | King County emergency news can bridge LOCAL and REGIONAL impacts. | R6 |
| king_county_emergency_alerts_tag | King County Emergency alerts tag | county_emergency | county_emergency | REGIONAL | https://kcemergency.com/tag/alerts/ | public official tag page | wordpress_feed_candidate | 10 min | 90 | official_candidate | low | medium | medium | medium | candidate_needs_verification | Alert-tagged county emergency updates should rank above generic posts. | R6 |
| alert_king_county | Alert King County page | county_emergency | county_emergency | REGIONAL | https://kingcounty.gov/en/dept/executive-services/health-safety/safety-injury-prevention/emergency-preparedness/alert-king-county | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | candidate_needs_verification | Human reference for county alert registration and authority. | R7 |
| king_county_flood_home | King County flood services | county_emergency | official_water_flood | REGIONAL | https://flood.kingcounty.gov/ | public official webpage | hydrology_api_json | 15 min | 85 | official | low | low | medium | medium | candidate_needs_verification | Flood status can affect major rivers and regional roads. | R7 |
| king_county_flood_warnings | King County Flood Control flood warnings | county_emergency | official_water_flood | REGIONAL | https://kingcountyfloodcontrol.org/flood-resources/flood-warnings-alerts/ | public official webpage | static_html_headline_candidate | 15 min | 85 | official_candidate | low | low | medium | medium | candidate_needs_verification | Flood warning explanation and potential live warning surface. | R7 |
| snohomish_alert_resources | Snohomish Public Alert Resources | county_emergency | county_emergency | REGIONAL | https://snohomishcountywa.gov/620/Public-Alert-Resources | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | candidate_needs_verification | County alert context for North Sound. | R7 |
| snohomish_emergency_news | Snohomish Emergency News | county_emergency | county_emergency | REGIONAL | https://snohomishcountywa.gov/5326/Emergency-News | public official webpage | static_html_headline_candidate | 15 min | 75 | official | low | low | medium | medium | candidate_needs_verification | North Sound emergency news can indicate regional hazards. | R7 |
| snohomish_alert_center | Snohomish Alert Center | county_emergency | county_emergency | REGIONAL | https://snohomishcountywa.gov/AlertCenter.aspx | public official webpage | static_html_headline_candidate | 15 min | 75 | official | low | low | medium | medium | candidate_needs_verification | County alert center for closures and emergency notices. | R7 |
| snohomish_river_levels | Snohomish river levels and flood stages | county_emergency | official_water_flood | REGIONAL | https://snohomishcountywa.gov/894/River-Levels-Flood-Stages | public official webpage | hydrology_api_json | 15 min | 75 | official | low | low | medium | medium | candidate_needs_verification | Flood-stage data for Snohomish river basins. | R7 |
| pierce_alert | Pierce County ALERT | county_emergency | county_emergency | REGIONAL | https://www.piercecountywa.gov/921/Pierce-County-ALERT | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | candidate_needs_verification | South Sound alert registration and authority. | R7 |
| pierce_alert_center | Pierce County Alert Center | county_emergency | county_emergency | REGIONAL | https://www.piercecountywa.gov/AlertCenter.aspx | public official webpage | static_html_headline_candidate | 15 min | 70 | official | low | low | medium | medium | candidate_needs_verification | Pierce County active notices and emergencies. | R7 |
| thurston_em_home | Thurston Emergency Management | county_emergency | county_emergency | REGIONAL | https://www.thurstoncountywa.gov/departments/emergency-management | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | candidate_needs_verification | South Sound emergency-management source. | R7 |
| thurston_em_info | Thurston emergency information | county_emergency | county_emergency | REGIONAL | https://www.thurstoncountywa.gov/departments/emergency-management/emergency-information | public official webpage | static_html_headline_candidate | 30 min | 65 | official | low | low | medium | medium | candidate_needs_verification | Regional emergency updates near Olympia and I-5. | R7 |
| thurston_alert_notification | Thurston alert and notification | county_emergency | county_emergency | REGIONAL | https://www.thurstoncountywa.gov/departments/emergency-management/emergency-information/alert-and-notification | public official webpage | source_health_probe_only | 24 h | 35 | official | low | low | low | low | candidate_needs_verification | Human reference for county notification channels. | R7 |
| whatcom_emergency_management | Whatcom Emergency Management | county_emergency | county_emergency | REGIONAL | https://www.whatcomcounty.us/200/Emergency-Management | public official webpage | static_html_headline_candidate | 30 min | 60 | official | low | low | medium | medium | candidate_needs_verification | North border/county emergency source. | R7 |
| skagit_emergency_management | Skagit Emergency Management | county_emergency | county_emergency | REGIONAL | https://www.skagitcounty.net/Departments/EmergencyManagement/main.htm | public official webpage | static_html_headline_candidate | 30 min | 60 | official | low | low | medium | medium | candidate_needs_verification | North Sound flood, wildfire, and emergency context. | R7 |
| kitsap_dem | Kitsap Department of Emergency Management | county_emergency | county_emergency | REGIONAL | https://www.kitsapdem.com/ | public official webpage | wordpress_feed_candidate | 30 min | 65 | official_candidate | low | medium | medium | medium | candidate_needs_verification | Peninsula and ferry-dependent emergency source. | R7 |
| clallam_emergency_management | Clallam Emergency Management | county_emergency | county_emergency | REGIONAL | https://www.clallamcountywa.gov/333/Emergency-Management | public official webpage | static_html_headline_candidate | 30 min | 55 | official | low | low | medium | medium | candidate_needs_verification | Olympic Peninsula hazard and tsunami source. | R7 |
| jefferson_emergency_management | Jefferson County Emergency Management | county_emergency | county_emergency | REGIONAL | https://www.jeffersoncountypublichealth.org/202/Emergency-Management | public official webpage | static_html_headline_candidate | 30 min | 55 | official | low | low | medium | medium | candidate_needs_verification | Olympic Peninsula emergency and public-health source. | R7 |
| wa_governor_news | WA Governor news | governor | official_state_civic | REGIONAL | https://governor.wa.gov/news | public official webpage | rss_atom | 60 min | 50 | official | low | low | medium | low | candidate_needs_verification | Statewide official news can matter during emergencies. | R8 |
| wa_governor_news_releases | WA Governor news releases | governor | official_state_civic | REGIONAL | https://governor.wa.gov/news/news-releases | public official webpage | rss_atom | 60 min | 55 | official | low | low | medium | low | candidate_needs_verification | Official releases can confirm emergency declarations. | R8 |
| wa_governor_executive_orders | WA Governor executive orders | governor | official_state_civic | REGIONAL | https://governor.wa.gov/office-governor/office/official-actions/executive-orders | public official webpage | static_html_headline_candidate | 6 h | 45 | official | low | low | medium | low | candidate_needs_verification | Executive orders can matter during emergencies or public-health events. | R8 |
| wa_doh_home | WA Department of Health | wa_doh | official_public_health | REGIONAL | https://doh.wa.gov/ | public official webpage | source_health_probe_only | 24 h | 55 | official | low | low | low | low | candidate_needs_verification | Public-health authority reference. | R7 |
| wa_doh_newsroom | WA DOH newsroom | wa_doh | official_public_health | REGIONAL | https://doh.wa.gov/newsroom | public official webpage | rss_atom | 60 min | 75 | official | low | low | medium | medium | candidate_needs_verification | Official health alerts and safety notices. | R7 |
| wa_doh_health_news_archive | WA DOH health news archive | wa_doh | official_public_health | REGIONAL | https://doh.wa.gov/newsroom/archive/category/health-news | public official webpage | static_html_headline_candidate | 6 h | 60 | official | low | low | medium | medium | candidate_needs_verification | Health news archive can provide official regional public-health metadata. | R8 |
| wsp_home | Washington State Patrol | wsp | official_incident | REGIONAL | https://wsp.wa.gov/ | public official webpage | source_health_probe_only | 24 h | 50 | official | medium | low | low | medium | candidate_needs_verification | State public-safety authority reference. | R8 |
| wsp_media | WSP media | wsp | official_incident | REGIONAL | https://wsp.wa.gov/media/ | public official webpage | static_html_headline_candidate | 60 min | 55 | official | medium | low | medium | medium | candidate_needs_verification | Major incidents and road-safety notices can corroborate travel disruption. | R8 |
| wsp_media_releases | WSP media releases | wsp | official_incident | REGIONAL | https://wsp.wa.gov/media/media-releases/ | public official webpage | rss_atom | 60 min | 60 | official | medium | low | medium | medium | candidate_needs_verification | Official public-safety releases for major regional events. | R8 |
| wsp_subscribe | WSP subscribe | wsp | source_health_only | REGIONAL | https://wsp.wa.gov/media/subscribe/ | public official webpage | source_health_probe_only | 24 h | 20 | official | low | low | low | low | candidate_needs_verification | Human reference for WSP update channels. | R8 |
| wa_ag_news | WA Attorney General news | attorney_general | official_state_civic | REGIONAL | https://www.atg.wa.gov/news | public official webpage | rss_atom | 6 h | 30 | official | low | low | medium | low | candidate_needs_verification | State civic news, usually lower priority unless public-impact rules match. | R8 |
| wa_ag_press_releases | WA Attorney General press releases | attorney_general | official_state_civic | REGIONAL | https://www.atg.wa.gov/pressrelease.aspx | public official webpage | rss_atom | 6 h | 30 | official | low | low | medium | low | candidate_needs_verification | Official state legal actions, low by default unless immediate impact exists. | R8 |
| wa_ag_rss_feeds | WA AGO RSS feeds | attorney_general | official_state_civic | REGIONAL | https://www.atg.wa.gov/washington-ago-rss-feeds | public official feed index | rss_atom | 6 h | 30 | official | low | low | medium | low | candidate_needs_verification | Feed index for future official RSS verification. | R8 |
| wa_ecology_home | WA Ecology | ecology | official_air_quality | REGIONAL | https://ecology.wa.gov/ | public official webpage | source_health_probe_only | 24 h | 60 | official | low | low | low | low | candidate_needs_verification | Official environmental and air quality authority. | R7 |
| wa_ecology_news | WA Ecology news | ecology | official_air_quality | REGIONAL | https://ecology.wa.gov/about-us/who-we-are/news | public official webpage | rss_atom | 60 min | 65 | official | low | low | medium | low | candidate_needs_verification | Environmental and air-quality alerts can affect Puget Sound. | R7 |
| wa_data_home | Washington Open Data | wa_open_data | official_open_data | REGIONAL | https://data.wa.gov/ | public official portal | socrata_json | 24 h | 40 | official | medium | low | medium | medium | candidate_needs_verification | Parent portal only; use explicit datasets, not general harvesting. | R1 |
| wa_geo_home | Washington Geospatial Open Data | wa_open_data | official_open_data | REGIONAL | https://geo.wa.gov/ | public official portal | arcgis_feature_service_candidate | 24 h | 40 | official | low | low | medium | low | candidate_needs_verification | Parent portal for explicit geospatial datasets and feature services. | R1 |
| wsdot_home | WSDOT homepage | wsdot | official_transport | REGIONAL | https://wsdot.wa.gov/ | public official webpage | source_health_probe_only | 24 h | 55 | official | low | low | low | low | candidate_needs_verification | Authority reference for statewide travel. | R6 |
| wsdot_traffic_api | WSDOT Traveler Information API | wsdot | official_transport | REGIONAL | https://wsdot.wa.gov/traffic/api/ | public official API docs | official_api_json | 5 min | 95 | official | low | low | medium | medium | official_page_seen | Strong first live candidate for roads, passes, and travel alerts. | R6 |
| wsdot_traffic_api_annotated | WSDOT API annotated docs | wsdot | source_health_only | REGIONAL | https://wsdot.wa.gov/traffic/api/Documentation/annotated.html | public official API docs | manual_review_only | none | 10 | official | low | low | low | low | official_page_seen | Reference for API object model and endpoint review. | R1 |
| wsdot_realtime_home | WSDOT real-time travel | wsdot | official_transport | REGIONAL | https://wsdot.com/travel/real-time/ | public official webpage | source_health_probe_only | 15 min | 70 | official | low | low | medium | medium | candidate_needs_verification | Human real-time travel reference. | R6 |
| wsdot_realtime_map | WSDOT real-time map | wsdot | official_transport | REGIONAL | https://wsdot.com/travel/real-time/map/ | public official map webpage | source_health_probe_only | 15 min | 65 | official | low | low | high | medium | candidate_needs_verification | Map reference only; do not screen scrape. | R9 |
| wsdot_travel_home | WSDOT travel page | wsdot | official_transport | REGIONAL | https://wsdot.wa.gov/travel | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | candidate_needs_verification | Travel source context. | R6 |
| wsdot_alert_signup | WSDOT travel alerts signup | wsdot | source_health_only | REGIONAL | https://wsdot.wa.gov/travel/sign-wsdot-travel-alerts | public official webpage | source_health_probe_only | 24 h | 25 | official | low | low | low | low | candidate_needs_verification | Human reference for official alert channels. | R6 |
| wsdot_mountain_passes | WSDOT mountain pass conditions | wsdot | official_transport | REGIONAL | https://wsdot.wa.gov/travel/roads-bridges/mountain-pass-conditions | public official webpage | official_api_json | 10 min | 95 | official | low | low | medium | medium | candidate_needs_verification | Pass closures and traction restrictions are core REGIONAL signals. | R6 |
| wsdot_border_crossings | WSDOT border crossings | wsdot | official_transport | REGIONAL | https://wsdot.wa.gov/travel/roads-bridges/border-crossings | public official webpage | official_api_json | 15 min | 75 | official | low | low | medium | medium | candidate_needs_verification | Cross-border travel disruption can matter regionally. | R7 |
| wsf_bulletins | WSF schedule bulletins | wsf | official_ferry | REGIONAL | https://wsdot.com/ferries/schedule/bulletin.aspx | public official webpage | static_html_headline_candidate | 10 min | 90 | official | low | low | medium | medium | candidate_needs_verification | Ferry cancellations and delays are core Puget Sound signals. | R6 |
| wsf_home | Washington State Ferries | wsf | official_ferry | REGIONAL | https://wsdot.wa.gov/travel/washington-state-ferries | public official webpage | source_health_probe_only | 24 h | 55 | official | low | low | low | low | candidate_needs_verification | Ferry authority reference. | R6 |
| wsf_schedule_api_docs | WSF schedule API docs | wsf | official_ferry | REGIONAL | https://www.wsdot.wa.gov/ferries/api/schedule/documentation/ | official API documentation | official_api_json | 30 min | 75 | official | low | medium | medium | medium | candidate_needs_verification | Candidate ferry API; review access-code/auth requirements. | R7 |
| wsf_terminals_api_docs | WSF terminals API docs | wsf | official_ferry | REGIONAL | https://www.wsdot.wa.gov/ferries/api/terminals/documentation/ | official API documentation | official_api_json | 10 min | 80 | official | low | medium | medium | medium | candidate_needs_verification | Terminal waits, status, and disruptions can rank highly. | R7 |
| wsf_vessels_api_docs | WSF vessels API docs | wsf | official_ferry | REGIONAL | https://www.wsdot.wa.gov/ferries/api/vessels/documentation/ | official API documentation | official_api_json | 10 min | 70 | official | low | medium | medium | low | candidate_needs_verification | Vessel status can support ferry disruption evidence. | R7 |
| wsdot_blog | WSDOT blog | wsdot | official_transport | REGIONAL | https://wsdotblog.blogspot.com/ | public official publisher page | rss_atom | 60 min | 55 | official_candidate | low | medium | medium | low | official_page_seen | Official transport context and construction/disruption posts. | R8 |
| wsdot_news | WSDOT news | wsdot | official_transport | REGIONAL | https://wsdot.wa.gov/about/news | public official webpage | rss_atom | 60 min | 55 | official | low | low | medium | low | candidate_needs_verification | Official news and incident context from WSDOT. | R8 |
| odot_tripcheck_home | ODOT TripCheck | odot | official_transport | REGIONAL | https://tripcheck.com/ | public official webpage | source_health_probe_only | 30 min | 30 | official | low | medium | medium | low | candidate_needs_verification | Oregon travel context only when Washington relevance rules match. | R7 |
| odot_tripcheck_api | ODOT TripCheck API page | odot | official_transport | REGIONAL | https://tripcheck.com/Pages/API | public official API page | open511_json | 30 min | 35 | official | low | medium | medium | low | candidate_needs_verification | Candidate Oregon travel API if terms/access permit. | R7 |
| odot_api_portal | ODOT TripCheck API portal | odot | official_transport | REGIONAL | https://apiportal.odot.state.or.us/product/tripcheck-data-api | API portal | manual_review_only | none | 20 | official | low | high | medium | low | candidate_needs_verification | Potential auth/terms-sensitive API; manual review first. | R7 |
| drivebc_home | DriveBC | drivebc | official_transport | REGIONAL | https://www.drivebc.ca/ | public official webpage | source_health_probe_only | 30 min | 30 | official | low | medium | medium | low | candidate_needs_verification | BC travel context only when cross-border relevance exists. | R7 |
| drivebc_open511_help | DriveBC Open511 help | drivebc | official_transport | REGIONAL | https://api.open511.gov.bc.ca/help | public Open511 docs | open511_json | 30 min | 45 | official | low | medium | medium | low | candidate_needs_verification | Candidate BC Open511 feed for cross-border travel disruption. | R7 |
| drivebc_open_data | DriveBC Open511 open data | drivebc | official_transport | REGIONAL | https://open.canada.ca/data/en/dataset/23a839e3-8fb4-4569-bb3d-c28a7621f687 | public open data page | open511_json | 30 min | 45 | official | low | medium | medium | low | candidate_needs_verification | Open data reference for BC highway events. | R7 |
| metro_service_advisories | King County Metro service advisories | metro | official_transit | REGIONAL | https://kingcounty.gov/en/dept/metro/rider-tools/service-advisories | public official webpage | static_html_headline_candidate | 10 min | 70 | official | low | low | medium | medium | candidate_needs_verification | Regional transit disruptions affecting Seattle/Puget Sound. | R6 |
| metro_service_advisories_rss | King County Metro service advisories RSS | metro | official_transit | REGIONAL | https://kingcounty.gov/en/dept/metro/rider-tools/service-advisories/rss | candidate RSS feed | rss_atom | 10 min | 75 | official | low | low | low | medium | candidate_needs_verification | Preferred metadata path for Metro service alerts if valid. | R6 |
| metro_blog_home | King County Metro blog | metro | official_transit | REGIONAL | https://kingcountymetro.blog/ | public official publisher page | wordpress_feed_candidate | 30 min | 45 | official | low | medium | medium | low | candidate_needs_verification | Official transit context and service changes. | R8 |
| metro_blog_feed | King County Metro blog feed | metro | official_transit | REGIONAL | https://kingcountymetro.blog/feed/ | candidate RSS feed | rss_atom | 30 min | 50 | official | low | medium | low | low | candidate_needs_verification | Preferred metadata path for Metro blog posts if valid. | R8 |
| sound_transit_alerts | Sound Transit service alerts | sound_transit | official_transit | REGIONAL | https://www.soundtransit.org/ride-with-us/service-alerts | public official webpage | static_html_headline_candidate | 10 min | 75 | official | low | low | medium | medium | candidate_needs_verification | Link/rail disruptions can affect Seattle and regional travel. | R7 |
| sound_transit_otd | Sound Transit open transit data | sound_transit | official_transit | REGIONAL | https://www.soundtransit.org/help-contacts/business-information/open-transit-data-otd/otd-downloads | official open data page | gtfs_realtime_alerts | 10 min | 70 | official | low | low | high | medium | candidate_needs_verification | GTFS realtime alerts need dependency review before implementation. | R7 |
| community_transit_alerts | Community Transit service alerts | community_transit | official_transit | REGIONAL | https://www.communitytransit.org/service-alerts | public official webpage | static_html_headline_candidate | 10 min | 65 | official | low | low | medium | medium | candidate_needs_verification | Snohomish transit disruption source. | R7 |
| pierce_transit_alerts | Pierce Transit rider alerts | pierce_transit | official_transit | REGIONAL | https://www.piercetransit.org/rider-alerts/ | public official webpage | rss_atom | 10 min | 60 | official | low | low | medium | medium | candidate_needs_verification | South Sound transit disruption source. | R7 |
| amtrak_cascades | Amtrak Cascades | rail | official_transport | REGIONAL | https://www.amtrakcascades.com/ | public official webpage | static_html_headline_candidate | 30 min | 50 | official_candidate | low | medium | medium | medium | candidate_needs_verification | Regional rail service disruption and corridor context. | R7 |
| wa_dnr_wildfire_resources | WA DNR wildfire resources | wa_dnr | official_wildfire | REGIONAL | https://dnr.wa.gov/wildfire-resources | public official webpage | source_health_probe_only | 24 h | 70 | official | low | low | low | medium | official_page_seen | Wildfire authority reference. | R7 |
| wa_dnr_current_wildfire | WA DNR current wildfire information | wa_dnr | official_wildfire | REGIONAL | https://dnr.wa.gov/wildfire-resources/current-wildfire-incident-information | public official webpage | arcgis_feature_service_candidate | 15 min | 95 | official | low | low | high | high | official_page_seen | Official wildfire incidents can drive hazard and smoke ranking. | R7 |
| wa_dnr_wildfire_dashboard | WA DNR wildfire dashboard | wa_dnr | official_wildfire | REGIONAL | https://experience.arcgis.com/experience/6cdda73cf6154949a1fae76ccb2900a0 | public ArcGIS dashboard | arcgis_dashboard_research | manual | 85 | official_candidate | low | medium | high | high | candidate_needs_verification | Dashboard must be researched for official feature services; no HTML scraping. | R9 |
| wa_dnr_open_data | WA DNR open data | wa_dnr | official_open_data | REGIONAL | https://data-wadnr.opendata.arcgis.com/ | public ArcGIS open data portal | arcgis_feature_service_candidate | 24 h | 65 | official | low | low | medium | medium | candidate_needs_verification | Candidate source for official wildfire/geology feature services. | R9 |
| nwcc_blog | NWCC Info blog | nwcc | official_wildfire | REGIONAL | https://nwccinfo.blogspot.com/ | public official/interagency blog | rss_atom | 30 min | 85 | official_candidate | low | medium | medium | medium | official_page_seen | Regional wildfire coordination and large-fire context. | R7 |
| nwcc_about | NWCC who we are | nwcc | source_health_only | REGIONAL | https://nwccinfo.blogspot.com/p/who-we-are.html | public reference page | manual_review_only | none | 10 | official_candidate | low | medium | low | low | official_page_seen | Source identity and authority reference for NWCC. | R7 |
| usfs_region6_fire | USFS Region 6 fire info | usfs | official_wildfire | REGIONAL | https://www.fs.usda.gov/r06/fire/info | public official webpage | static_html_headline_candidate | 60 min | 65 | official | low | low | medium | medium | candidate_needs_verification | Federal fire information for Oregon/Washington forests. | R7 |
| inciweb | InciWeb | wildfire_federal | official_wildfire | REGIONAL | https://inciweb.wildfire.gov/ | public federal wildfire site | official_api_json | 30 min | 75 | official | low | medium | medium | high | candidate_needs_verification | Incident-level wildfire metadata if API/feed is verified. | R7 |
| nifc_fire_information | NIFC fire information | wildfire_federal | official_wildfire | REGIONAL | https://www.nifc.gov/fire-information | public official webpage | source_health_probe_only | 60 min | 55 | official | low | low | medium | medium | candidate_needs_verification | National fire context for regional wildfire events. | R7 |
| nws_fire_weather | NWS fire weather | nws | official_weather_hazard | REGIONAL | https://www.weather.gov/fire/ | public official webpage | source_health_probe_only | 60 min | 60 | official | low | low | low | medium | candidate_needs_verification | Fire weather reference and alert context. | R7 |
| spc_fire_weather | SPC fire weather | nws | official_weather_hazard | REGIONAL | https://www.spc.noaa.gov/products/fire_wx/ | public official webpage | static_html_headline_candidate | 30 min | 70 | official | low | low | medium | medium | candidate_needs_verification | Fire weather outlooks can corroborate wildfire/smoke risk. | R7 |
| wasmoke_blog | Washington Smoke Blog | ecology | official_air_quality | REGIONAL | https://wasmoke.blogspot.com/ | public multi-agency blog | rss_atom | 30 min | 80 | official_candidate | low | medium | medium | medium | official_page_seen | Smoke explanations and forecasts are core regional signals. | R7 |
| wa_ecology_air_quality | WA Ecology air quality | ecology | official_air_quality | REGIONAL | https://ecology.wa.gov/air-climate/air-quality | public official webpage | source_health_probe_only | 60 min | 65 | official | low | low | low | low | candidate_needs_verification | Official AQI authority and source context. | R7 |
| wa_ecology_aqi | WA Ecology AQI | ecology | official_air_quality | REGIONAL | https://ecology.wa.gov/research-data/monitoring-assessment/air-quality-index | public official webpage | official_api_json | 30 min | 75 | official | low | low | medium | medium | candidate_needs_verification | Official AQI thresholds and data access context. | R7 |
| wa_ecology_airquality_map | WA Ecology air quality map | ecology | official_air_quality | REGIONAL | https://airqualitymap.ecology.wa.gov/ | public official map | arcgis_feature_service_candidate | 30 min | 80 | official | low | medium | high | medium | candidate_needs_verification | AQI source candidate if official feature service/API is found. | R9 |
| pscleanair_air_quality | Puget Sound Clean Air air quality | pscleanair | official_air_quality | REGIONAL | https://pscleanair.gov/27/Air-Quality | public official webpage | source_health_probe_only | 30 min | 75 | official | low | low | medium | medium | candidate_needs_verification | Puget Sound air-quality authority. | R7 |
| pscleanair_rss | Puget Sound Clean Air RSS | pscleanair | official_air_quality | REGIONAL | https://pscleanair.gov/rss.aspx | candidate RSS feed | rss_atom | 30 min | 75 | official | low | low | low | medium | candidate_needs_verification | Preferred metadata path for Puget Sound air-quality notices if valid. | R7 |
| pscleanair_sensormap | Puget Sound Clean Air sensor map | pscleanair | official_air_quality | REGIONAL | https://pscleanair.gov/sensormap | public official map | source_health_probe_only | 30 min | 50 | official | low | low | high | medium | candidate_needs_verification | Map reference only unless official machine-readable endpoint is found. | R9 |
| airnow_home | AirNow | airnow | official_air_quality | REGIONAL | https://www.airnow.gov/ | public official webpage | source_health_probe_only | 30 min | 60 | official | low | low | medium | medium | candidate_needs_verification | National AQI source context. | R7 |
| airnow_api_docs | AirNow API docs | airnow | official_air_quality | REGIONAL | https://docs.airnowapi.org/ | official API docs | official_api_json | 30 min | 75 | official | low | medium | medium | medium | candidate_needs_verification | Candidate AQI API if explicitly configured and key rules allow. | R7 |
| oregon_odf_firestats | Oregon ODF fire stats | oregon_fire | official_wildfire | REGIONAL | https://www.oregon.gov/odf/fire/pages/firestats.aspx | public official webpage | static_html_headline_candidate | 6 h | 35 | official | low | low | medium | low | candidate_needs_verification | Oregon wildfire context only when WA smoke/relevance rules match. | R7 |
| oregon_wildfire_dashboard | Oregon wildfire dashboard | oregon_fire | official_wildfire | REGIONAL | https://geo.maps.arcgis.com/apps/instant/portfolio/index.html?appid=22d04c007866419c91ccf00d097526c8 | public ArcGIS dashboard | arcgis_dashboard_research | manual | 30 | official_candidate | low | medium | high | medium | candidate_needs_verification | Oregon wildfire context; no dashboard scraping. | R9 |
| bc_emergency_info | EmergencyInfoBC | bc_emergency | official_emergency | REGIONAL | https://www.emergencyinfobc.gov.bc.ca/ | public official webpage | rss_atom | 30 min | 35 | official | low | medium | medium | medium | candidate_needs_verification | BC emergency context only when cross-border/regional relevance exists. | R7 |
| bc_emergency_alerts | BC emergency alerts | bc_emergency | official_alert | REGIONAL | https://www2.gov.bc.ca/gov/content/safety/public-safety/emergency-alerts | public official webpage | static_html_headline_candidate | 30 min | 35 | official | low | medium | medium | medium | candidate_needs_verification | BC alert context for cross-border hazards. | R7 |
| nws_seattle_home | NWS Seattle office | nws | official_weather_hazard | REGIONAL | https://www.weather.gov/sew/ | public official webpage | source_health_probe_only | 30 min | 70 | official | low | low | medium | medium | candidate_needs_verification | Western Washington weather office. | R6 |
| nws_portland_home | NWS Portland office | nws | official_weather_hazard | REGIONAL | https://www.weather.gov/pqr/ | public official webpage | source_health_probe_only | 30 min | 45 | official | low | low | medium | medium | candidate_needs_verification | SW Washington and Oregon weather context. | R7 |
| nws_spokane_home | NWS Spokane office | nws | official_weather_hazard | REGIONAL | https://www.weather.gov/otx/ | public official webpage | source_health_probe_only | 30 min | 45 | official | low | low | medium | medium | candidate_needs_verification | Eastern Washington weather context. | R7 |
| nws_pendleton_home | NWS Pendleton office | nws | official_weather_hazard | REGIONAL | https://www.weather.gov/pdt/ | public official webpage | source_health_probe_only | 30 min | 35 | official | low | low | medium | medium | candidate_needs_verification | South-central Washington weather context. | R7 |
| nwrfc_home | Northwest River Forecast Center | nwrfc | official_water_flood | REGIONAL | https://www.nwrfc.noaa.gov/ | public official webpage | hydrology_api_json | 15 min | 85 | official | low | low | medium | medium | candidate_needs_verification | Regional river and flood forecast authority. | R7 |
| nwrfc_river_summary | NWRFC river summary | nwrfc | official_water_flood | REGIONAL | https://www.nwrfc.noaa.gov/river/river_summary.php | public official webpage | hydrology_api_json | 15 min | 85 | official | low | low | medium | medium | candidate_needs_verification | River stage summaries can drive flood ranking. | R7 |
| nwrfc_ten_day_weather | NWRFC 10-day weather | nwrfc | official_water_flood | REGIONAL | https://www.nwrfc.noaa.gov/weather/10_day.cgi | public official webpage | hydrology_api_json | 6 h | 50 | official | low | low | medium | low | candidate_needs_verification | Hydrology weather context, not a primary live alert. | R7 |
| usgs_water_api | USGS Water Data APIs | usgs_water | official_water_flood | REGIONAL | https://api.waterdata.usgs.gov/ | public official API | hydrology_api_json | 15 min | 85 | official | low | low | medium | medium | official_page_seen | Strong source for river gauges and flood evidence. | R7 |
| usgs_water_services | USGS Water Services | usgs_water | official_water_flood | REGIONAL | https://waterservices.usgs.gov/ | public official API docs | hydrology_api_json | 15 min | 85 | official | low | low | medium | medium | official_page_seen | Water-service endpoint reference for gauge allowlists. | R7 |
| usgs_wa_water_center | USGS Washington Water Science Center | usgs_water | official_water_flood | REGIONAL | https://www.usgs.gov/centers/washington-water-science-center | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | candidate_needs_verification | Authority and local water-data context. | R7 |
| usgs_landslides | USGS Landslide Hazards | usgs | official_weather_hazard | REGIONAL | https://landslides.usgs.gov/ | public official webpage | source_health_probe_only | 6 h | 45 | official | low | low | medium | medium | candidate_needs_verification | Landslide hazard context for storms and slopes. | R7 |
| wa_dnr_landslides | WA DNR landslides | wa_dnr | official_weather_hazard | REGIONAL | https://www.dnr.wa.gov/programs-and-services/geology/geologic-hazards/landslides | public official webpage | source_health_probe_only | 6 h | 55 | official | low | low | medium | medium | candidate_needs_verification | Washington landslide hazard reference. | R7 |
| usgs_earthquake_home | USGS Earthquake Hazards | usgs | official_seismic_volcano | REGIONAL | https://earthquake.usgs.gov/ | public official webpage | source_health_probe_only | 30 min | 60 | official | low | low | low | medium | candidate_needs_verification | Earthquake authority reference. | R6 |
| usgs_earthquake_feeds | USGS earthquake feeds | usgs | official_seismic_volcano | REGIONAL | https://earthquake.usgs.gov/earthquakes/feed/ | official feed index | geojson_feed | 5 min | 80 | official | low | low | low | medium | official_page_seen | Feed index for regional earthquake source selection. | R6 |
| usgs_earthquake_v1 | USGS earthquake feed v1 | usgs | official_seismic_volcano | REGIONAL | https://earthquake.usgs.gov/earthquakes/feed/v1.0/ | official feed docs | geojson_feed | 5 min | 80 | official | low | low | low | medium | official_page_seen | Reference for GeoJSON feeds. | R6 |
| usgs_earthquake_geojson | USGS earthquake GeoJSON | usgs | official_seismic_volcano | REGIONAL | https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php | official GeoJSON feed docs | geojson_feed | 5 min | 90 | official | low | low | low | medium | official_page_seen | First candidate for region-filtered earthquake metadata. | R6 |
| pnsn_home | Pacific Northwest Seismic Network | pnsn | official_seismic_volcano | REGIONAL | https://pnsn.org/ | public seismic network webpage | source_health_probe_only | 30 min | 75 | official_candidate | low | low | medium | medium | candidate_needs_verification | Regional seismic authority and corroboration source. | R7 |
| pnsn_recent | PNSN recent earthquakes | pnsn | official_seismic_volcano | REGIONAL | https://pnsn.org/earthquakes/recent | public webpage | geojson_feed | 5 min | 80 | official_candidate | low | low | medium | medium | candidate_needs_verification | Regional earthquake list and possible feed target. | R7 |
| pnsn_recent_list | PNSN recent earthquake list | pnsn | official_seismic_volcano | REGIONAL | https://pnsn.org/earthquakes/recent/list | public webpage/list | geojson_feed | 5 min | 80 | official_candidate | low | low | medium | medium | candidate_needs_verification | Regional earthquake list parser candidate if stable feed exists. | R7 |
| usgs_cvo | USGS Cascades Volcano Observatory | usgs_volcano | official_seismic_volcano | REGIONAL | https://www.usgs.gov/observatories/cascades-volcano-observatory | public official webpage | rss_atom | 6 h | 80 | official | low | low | medium | medium | candidate_needs_verification | Official Cascades volcano source. | R7 |
| usgs_vhp | USGS Volcano Hazards Program | usgs_volcano | official_seismic_volcano | REGIONAL | https://www.usgs.gov/programs/VHP | public official webpage | rss_atom | 6 h | 70 | official | low | low | medium | medium | candidate_needs_verification | Volcano alert context and national program source. | R7 |
| usgs_volcanoes | USGS volcanoes | usgs_volcano | official_seismic_volcano | REGIONAL | https://volcanoes.usgs.gov/ | public official webpage | official_api_json | 6 h | 75 | official | low | low | medium | medium | candidate_needs_verification | Candidate volcano alert endpoint discovery source. | R7 |
| tsunami_gov | Tsunami.gov | tsunami | official_weather_hazard | REGIONAL | https://www.tsunami.gov/ | public official webpage | cap_alerts | 10 min | 90 | official | low | low | medium | medium | candidate_needs_verification | Tsunami watches/warnings/advisories are high-impact REGIONAL signals. | R7 |
| pse_outage_map | PSE outage map | pse | official_utility | REGIONAL | https://www.pse.com/outage/outage-map | public outage map | source_health_probe_only | 15 min | 75 | official | low | medium | high | medium | official_page_seen | Major PSE outages can affect Puget Sound region. | R9 |
| pse_outage_center | PSE outage center | pse | official_utility | REGIONAL | https://www.pse.com/en/outage | public official webpage | static_html_headline_candidate | 15 min | 70 | official | low | low | medium | medium | candidate_needs_verification | Official outage and restoration context. | R7 |
| snopud_outage_map | SnoPUD outage map | snopud | official_utility | REGIONAL | https://outagemap.snopud.com/ | public outage map | source_health_probe_only | 15 min | 70 | official | low | medium | high | medium | candidate_needs_verification | Snohomish regional outage reference; no map scraping. | R9 |
| snopud_outage_center | SnoPUD outage center | snopud | official_utility | REGIONAL | https://www.snopud.com/outages-safety/outage-center/ | public official webpage | static_html_headline_candidate | 15 min | 65 | official | low | low | medium | medium | candidate_needs_verification | Snohomish outage notices and safety context. | R7 |
| tacoma_power_outages | Tacoma Power outages | tacoma_power | official_utility | REGIONAL | https://www.mytpu.org/outages-safety/power-outages/ | public official webpage | static_html_headline_candidate | 15 min | 65 | official | low | low | medium | medium | candidate_needs_verification | Pierce County utility disruption source. | R7 |
| tacoma_power_outages_safety | Tacoma Power outages and safety | tacoma_power | official_utility | REGIONAL | https://www.mytpu.org/outages-safety/ | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | candidate_needs_verification | Utility source context. | R7 |
| city_light_outages | Seattle City Light outages | city_light | official_utility | REGIONAL | https://www.seattle.gov/city-light/outages | public official webpage | source_health_probe_only | 15 min | 70 | official | low | low | medium | medium | candidate_needs_verification | Seattle utility outages can become REGIONAL if widespread or grid-related. | R7 |
| city_light_datacapable | Seattle City Light DataCapable map | city_light | official_utility | REGIONAL | https://scl.datacapable.com/map/ | public outage map | source_health_probe_only | manual | 65 | official_candidate | low | medium | high | medium | candidate_needs_verification | Outage map reference only unless official endpoint is verified. | R9 |
| city_light_arcgis_seattle | Seattle City Light ArcGIS outage map | city_light | official_utility | REGIONAL | https://experience.arcgis.com/experience/66636c38766c4fb4aca16976d79b0527/page/Energy-Page---Seattle-Light-Outage-Map | public ArcGIS dashboard | arcgis_dashboard_research | manual | 65 | official_candidate | low | medium | high | medium | candidate_needs_verification | Do not screen scrape; research underlying feature service. | R9 |
| city_light_arcgis_puget_sound | Puget Sound outage ArcGIS page | utility_region | official_utility | REGIONAL | https://experience.arcgis.com/experience/66636c38766c4fb4aca16976d79b0527/page/Energy-Page---Puget-Sound-Outage-Map | public ArcGIS dashboard | arcgis_dashboard_research | manual | 65 | official_candidate | low | medium | high | medium | candidate_needs_verification | Possible regional outage map; feature-service research only. | R9 |
| bpa_home | Bonneville Power Administration | bpa | official_utility | REGIONAL | https://www.bpa.gov/ | public official webpage | source_health_probe_only | 6 h | 45 | official | low | low | medium | low | candidate_needs_verification | Regional grid context, lower priority unless public impact is clear. | R8 |
| port_seattle_home | Port of Seattle | port_seattle | official_airport_port | REGIONAL | https://www.portseattle.org/ | public official webpage | source_health_probe_only | 24 h | 60 | official | low | low | low | low | candidate_needs_verification | Regional airport/port authority reference. | R7 |
| port_seattle_news | Port of Seattle news | port_seattle | official_airport_port | REGIONAL | https://www.portseattle.org/news | public official webpage | rss_atom | 60 min | 60 | official | low | low | medium | low | candidate_needs_verification | Port/airport operations and public notices. | R8 |
| sea_airport_home | SEA Airport | port_seattle | official_airport_port | REGIONAL | https://www.portseattle.org/sea | public official webpage | source_health_probe_only | 30 min | 65 | official | low | low | medium | low | candidate_needs_verification | Regional airport operations context. | R7 |
| sea_flight_status | SEA flight status | port_seattle | official_airport_port | REGIONAL | https://www.portseattle.org/sea/flight-status | public official webpage | airport_status_json_or_xml | 15 min | 70 | official | low | medium | medium | medium | candidate_needs_verification | SEA disruptions can affect regional travel. | R7 |
| sea_traveler_updates | SEA traveler updates | port_seattle | official_airport_port | REGIONAL | https://www.portseattle.org/actions/airport-traveler-updates | public official webpage | static_html_headline_candidate | 15 min | 75 | official | low | low | medium | medium | candidate_needs_verification | Official airport advisories. | R7 |
| sea_checkpoint_waits | SEA checkpoint waits | port_seattle | official_airport_port | REGIONAL | https://www.portseattle.org/page/live-estimated-checkpoint-wait-times | public official webpage | airport_status_json_or_xml | 15 min | 45 | official | low | medium | medium | low | candidate_needs_verification | Useful only if endpoint and policy allow metadata ingest. | R7 |
| port_tacoma_home | Port of Tacoma | port_tacoma | official_airport_port | REGIONAL | https://www.portoftacoma.com/ | public official webpage | source_health_probe_only | 24 h | 45 | official | low | low | low | low | candidate_needs_verification | Regional freight and port authority reference. | R8 |
| port_tacoma_news | Port of Tacoma news releases | port_tacoma | official_airport_port | REGIONAL | https://www.portoftacoma.com/news-releases | public official webpage | rss_atom | 6 h | 45 | official | low | low | medium | low | candidate_needs_verification | Freight/port disruption context. | R8 |
| port_everett_home | Port of Everett | port_everett | official_airport_port | REGIONAL | https://www.portofeverett.com/ | public official webpage | source_health_probe_only | 24 h | 35 | official | low | low | low | low | candidate_needs_verification | North Sound port context. | R8 |
| port_everett_news | Port of Everett news | port_everett | official_airport_port | REGIONAL | https://www.portofeverett.com/news/ | public official webpage | rss_atom | 6 h | 35 | official | low | low | medium | low | candidate_needs_verification | Port news only when public-impact rules match. | R8 |
| port_vancouver_home | Port of Vancouver USA | port_vancouver | official_airport_port | REGIONAL | https://www.portvancouverusa.com/ | public official webpage | source_health_probe_only | 24 h | 30 | official | low | low | low | low | candidate_needs_verification | Columbia River freight context when regionally relevant. | R8 |
| port_vancouver_news | Port of Vancouver news releases | port_vancouver | official_airport_port | REGIONAL | https://www.portvancouverusa.com/news-releases/ | public official webpage | rss_atom | 6 h | 30 | official | low | low | medium | low | candidate_needs_verification | Freight/port news only with public-impact relevance. | R8 |
| paine_field_fly | Paine Field passenger airport | paine_field | official_airport_port | REGIONAL | https://www.flypainefield.com/ | public airport webpage | airport_status_json_or_xml | 30 min | 40 | official_candidate | low | medium | medium | low | candidate_needs_verification | Regional airport context for Snohomish/North Sound. | R8 |
| paine_field_county | Paine Field county airport | paine_field | official_airport_port | REGIONAL | https://www.painefield.com/ | public official webpage | source_health_probe_only | 24 h | 35 | official | low | low | low | low | candidate_needs_verification | Airport authority reference. | R8 |
| bellingham_airport | Bellingham airport | bellingham_airport | official_airport_port | REGIONAL | https://www.portofbellingham.com/173/Airport | public official webpage | airport_status_json_or_xml | 30 min | 35 | official | low | low | medium | low | candidate_needs_verification | Border-region airport context. | R8 |
| spokane_airport | Spokane Airports | spokane_airport | official_airport_port | REGIONAL | https://spokaneairports.net/ | public official webpage | airport_status_json_or_xml | 30 min | 30 | official | low | low | medium | low | candidate_needs_verification | Eastern Washington airport context only when regionally relevant. | R8 |
| pdx_airport | Portland International Airport | pdx_airport | official_airport_port | REGIONAL | https://www.flypdx.com/ | public airport webpage | airport_status_json_or_xml | 30 min | 25 | official_candidate | low | medium | medium | low | candidate_needs_verification | Oregon airport context only when Washington travel relevance exists. | R8 |
| yvr_flights | YVR flights | yvr_airport | official_airport_port | REGIONAL | https://www.yvr.ca/en/passengers/flights | public airport webpage | airport_status_json_or_xml | 30 min | 25 | official_candidate | low | medium | medium | low | candidate_needs_verification | BC airport context only when cross-border relevance exists. | R8 |
| faa_fly_sea | FAA fly SEA status | airport_faa | official_airport_port | REGIONAL | https://www.fly.faa.gov/fly/flyfaa/flyfaaindex?ARPT=SEA&p=1 | public official webpage | airport_status_json_or_xml | 15 min | 75 | official | low | low | medium | medium | candidate_needs_verification | FAA operational status for SEA. | R7 |
| nasstatus_home | NAS Status | airport_faa | official_airport_port | REGIONAL | https://nasstatus.faa.gov/ | public official webpage | source_health_probe_only | 15 min | 65 | official | low | low | medium | medium | candidate_needs_verification | National airspace status context for regional airports. | R7 |
| nasstatus_airport_api | NAS Status airport API | airport_faa | official_airport_port | REGIONAL | https://nasstatus.faa.gov/api/airport-status-information | public official API candidate | official_api_json | 15 min | 80 | official_candidate | low | low | medium | medium | candidate_needs_verification | Candidate machine-readable airport status source. | R7 |
| faa_airport_status_sea | FAA airport status SEA | airport_faa | official_airport_port | REGIONAL | https://www.faa.gov/airport-status/SEA | public official webpage | airport_status_json_or_xml | 15 min | 75 | official | low | low | medium | medium | candidate_needs_verification | Official SEA ground delay/stop status reference. | R7 |
| faa_asws_github | FAA ASWS reference | airport_faa | source_health_only | REGIONAL | https://github.com/Federal-Aviation-Administration/ASWS | public code/docs reference | manual_review_only | none | 10 | official_reference_candidate | low | medium | low | low | candidate_needs_verification | Research reference only; no GitHub API calls or automatic fetches. | R7 |
| seattle_times_news | Seattle Times Seattle news | regional_newspaper | regional_news | REGIONAL | https://www.seattletimes.com/seattle-news/ | public publisher webpage | rss_atom | 30 min | 55 | regional_media | medium | medium | medium | medium | candidate_needs_verification | Major regional newspaper; use metadata only and avoid paywall bypass. | R8 |
| seattle_times_feed | Seattle Times feed | regional_newspaper | regional_news | REGIONAL | https://www.seattletimes.com/feed/ | candidate RSS feed | rss_atom | 30 min | 55 | regional_media | medium | medium | medium | medium | candidate_needs_verification | Preferred metadata path if feed policy supports use. | R8 |
| heraldnet_home | Everett Herald | regional_newspaper | regional_news | REGIONAL | https://www.heraldnet.com/ | public publisher webpage | rss_atom | 30 min | 45 | regional_media | medium | medium | medium | medium | candidate_needs_verification | North Sound regional reporting. | R8 |
| heraldnet_feed | Everett Herald feed | regional_newspaper | regional_news | REGIONAL | https://www.heraldnet.com/feed/ | candidate RSS feed | rss_atom | 30 min | 45 | regional_media | medium | medium | medium | medium | candidate_needs_verification | Preferred metadata path if valid. | R8 |
| news_tribune | Tacoma News Tribune | regional_newspaper | regional_news | REGIONAL | https://www.thenewstribune.com/ | public publisher webpage | static_html_headline_candidate | 30 min | 40 | regional_media | medium | high | high | medium | candidate_needs_verification | South Sound reporting; prefer feed if found later. | R8 |
| spokesman | The Spokesman-Review | regional_newspaper | regional_news | REGIONAL | https://www.spokesman.com/ | public publisher webpage | rss_atom | 60 min | 35 | regional_media | medium | medium | medium | low | candidate_needs_verification | Eastern Washington context when regionally relevant. | R8 |
| columbian | The Columbian | regional_newspaper | regional_news | REGIONAL | https://www.columbian.com/ | public publisher webpage | rss_atom | 60 min | 35 | regional_media | medium | medium | medium | low | candidate_needs_verification | Southwest Washington reporting. | R8 |
| bellingham_herald | Bellingham Herald | regional_newspaper | regional_news | REGIONAL | https://www.bellinghamherald.com/ | public publisher webpage | static_html_headline_candidate | 60 min | 30 | regional_media | medium | high | high | low | candidate_needs_verification | North border regional reporting; prefer feed if available. | R8 |
| tri_city_herald | Tri-City Herald | regional_newspaper | regional_news | REGIONAL | https://www.tri-cityherald.com/ | public publisher webpage | static_html_headline_candidate | 60 min | 25 | regional_media | medium | high | high | low | candidate_needs_verification | Eastern/South-central WA context when relevant. | R8 |
| wa_state_standard_home | Washington State Standard | nonprofit_news | regional_news | REGIONAL | https://washingtonstatestandard.com/ | public publisher webpage | wordpress_feed_candidate | 60 min | 45 | nonprofit_media | low | medium | medium | low | candidate_needs_verification | State civic and policy reporting; rank only for immediate impact. | R8 |
| wa_state_standard_news | Washington State Standard news | nonprofit_news | regional_news | REGIONAL | https://washingtonstatestandard.com/news/ | public publisher webpage | wordpress_feed_candidate | 60 min | 45 | nonprofit_media | low | medium | medium | low | candidate_needs_verification | State news landing page. | R8 |
| wa_state_standard_feed | Washington State Standard feed | nonprofit_news | regional_news | REGIONAL | https://washingtonstatestandard.com/feed/ | candidate RSS feed | rss_atom | 60 min | 45 | nonprofit_media | low | medium | low | low | candidate_needs_verification | Preferred metadata path if valid. | R8 |
| states_newsroom_rss | States Newsroom RSS feeds | nonprofit_news | source_health_only | REGIONAL | https://statesnewsroom.com/rss-feeds/ | public feed index | rss_atom | 6 h | 20 | nonprofit_media | low | medium | low | low | candidate_needs_verification | Feed index for state-standard feed verification. | R8 |
| cascadepbs_news | Cascade PBS news | public_media | public_media | REGIONAL | https://www.cascadepbs.org/news/ | public publisher webpage/feed candidate | rss_atom | 60 min | 45 | public_media | low | medium | medium | low | candidate_needs_verification | Regional public media and civic context. | R8 |
| kuow_home | KUOW | public_media | public_media | REGIONAL | https://www.kuow.org/ | public publisher webpage/feed candidate | rss_atom | 30 min | 45 | public_media | low | medium | medium | low | candidate_needs_verification | Puget Sound public radio signal. | R8 |
| knkx_home | KNKX | public_media | public_media | REGIONAL | https://www.knkx.org/ | public publisher webpage/feed candidate | rss_atom | 30 min | 45 | public_media | low | medium | medium | low | candidate_needs_verification | Regional public radio signal. | R8 |
| opb_home | OPB | public_media | public_media | REGIONAL | https://www.opb.org/ | public publisher webpage/feed candidate | rss_atom | 60 min | 35 | public_media | low | medium | medium | low | candidate_needs_verification | Oregon/PNW public media only with WA relevance. | R8 |
| opb_rss_feeds | OPB RSS feeds | public_media | public_media | REGIONAL | https://www.opb.org/rss-feeds/ | public feed index | rss_atom | 60 min | 35 | public_media | low | medium | low | low | candidate_needs_verification | Preferred OPB metadata path if a relevant feed is selected. | R8 |
| opb_pnw_tag | OPB Pacific Northwest tag | public_media | public_media | REGIONAL | https://www.opb.org/tag/pacific-northwest/ | public publisher tag page | rss_atom | 60 min | 35 | public_media | low | medium | medium | low | candidate_needs_verification | PNW-focused OPB context. | R8 |
| king5_rss | KING 5 RSS | local_tv | local_tv_radio | REGIONAL | https://www.king5.com/rss | public feed index | rss_atom | 30 min | 45 | local_tv | medium | medium | medium | medium | candidate_needs_verification | Local TV can corroborate regional public-impact events. | R8 |
| kiro7_home | KIRO 7 homepage | local_tv | local_tv_radio | REGIONAL | https://www.kiro7.com/homepage | public publisher webpage | static_html_headline_candidate | 30 min | 35 | local_tv | medium | medium | high | medium | candidate_needs_verification | Prefer feed over homepage extraction. | R8 |
| kiro7_rss | KIRO 7 RSS candidate | local_tv | local_tv_radio | REGIONAL | https://www.kiro7.com/rss-snd/ | candidate RSS feed | rss_atom | 30 min | 45 | local_tv | medium | medium | medium | medium | candidate_needs_verification | Candidate metadata path for TV headlines. | R8 |
| komo_home | KOMO | local_tv | local_tv_radio | REGIONAL | https://komonews.com/ | public publisher webpage | static_html_headline_candidate | 30 min | 35 | local_tv | medium | medium | high | medium | candidate_needs_verification | TV source; avoid homepage extraction unless reviewed. | R8 |
| komo_local | KOMO local news | local_tv | local_tv_radio | REGIONAL | https://komonews.com/news/local | public publisher webpage | static_html_headline_candidate | 30 min | 40 | local_tv | medium | medium | high | medium | candidate_needs_verification | Local/regional headlines if feed unavailable and policy allows. | R8 |
| fox13_home | FOX 13 Seattle | local_tv | local_tv_radio | REGIONAL | https://www.fox13seattle.com/ | public publisher webpage | static_html_headline_candidate | 30 min | 35 | local_tv | medium | medium | high | medium | candidate_needs_verification | TV source; prefer feed if found later. | R8 |
| oregonlive_home | OregonLive | regional_newspaper | regional_news | REGIONAL | https://www.oregonlive.com/ | public publisher webpage | rss_atom | 60 min | 25 | regional_media | medium | medium | medium | low | candidate_needs_verification | Oregon context only with Washington relevance. | R8 |
| seattle_times_pnw_magazine | Seattle Times Pacific NW Magazine | regional_newspaper | regional_news | REGIONAL | https://www.seattletimes.com/seattle-news/pacific-nw-magazine/ | public publisher webpage | rss_atom | 6 h | 15 | regional_media | low | medium | medium | low | candidate_needs_verification | Usually feature content; low recent-signal priority. | R8 |
| nps_rainier_conditions | Mount Rainier conditions | recreation_access | official_state_civic | REGIONAL | https://www.nps.gov/mora/planyourvisit/conditions.htm | public official webpage | static_html_headline_candidate | 6 h | 45 | official | low | low | medium | low | candidate_needs_verification | Park closures and road conditions can affect regional access. | R8 |
| nps_olympic_roads | Olympic road conditions | recreation_access | official_state_civic | REGIONAL | https://www.nps.gov/olym/planyourvisit/current-road-conditions.htm | public official webpage | static_html_headline_candidate | 6 h | 45 | official | low | low | medium | low | candidate_needs_verification | Olympic Peninsula road/access closures. | R8 |
| nps_north_cascades_roads | North Cascades road conditions | recreation_access | official_state_civic | REGIONAL | https://www.nps.gov/noca/planyourvisit/road-conditions.htm | public official webpage | static_html_headline_candidate | 6 h | 45 | official | low | low | medium | low | candidate_needs_verification | North Cascades access and SR 20 context. | R8 |
| wta_trip_reports | WTA trip reports | recreation_access | unofficial_aggregator | REGIONAL | https://www.wta.org/go-outside/trip-reports | public community site | manual_review_only | disabled | 10 | nonprofit_community | medium | high | high | medium | candidate_policy_sensitive | Community reports are not official; disabled and review-only. | R10 |
| wta_pass_news | WTA pass news | recreation_access | regional_news | REGIONAL | https://www.wta.org/go-outside/trail-smarts/pass-news | public nonprofit webpage | rss_atom | 6 h | 25 | nonprofit_community | low | medium | medium | low | candidate_needs_verification | Recreation-access news, lower priority. | R8 |
| usfs_region6_home | USFS Region 6 | usfs | official_state_civic | REGIONAL | https://www.fs.usda.gov/r06 | public official webpage | source_health_probe_only | 24 h | 30 | official | low | low | low | low | candidate_needs_verification | Federal land access and fire context. | R8 |
| reddit_washington | Reddit r/Washington | reddit | social_candidate | REGIONAL | https://www.reddit.com/r/Washington/ | platform community page/API candidate | manual_review_only | disabled | 15 | platform | high | high | high | high | candidate_policy_sensitive | Community echo only through compliant configured access. | R10 |
| reddit_pnw | Reddit r/PacificNorthwest | reddit | social_candidate | REGIONAL | https://www.reddit.com/r/PacificNorthwest/ | platform community page/API candidate | manual_review_only | disabled | 12 | platform | high | high | high | high | candidate_policy_sensitive | Broad community signal, disabled by default. | R10 |
| reddit_seattlewa | Reddit r/SeattleWA | reddit | social_candidate | REGIONAL | https://www.reddit.com/r/SeattleWA/ | platform community page/API candidate | manual_review_only | disabled | 10 | platform | high | high | high | high | candidate_policy_sensitive | Seattle-adjacent community echo, no HTML scraping. | R10 |
| reddit_bellingham | Reddit r/Bellingham | reddit | social_candidate | REGIONAL | https://www.reddit.com/r/Bellingham/ | platform community page/API candidate | manual_review_only | disabled | 8 | platform | high | high | high | high | candidate_policy_sensitive | North Sound community echo, disabled. | R10 |
| reddit_tacoma | Reddit r/Tacoma | reddit | social_candidate | REGIONAL | https://www.reddit.com/r/Tacoma/ | platform community page/API candidate | manual_review_only | disabled | 8 | platform | high | high | high | high | candidate_policy_sensitive | South Sound community echo, disabled. | R10 |
| reddit_spokane | Reddit r/Spokane | reddit | social_candidate | REGIONAL | https://www.reddit.com/r/Spokane/ | platform community page/API candidate | manual_review_only | disabled | 6 | platform | high | high | high | high | candidate_policy_sensitive | Eastern WA community echo, disabled. | R10 |
| reddit_portland | Reddit r/Portland | reddit | social_candidate | REGIONAL | https://www.reddit.com/r/Portland/ | platform community page/API candidate | manual_review_only | disabled | 5 | platform | high | high | high | high | candidate_policy_sensitive | Oregon community echo only when WA relevance exists. | R10 |
| x_waemd | X WA EMD account | x_api | social_candidate | REGIONAL | https://x.com/waEMD | platform account/API candidate | manual_review_only | disabled | 20 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Official agency social echo only through compliant API access. | R10 |
| x_wsdot | X WSDOT account | x_api | social_candidate | REGIONAL | https://x.com/wsdot | platform account/API candidate | manual_review_only | disabled | 20 | platform_official_account | low | high | high | high | candidate_policy_sensitive | WSDOT social echo only through compliant API access. | R10 |
| x_wsdot_traffic | X WSDOT traffic account | x_api | social_candidate | REGIONAL | https://x.com/wsdot_traffic | platform account/API candidate | manual_review_only | disabled | 20 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Traffic echo only through compliant API access. | R10 |
| x_wsdot_passes | X WSDOT passes account | x_api | social_candidate | REGIONAL | https://x.com/wsdot_passes | platform account/API candidate | manual_review_only | disabled | 20 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Pass echo only through compliant API access. | R10 |
| x_wsferries | X WSFerries account | x_api | social_candidate | REGIONAL | https://x.com/wsferries | platform account/API candidate | manual_review_only | disabled | 20 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Ferry echo only through compliant API access. | R10 |
| x_washdnr | X WA DNR account | x_api | social_candidate | REGIONAL | https://x.com/WashDNR | platform account/API candidate | manual_review_only | disabled | 20 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Wildfire/social echo only through compliant API access. | R10 |
| x_wadepthealth | X WA Dept Health account | x_api | social_candidate | REGIONAL | https://x.com/WADeptHealth | platform account/API candidate | manual_review_only | disabled | 18 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Health social echo only through compliant API access. | R10 |
| x_wastatepatrol | X WA State Patrol account | x_api | social_candidate | REGIONAL | https://x.com/wastatepatrol | platform account/API candidate | manual_review_only | disabled | 15 | platform_official_account | medium | high | high | high | candidate_policy_sensitive | Public-safety social echo only through compliant API access. | R10 |
| x_pnsn | X PNSN account | x_api | social_candidate | REGIONAL | https://x.com/PNSN1 | platform account/API candidate | manual_review_only | disabled | 15 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Seismic social echo only through compliant API access. | R10 |
| x_nwccinfo | X NWCC Info account | x_api | social_candidate | REGIONAL | https://x.com/NWCCInfo | platform account/API candidate | manual_review_only | disabled | 15 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Wildfire coordination echo only through compliant API access. | R10 |
| x_nws_seattle | X NWS Seattle account | x_api | social_candidate | REGIONAL | https://x.com/NWSSeattle | platform account/API candidate | manual_review_only | disabled | 15 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Weather social echo only through compliant API access. | R10 |
| x_nws_portland | X NWS Portland account | x_api | social_candidate | REGIONAL | https://x.com/NWSPortland | platform account/API candidate | manual_review_only | disabled | 10 | platform_official_account | low | high | high | high | candidate_policy_sensitive | SW WA/Oregon weather echo only if relevant. | R10 |
| x_nws_spokane | X NWS Spokane account | x_api | social_candidate | REGIONAL | https://x.com/NWSSpokane | platform account/API candidate | manual_review_only | disabled | 10 | platform_official_account | low | high | high | high | candidate_policy_sensitive | Eastern WA weather echo only if relevant. | R10 |
| bluesky_wildfire_search | Bluesky Washington wildfire search | bluesky | social_candidate | REGIONAL | https://bsky.app/search?q=Washington%20wildfire | platform search/API candidate | manual_review_only | disabled | 8 | platform | high | high | high | high | candidate_policy_sensitive | AT Protocol candidate only after policy review. | R10 |
| bluesky_puget_sound_search | Bluesky Puget Sound search | bluesky | social_candidate | REGIONAL | https://bsky.app/search?q=Puget%20Sound | platform search/API candidate | manual_review_only | disabled | 8 | platform | high | high | high | high | candidate_policy_sensitive | Community echo only through compliant AT Protocol access. | R10 |
| bluesky_pnw_search | Bluesky Pacific Northwest search | bluesky | social_candidate | REGIONAL | https://bsky.app/search?q=Pacific%20Northwest | platform search/API candidate | manual_review_only | disabled | 8 | platform | high | high | high | high | candidate_policy_sensitive | Broad PNW community echo, disabled. | R10 |
| bluesky_wsdot_search | Bluesky WSDOT search | bluesky | social_candidate | REGIONAL | https://bsky.app/search?q=WSDOT | platform search/API candidate | manual_review_only | disabled | 8 | platform | high | high | high | high | candidate_policy_sensitive | Transport community echo only after policy review. | R10 |
| bluesky_snoqualmie_pass_search | Bluesky Snoqualmie Pass search | bluesky | social_candidate | REGIONAL | https://bsky.app/search?q=Snoqualmie%20Pass | platform search/API candidate | manual_review_only | disabled | 8 | platform | high | high | high | high | candidate_policy_sensitive | Pass community echo only after policy review. | R10 |
| rfc9309_robots | RFC 9309 Robots Exclusion Protocol | policy_reference | source_health_only | REGIONAL | https://www.rfc-editor.org/rfc/rfc9309.html | public standards reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | Policy reference for robots handling. | R1 |
| rss_specification | RSS specification | policy_reference | source_health_only | REGIONAL | https://www.rssboard.org/rss-specification | public standards reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | Reference for RSS parser expectations. | R1 |
| sitemap_protocol | Sitemaps protocol | policy_reference | source_health_only | REGIONAL | https://www.sitemaps.org/protocol.html | public standards reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | Reference only; no sitemap crawling in early phases. | R1 |
| schema_newsarticle | Schema.org NewsArticle | policy_reference | source_health_only | REGIONAL | https://schema.org/NewsArticle | public schema reference | manual_review_only | none | 0 | reference | low | low | low | low | user_seeded | Metadata reference for possible publisher markup review. | R8 |
| reddit_developer_terms | Reddit Developer Terms | policy_reference | source_health_only | REGIONAL | https://redditinc.com/policies/developer-terms | public platform policy | manual_review_only | none | 0 | reference | low | high | low | low | candidate_policy_sensitive | Must be reviewed before Reddit access. | R10 |
| reddit_data_api_terms | Reddit Data API Terms | policy_reference | source_health_only | REGIONAL | https://redditinc.com/policies/data-api-terms | public platform policy | manual_review_only | none | 0 | reference | low | high | low | low | candidate_policy_sensitive | Must be reviewed before Reddit API use. | R10 |
| x_api_docs | X API introduction | policy_reference | source_health_only | REGIONAL | https://docs.x.com/x-api/introduction | public platform API docs | manual_review_only | none | 0 | reference | low | high | low | low | candidate_policy_sensitive | Must be reviewed before X source enablement. | R10 |
| bluesky_atproto_docs | Bluesky AT Protocol XRPC API docs | policy_reference | source_health_only | REGIONAL | https://docs.bsky.app/docs/api/at-protocol-xrpc-api | public platform API docs | manual_review_only | none | 0 | reference | low | medium | low | low | candidate_policy_sensitive | Reference for possible compliant Bluesky adapter. | R10 |

## SECTION 5: Source admission tiers

Tier 0 - local fixtures only:

- No network.
- Used for tests.
- Best first implementation target.
- Fixture adapters must produce the same normalized shapes as later live adapters.

Tier 1 - official APIs, official open data, RSS/Atom, CAP feeds, GeoJSON feeds, hydrology APIs, and
official agency JSON endpoints:

- Best first live candidates.
- Examples: NWS active alerts, WSDOT Traveler API, USGS earthquake GeoJSON, USGS water services,
  WSF APIs after access review, and King County Emergency feed if valid.
- Must be disabled by default and opt-in.

Tier 2 - official pages with stable public operational data but no obvious feed/API:

- Candidate only after source-policy review.
- Prefer source-health checks and manual review before parser implementation.
- Must use per-source selectors if extraction is ever allowed.
- No recursive crawling and no article-body fetch.

Tier 3 - regional news RSS or publisher-provided feeds:

- Store headline metadata only.
- No article-body archive.
- No paywall bypass.
- Repeated syndicated headlines should not create fake source diversity.

Tier 4 - public media, nonprofit regional outlets, and regional blogs:

- Prefer RSS/Atom.
- Store headline metadata only.
- Respect robots, terms, and source policy.
- Rank by public-impact relevance, not general civic interest alone.

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

## SECTION 6: REGIONAL event model

The system should not only store "news items." It should infer when multiple recent items refer to
the same regional event. The global architecture's `news_clusters` can handle generic topic
clusters, but REGIONAL needs richer geography, route, hazard, and public-impact features. A future
`regional_events` table is clearer than overloading generic clusters.

Candidate future `regional_events` table:

| Column | Purpose |
| --- | --- |
| `regional_event_id` | Internal integer primary key. |
| `scope` | Always `REGIONAL` initially, stored for consistency with shared readers. |
| `event_key` | Deterministic key from event type, source families, time bucket, county/route/basin/facility tokens, and normalized title tokens. |
| `event_type` | Controlled REGIONAL event type. |
| `title` | Representative bounded title, not an LLM summary. |
| `representative_item_id` | Best item to display as primary evidence. |
| `severity` | Deterministic severity bucket such as `info`, `notice`, `elevated`, `major`, or `critical`. |
| `public_impact_score` | Direct regional impact component. |
| `source_diversity_score` | Independent source-family convergence component. |
| `official_confirmation_score` | Official-source strength component. |
| `social_echo_score` | Optional compliant social echo component. |
| `news_echo_score` | Regional news/public media convergence component. |
| `transportation_impact_score` | Highway, bridge, pass, rail, border, or travel disruption component. |
| `ferry_impact_score` | WSF route, terminal, vessel, or delay component. |
| `wildfire_impact_score` | Fire size, containment, closure, evacuation, or incident-name component. |
| `smoke_air_quality_score` | AQI, smoke, station, and regional exposure component. |
| `flood_hydrology_score` | River gauge, flood stage, NWRFC, USGS, county flood component. |
| `seismic_volcano_score` | Earthquake magnitude/intensity, volcano alert, tsunami component. |
| `public_health_score` | DOH/county health alert component. |
| `utility_impact_score` | Customer count, region, grid, utility outage component. |
| `airport_port_score` | Airport, port, freight, maritime, or NAS component. |
| `first_seen_at` | First local observation. |
| `last_seen_at` | Most recent matching observation. |
| `last_elevated_at` | Most recent time the event crossed display/ranking threshold. |
| `expires_at` | Purge cutoff. |
| `geography_json` | Bounded structured geography such as counties, corridors, zones, basin, pass, port, airport, or region. |
| `counties_json` | Normalized county labels. |
| `corridors_json` | Normalized route/pass/ferry/border/rail labels. |
| `source_ids_json` | Source ids represented in the event. |
| `item_ids_json` | Item ids represented in the event. |
| `evidence_json` | Source, parser, matching, ranking, policy, and redaction evidence. |
| `ranking_explanation_json` | Score factors and deterministic reason strings. |
| `status` | `active`, `monitoring`, `expired`, `hidden`, `policy_blocked`, or `resolved`. |

Required event types:

- `state_emergency_alert`
- `county_emergency_alert`
- `wildfire`
- `smoke_air_quality`
- `evacuation_order`
- `red_flag_warning`
- `weather_alert`
- `atmospheric_river`
- `flood`
- `river_flood`
- `landslide`
- `earthquake`
- `tsunami`
- `volcano_unrest`
- `mountain_pass_closure`
- `highway_closure`
- `ferry_disruption`
- `bridge_disruption`
- `transit_disruption`
- `airport_disruption`
- `port_disruption`
- `power_outage`
- `utility_disruption`
- `public_health_alert`
- `food_water_shellfish_alert`
- `state_civic_action`
- `major_regional_news`
- `recreation_access_closure`
- `border_crossing_disruption`
- `source_health_problem`
- `community_signal`

Routine small incidents should not automatically become elevated REGIONAL events. Small road
incidents, routine public-safety releases, isolated residential outages, and single-source social
reports should remain hidden, low-priority, or background pulse unless official severity,
public-impact rules, or independent cross-source convergence justify elevation.

## SECTION 7: Cross-source convergence ranking

The ranking model should implement this idea deterministically: if something appears in official
sources, regional news, transport feeds, utility feeds, hazard feeds, and compliant community/social
signals within a short window, it is probably important or interesting.

This is not an LLM summarizer. The system should compute features, scores, and explanations from
stored metadata only.

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
- City, county, PSE, SnoPUD, Tacoma Power, or Seattle City Light outage with regional customer
  impact.
- DOH health or safety alert.
- WSP major traffic/public-safety release.
- FAA/NAS airport ground delay, ground stop, or major airport disruption.

2. Source diversity

Independent source families count more than repeated mentions from the same family. Candidate
families:

- `wa_emd`
- `county_emergency`
- `nws`
- `nwrfc`
- `usgs`
- `pnsn`
- `wa_dnr`
- `nwcc`
- `ecology`
- `airnow`
- `wsdot`
- `wsf`
- `metro`
- `sound_transit`
- `community_transit`
- `pierce_transit`
- `pse`
- `snopud`
- `tacoma_power`
- `city_light`
- `port_seattle`
- `port_tacoma`
- `airport_faa`
- `wa_doh`
- `wsp`
- `governor`
- `attorney_general`
- `regional_newspaper`
- `public_radio`
- `local_tv`
- `nonprofit_news`
- `reddit`
- `bluesky`
- `x_api`
- `source_health`

3. Temporal proximity

Items closer in time are more likely to refer to the same event. Initial matching windows:

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

- County.
- City.
- Route.
- Mountain pass.
- Ferry route.
- Airport.
- Port.
- River basin.
- Weather zone.
- Fire incident name.
- Volcano.
- Seismic region.
- Air-quality station.
- Evacuation zone.
- Public-health jurisdiction.
- Regional label, such as Puget Sound, Olympic Peninsula, Cascades, Inland Northwest, Southwest
  Washington, North Sound, South Sound, or Columbia River Gorge.

5. Public impact

Boost:

- Statewide alerts.
- Evacuations.
- Major bridge or highway closures.
- Ferry route shutdowns.
- Pass closures.
- Airport ground stops.
- Port disruptions.
- Large wildfires.
- Smoke affecting Puget Sound.
- AQI above threshold.
- Earthquake above threshold or felt in Puget Sound.
- Tsunami notices.
- Flood stage or evacuation.
- Utility outages above configured customer count.
- Public-health alerts with action guidance.
- Official emergency declarations.
- School closures at regional scale.
- Infrastructure damage.
- Cross-border travel disruptions.

6. Recency

Recent items matter more, but older active hazards can stay elevated while still active. Ranking
evidence must show whether an item is fresh, active-but-older, stale, or retained only for
source-health/debug evidence.

7. User-configured priority

Future config should allow boosts for:

- Puget Sound.
- King County.
- Snohomish County.
- Pierce County.
- Kitsap County.
- I-5.
- I-90.
- Snoqualmie Pass.
- Stevens Pass.
- Blewett Pass.
- Ferries.
- WSF.
- Wildfires.
- Smoke.
- Air quality.
- Earthquakes.
- Flood.
- Public health.
- Power outages.
- Airports.
- Ports.
- State government.

8. Privacy and low-public-value penalty

De-emphasize:

- Routine local police/fire incidents outside Seattle unless regional impact exists.
- Isolated residential outages below threshold.
- Small traffic incidents with no corridor impact.
- Vague social-only reports.
- Single-source rumor.
- Agency news releases with no immediate public effect.
- Duplicate syndicated stories.

Sample scoring formula:

```text
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
```

Possible normalization:

```text
recency_score = 0..20
official_severity_score = 0..40
source_diversity_score = min(35, independent_family_count * 6 + official_family_count * 4)
public_impact_score = 0..30
geographic_relevance_score = 0..25
active_alert_score = 0 or 20
source_priority_score = configured_priority / 10
cluster_size_score = min(10, unique_item_count)
privacy_penalty = 0..40
duplicate_family_penalty = max(0, duplicate_mentions_same_family - 1) * 2
stale_source_penalty = 0..25
low_confidence_penalty = 0..30
out_of_region_penalty = 0..50
```

The exact constants can change in implementation, but the score must stay explainable in JSON and
visible in evidence. A display row should be able to say:

```json
{
  "reason": "Elevated by WSDOT pass closure, NWS winter storm warning, WSF route impacts, and two independent regional news families within 8 hours.",
  "features": {
    "official_severity_score": 34,
    "source_diversity_score": 24,
    "public_impact_score": 26,
    "geographic_relevance_score": 21,
    "out_of_region_penalty": 0
  }
}
```

"Frequency of appearance" means independent cross-source convergence, not raw duplicate counts.

Bad ranking:

- 20 syndicated copies of the same wire story dominate.

Good ranking:

- WA DNR wildfire and NWCC brief.
- NWS red flag warning.
- Ecology or AirNow smoke impact.
- WSDOT closure nearby.
- County evacuation alert.
- Local TV or public radio report.
- Bluesky/Reddit chatter only if compliant.
- All within a plausible time window.

## SECTION 8: REGIONAL source category design

REGIONAL sources should be grouped by operational purpose, not by visual placement alone. The
category decides the parser family, retention, privacy rules, source-health expectations, and
ranking contribution. Every source remains disabled by default until a later implementation phase
adds config, fixture tests, source-policy evidence, and explicit operator enablement.

### 1. Emergency alerts and county emergency pages

Why it exists:

- Provides the highest-authority state and county public-safety signal.
- Covers statewide alerts, county emergency posts, flood warnings, tsunami information, and official
  emergency instructions.
- Supplies official confirmation for cross-source convergence.

First safe sources:

- WA EMD alerts.
- NWS active alerts.
- King County Emergency News.
- King County flood pages.
- Snohomish, Pierce, Thurston, Whatcom, Skagit, Kitsap, Clallam, and Jefferson emergency pages after
  verification.

Parser/adaptor class:

- `official_api_json` for NWS alerts.
- `wordpress_feed_candidate` for WordPress-based county emergency sources.
- `static_html_headline_candidate` only after source-policy and selector review.
- `source_health_probe_only` for registration pages and human-reference pages.

Likely refresh interval:

- 5 to 10 minutes for active official alert APIs.
- 10 to 30 minutes for emergency news feeds.
- 24 hours for human-reference pages.

Privacy risk:

- Low for statewide alert metadata.
- Medium for incident-specific county posts if they include exact addresses or private distress.

Policy risk:

- Low for official APIs and feeds.
- Medium for official pages that require HTML extraction.

Source-health signals:

- Last successful parse.
- Active alert count.
- Feed timestamp.
- HTTP status in later live phases.
- Parser error message.
- Stale threshold by source.

Sample item fields:

- `alert_id`
- `event_type`
- `source_published_at`
- `effective_at`
- `expires_at`
- `severity`
- `urgency`
- `certainty`
- `affected_counties`
- `affected_zones`
- `instructions_url`
- `source_url`

Ranking contribution:

- Strong official severity boost.
- Strong public-impact boost for evacuation, warning, flood, tsunami, and emergency declaration.
- Cross-source anchor for related transport, weather, news, and utility items.

Later implementation phase:

- R2 for fixtures.
- R6 for NWS and King County live candidates.
- R7 for additional county pages after verification.

### 2. Transportation and ferries

Why it exists:

- Regional utility of the dashboard depends heavily on movement: highways, passes, bridges,
  ferries, transit, borders, rail, airport access, and closures.
- Transportation disruption is often the earliest practical signal that an event matters.

First safe sources:

- WSDOT Traveler API and documentation.
- WSDOT real-time travel pages as human references.
- WSF APIs and bulletins after access-code handling is designed.
- Metro RSS.
- Sound Transit service alerts.
- Community Transit and Pierce Transit alerts.
- ODOT TripCheck and DriveBC Open511 only when Washington relevance and policy allow.

Parser/adaptor class:

- `official_api_json` for WSDOT and WSF.
- `rss_atom` for Metro and publisher-like alert feeds.
- `open511_json` for DriveBC and ODOT if permitted.
- `source_health_probe_only` for maps and pages without stable endpoints.

Likely refresh interval:

- 5 minutes for WSDOT major incidents and pass status.
- 5 to 10 minutes for ferry route disruptions.
- 10 to 15 minutes for transit advisories.
- 15 to 30 minutes for cross-border and Oregon/BC relevance-filtered sources.

Privacy risk:

- Low for road, route, vessel, and pass metadata.
- Medium if incident text contains personally identifying crash or injury detail.

Policy risk:

- Low for documented official APIs.
- Medium for sources requiring access codes or terms review.
- High for map extraction or dashboard scraping, which should be avoided.

Source-health signals:

- Last update time from API or feed.
- Item count by corridor.
- Route/pass/ferry coverage.
- Consecutive failures.
- Access/auth status.
- Conditional request behavior when available.

Sample item fields:

- `route`
- `direction`
- `milepost`
- `pass`
- `ferry_route`
- `terminal`
- `facility`
- `start_time`
- `end_time`
- `delay_minutes`
- `closure_status`
- `detour_note`
- `source_url`

Ranking contribution:

- Major route, pass, bridge, ferry, airport-access, and border disruption gets high public-impact
  score.
- Transport matches can elevate weather, wildfire, flood, and public-safety events when they affect
  movement.

Later implementation phase:

- R2 for WSDOT, WSF, and transit fixtures.
- R6 for WSDOT live candidate.
- R7 for WSF and cross-border sources after access review.

### 3. Wildfire, smoke, and air quality

Why it exists:

- Wildfire and smoke can affect the entire region even when the fire is outside the user's city.
- Fire, smoke, burn restrictions, evacuations, AQI, and closures have strong public-impact value.

First safe sources:

- WA DNR wildfire resources.
- WA DNR open-data and ArcGIS-backed candidates after feature-service research.
- NWCC Info if feed endpoint is verified.
- USFS Region 6 fire information.
- InciWeb and NIFC as official/federal references where suitable.
- NWS fire weather.
- SPC fire weather products.
- WA Smoke blog.
- WA Ecology AQI.
- Puget Sound Clean Air RSS/sensor pages where policy allows.
- AirNow API docs for later configured access.

Parser/adaptor class:

- `rss_atom` for verified feeds.
- `official_api_json` for AirNow or Ecology APIs if configured.
- `arcgis_feature_service_candidate` for official feature layers only.
- `static_html_headline_candidate` only for official pages after review.
- `source_health_probe_only` for dashboards when no data endpoint is suitable.

Likely refresh interval:

- 15 minutes for active fire/AQI official APIs.
- 30 minutes for wildfire coordination feeds.
- 60 minutes for lower-priority reference pages.

Privacy risk:

- Low for fire perimeter, public AQI, and official evacuation metadata.
- Medium for evacuation zone or incident text that could expose household-level distress.

Policy risk:

- Low for official APIs and feeds.
- Medium for public blogs and nonprofit/community sources.
- High for dashboard HTML scraping, which is a non-goal.

Source-health signals:

- Last incident update.
- Fire count.
- AQI station freshness.
- Endpoint verification status.
- Feature-service layer id when verified.
- Parser failure reason.

Sample item fields:

- `fire_name`
- `incident_id`
- `county`
- `acres`
- `containment_percent`
- `evacuation_level`
- `smoke_region`
- `aqi_value`
- `aqi_category`
- `station_id`
- `affected_routes`
- `source_url`

Ranking contribution:

- Large fires, evacuations, smoke over Puget Sound, AQI above threshold, road closures, and
  convergent NWS/Ecology/news signals get high score.
- Single generic wildfire articles without public impact remain low.

Later implementation phase:

- R2 for fixtures.
- R7 for WA DNR, NWCC, Ecology, and AirNow after endpoint verification.
- R9 for official ArcGIS feature-service research.

### 4. Weather, river, flood, hydrology, landslide

Why it exists:

- Weather, river forecasts, floods, atmospheric rivers, landslides, and hydrology data have broad
  regional impact and often explain transport, utility, and emergency events.

First safe sources:

- NWS Seattle, Portland, Spokane, and Pendleton office pages.
- NWS active alerts API.
- NWRFC river summary and weather pages after endpoint verification.
- USGS Water Data APIs.
- USGS Washington Water Science Center.
- USGS landslide resources.
- WA DNR landslide resources.

Parser/adaptor class:

- `official_api_json` for NWS and later verified NOAA endpoints.
- `hydrology_api_json` for USGS and NWRFC-like sources.
- `cap_alerts` if CAP records are useful.
- `static_html_headline_candidate` only after review.

Likely refresh interval:

- 5 to 10 minutes for active warnings.
- 15 minutes for river gauges during active events.
- 30 to 60 minutes for forecast summaries.

Privacy risk:

- Low for weather zones and river gauges.
- Medium if flood impacts include private-address details from local pages.

Policy risk:

- Low for official machine-readable services.
- Medium for pages without stable endpoints.

Source-health signals:

- Active alert count.
- Gauge timestamp.
- Gauge stale state.
- Forecast issue time.
- API status and parser validity.

Sample item fields:

- `alert_event`
- `weather_zone`
- `river_gauge_id`
- `river_name`
- `stage_value`
- `stage_category`
- `basin`
- `forecast_time`
- `landslide_region`
- `source_url`

Ranking contribution:

- Flood stage, atmospheric river, landslide warnings, and active NWS alerts elevate related road,
  outage, and emergency events.

Later implementation phase:

- R2 for fixtures.
- R6 for NWS live candidate.
- R7 for USGS water and NWRFC research.

### 5. Earthquake, tsunami, and volcano

Why it exists:

- Cascadia seismic, tsunami, and volcano signals are low-frequency but high-impact.
- The dashboard needs official-only treatment, clear thresholds, and short, factual evidence.

First safe sources:

- USGS earthquake GeoJSON.
- USGS earthquake feed pages.
- PNSN recent earthquakes and lists after endpoint verification.
- USGS Cascades Volcano Observatory.
- USGS Volcano Hazards Program.
- Volcanoes.usgs.gov.
- Tsunami.gov.
- WA EMD tsunami page.

Parser/adaptor class:

- `geojson_feed` for USGS earthquake feeds.
- `static_html_headline_candidate` only for official volcano/tsunami pages after selector review.
- `source_health_probe_only` for reference pages.

Likely refresh interval:

- 5 minutes for USGS GeoJSON.
- 15 to 30 minutes for tsunami/volcano official status pages during active events.
- 24 hours for reference pages.

Privacy risk:

- Low.

Policy risk:

- Low for official feeds.
- Medium for pages requiring extraction.

Source-health signals:

- Last event timestamp.
- Feed age.
- GeoJSON schema validity.
- Magnitude threshold coverage.
- Official status text update time.

Sample item fields:

- `event_id`
- `magnitude`
- `depth_km`
- `place`
- `time`
- `felt_count`
- `mmi`
- `volcano_name`
- `alert_level`
- `tsunami_status`
- `source_url`

Ranking contribution:

- Earthquakes above configured magnitude or felt in Puget Sound elevate quickly.
- Tsunami warning/watch/advisory gets critical official severity.
- Volcano unrest is official-only and stays active longer when status remains elevated.

Later implementation phase:

- R2 for USGS fixtures.
- R6 for USGS GeoJSON live candidate.
- R7 for PNSN, tsunami, and volcano sources.

### 6. Utilities and regional outages

Why it exists:

- Power outages, grid disruptions, and utility status can materially affect daily decisions and
  explain emergency, weather, and transport impacts.

First safe sources:

- PSE outage map and outage page.
- SnoPUD outage map and outage center.
- Tacoma Power outage page.
- Seattle City Light outage pages and maps.
- BPA public pages as regional grid context.

Parser/adaptor class:

- `source_health_probe_only` until official data endpoints are identified.
- `arcgis_feature_service_candidate` only for official feature services after verification.
- `static_html_headline_candidate` only for utility pages with stable public notices and policy
  review.

Likely refresh interval:

- 15 minutes for verified official outage data.
- 30 to 60 minutes for source-health references.

Privacy risk:

- Medium because small outage clusters can approximate residential locations.

Policy risk:

- Medium to high until official machine-readable endpoints are identified.

Source-health signals:

- Endpoint verified or not.
- Last map/service update if available.
- Customer count parsed.
- Service territory parsed.
- Parser unsupported reason.

Sample item fields:

- `utility`
- `outage_id`
- `county`
- `service_area`
- `customer_count`
- `started_at`
- `estimated_restore_at`
- `cause`
- `source_url`

Ranking contribution:

- Outages above configured customer threshold or affecting critical regional infrastructure get
  public-impact score.
- Small residential outages receive privacy and low-public-value penalties.

Later implementation phase:

- R2 only if verified fixture endpoint exists.
- R7/R9 for endpoint and dashboard feature-service research.

### 7. Public health and environmental health

Why it exists:

- State and county public-health alerts can have immediate practical value, especially when tied to
  air quality, water, shellfish, disease exposure, heat, cold, or food safety.

First safe sources:

- WA Department of Health homepage, newsroom, and health news archive.
- County public-health pages where emergency alert feeds are found.
- WA Ecology air quality and environmental alerts.
- Puget Sound Clean Air.

Parser/adaptor class:

- `rss_atom` for official feeds if verified.
- `official_api_json` for environmental data APIs.
- `static_html_headline_candidate` for official pages only after review.
- `source_health_probe_only` for reference pages.

Likely refresh interval:

- 60 minutes for official health alert feeds.
- 15 to 30 minutes for AQI during active smoke events.
- 6 to 24 hours for low-priority archives.

Privacy risk:

- Low for public advisories.
- Medium if local exposure notices contain sensitive detail.

Policy risk:

- Low to medium depending on feed/API availability.

Source-health signals:

- Feed timestamp.
- Alert category coverage.
- Agency update time.
- Data station timestamp.

Sample item fields:

- `health_topic`
- `jurisdiction`
- `advisory_type`
- `action_guidance_url`
- `effective_at`
- `expires_at`
- `affected_area`
- `source_url`

Ranking contribution:

- Official advisories with action guidance or multi-county impact get high public-impact score.
- Generic agency news remains low unless convergence or active guidance exists.

Later implementation phase:

- R2 for fixtures.
- R7 for WA DOH, county, Ecology, and AirNow verification.

### 8. Ports, airports, rail, and freight

Why it exists:

- Airport, port, ferry, rail, and freight disruptions can have regional consequences even when the
  source is outside Seattle proper.

First safe sources:

- Port of Seattle and SEA pages.
- SEA flight status and traveler updates.
- SEA checkpoint wait-time page as human reference.
- Port of Tacoma, Everett, Vancouver USA, and Bellingham pages.
- Paine Field, Spokane Airports, PDX, and YVR when relevance rules match.
- FAA/NAS airport status pages and API candidate.
- FAA ASWS repository as documentation/reference only.

Parser/adaptor class:

- `airport_status_json_or_xml` for FAA/NAS if endpoint policy is verified.
- `rss_atom` or `static_html_headline_candidate` for official airport/port news after review.
- `source_health_probe_only` for traveler pages without stable endpoints.

Likely refresh interval:

- 5 to 15 minutes for verified airport operational status.
- 30 to 60 minutes for official port/airport news.

Privacy risk:

- Low for facility status.

Policy risk:

- Low to medium for official pages and APIs.
- Medium for undocumented operational endpoints.

Source-health signals:

- Airport status issue time.
- Feed update time.
- Source status state.
- Parser support state.

Sample item fields:

- `facility`
- `airport_code`
- `port_name`
- `status`
- `delay_type`
- `delay_minutes`
- `ground_stop`
- `checkpoint_wait`
- `cargo_or_marine_impact`
- `source_url`

Ranking contribution:

- Ground stops, major airport delays, port closures, ferry terminal disruptions, and freight impacts
  boost regional public-impact score.

Later implementation phase:

- R2 fixtures for FAA/SEA if endpoint is verified.
- R7/R8 for port and airport feed verification.

### 9. State civic and agency news

Why it exists:

- State government, governor, WSP, AGO, Ecology, and agency announcements sometimes confirm
  emergency declarations, legal orders, health advisories, infrastructure actions, and statewide
  service changes.

First safe sources:

- WA Governor news, releases, and executive orders.
- WSP media and releases.
- WA AGO news and RSS feeds.
- WA Ecology news.
- Data.wa.gov and geo.wa.gov as source discovery/reference surfaces.

Parser/adaptor class:

- `rss_atom` for feed-backed agency pages.
- `static_html_headline_candidate` for official pages only after review.
- `source_health_probe_only` for portals and references.

Likely refresh interval:

- 60 minutes to 6 hours.

Privacy risk:

- Low for general state civic news.
- Medium for WSP incident details if exact locations or victims are present.

Policy risk:

- Low to medium.

Source-health signals:

- Feed timestamp.
- Latest release date.
- Parser support state.
- Staleness by source class.

Sample item fields:

- `agency`
- `release_type`
- `title`
- `published_at`
- `affected_region`
- `topic`
- `source_url`

Ranking contribution:

- Confirms emergency declarations and public-impact official actions.
- Does not outrank operational alerts unless severity and public impact match.

Later implementation phase:

- R2 fixtures for agency feed shapes.
- R8 after higher-priority operational sources.

### 10. Regional news and public media

Why it exists:

- Journalism can explain official signals, provide local context, and surface events before every
  official page is updated.
- It must not become a general regional news archive.

First safe sources:

- Seattle Times feed.
- HeraldNet feed.
- Washington State Standard feed and States Newsroom RSS index.
- KUOW, KNKX, OPB, Cascade PBS.
- KING5 RSS, KIRO7 RSS candidate, KOMO, FOX 13.
- Other regional newspapers only through verified feeds or explicit source policy review.

Parser/adaptor class:

- `rss_atom` preferred.
- `static_html_headline_candidate` only when policy and selectors are explicitly allowed.

Likely refresh interval:

- 30 to 60 minutes.

Privacy risk:

- Low for headline metadata.
- Medium when crime, victims, medical, or exact-address content is present.

Policy risk:

- Medium because publisher terms, paywalls, and syndication require caution.

Source-health signals:

- Feed parse status.
- Latest feed item time.
- Duplicate/syndicated fingerprint rate.
- Policy-blocked status.

Sample item fields:

- `headline`
- `url`
- `canonical_url`
- `published_at`
- `description_bounded`
- `tags`
- `publisher`
- `syndication_hint`

Ranking contribution:

- Adds news/public-media echo to official events.
- Multiple publishers increase convergence only when they are independent source families, not
  duplicated wire copies.

Later implementation phase:

- R2 for fixtures.
- R8 for live RSS after source verification.

### 11. Social/community echoes

Why it exists:

- Community signals can provide early awareness, public sentiment, and eyewitness echo, but they are
  policy-sensitive and must never become primary evidence.

First safe sources:

- Bluesky AT Protocol candidate after policy review.
- Reddit official API or permitted feed access after policy review.
- X official API only if explicitly configured and policy allows.

Parser/adaptor class:

- `manual_review_only` in this design.
- Future compliant API adapters only.

Likely refresh interval:

- Disabled by default.
- If ever enabled, 15 to 60 minutes depending on source terms and rate limits.

Privacy risk:

- High.

Policy risk:

- High.

Source-health signals:

- Policy review state.
- Auth configured state.
- Rate-limit state.
- Storage allowed state.
- Retention rule.

Sample item fields:

- `platform`
- `post_id`
- `author_display_policy`
- `bounded_text`
- `created_at`
- `url`
- `matched_tokens`
- `retention_expires_at`

Ranking contribution:

- Community echo can add weak convergence only after official or news evidence exists.
- Social-only reports must not outrank official sources or be presented as verified fact.

Later implementation phase:

- R10 only.

### 12. Source health and disabled states

Why it exists:

- A disabled or stale REGIONAL layer must be honest. Users need to know whether the absence of
  signals means "nothing known," "disabled," "stale," "policy blocked," or "parser failed."

First safe sources:

- All configured REGIONAL sources, including disabled and manual-review-only entries.

Parser/adaptor class:

- `source_health_probe_only`
- Registry and config validation.

Likely refresh interval:

- Source-health rows update when fixture/live ingest runs.
- Disabled and not-configured states are computed from config without network.

Privacy risk:

- Low.

Policy risk:

- Low, unless health probes perform network in later phases. Page loads must never do that.

Source-health signals:

- State.
- Last success/failure.
- Stale threshold.
- Parser support.
- Policy status.
- Disabled reason.

Sample item fields:

- `source_id`
- `state`
- `last_attempt_at`
- `last_success_at`
- `consecutive_failures`
- `message`
- `evidence_json`

Ranking contribution:

- Stale and failing sources lower confidence.
- Source-health problems can appear as SYSTEM/REGIONAL maintenance items, not public events.

Later implementation phase:

- R1/R2 for registry and fixture-only health.
- R5 for UI states.

## SECTION 9: REGIONAL public-safety and privacy posture

REGIONAL is a public-impact metadata layer, not a private incident monitor. It should prefer
official, public, bounded fields and should minimize amplification of low-value distress.

Rules:

- Store source-provided public metadata only.
- Do not store full narratives from public-safety articles beyond bounded descriptions.
- Do not archive social posts long term.
- Do not surface exact private addresses unless an official source clearly frames the item as a
  public-impact incident.
- Prefer county, route, neighborhood, facility, zone, basin, pass, ferry route, airport, port,
  river gauge, or corridor display.
- Preserve source links in evidence so the user can click through to official sources.
- For major incidents, show public operational facts: event type, source, source family, affected
  county/corridor/zone, public impact, observed time, and source link.
- Treat early official reports as preliminary when the source uses preliminary language or when the
  parser cannot determine final status.
- Do not turn REGIONAL into a fear dashboard, crime ticker, police scanner clone, or wildfire
  obsession surface.
- Low-acuity public-safety data should remain background pulse only unless elevated by official
  severity or independent cross-source convergence.
- Suppress or blur location granularity for residential outages, private medical response,
  low-level police/fire items, and single-household distress.
- Keep social/community metadata disabled by default and short-retention if ever enabled.
- Never infer identities, victim status, private addresses, personal attributes, or blame from
  source metadata.
- Never use LLMs to summarize sensitive incident narratives in runtime behavior.

Default display posture:

| Source shape | Display location | Retention posture | Elevation rule |
| --- | --- | --- | --- |
| Official statewide alert | County/zone/corridor | Expiration plus 24 hours | Elevate by severity. |
| County emergency alert | County/city/zone | Expiration plus 24 hours | Elevate if action guidance or broad impact exists. |
| Transportation closure | Route/pass/ferry/facility | 3 to 7 days | Elevate by closure, delay, route priority, or convergence. |
| Wildfire/smoke | Incident/county/region/AQI station | 7 to 14 days while active | Elevate by acres, evacuation, smoke, AQI, or closures. |
| Utility outage | Service area/county | 3 to 7 days | Elevate only above configured customer or infrastructure threshold. |
| Regional news headline | Publisher headline metadata | 7 days | Elevate only with public impact or convergence. |
| Social/community echo | Platform/link only if allowed | 24 to 72 hours max | Never primary; weak echo only. |

## SECTION 10: REGIONAL source freshness and retention

REGIONAL is a recent-signal layer with short retention. It is not an archive. Every future ingest
run must purge expired data before or after writing new rows, and purge evidence must be visible in
source-health or SYSTEM evidence.

Default candidate retention:

| Data class | Candidate retention | Notes |
| --- | --- | --- |
| Raw fetch diagnostics | 7 days or less | Status, timing, byte counts, and parser outcome only. |
| Raw payload debug | Disabled by default; 6 hours max if enabled | Must never be enabled in `config.example.yml`. |
| Official alert metadata | Expiration plus 24 hours | If no expiration exists, use 7 days max. |
| Transportation/ferry/pass disruption metadata | 3 to 7 days | Longer only for unresolved disruptions. |
| Weather/hazard metadata | Expiration plus 24 to 48 hours | Active hazards stay until expiration plus grace window. |
| Wildfire/smoke metadata | 7 to 14 days while active, then expire | Keep active incident evidence bounded. |
| Earthquake metadata | 7 days for small regional events, 14 days for felt/significant events | Threshold-driven. |
| Volcano unrest metadata | 14 days while active, official-only | Do not keep stale unofficial chatter. |
| News headline metadata | 7 days | Metadata only, no article body archive. |
| Regional event clusters | 7 to 14 days | Same or slightly longer than member items. |
| Source health | 30 days | Enough for local troubleshooting. |
| Ranking explanations | Same as item/event retention | Ranking evidence should expire with the row. |
| Social metadata, if ever enabled | 24 to 72 hours unless terms require shorter or prohibit storage | Disabled by default. |

Freshness classes:

| Class | Meaning | Display behavior |
| --- | --- | --- |
| `fresh` | Source item is inside normal update window. | Eligible for normal ranking. |
| `active_but_older` | Item is older but source says it is still active or unexpired. | Eligible with active-alert score and age disclosure. |
| `stale_source` | Source has not updated within `stale_after_minutes`. | Lower confidence and show source-health warning. |
| `expired` | Item passed expiration/retention cutoff. | Purge or hide. |
| `debug_only` | Retained only for source-health/debug evidence. | Never show as live public event. |

No article body archive, no permanent regional incident archive, and no permanent social archive are
allowed.

## SECTION 11: Adapter design for REGIONAL

The adapter layer should normalize source-specific records into a shared item/event input shape
without fetching article bodies, crawling, or making page-load network requests. Adapters should be
pure parser/normalizer units in early phases and should run against local fixtures before any live
source is enabled.

Shared adapter output fields:

```yaml
normalized_item:
  source_id: "nws_active_alerts_wa"
  source_family: "nws"
  source_class: "official_weather_hazard"
  scope: "REGIONAL"
  title: "Winter Storm Warning"
  url: "https://..."
  canonical_url: "https://..."
  published_at: "2026-01-01T12:00:00Z"
  observed_at: "2026-01-01T12:01:00Z"
  expires_at: "2026-01-02T12:00:00Z"
  description_bounded: "Short source-provided description."
  event_type_hint: "weather_alert"
  geography:
    counties: ["King", "Kittitas"]
    corridors: ["I-90", "Snoqualmie Pass"]
    zones: ["WAZ..."]
  severity:
    source_severity: "Warning"
    normalized: "major"
  policy:
    body_fetched: false
    source_terms_reviewed: false
    homepage_extractor_used: false
  evidence:
    parser: "nws_alerts_json_v1"
    fixture: true
```

Adapter families:

`rss_atom`

- Targets: WSDOT blog if feed verified, Metro RSS, regional news/blog feeds, public media feeds,
  and county alert RSS where available.
- Must parse title, URL, canonical URL when available, published timestamp, bounded description,
  categories, tags, and feed source.
- Must bound description length.
- Must not fetch article bodies.
- Must fail soft on malformed feeds.
- Must produce duplicate fingerprints for syndicated articles.

`wordpress_feed_candidate`

- Targets: WordPress-backed county emergency pages and blogs where feed URLs are confirmed.
- Should prefer feed endpoints over homepage extraction.
- Must record whether the feed endpoint was verified later.
- Must not guess undocumented feed URLs as live enabled sources without verification.

`official_api_json`

- Targets: NWS alerts, WSDOT Traveler API, WSF API after access-code review, NWRFC or NOAA
  endpoints if verified, Ecology or AirNow APIs if configured, and FAA/NAS airport status.
- Must support timeouts, response size caps, source-specific rate limits, conditional requests when
  available, schema validation, and per-source fail-soft behavior.
- Must preserve official IDs, issue/update times, expiration times, status, severity, and source
  URLs.

`open511_json`

- Targets: DriveBC Open511 and ODOT TripCheck only if endpoint terms and access permit.
- Must be disabled by default and region-filtered.
- Must mark Oregon/BC relevance basis in evidence.

`geojson_feed`

- Targets: USGS earthquake GeoJSON and possible wildfire or ArcGIS feature layers if verified.
- Must support bounding boxes, magnitude/severity filters, feature IDs, geometry handling,
  source-provided update times, and provenance.
- Must reduce display location precision where appropriate.

`hydrology_api_json`

- Targets: USGS Water Data APIs and NWRFC candidates if machine-readable endpoints are verified.
- Must support gauge allowlists, river-basin filters, stage category mapping, stale gauge detection,
  and flood-stage evidence.

`arcgis_feature_service_candidate`

- Targets: WA DNR wildfire dashboard underlying layers, WA Ecology layers, and outage dashboards
  only if official feature services are found.
- Must not screen scrape ArcGIS dashboard HTML.
- Must record service URL, layer ID, field mapping, geometry policy, paging limits, query filters,
  and source ownership evidence.
- Must stay `manual_review_only` or `source_health_probe_only` until verified.

`cap_alerts`

- Targets: NWS CAP or API alert records if useful.
- Must preserve severity, urgency, certainty, effective time, expiration, affected area, source
  instruction URL, and alert ID.

`static_html_headline_candidate`

- Targets: official pages or regional news pages with no RSS/API.
- Disabled unless homepage extractor support is explicitly allowed in future config.
- Must use per-source selectors, no recursive crawling, no article-body fetch, payload size caps,
  robots/policy review, and source-health evidence.

`source_health_probe_only`

- Targets: maps, dashboards, portals, source docs, and registration pages useful as human status
  references but not suitable for ingestion.
- Page loads must not run probes. Probes, if ever implemented, run only in explicit ingest/source
  health commands.

`manual_review_only`

- Targets: policy-sensitive, parser-risky, login-required, unclear, social, or source-terms-sensitive
  sources.
- These sources can exist in registry and docs but cannot produce live items.

## SECTION 12: Candidate regional source registry example

Do not edit `config.example.yml` for this design pass. A later implementation can add disabled
examples after the common news/registry configuration exists. The candidate shape below is
intentionally disabled by default.

```yaml
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
```

Config validation rules for later:

- `regional_sources.enabled` defaults to `false`.
- Every source defaults to `enabled: false`.
- Unknown source classes, adapters, verification statuses, and source families are rejected.
- Social source IDs are rejected unless `allow_social_sources` is explicitly true.
- Homepage extraction is rejected unless a future `allow_homepage_extractors` flag is true.
- Oregon and BC sources are rejected unless relevance flags are enabled and relevance evidence is
  produced.
- Secrets must not appear in `config.example.yml`; access tokens should be read from local runtime
  config or environment only if a future adapter explicitly needs them.

## SECTION 13: REGIONAL UI architecture

Do not implement the UI in this task. The eventual REGIONAL page should use the existing
console-1701 style and template conventions, but it should show honest source-backed states rather
than placeholders or fake headlines.

Proposed bays:

### Bay 1: Regional attention now

Purpose:

- Show the highest-ranking REGIONAL events only.
- Answer "what might matter right now around Washington / PNW?"

Required row content:

- Title.
- Event type.
- Representative source.
- Source-family badges.
- Official/news/community convergence badges.
- Observed time.
- Last seen time.
- Ranking reason.
- Geographic label.
- Evidence affordance.

Rules:

- Must show why each item is ranked.
- Must not dump raw low-impact incidents.
- Must identify official confirmation versus news echo versus community echo.
- Must show stale-source or partial-evidence warnings when relevant.

### Bay 2: Hazards and emergency

Purpose:

- Show WA EMD, county emergency pages, NWS, NWRFC, WA DNR, NWCC, USGS, PNSN, Ecology, AirNow, and
  related official hazard signals.

Required behavior:

- Active official alerts first.
- Wildfire, smoke, flood, earthquake, tsunami, volcano, landslide, air-quality, and public-health
  signals grouped by event type.
- Source freshness visible.
- Expired hazards hidden or clearly marked as retained for evidence only.

### Bay 3: Movement and infrastructure

Purpose:

- Show "will this affect getting around, power, travel, freight, airport, ferry, or region-wide
  operations?"

Sources:

- WSDOT.
- WSF.
- Passes.
- Bridges.
- Highways.
- Border crossings.
- Transit.
- Ports.
- Airports.
- Utilities.

Required behavior:

- Prioritize closure, cancellation, delay, outage, and facility status.
- Show route/pass/ferry/airport/port labels prominently.
- Link transport items to hazard events when convergence exists.

### Bay 4: Regional press and civic pulse

Purpose:

- Show source-backed regional news/public-media/civic context only when configured and policy
  allows.

Sources:

- Washington State Standard.
- KUOW.
- KNKX.
- OPB.
- Cascade PBS.
- Seattle Times.
- Herald.
- Tacoma News Tribune.
- Spokesman.
- KING5.
- KIRO.
- KOMO.
- FOX 13.
- Future configured sources.

Required behavior:

- No fake headlines.
- If disabled, show "REGIONAL news sources not configured."
- Social/community signals only if configured, compliant, and short-retention.
- Publisher metadata only; no article bodies.

Shared empty states:

- REGIONAL recent-signal layer disabled.
- REGIONAL sources not configured.
- REGIONAL sources configured but disabled.
- REGIONAL sources configured but never scanned.
- REGIONAL sources stale.
- REGIONAL source policy blocked.
- REGIONAL parser failed.
- REGIONAL social sources disabled by policy.
- REGIONAL homepage extraction disabled by policy.

## SECTION 14: Evidence model for REGIONAL

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
- Geographic match basis.
- Public impact basis.
- Source diversity basis.
- Privacy redaction decision.
- Retention expiration.
- Matching tokens.
- Event type.
- Event confidence.
- Policy notes.

Hazard-specific evidence should include where available:

- Alert severity.
- Urgency.
- Certainty.
- Effective time.
- Expiration time.
- Affected zones.
- County.
- Route.
- River gauge.
- AQI station.
- Fire name.
- Fire size.
- Containment.
- Evacuation level.
- Earthquake magnitude.
- Earthquake depth.
- Volcano alert level.
- Tsunami status.
- Source instructions URL.

Transport-specific evidence should include where available:

- Route.
- Direction.
- Pass.
- Ferry route.
- Terminal.
- Airport.
- Port.
- Start time.
- End time.
- Delay estimate.
- Closure status.
- Detour note.
- Source update time.

Candidate evidence shape:

```json
{
  "event_type": "mountain_pass_closure",
  "event_confidence": "high",
  "source_ids": ["wsdot_traveler_api", "nws_active_alerts_wa", "king5_rss"],
  "source_families": ["wsdot", "nws", "local_tv"],
  "source_classes": ["official_transport", "official_weather_hazard", "local_tv_radio"],
  "official_source_count": 2,
  "news_echo_count": 1,
  "community_echo_count": 0,
  "geographic_match_basis": {
    "corridors": ["I-90", "Snoqualmie Pass"],
    "counties": ["King", "Kittitas"],
    "weather_zones": ["candidate_zone_id"]
  },
  "ranking_features": {
    "recency_score": 18,
    "official_severity_score": 30,
    "source_diversity_score": 16,
    "public_impact_score": 28,
    "geographic_relevance_score": 24,
    "privacy_penalty": 0,
    "stale_source_penalty": 0
  },
  "privacy": {
    "exact_private_address_suppressed": true,
    "display_granularity": "corridor"
  },
  "retention": {
    "expires_at": "2026-01-08T00:00:00Z"
  },
  "policy_notes": [
    "No article bodies fetched.",
    "No social sources used."
  ]
}
```

## SECTION 15: Source health for REGIONAL

Source health is part of the feature, not a debugging afterthought. The UI and SYSTEM evidence must
tell the user when REGIONAL is disabled, stale, unsupported, or policy blocked.

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
| `evidence_json` | Parser, policy, config, and source-health details. |

Health rules:

- Disabled sources are not failures.
- Manual-review-only sources are not failures.
- Auth-required sources must not prompt for secrets in the UI.
- Rate-limited sources back off and preserve the last known source health.
- Parser failures should never crash unrelated sources.
- Page rendering must read stored health only and must not fetch.
- SYSTEM should eventually summarize stale, failing, disabled, policy-blocked, and manual-review
  source counts.

## SECTION 16: First implementation sequence for REGIONAL

Phase R0: this design

- Create this design doc.
- Update BACKLOG.
- No runtime behavior change.
- No network.
- No collectors.

Phase R1: source registry scaffolding

- Add disabled REGIONAL source config.
- Add source registry schema or shared news source tables if not already provided by the global
  architecture work.
- Add tests proving REGIONAL is disabled by default.
- Add enum validation for source class, adapter, verification status, and source health state.
- No network.

Phase R2: local fixtures only

- Create fixture files for NWS active alert JSON for Washington.
- Create WSDOT travel alert JSON fixture.
- Create WSF bulletin/API fixture.
- Create WA DNR wildfire fixture.
- Create NWCC RSS/Atom fixture if feed is verified later.
- Create USGS earthquake GeoJSON fixture.
- Create USGS water API fixture.
- Create King County emergency WordPress feed fixture.
- Create Ecology AQI fixture.
- Create regional news RSS fixture.
- Create PSE outage fixture only if a source endpoint is verified later.
- Parse fixtures only.
- Store normalized metadata.
- Update fixture source health.
- No live fetch.

Phase R3: REGIONAL event correlation

- Implement deterministic token/location/time matching.
- No LLM.
- Tests for convergence.
- Tests for duplicate suppression.
- Tests for source-family diversity.
- Tests for route, pass, ferry, county, basin, weather-zone, and facility matching.

Phase R4: REGIONAL ranking

- Implement the scoring model.
- Explain ranking in JSON.
- Tests for official severity, source diversity, recency, public impact, out-of-region penalty,
  stale-source penalty, privacy penalty, and duplicate-family penalty.

Phase R5: REGIONAL UI disabled and fixture-backed states

- Replace REGIONAL placeholders with honest disabled/not-configured/source-health states.
- Fixture-backed rows can be used in tests only.
- No live fetch.
- No fake headlines.

Phase R6: official API/RSS live fetch, opt-in only

- Start with one safe official source at a time.
- Suggested first candidates: NWS alerts for Washington, WSDOT Traveler API, USGS earthquake
  GeoJSON, and King County Emergency News feed if valid.
- Must be disabled by default.
- Must run through an explicit ingest command or separate disabled timer, not page load.
- Must use timeouts, size caps, source intervals, conditional requests when available, and fail-soft
  behavior.

Phase R7: additional official sources

- WA DNR wildfire source only after official endpoint verification.
- NWRFC/USGS water after endpoint/filter design.
- WSF API after access-code/auth handling is designed.
- Ecology/AirNow after endpoint and policy review.
- County emergency sources after feed verification.
- Utility sources after endpoint verification.

Phase R8: regional news RSS

- Publisher feeds only.
- Store metadata only.
- No article bodies.
- No paywall bypass.
- Detect duplicate/syndicated stories.
- Keep disabled by default.

Phase R9: official dashboards and ArcGIS research

- WA DNR dashboard, outage maps, and other dashboards only through official feature services if
  found.
- No HTML dashboard scraping.
- If no official data endpoint is found, keep `source_health_probe_only` or `manual_review_only`.

Phase R10: social/community

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

- REGIONAL disabled by default.
- Source disabled by default.
- Invalid source class rejected.
- Invalid adapter rejected.
- Invalid verification status rejected.
- Social source rejected unless `allow_social_sources` is true.
- Homepage extraction rejected unless `allow_homepage_extractors` is true.
- Oregon/BC sources rejected unless `include_oregon_when_relevant` or
  `include_bc_when_relevant` is true.
- Source without URL rejected unless adapter supports no URL.
- Secrets not allowed in `config.example.yml`.

Registry tests:

- Source keys unique.
- Source family valid.
- Source class valid.
- Verification status valid.
- Retention settings valid.
- Geography filters valid.
- Corridor filters valid.
- Source priority bounded.
- Refresh intervals bounded.

Parser fixture tests:

- NWS alert JSON fixture parses.
- WSDOT travel alert fixture parses.
- WSF bulletin fixture parses.
- USGS earthquake GeoJSON fixture parses.
- USGS water API fixture parses.
- WA DNR wildfire fixture parses after endpoint shape is verified.
- King County emergency feed fixture parses.
- Regional news RSS fixture parses.
- Malformed feed fails soft.
- Oversized payload blocked or truncated.
- Timestamps normalize deterministically.
- Descriptions are bounded.

Privacy tests:

- Routine local police/fire item does not elevate to REGIONAL.
- Exact private address suppressed unless official public-impact incident.
- Social-only vague report does not outrank official alert.
- State/county public-health alert shows official source and action URL, not invented advice.
- Residential utility outage below threshold is hidden or low-priority.

Correlation tests:

- WSDOT pass closure plus NWS winter storm warning plus regional news becomes one event.
- WA DNR wildfire plus NWS red flag plus Ecology smoke/AQI plus news becomes one event.
- Same event from multiple news outlets counts as news-family convergence but not endless duplicate
  inflation.
- Same source repeated does not inflate source diversity.
- Different source families increase diversity.
- Route/county mismatch prevents false merge.
- Out-of-region Oregon/BC item appears only if relevant to configured REGIONAL rules.

Ranking tests:

- Official severe weather warning outranks generic news.
- Major pass closure outranks minor local road incident.
- WSF route shutdown outranks small local traffic delay.
- Large wildfire with evacuation and smoke impact outranks generic wildfire article.
- Earthquake above threshold near Puget Sound outranks small distant quake.
- Regional outage above customer threshold outranks single small outage.
- Stale source lowers confidence.
- Source policy blocked item never displays as live.
- Duplicate syndicated articles do not create fake independent confirmation.

API design tests for later:

- GET routes read SQLite only.
- GET routes do not fetch network.
- Disabled, not-configured, stale, failing, manual-review-only, policy-blocked, and parser-failed
  states remain distinct.

UI tests for later:

- No fake headlines.
- Empty states clear.
- Evidence visible.
- Ranking reason visible.
- Source health visible.
- Geographic label visible.
- Social disabled state visible.
- Homepage extraction disabled state visible.

Safety tests:

- No page-load external fetches.
- No hidden LLM calls.
- No telemetry.
- No package install.
- No sudo.
- No social fetch unless explicitly configured.
- No source target curl/live verification in fixture tests.

## SECTION 18: Backlog update requirements

`BACKLOG.md` must include a section named `REGIONAL Pacific Northwest Recent Signal Layer`. Every
REGIONAL backlog item added for this design must say `Status: not implemented.` Future tasks should
be concrete enough for a later agent to implement without reading chat history.

The required backlog work areas are:

- REGIONAL source registry design implemented from this document.
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
- No exact-address amplification for low-value private incidents.
- No scraping behind login.
- No bypassing Reddit, X, API, auth, rate-limit, paywall, or bot-control restrictions.
- No claiming social chatter is verified fact.
- No treating unofficial aggregators as official.
- No treating duplicate articles as independent confirmation.
- No turning REGIONAL into a fear dashboard.
- No burying LOCAL urgent items under REGIONAL headlines.
- No importing Oregon or BC content unless regional relevance rules allow it.
- No adding dependencies.
- No API keys or secrets in the repo.
- No scheduled REGIONAL ingest until a separate disabled-by-default timer/command is designed.

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
6. Confirmation that REGIONAL remains disabled by default.
7. Test commands run and exact results.
8. `git diff --check` result.
9. `git status --short`.
10. BACKLOG entries added.
11. Uncertainties and source targets needing later verification.

Do not commit, push, install packages, run sudo, fetch live external sites, or curl source targets
for this task.
