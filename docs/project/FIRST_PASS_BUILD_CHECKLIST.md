# Recent Signal First-Pass Build Checklist

Status: frozen selection, 2026-10-15. This is the Goal completion target.

## Baseline and counting

- Source of truth: `BACKLOG.md` at the 2026-10-15 starting point.
- Open or partial entries at freeze: **202**.
- First-pass entries selected below: **150**.
- Recent Signal entries deferred below: **45**.
- Host-console entries outside this Recent Signal Goal: **7**.
- The selection is a work boundary, not a claim that the deferred entries are done.
- Keep backlog status authoritative as implementation proceeds. Do not remove a selected row or mark it complete without evidence.

## Completion rule

Each selected row needs working implementation, relevant verification, and a matching `BACKLOG.md` status update. A partial row remains open until its first-pass acceptance is met. Use the existing design and source-verification documents for acceptance details. Preserve disabled-by-default behavior, exact official-source allowlists, privacy rules, and no page-load/host-scan/test fetches. Unsupported live sources must remain visibly disabled.

## Selected first-pass work

### Scoped Recent Signal / News Ingestion

- [ ] **RS-001** [Deterministic Ranking](../../BACKLOG.md#L161) — partially implemented.
- [ ] **RS-002** [Official API/RSS First Live Ingest](../../BACKLOG.md#L206) — partially implemented.
- [ ] **RS-003** [Documentation Update](../../BACKLOG.md#L251) — partially implemented.

### LOCAL Seattle Recent Signal Layer

- [x] **RS-004** [LOCAL Source Registry Design Implementation](../../BACKLOG.md#L282) — all 119 design entries disabled, validated, inherited by config, and synced to SQLite; reference entries cannot ingest.
- [x] **RS-005** [LOCAL SQLite Schema Or Extension](../../BACKLOG.md#L310) — local events, ranking JSON, scoped family/impact indexes, item/source health, and expiry purge verified.
- [x] **RS-006** [FAA/SEA Airport Status Research](../../BACKLOG.md#L393) — official NAS XML endpoint, active-event shape, public access, and Port page-only limits documented; live parser remains in RS-011/RS-044.
- [x] **RS-007** [LOCAL Deterministic Ranking](../../BACKLOG.md#L461) — all first-pass factors and reasons are stored; NWS active-window and older-alert ranking is verified.
- [x] **RS-008** [LOCAL Privacy Redaction Rules](../../BACKLOG.md#L482) — supported SFD/SPD parsers redact private addresses before storage and rank isolated minor incidents down.
- [x] **RS-009** [LOCAL Source Health States](../../BACKLOG.md#L511) — all first-pass source/scope states are derived and visible in LOCAL and SYSTEM; offline matrix coverage added.
- [x] **RS-010** [LOCAL Evidence Drawer Contract](../../BACKLOG.md#L527) — item drawer and event API expose provenance, ranking, redaction, matching, geography, confidence, policy, and retention evidence.
- [x] **RS-011** [LOCAL Official-Source Live Ingest Phase](../../BACKLOG.md#L546) — one verified NWS Washington feed works through explicit, opt-in, bounded `news-scan`; other candidates require separate signoff.
- [x] **RS-012** [Documentation For Source Verification](../../BACKLOG.md#L588) — shared signoff record, release gate, worked NWS example, and blocked FAA/NAS example linked.

### REGIONAL Pacific Northwest Recent Signal Layer

- [x] **RS-013** [REGIONAL Source Registry Design Implementation](../../BACKLOG.md#L620) — all 224 design rows plus six existing candidates disabled, validated, inherited by config, and synced to SQLite.
- [x] **RS-014** [Disabled-By-Default REGIONAL Config](../../BACKLOG.md#L634) — validated geography/topic flags and explicit social/homepage gates; defaults remain off.
- [x] **RS-015** [REGIONAL SQLite Schema Or Extension](../../BACKLOG.md#L649) — scoped clusters, ranking JSON, official geography facets, indexed queries, and expiry purge verified.
- [ ] **RS-016** [REGIONAL Fixture Pack](../../BACKLOG.md#L665) — partially implemented.
- [x] **RS-017** [NWS Alert Parser For Washington](../../BACKLOG.md#L682) — dedicated WA/OR fixture, official county/zone evidence, configurable filters, and offline scan verified.
- [x] **RS-018** [WSDOT Traveler API Fixture Parser](../../BACKLOG.md#L697) — documented WSDOT JSON shape, roadway and WCF time evidence, status/ranking, and offline scan verified; authenticated live JSON held.
- [x] **RS-019** [USGS Earthquake GeoJSON Parser](../../BACKLOG.md#L738) — official GeoJSON identity, bounded geography/magnitude/radius, event evidence, and fixture scan verified.
- [x] **RS-020** [King County Emergency Feed Parser](../../BACKLOG.md#L787) — official RSS source, bounded item parser, classification/ranking and offline scan verified; live ingest disabled.
- [x] **RS-021** [County Emergency Alert Source Verification](../../BACKLOG.md#L795) — eight county access paths, feed candidates, risks and fallbacks recorded; no live feed enabled.
- [ ] **RS-022** [REGIONAL Deterministic Event Correlation](../../BACKLOG.md#L816) — partially implemented.
- [ ] **RS-023** [REGIONAL Deterministic Ranking](../../BACKLOG.md#L831) — partially implemented.
- [ ] **RS-024** [REGIONAL Privacy And Public-Impact Rules](../../BACKLOG.md#L846) — not implemented.
- [x] **RS-025** [REGIONAL UI Disabled States](../../BACKLOG.md#L855) — page/API state matrix and scope-specific social/homepage blocked messaging verified without fetch.
- [x] **RS-026** [REGIONAL Source Health States](../../BACKLOG.md#L869) — implemented; REGIONAL API/page state matrix test passes.
- [ ] **RS-027** [REGIONAL Evidence Drawer Contract](../../BACKLOG.md#L883) — partially implemented.
- [ ] **RS-028** [REGIONAL Official-Source Live Ingest Phase](../../BACKLOG.md#L898) — partially implemented.
- [x] **RS-029** [Documentation For Source Verification](../../BACKLOG.md#L942) — shared signoff/release gate and REGIONAL geography, privacy and fallback checks linked to worked decisions.
- [x] **RS-030** [Tests For No Page-Load External Fetches](../../BACKLOG.md#L955) — REGIONAL/SYSTEM state matrix and opt-in HTTP GET no-fetch regression verified.

### NATIONAL United States Recent Signal Layer

- [x] **RS-031** [NATIONAL Source Registry Design Implementation](../../BACKLOG.md#L973) — 227 disabled design entries, validated metadata, config defaults, SQLite sync, and summary.
- [x] **RS-032** [Disabled-By-Default NATIONAL Config](../../BACKLOG.md#L982) — validated national policy tree, separate scope gate, social-source rejection, and disabled defaults.
- [x] **RS-033** [NATIONAL SQLite Schema Or Extension](../../BACKLOG.md#L993) — scoped storage, agency/sector/state indexed facets, migration backfill and expiry purge verified.
- [ ] **RS-034** [NATIONAL Fixture Pack](../../BACKLOG.md#L1003) — not implemented.
- [x] **RS-035** [NWS Active Alert Parser](../../BACKLOG.md#L1012) — fixture parser preserves national alert geography, timing, instruction, and ranking evidence; focused tests pass.
- [ ] **RS-036** [NHC Advisory/Feed Verification](../../BACKLOG.md#L1020) — partial: official feed ownership/endpoints and advisory semantics documented; actual XML item shape remains unverified.
- [ ] **RS-037** [USGS Earthquake GeoJSON Parser](../../BACKLOG.md#L1028) — partial: national coordinate regions, threshold, and fixture ingest work; nuanced cross-border and multi-state impact routing remains.
- [ ] **RS-038** [FEMA/OpenFEMA Disaster Declarations Research](../../BACKLOG.md#L1037) — not implemented.
- [ ] **RS-039** [CDC HAN Parser](../../BACKLOG.md#L1046) — not implemented.
- [ ] **RS-040** [FDA Recall Endpoint/Feed Verification](../../BACKLOG.md#L1055) — not implemented.
- [ ] **RS-041** [FSIS Recall API Parser](../../BACKLOG.md#L1064) — not implemented.
- [ ] **RS-042** [CPSC Recalls API Parser](../../BACKLOG.md#L1072) — not implemented.
- [ ] **RS-043** [NHTSA Recalls API Parser](../../BACKLOG.md#L1080) — not implemented.
- [ ] **RS-044** [FAA NAS Status Fixture Parser](../../BACKLOG.md#L1088) — not implemented.
- [ ] **RS-045** [CISA Advisory Parser](../../BACKLOG.md#L1097) — not implemented.
- [ ] **RS-046** [CISA KEV Endpoint Research](../../BACKLOG.md#L1106) — not implemented.
- [ ] **RS-047** [Federal Register API Parser With Filters](../../BACKLOG.md#L1114) — not implemented.
- [ ] **RS-048** [GovInfo RSS Parser](../../BACKLOG.md#L1122) — not implemented.
- [ ] **RS-049** [NATIONAL Deterministic Event Correlation](../../BACKLOG.md#L1155) — not implemented.
- [ ] **RS-050** [NATIONAL Deterministic Ranking](../../BACKLOG.md#L1165) — not implemented.
- [ ] **RS-051** [NATIONAL Low-Public-Value And Public-Impact Rules](../../BACKLOG.md#L1175) — not implemented.
- [x] **RS-052** [NATIONAL UI Disabled States](../../BACKLOG.md#L1185) — shared NATIONAL page shows verified disabled/failure states without fake items or fetch.
- [x] **RS-053** [NATIONAL Source Health States](../../BACKLOG.md#L1194) — shared health and NATIONAL page/API state matrix verified without fetch.
- [ ] **RS-054** [NATIONAL Evidence Drawer Contract](../../BACKLOG.md#L1203) — not implemented.
- [ ] **RS-055** [NATIONAL Official-Source Live Ingest Phase](../../BACKLOG.md#L1213) — not implemented.
- [ ] **RS-056** [Documentation For Source Verification](../../BACKLOG.md#L1240) — partially implemented.
- [x] **RS-057** [Tests For No Page-Load External Fetches](../../BACKLOG.md#L1253) — NATIONAL/SYSTEM GET and state regressions run without scan, fixture read, or official HTTP fetch.
- [x] **RS-058** [Tests For No API-Key Source Running Without Config](../../BACKLOG.md#L1261) — known key-based candidates and a custom auth source fail before fixture/HTTP access with `auth_required` health.

### GLOBAL World Recent Signal Layer

- [x] **RS-059** [GLOBAL Source Registry Design Implementation](../../BACKLOG.md#L1275) — 172 disabled design entries, enum validation, config defaults, SQLite sync, and summary.
- [x] **RS-060** [Disabled-By-Default GLOBAL Config](../../BACKLOG.md#L1285) — validated inclusion/attention flags and explicit social, auth, heavy-data, homepage, conflict gates.
- [x] **RS-061** [GLOBAL SQLite Schema Or Extension](../../BACKLOG.md#L1296) — scoped registry/cluster/item storage plus indexed geography, event, family, impact and sensitivity facets; migration, refresh, expiry and purge verified.
- [ ] **RS-062** [GLOBAL Fixture Pack](../../BACKLOG.md#L1306) — partial: GDACS RSS/API, ReliefWeb disaster/report, and WHO DON fixtures with offline scan tests; other families/states pending.
- [x] **RS-063** [GDACS Feed Parser](../../BACKLOG.md#L1316) — official RSS shape verified; dedicated GLOBAL parser, evidence, fixture, and scan persistence test.
- [x] **RS-064** [GDACS API Fixture Parser](../../BACKLOG.md#L1324) — official Search GeoJSON shape verified; dedicated GLOBAL parser, evidence, fixture, and scan persistence test.
- [x] **RS-065** [ReliefWeb Disasters API Parser](../../BACKLOG.md#L1332) — documented v2 fixture contract, metadata-only parser, offline persistence and appname gate tests; live response unverified.
- [x] **RS-066** [ReliefWeb Reports API Parser](../../BACKLOG.md#L1340) — explicit active-disaster/source/theme filters, cap, short expiry, metadata-only fixture ingest; live blocked.
- [x] **RS-067** [WHO Disease Outbreak News Parser](../../BACKLOG.md#L1349) — official OData shape/article verified, bounded summary and cautious label evidence, offline scan test.
- [x] **RS-068** [ECDC RSS Parser](../../BACKLOG.md#L1358) — official news RSS shape and endpoint verified; bounded metadata parser, optional category, offline scan, and cautious impact labels.
- [x] **RS-069** [WMO CAP Warning Source Verification](../../BACKLOG.md#L1366) — official directory, BoM RSS/CAP 1.2 shape, and DWD channel checked; dashboard/directory remain reference-only with no ingest.
- [x] **RS-070** [USGS Global Earthquake GeoJSON Parser](../../BACKLOG.md#L1374) — official summary shape verified; GLOBAL filters, cautious place evidence, offline fixture ingest, and ranking tests.
- [x] **RS-071** [NHC RSS Parser](../../BACKLOG.md#L1382) — verified basin RSS shapes; fixture parser keeps explicit storm/advisory evidence, skips inactive/outlook items, and remains offline.
- [ ] **RS-072** [Smithsonian GVP Weekly Report Parser](../../BACKLOG.md#L1390) — official RSS URL found; direct feed access returned HTTP 403, so XML shape and parser remain open.
- [x] **RS-073** [UN News RSS Parser](../../BACKLOG.md#L1407) — exact official RSS shape and story GUID verified; bounded fixture parser, narrow low-value exclusions, and offline scan.
- [ ] **RS-074** [UN Press RSS Parser](../../BACKLOG.md#L1415) — not implemented.
- [ ] **RS-075** [IAEA RSS Parser](../../BACKLOG.md#L1423) — not implemented.
- [ ] **RS-076** [Humanitarian Source Evidence Contract](../../BACKLOG.md#L1432) — not implemented.
- [ ] **RS-077** [Conflict-Humanitarian Sensitivity Rules](../../BACKLOG.md#L1441) — not implemented.
- [ ] **RS-078** [GLOBAL Deterministic Event Correlation](../../BACKLOG.md#L1485) — partial: structured identity/context matching, complete-link bridge guard, family dedupe, and auditable cluster evidence; source-specific parser/fixture coverage remains.
- [x] **RS-079** [GLOBAL Deterministic Ranking](../../BACKLOG.md#L1494) — bounded event factors/reasons, stored scores, and tests across every named first-pass factor.
- [ ] **RS-080** [GLOBAL Low-Public-Value, Rumor, And Public-Impact Rules](../../BACKLOG.md#L1504) — partial: explicit policy-tag penalties and first-pass official-impact boosts; classification/suppression coverage remains.
- [x] **RS-081** [GLOBAL UI Disabled States](../../BACKLOG.md#L1515) — honest GLOBAL state matrix, complete source-health overflow list, and expired-content hiding.
- [x] **RS-082** [GLOBAL Source Health States](../../BACKLOG.md#L1525) — configured health states surfaced on GLOBAL and SYSTEM and verified across transition and gate cases.
- [ ] **RS-083** [GLOBAL Evidence Drawer Contract](../../BACKLOG.md#L1535) — partial: item and event payloads/drawers now include matching, score factors, public-impact basis, and penalties; wider source-specific coverage remains.
- [ ] **RS-084** [GLOBAL Official-Source Live Ingest Phase, Disabled By Default](../../BACKLOG.md#L1545) — not implemented.
- [ ] **RS-085** [Documentation For Source Verification](../../BACKLOG.md#L1581) — partially implemented.
- [x] **RS-086** [Tests For No Page-Load External Fetches](../../BACKLOG.md#L1596) — GLOBAL/SYSTEM/API GETs trapped across unstarted, stored-health, and gated-source states.
- [x] **RS-087** [Tests For No Heavy Source Running Without Explicit Config](../../BACKLOG.md#L1605) — all 20 heavy registry candidates blocked before file/network access.
- [x] **RS-088** [Tests For No Token/Account Source Running Without Config](../../BACKLOG.md#L1613) — known auth/account/social candidates blocked before file/network access.

### ORBITAL Space Recent Signal Layer

- [ ] **RS-089** [ORBITAL Source Registry Design Implementation](../../BACKLOG.md#L1627) — not implemented.
- [ ] **RS-090** [Disabled-By-Default ORBITAL Config](../../BACKLOG.md#L1637) — not implemented.
- [ ] **RS-091** [ORBITAL SQLite Schema Or Extension](../../BACKLOG.md#L1647) — not implemented.
- [ ] **RS-092** [ORBITAL Fixture Pack](../../BACKLOG.md#L1658) — not implemented.
- [ ] **RS-093** [SWPC Alerts JSON Parser](../../BACKLOG.md#L1670) — not implemented.
- [ ] **RS-094** [SWPC NOAA Scales Parser](../../BACKLOG.md#L1679) — not implemented.
- [ ] **RS-095** [SWPC Kp And Aurora Fixture Parsers](../../BACKLOG.md#L1687) — not implemented.
- [ ] **RS-096** [JPL CNEOS Close Approach Parser](../../BACKLOG.md#L1696) — not implemented.
- [ ] **RS-097** [JPL CNEOS Fireball Parser](../../BACKLOG.md#L1705) — not implemented.
- [ ] **RS-098** [NASA RSS Parser](../../BACKLOG.md#L1748) — not implemented.
- [ ] **RS-099** [ESA RSS Parser](../../BACKLOG.md#L1757) — not implemented.
- [ ] **RS-100** [Official Launch Provider Source Verification](../../BACKLOG.md#L1766) — not implemented.
- [ ] **RS-101** [ISS And Crewed-Spaceflight Source Verification](../../BACKLOG.md#L1775) — not implemented.
- [ ] **RS-102** [ESA Reentry Source Verification](../../BACKLOG.md#L1801) — not implemented.
- [ ] **RS-103** [NASA Orbital Debris Source Verification](../../BACKLOG.md#L1809) — not implemented.
- [ ] **RS-104** [ORBITAL Deterministic Event Correlation](../../BACKLOG.md#L1818) — not implemented.
- [ ] **RS-105** [ORBITAL Deterministic Ranking](../../BACKLOG.md#L1828) — not implemented.
- [ ] **RS-106** [ORBITAL Safety And Sensitivity Rules](../../BACKLOG.md#L1838) — not implemented.
- [ ] **RS-107** [ORBITAL Local And Global Impact Tag Rules](../../BACKLOG.md#L1847) — not implemented.
- [ ] **RS-108** [ORBITAL UI Disabled States](../../BACKLOG.md#L1856) — not implemented.
- [ ] **RS-109** [ORBITAL Source Health States](../../BACKLOG.md#L1866) — not implemented.
- [ ] **RS-110** [ORBITAL Evidence Drawer Contract](../../BACKLOG.md#L1876) — not implemented.
- [ ] **RS-111** [ORBITAL Official-Source Live Ingest Phase, Disabled By Default](../../BACKLOG.md#L1887) — not implemented.
- [ ] **RS-112** [Documentation For ORBITAL Source Verification](../../BACKLOG.md#L1933) — partially implemented.
- [ ] **RS-113** [Tests For No Page-Load External Fetches](../../BACKLOG.md#L1948) — not implemented.
- [ ] **RS-114** [Tests For No Restricted Source Running Without Explicit Config](../../BACKLOG.md#L1957) — not implemented.
- [ ] **RS-115** [Tests For No API-Key Source Running Without Config](../../BACKLOG.md#L1966) — not implemented.
- [ ] **RS-116** [Tests For No Tactical Satellite Tracking Output](../../BACKLOG.md#L1974) — not implemented.

### Solar System and Beyond Recent Signal Layer

- [ ] **RS-117** [Resolve SYSTEM Naming Collision](../../BACKLOG.md#L1989) — not implemented.
- [ ] **RS-118** [Decide Final UI Label For Solar System And Beyond](../../BACKLOG.md#L1998) — not implemented.
- [ ] **RS-119** [Disabled-By-Default Solar System And Beyond Config](../../BACKLOG.md#L2006) — not implemented.
- [ ] **RS-120** [Solar System And Beyond Source Registry Design Implementation](../../BACKLOG.md#L2016) — not implemented.
- [ ] **RS-121** [Solar System And Beyond SQLite Schema Or Extension](../../BACKLOG.md#L2026) — not implemented.
- [ ] **RS-122** [Solar System And Beyond Fixture Pack](../../BACKLOG.md#L2038) — not implemented.
- [ ] **RS-123** [NASA/JPL RSS Parser](../../BACKLOG.md#L2049) — not implemented.
- [ ] **RS-124** [ESA RSS Parser](../../BACKLOG.md#L2058) — not implemented.
- [ ] **RS-125** [Hubble/JWST RSS Parser](../../BACKLOG.md#L2066) — not implemented.
- [ ] **RS-126** [NASA Exoplanet Archive Tiny Metadata Parser](../../BACKLOG.md#L2074) — not implemented.
- [ ] **RS-127** [MAST Tiny Metadata Parser](../../BACKLOG.md#L2083) — not implemented.
- [ ] **RS-128** [PDS Metadata-Only Parser](../../BACKLOG.md#L2091) — not implemented.
- [ ] **RS-129** [GCN Notice Fixture Parser](../../BACKLOG.md#L2099) — not implemented.
- [ ] **RS-130** [GCN Circular Source Verification](../../BACKLOG.md#L2107) — not implemented.
- [ ] **RS-131** [ATel RSS Parser](../../BACKLOG.md#L2115) — not implemented.
- [ ] **RS-132** [GraceDB/LIGO Public Alert Policy Design](../../BACKLOG.md#L2132) — not implemented.
- [ ] **RS-133** [Minor Planet Center Science-Context Source Verification](../../BACKLOG.md#L2141) — not implemented.
- [ ] **RS-134** [HEASARC Metadata Source Verification](../../BACKLOG.md#L2149) — not implemented.
- [ ] **RS-135** [Deterministic Event Correlation For Transients, Exoplanets, Missions, And Telescope Releases](../../BACKLOG.md#L2173) — not implemented.
- [ ] **RS-136** [Deterministic Ranking For Official Science And Rarity](../../BACKLOG.md#L2182) — not implemented.
- [ ] **RS-137** [Hype And Speculation Suppression Rules](../../BACKLOG.md#L2192) — not implemented.
- [ ] **RS-138** [Archive Firehose Blocking Rules](../../BACKLOG.md#L2202) — not implemented.
- [ ] **RS-139** [UI Disabled States After Naming Decision](../../BACKLOG.md#L2211) — not implemented.
- [ ] **RS-140** [Source Health States](../../BACKLOG.md#L2220) — not implemented.
- [ ] **RS-141** [Evidence Drawer Contract](../../BACKLOG.md#L2231) — not implemented.
- [ ] **RS-142** [Official RSS Live Ingest Phase, Disabled By Default](../../BACKLOG.md#L2242) — not implemented.
- [ ] **RS-143** [Official Small API Live Ingest Phase, Disabled By Default](../../BACKLOG.md#L2250) — not implemented.
- [ ] **RS-144** [Transient Alert Ingest Phase, Disabled By Default](../../BACKLOG.md#L2259) — not implemented.
- [ ] **RS-145** [Documentation For Source Verification](../../BACKLOG.md#L2292) — partially implemented.
- [ ] **RS-146** [Tests For No Page-Load External Fetches](../../BACKLOG.md#L2307) — not implemented.
- [ ] **RS-147** [Tests For No Heavy Archive Source Running Without Explicit Config](../../BACKLOG.md#L2316) — not implemented.
- [ ] **RS-148** [Tests For No Auth Source Running Without Config](../../BACKLOG.md#L2325) — not implemented.
- [ ] **RS-149** [Tests For No Data Product Downloads](../../BACKLOG.md#L2333) — not implemented.
- [ ] **RS-150** [Tests For No Alien-Life Or UFO Hype Leakage](../../BACKLOG.md#L2342) — not implemented.

## Deferred from this first pass

These stay in `BACKLOG.md` for later work. The first pass uses verified official feeds and deterministic fixture coverage before broader news, social, auth-gated, heavy, or speculative sources. Endpoint research without a proven machine-readable official path does not authorize a live adapter.

| Scope | Backlog entry | Reason |
| --- | --- | --- |
| Scoped Recent Signal / News Ingestion | [Homepage Extractor Later And Disabled](../../BACKLOG.md#L225) | Later source expansion. |
| Scoped Recent Signal / News Ingestion | [Social Adapters Later And Terms-Sensitive](../../BACKLOG.md#L238) | Terms and privacy policy; later phase. |
| LOCAL Seattle Recent Signal Layer | [City Light Outage Endpoint Research](../../BACKLOG.md#L406) | Additional endpoint research after core feeds work. |
| LOCAL Seattle Recent Signal Layer | [ArcGIS Dashboard Underlying Endpoint Research](../../BACKLOG.md#L433) | Additional endpoint research after core feeds work. |
| LOCAL Seattle Recent Signal Layer | [LOCAL News/Blog RSS Ingest Phase](../../BACKLOG.md#L562) | Secondary news coverage; official-source path first. |
| LOCAL Seattle Recent Signal Layer | [LOCAL Social Source Policy Review](../../BACKLOG.md#L575) | Terms and privacy policy; later phase. |
| REGIONAL Pacific Northwest Recent Signal Layer | [WSF Bulletin/API Fixture Parser](../../BACKLOG.md#L713) | Additional source family after core official fixtures. |
| REGIONAL Pacific Northwest Recent Signal Layer | [WA DNR Wildfire Endpoint Research](../../BACKLOG.md#L721) | Additional endpoint research after core feeds work. |
| REGIONAL Pacific Northwest Recent Signal Layer | [NWCC Feed Verification](../../BACKLOG.md#L730) | Additional endpoint research after core feeds work. |
| REGIONAL Pacific Northwest Recent Signal Layer | [USGS Water/Hydrology Fixture Parser](../../BACKLOG.md#L755) | Additional source family after core official fixtures. |
| REGIONAL Pacific Northwest Recent Signal Layer | [NWRFC Endpoint Research](../../BACKLOG.md#L763) | Additional endpoint research after core feeds work. |
| REGIONAL Pacific Northwest Recent Signal Layer | [Ecology/AirNow AQI Endpoint Research](../../BACKLOG.md#L771) | Additional endpoint research after core feeds work. |
| REGIONAL Pacific Northwest Recent Signal Layer | [PSE/SnoPUD/Tacoma Outage Endpoint Research](../../BACKLOG.md#L779) | Additional endpoint research after core feeds work. |
| REGIONAL Pacific Northwest Recent Signal Layer | [Regional News RSS Parser](../../BACKLOG.md#L803) | Secondary news coverage; official-source path first. |
| REGIONAL Pacific Northwest Recent Signal Layer | [REGIONAL News RSS Ingest Phase](../../BACKLOG.md#L926) | Secondary news coverage; official-source path first. |
| REGIONAL Pacific Northwest Recent Signal Layer | [REGIONAL Social Source Policy Review](../../BACKLOG.md#L934) | Terms and privacy policy; later phase. |
| NATIONAL United States Recent Signal Layer | [Congress.gov API Design, Disabled And Auth-Required](../../BACKLOG.md#L1130) | Credential or account policy; later phase. |
| NATIONAL United States Recent Signal Layer | [BLS/BEA/FRED/Treasury Economic Source Allowlist Design](../../BACKLOG.md#L1138) | Heavy or broad-data policy; later phase. |
| NATIONAL United States Recent Signal Layer | [National News RSS Parser](../../BACKLOG.md#L1146) | Secondary news coverage; official-source path first. |
| NATIONAL United States Recent Signal Layer | [NATIONAL News RSS Ingest Phase](../../BACKLOG.md#L1223) | Secondary news coverage; official-source path first. |
| NATIONAL United States Recent Signal Layer | [NATIONAL Social Source Policy Review](../../BACKLOG.md#L1232) | Terms and privacy policy; later phase. |
| GLOBAL World Recent Signal Layer | [NASA FIRMS API Review And Filtered Fixture Parser](../../BACKLOG.md#L1398) | Heavy or broad-data policy; later phase. |
| GLOBAL World Recent Signal Layer | [GDELT Policy Review And Strict Allowlist Design](../../BACKLOG.md#L1450) | Later source expansion. |
| GLOBAL World Recent Signal Layer | [ACLED Policy/Auth/Attribution Review](../../BACKLOG.md#L1458) | Credential or account policy; later phase. |
| GLOBAL World Recent Signal Layer | [World Bank / IMF / OWID Configured-Indicator Design](../../BACKLOG.md#L1467) | Heavy or broad-data policy; later phase. |
| GLOBAL World Recent Signal Layer | [Global News RSS Parser](../../BACKLOG.md#L1476) | Secondary news coverage; official-source path first. |
| GLOBAL World Recent Signal Layer | [GLOBAL News RSS Ingest Phase, Disabled By Default](../../BACKLOG.md#L1555) | Secondary news coverage; official-source path first. |
| GLOBAL World Recent Signal Layer | [GLOBAL Heavy Open-Data Phase, Disabled By Default](../../BACKLOG.md#L1564) | Heavy or broad-data policy; later phase. |
| GLOBAL World Recent Signal Layer | [GLOBAL Social Source Policy Review, Disabled By Default](../../BACKLOG.md#L1572) | Terms and privacy policy; later phase. |
| ORBITAL Space Recent Signal Layer | [JPL Sentry And Scout Source Verification](../../BACKLOG.md#L1713) | Specialized or sensitive feed; later phase. |
| ORBITAL Space Recent Signal Layer | [MPC MPEC And NEOCP Source Verification](../../BACKLOG.md#L1721) | Specialized or sensitive feed; later phase. |
| ORBITAL Space Recent Signal Layer | [Launch Library 2 Fixture Parser](../../BACKLOG.md#L1730) | Specialized or sensitive feed; later phase. |
| ORBITAL Space Recent Signal Layer | [Spaceflight News API Fixture Parser](../../BACKLOG.md#L1739) | Secondary news coverage; official-source path first. |
| ORBITAL Space Recent Signal Layer | [CelesTrak Public GP Safety Review And Tiny Allowlisted Fixture Parser](../../BACKLOG.md#L1784) | Specialized or sensitive feed; later phase. |
| ORBITAL Space Recent Signal Layer | [Space-Track Auth-Required Policy Design](../../BACKLOG.md#L1793) | Credential or account policy; later phase. |
| ORBITAL Space Recent Signal Layer | [ORBITAL Launch/Event API Ingest Phase, Disabled By Default](../../BACKLOG.md#L1897) | Later source expansion. |
| ORBITAL Space Recent Signal Layer | [ORBITAL Space News RSS Ingest Phase, Disabled By Default](../../BACKLOG.md#L1906) | Secondary news coverage; official-source path first. |
| ORBITAL Space Recent Signal Layer | [ORBITAL Restricted/Auth Source Policy Review, Disabled By Default](../../BACKLOG.md#L1915) | Credential or account policy; later phase. |
| ORBITAL Space Recent Signal Layer | [ORBITAL Social Source Policy Review, Disabled By Default](../../BACKLOG.md#L1924) | Terms and privacy policy; later phase. |
| Solar System and Beyond Recent Signal Layer | [TNS Auth/Policy Design](../../BACKLOG.md#L2124) | Credential or account policy; later phase. |
| Solar System and Beyond Recent Signal Layer | [SIMBAD/VizieR/Gaia Heavy-Archive Policy Design](../../BACKLOG.md#L2157) | Heavy or broad-data policy; later phase. |
| Solar System and Beyond Recent Signal Layer | [ADS Literature Metadata Policy Design, Disabled And Auth-Required](../../BACKLOG.md#L2165) | Credential or account policy; later phase. |
| Solar System and Beyond Recent Signal Layer | [Heavy Archive Phase, Disabled By Default](../../BACKLOG.md#L2267) | Heavy or broad-data policy; later phase. |
| Solar System and Beyond Recent Signal Layer | [Literature Metadata Phase, Disabled By Default](../../BACKLOG.md#L2275) | Heavy or broad-data policy; later phase. |
| Solar System and Beyond Recent Signal Layer | [Social Source Policy Review, Disabled By Default](../../BACKLOG.md#L2283) | Terms and privacy policy; later phase. |

## Host-console items outside this Goal

The seven open host-console entries under High and Medium Priority remain in `BACKLOG.md` and are not silently included in this Recent Signal build.

## Progress log

- **2026-10-15:** Completed RS-033. Added NATIONAL agency/sector/state/source-family facets on the shared indexed facet table, active scoped lookup, old-row backfill, and tests for NWS/USGS labels and expiry purge. Full pytest passed (330 tests); Ruff passed. Progress: 48/150.
- **2026-10-15:** Completed RS-029 and RS-030. Expanded the REGIONAL verification guide with the shared per-source signoff, regional scope checks and worked decisions; audited existing REGIONAL/SYSTEM state coverage and extended the opt-in HTTP GET no-fetch regression to REGIONAL. Full pytest passed (330 tests); Ruff passed. Progress: 47/150.
- **2026-10-15:** Completed RS-021 as a cross-county source review. Recorded official access and RSS candidates or signup-only fallbacks for eight counties, with parser, policy, privacy, health and activation gates. No county feed was enabled. Progress: 45/150.
- **2026-10-15:** Completed RS-020 and advanced RS-016. Verified the official King County Emergency News RSS source, added a synthetic warning/recovery/test fixture, source-specific classification and public-impact ranking, and exercised a configured offline scan. Live ingest remains disabled pending a separate release gate. Full pytest passed (330 tests); Ruff passed. Progress: 44/150.
- **2026-10-15:** Completed RS-018 and advanced RS-016. Replaced the REGIONAL WSDOT JSON test fixture with the official documented Alert/RoadwayLocation shape, added WCF date parsing and roadway/status evidence, documented the access-code hold, and verified a configured offline scan. Full pytest passed (328 tests); Ruff passed. Progress: 43/150.
- **2026-10-15:** Completed RS-019. Added optional validated REGIONAL USGS center/radius filtering using great-circle distance, retained distance and geography basis in evidence, and verified parser plus configured scan behavior. Existing official GeoJSON identity, seismic ranking, and exact live-source gate remain intact. Full pytest passed (327 tests); Ruff passed. Progress: 42/150.
- **2026-10-15:** Completed RS-017 and advanced RS-016. Added a dedicated REGIONAL NWS WA/OR fixture, official UGC/SAME geography evidence, configured county/zone filters, and a scan regression. The broader pack remains open for sources whose machine-readable shapes require verification. Full pytest passed (327 tests); Ruff passed. Progress: 41/150.
- **2026-10-15:** Completed RS-012. Expanded the shared verification workflow with a per-source signoff record and release gate, linking the existing NWS signoff and FAA/NAS reference-only decision. The record distinguishes documentation, bounded observations, fixture tests, and actual live smoke checks. Progress: 40/150.
- **2026-10-15:** Completed RS-011 at its first-source boundary. Audited the existing exact NWS Washington allowlist and opt-in command; prior controlled scan evidence recorded successful fetch plus immediate interval skip. Focused offline tests passed (7 tests) for gate, conditional request, interval, retirement, rate limit, and GET isolation. Other candidate endpoints remain disabled. Progress: 39/150.
- **2026-10-15:** Completed RS-010. Expanded LOCAL item drawer fields and event-member API provenance, added explicit deterministic event confidence, and verified linked item/event evidence. Full pytest passed (325 tests); Ruff passed. Progress: 38/150.
- **2026-10-15:** Completed RS-009. Audited the existing source-health derivation and scope/SYSTEM presentation; extended the shared offline state-matrix test to LOCAL. `not_configured` correctly applies at scope level, while rate-limit and robots states await real evidence from a future verified live source. App tests passed (28 tests); Ruff passed. Progress: 37/150.
- **2026-10-15:** Completed RS-008 for supported public-safety parsers. Removed nested SFD address and low-acuity cross-street leakage from event tokens. SPD now replaces sensitive title/description and suppresses unverified numeric route tokens for low-acuity and minor reports, with explicit privacy evidence and ranking penalty. Full pytest passed (324 tests); Ruff passed. Progress: 36/150.
- **2026-10-15:** Completed RS-007. Audited existing LOCAL parser and event ranking factors, then added a bounded NWS active-window bonus and explicit recency state so older active hazards remain visible while expired alerts receive no active boost. Event adjustment preserves the state. Full pytest passed (323 tests); Ruff passed. Progress: 35/150.
- **2026-10-15:** Completed RS-006. Verified the official NAS Status XML endpoint and active-event fields with a bounded read, documented public access and unresolved rate-limit/DTD details, and corrected the LOCAL registry's false JSON API candidate to a disabled reference-only XML entry. Port flight/checkpoint pages remain human references; the synthetic JSON fixture is not a live parser. Registry tests and Ruff passed. Progress: 34/150.
- **2026-10-15:** Completed RS-015. Audited the shared REGIONAL item/health/cluster storage, then added indexed geography facets for official NWS zones and WSDOT routes, facilities, counties, and regions. USGS free-text place labels remain outside county facets. An offline scan regression verifies facet and cluster query plans, scoped lookups, and facet deletion on item expiry. Full pytest passed (322 tests); Ruff passed. Progress: 33/150.
- **2026-10-15:** Completed RS-005. Audited the existing `local_events` and shared news schema, which already stored LOCAL event ranking explanations and linked items. Added scoped source-family and LOCAL impact-ranking indexes, with query-plan and expiry-purge checks; existing body-free item, health, fetch, and retention contracts remain covered. Full pytest passed (321 tests); Ruff passed. Progress: 32/150.
- **2026-10-15:** Completed RS-013. Added all 224 REGIONAL design-table entries to the disabled registry and retained six reviewed operational candidates. Extended config enums, validated registry metadata and HTTPS URLs, and verified full SQLite persistence. Reference-only sources are blocked before file or HTTP access. Full pytest passed (319 tests); Ruff passed. Progress: 31/150.
- **2026-10-15:** Completed RS-004. Added all 119 LOCAL design-table sources to the disabled registry while preserving reviewed core metadata. Validation covers unique keys, classes/adapters/kinds, risks/statuses, HTTPS URLs, priority, interval, and phase. Config and SQLite expose the complete inventory; a source-kind gate prevents reference-only pages from loading fixtures or fetching HTTP when configured. Full pytest passed (317 tests); Ruff passed. Progress: 30/150.
- **2026-10-15:** Completed RS-073. Verified the official UN News all-news RSS endpoint and observed title/link/GUID/time/source fields with optional category. Added a GLOBAL fixture parser that keeps canonical story URL and feed-link evidence, bounded plain-text description, institution identity, and narrow routine/feature exclusions. The homepage is now reference-only and the exact RSS entry remains disabled for HTTP. Full pytest passed (315 tests); Ruff passed. Progress: 29/150.
- **2026-10-15:** RS-072 source review found the official Smithsonian/USGS weekly report RSS URL and its stated category/cadence limits, but the exact feed returned HTTP 403 to bounded direct inspection. No parser or completion claim; continue after legitimate sample access. Next: UN News RSS.
- **2026-10-15:** Completed RS-071. Inspected NHC/CPHC Atlantic, Eastern Pacific, and Central Pacific basin XML, including live Eastern Pacific storm summaries and Public Advisories. The GLOBAL entry now names the exact Eastern Pacific feed and remains disabled. Added a source-specific fixture parser with explicit storm ID, basin, advisory, watch-term, time, and official-URL evidence; it skips inactive/outlook entries and avoids country-impact inference. Full pytest passed (312 tests); Ruff passed. Progress: 28/150.
- **2026-10-15:** Completed RS-069. Checked WMO SWIC source directory, its national issuing-service links, a BoM RSS item and linked CAP 1.2 warning, and an empty DWD RSS channel. Documented attribution, source terms, exact-feed review, parser shape, tentative cadence, and health rules. Changed the dashboard and directory registry entries to reference-only health sources; an offline scan test confirms no file or HTTP ingest even when configured. CAP parsing and exact-feed live ingest remain open in later work. Full pytest passed (309 tests); Ruff passed. Progress: 27/150.
- **2026-10-15:** Completed RS-068. Verified the ECDC RSS index, its exact News/press feed URL, and the live RSS 2.0 item shape. Added a GLOBAL fixture parser that keeps official title/link/time, optional category, creator/GUID, and bounded plain-text description, with Europe/GLOBAL context but no inferred event impact. The disabled registry entry now points at the feed rather than the HTML index and remains lower priority than WHO DON. Offline fixture/scan tests passed; the app has no ECDC live allowlist. Full pytest passed (308 tests); Ruff passed. Next: continue verified GLOBAL source adapters and WMO source review.
- **2026-10-15:** Completed RS-070. Verified the USGS GeoJSON summary format and a current official M4.5+ week feed, then extended the existing parser with GLOBAL magnitude, tsunami, depth, felt, MMI, source-place country/region term, and optional origin-age filters. It preserves event identity and official seismic evidence without treating the free-text place as a verified country. A synthetic official-shape fixture and offline scan regression exercise the GLOBAL threshold, event/ranking evidence, malformed filters, and no HTTP access. The source remains disabled for live ingest. Full pytest passed (305 tests); Ruff passed. Next: continue verified GLOBAL source adapters and event-policy coverage.
- **2026-10-15:** Completed RS-079; advanced RS-080 and RS-083. GLOBAL event clusters now store bounded, explainable scores for recency, official severity, independent source families, temporal proximity, verified geography, public/humanitarian impact, alert state, source priority, cluster size, domestic-impact tags, and explicit duplicate/stale/confidence/value/scope/rumor penalties. The drawer renders score and reasons; linked item evidence records impact basis and policy penalties. Tests cover every named first-pass factor, including humanitarian impact, age, source priority, cluster size, confidence, and no headline-only inference. Full pytest passed (302 tests); Ruff passed. Next: source-specific classification and fixture evidence for the remaining policy and adapter rows.
- **2026-10-15:** Advanced RS-078. Added complete-link compatibility checks so one broad item cannot transitively merge two incompatible GLOBAL events. Structured parser evidence now supports verified region/basin, storm and earthquake IDs, volcano/disease/institution/transport/cyber context, and impact tags, with USGS IDs recognized when present. Synthetic tests cover the new identity paths and a multi-country bridge. Full pytest passed (297 tests); Ruff passed. Next: connect these fields to verified source-specific fixtures and continue GLOBAL ranking.
- **2026-10-15:** Advanced RS-078 and RS-083. GLOBAL cluster rebuilding now correlates shared official event IDs and conservative cross-family verified-country/type/title/time matches. Stored cluster evidence includes match basis, source families, identifiers, countries, confidence, and family-deduplicated aggregate score; item evidence and the cluster drawer expose the result. Tests cover same-family duplicate scoring, cross-scope exclusion, unverified geography, wrong type/country/time, and offline fixture ingest. Full pytest passed (294 tests); Ruff passed. Next: broaden identity matching and guard transitive event bridges before ranking and public-impact rules.
- **2026-10-15:** Advanced RS-083. GLOBAL fixture items now persist a versioned evidence contract with source identity, timing, URLs, parser and health context, source-provided geography/event type, policy/sensitivity notes, and explicit unassessed correlation/impact/penalty fields. The item drawer renders these values with existing ranking and retention data. Event-level evidence waits on RS-078 through RS-080; this row stays open. Full pytest passed (291 tests); Ruff passed. Next: implement GLOBAL deterministic correlation and ranking before completing the event-level contract.
- **2026-10-15:** Completed RS-081, RS-082, and RS-086. GLOBAL now exposes every configured source health state through a six-card preview and expandable remainder; SYSTEM shows per-scope health counts. GET-only tests cover unstarted, stale/failing, parser/policy, and gated-source states with fixture and HTTP fetch hooks trapped. Expired items and representative cluster traces no longer render as active before another scan. Full pytest passed (290 tests); Ruff passed. Next: implement GLOBAL evidence and deterministic event/ranking work.
- **2026-10-15:** Completed RS-059 and RS-060; advanced RS-061. Added 172 disabled GLOBAL design inventory entries, registry metadata validation/persistence, and a disabled policy config with geography/attention settings. Explicit gates cover social, auth-required, heavy open-data, homepage, and high-risk conflict sources. Every inventory entry was checked for config seeding under its explicit policy gates. No GLOBAL HTTP allowlist entry was added. Full pytest passed (257 tests); Ruff passed. Next: continue GLOBAL fixture/parser and storage paths.
- **2026-10-15:** Completed RS-058. The scanner now records `auth_required` before fixture or official HTTP access when declared credentials are absent. Congress.gov, BEA, FRED, and AirNow API candidates default to a local key requirement; a custom auth source uses the same gate. The regression proves no item or network/fixture read occurs. Full pytest passed (248 tests); Ruff passed. Next: advance NATIONAL evidence/schema work.
- **2026-10-15:** Completed RS-057. Extended the no-fetch GET regression to NATIONAL page/API and SYSTEM summary using a missing fixture, with scan and official HTTP fetch hooks set to fail. NATIONAL/SYSTEM source-state tests cover disabled/not configured, never-run, healthy, stale, parser failure, policy blocking, auth required, and failing aggregation. Full pytest passed (247 tests); Ruff passed. Next: continue NATIONAL API-key gating and schema evidence.
- **2026-10-15:** Advanced RS-005, RS-015, and RS-033. Migrated configured `news_sources` to `(scope, source_key)` uniqueness while preserving primary IDs and dependent fetch/item rows. Config accepts the same source key in distinct scopes but still rejects duplicates within one scope; status lookup and live-success checks are scope-aware. A local/NATIONAL fixture scan proves independent ingest under the same documented ID. Full pytest passed (247 tests); Ruff passed. Next: add queryable geographic and agency/sector evidence to the shared schema.
- **2026-10-15:** Completed RS-014 and RS-025. Verified REGIONAL defaults, geography/topic flag validation, social and homepage config gates, and page states for disabled/not configured/configured disabled/never run plus blocked and failure outcomes. Added a REGIONAL-specific social-disabled health message. Full pytest passed (245 tests); Ruff passed. Next: address scoped configured-source identity so overlapping LOCAL/NATIONAL source IDs can be used together; then continue broader REGIONAL parser and storage gaps.
- **2026-10-15:** Advanced RS-036 through official NHC/CPHC documentation. Recorded basin RSS endpoints, advisory timing, storm identity/watch-warning distinctions, health policy, and the remaining need for a bounded official XML fixture. No live source admitted. Next: obtain a verifiable XML shape through the allowed research/fixture path, then implement the parser.
- **2026-10-15:** Completed RS-031 and advanced RS-033. Added all 227 disabled NATIONAL design inventory entries as checked-in data with enum validation and config defaults. Generalized registry sync/summary across LOCAL, REGIONAL, and NATIONAL; migrated SQLite uniqueness to `(scope, source_key)` so overlapping documented IDs coexist. The inventory is metadata only and does not add a live URL allowlist. Full pytest passed (233 tests); Ruff passed. A wheel build check could not run because setuptools is absent from the local virtual environment; `pyproject.toml` declares the JSON as package data. Next: continue NATIONAL schema/query work.
- **2026-10-15:** Completed RS-052. Extended page tests to NATIONAL for configured-disabled, not-configured, never-run, stale/failure, and social/homepage-blocked states. Added NATIONAL social-source policy and a scope-specific health message for read-only status. No ingest or page-load fetch is used. Full pytest passed (228 tests); Ruff passed. Next: build NATIONAL registry and storage foundation.
- **2026-10-15:** Completed RS-053. Reused the REGIONAL page/API source-health matrix for NATIONAL with isolated SQLite state and no scan/fetch, verifying ten source states including stale, parser failure, policy blocking, and auth/rate/policy outcomes. A NATIONAL baseline regression covers disabled, not-configured, never-run, and healthy scope outcomes. Full pytest passed (225 tests); Ruff passed. Next: continue NATIONAL storage/registry foundation and UI disabled-state acceptance.
- **2026-10-15:** Advanced RS-013. Corrected LOCAL and REGIONAL SQLite registry cleanup to delete only stale keys; the old REGIONAL query could delete current rows when any stale key existed. A repeat-scan regression verifies the full current REGIONAL key set survives and the obsolete key is removed. Full pytest passed (223 tests); Ruff passed. Next: inspect the remaining REGIONAL registry acceptance details, then move to the next missing scope foundation.
- **2026-10-15:** Integration state: [PR #28](https://github.com/joeszilagyi/Console-1701/pull/28) has passing required CI and is ready for review. A normal `gh pr merge 28 --merge` call was rejected by the automatic PreToolUse hook, which requires `CODEX_ALLOW_PR_MERGE=28` or an audited project merge steward. No bypass was attempted. [PR #29](https://github.com/joeszilagyi/Console-1701/pull/29) is stacked on #28 for the NATIONAL config/USGS slice. Continue independent first-pass work while integration waits for the required authority path.
- **2026-10-15:** Advanced RS-037 and RS-034. Added a NATIONAL USGS fixture and coarse U.S./territory coordinate relevance filter with configurable magnitude threshold, stored geographic basis, and end-to-end fixture ingest coverage. Regional USGS parsing remains unchanged. Full pytest passed (222 tests); Ruff passed. Nuanced cross-border and multi-state impact routing is still open.
- **2026-10-15:** Completed RS-032 on a stacked branch while PR #28 awaits the project merge gate. Added the disabled NATIONAL policy config and example, validated source and threshold settings, rejected unapproved social candidates, and connected the policy gate for future exact-allowlisted live sources. Full pytest passed (220 tests); Ruff passed. No NATIONAL live source was enabled.
- **2026-10-15:** Completed RS-035 and advanced RS-034. Added a NATIONAL NWS fixture with Washington and Puerto Rico alerts, UGC-derived state/territory evidence, official instruction-link validation, parser tests, and an end-to-end fixture `news-scan` regression. Full pytest passed (219 tests); Ruff passed. NATIONAL live HTTP remains disabled.
- **2026-10-15:** Completed RS-026. Expanded the REGIONAL source-state regression to include robots-blocked, auth-required, rate-limited, and unsupported states through the SQLite-only page/API path. Focused pytest passed. Next: inspect the remaining REGIONAL config/fixture and official-source gaps, then take the smallest verified slice.
- **2026-10-15:** Goal contract saved. Selection frozen at 150 selected / 45 deferred / 7 host-console entries. Next: inspect shared news code and choose the smallest unfinished foundation or LOCAL/REGIONAL slice; implement and verify it.
