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

- [ ] **RS-004** [LOCAL Source Registry Design Implementation](../../BACKLOG.md#L282) — partially implemented.
- [ ] **RS-005** [LOCAL SQLite Schema Or Extension](../../BACKLOG.md#L310) — partially implemented.
- [ ] **RS-006** [FAA/SEA Airport Status Research](../../BACKLOG.md#L393) — partially implemented.
- [ ] **RS-007** [LOCAL Deterministic Ranking](../../BACKLOG.md#L461) — partially implemented.
- [ ] **RS-008** [LOCAL Privacy Redaction Rules](../../BACKLOG.md#L482) — partially implemented.
- [ ] **RS-009** [LOCAL Source Health States](../../BACKLOG.md#L511) — partially implemented.
- [ ] **RS-010** [LOCAL Evidence Drawer Contract](../../BACKLOG.md#L527) — partially implemented.
- [ ] **RS-011** [LOCAL Official-Source Live Ingest Phase](../../BACKLOG.md#L546) — partially implemented.
- [ ] **RS-012** [Documentation For Source Verification](../../BACKLOG.md#L588) — partially implemented.

### REGIONAL Pacific Northwest Recent Signal Layer

- [ ] **RS-013** [REGIONAL Source Registry Design Implementation](../../BACKLOG.md#L620) — partially implemented.
- [ ] **RS-014** [Disabled-By-Default REGIONAL Config](../../BACKLOG.md#L634) — partially implemented.
- [ ] **RS-015** [REGIONAL SQLite Schema Or Extension](../../BACKLOG.md#L649) — partially implemented.
- [ ] **RS-016** [REGIONAL Fixture Pack](../../BACKLOG.md#L665) — partially implemented.
- [ ] **RS-017** [NWS Alert Parser For Washington](../../BACKLOG.md#L682) — partially implemented.
- [ ] **RS-018** [WSDOT Traveler API Fixture Parser](../../BACKLOG.md#L697) — partially implemented.
- [ ] **RS-019** [USGS Earthquake GeoJSON Parser](../../BACKLOG.md#L738) — partially implemented.
- [ ] **RS-020** [King County Emergency Feed Parser](../../BACKLOG.md#L787) — not implemented.
- [ ] **RS-021** [County Emergency Alert Source Verification](../../BACKLOG.md#L795) — not implemented.
- [ ] **RS-022** [REGIONAL Deterministic Event Correlation](../../BACKLOG.md#L816) — partially implemented.
- [ ] **RS-023** [REGIONAL Deterministic Ranking](../../BACKLOG.md#L831) — partially implemented.
- [ ] **RS-024** [REGIONAL Privacy And Public-Impact Rules](../../BACKLOG.md#L846) — not implemented.
- [ ] **RS-025** [REGIONAL UI Disabled States](../../BACKLOG.md#L855) — partially implemented.
- [x] **RS-026** [REGIONAL Source Health States](../../BACKLOG.md#L869) — implemented; REGIONAL API/page state matrix test passes.
- [ ] **RS-027** [REGIONAL Evidence Drawer Contract](../../BACKLOG.md#L883) — partially implemented.
- [ ] **RS-028** [REGIONAL Official-Source Live Ingest Phase](../../BACKLOG.md#L898) — partially implemented.
- [ ] **RS-029** [Documentation For Source Verification](../../BACKLOG.md#L942) — partially implemented.
- [ ] **RS-030** [Tests For No Page-Load External Fetches](../../BACKLOG.md#L955) — partially implemented.

### NATIONAL United States Recent Signal Layer

- [ ] **RS-031** [NATIONAL Source Registry Design Implementation](../../BACKLOG.md#L973) — not implemented.
- [x] **RS-032** [Disabled-By-Default NATIONAL Config](../../BACKLOG.md#L982) — validated national policy tree, separate scope gate, social-source rejection, and disabled defaults.
- [ ] **RS-033** [NATIONAL SQLite Schema Or Extension](../../BACKLOG.md#L993) — not implemented.
- [ ] **RS-034** [NATIONAL Fixture Pack](../../BACKLOG.md#L1003) — not implemented.
- [x] **RS-035** [NWS Active Alert Parser](../../BACKLOG.md#L1012) — fixture parser preserves national alert geography, timing, instruction, and ranking evidence; focused tests pass.
- [ ] **RS-036** [NHC Advisory/Feed Verification](../../BACKLOG.md#L1020) — not implemented.
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
- [ ] **RS-052** [NATIONAL UI Disabled States](../../BACKLOG.md#L1185) — not implemented.
- [ ] **RS-053** [NATIONAL Source Health States](../../BACKLOG.md#L1194) — not implemented.
- [ ] **RS-054** [NATIONAL Evidence Drawer Contract](../../BACKLOG.md#L1203) — not implemented.
- [ ] **RS-055** [NATIONAL Official-Source Live Ingest Phase](../../BACKLOG.md#L1213) — not implemented.
- [ ] **RS-056** [Documentation For Source Verification](../../BACKLOG.md#L1240) — partially implemented.
- [ ] **RS-057** [Tests For No Page-Load External Fetches](../../BACKLOG.md#L1253) — not implemented.
- [ ] **RS-058** [Tests For No API-Key Source Running Without Config](../../BACKLOG.md#L1261) — not implemented.

### GLOBAL World Recent Signal Layer

- [ ] **RS-059** [GLOBAL Source Registry Design Implementation](../../BACKLOG.md#L1275) — not implemented.
- [ ] **RS-060** [Disabled-By-Default GLOBAL Config](../../BACKLOG.md#L1285) — not implemented.
- [ ] **RS-061** [GLOBAL SQLite Schema Or Extension](../../BACKLOG.md#L1296) — not implemented.
- [ ] **RS-062** [GLOBAL Fixture Pack](../../BACKLOG.md#L1306) — not implemented.
- [ ] **RS-063** [GDACS Feed Parser](../../BACKLOG.md#L1316) — not implemented.
- [ ] **RS-064** [GDACS API Fixture Parser](../../BACKLOG.md#L1324) — not implemented.
- [ ] **RS-065** [ReliefWeb Disasters API Parser](../../BACKLOG.md#L1332) — not implemented.
- [ ] **RS-066** [ReliefWeb Reports API Parser](../../BACKLOG.md#L1340) — not implemented.
- [ ] **RS-067** [WHO Disease Outbreak News Parser](../../BACKLOG.md#L1349) — not implemented.
- [ ] **RS-068** [ECDC RSS Parser](../../BACKLOG.md#L1358) — not implemented.
- [ ] **RS-069** [WMO CAP Warning Source Verification](../../BACKLOG.md#L1366) — not implemented.
- [ ] **RS-070** [USGS Global Earthquake GeoJSON Parser](../../BACKLOG.md#L1374) — not implemented.
- [ ] **RS-071** [NHC RSS Parser](../../BACKLOG.md#L1382) — not implemented.
- [ ] **RS-072** [Smithsonian GVP Weekly Report Parser](../../BACKLOG.md#L1390) — not implemented.
- [ ] **RS-073** [UN News RSS Parser](../../BACKLOG.md#L1407) — not implemented.
- [ ] **RS-074** [UN Press RSS Parser](../../BACKLOG.md#L1415) — not implemented.
- [ ] **RS-075** [IAEA RSS Parser](../../BACKLOG.md#L1423) — not implemented.
- [ ] **RS-076** [Humanitarian Source Evidence Contract](../../BACKLOG.md#L1432) — not implemented.
- [ ] **RS-077** [Conflict-Humanitarian Sensitivity Rules](../../BACKLOG.md#L1441) — not implemented.
- [ ] **RS-078** [GLOBAL Deterministic Event Correlation](../../BACKLOG.md#L1485) — not implemented.
- [ ] **RS-079** [GLOBAL Deterministic Ranking](../../BACKLOG.md#L1494) — not implemented.
- [ ] **RS-080** [GLOBAL Low-Public-Value, Rumor, And Public-Impact Rules](../../BACKLOG.md#L1504) — not implemented.
- [ ] **RS-081** [GLOBAL UI Disabled States](../../BACKLOG.md#L1515) — not implemented.
- [ ] **RS-082** [GLOBAL Source Health States](../../BACKLOG.md#L1525) — not implemented.
- [ ] **RS-083** [GLOBAL Evidence Drawer Contract](../../BACKLOG.md#L1535) — not implemented.
- [ ] **RS-084** [GLOBAL Official-Source Live Ingest Phase, Disabled By Default](../../BACKLOG.md#L1545) — not implemented.
- [ ] **RS-085** [Documentation For Source Verification](../../BACKLOG.md#L1581) — partially implemented.
- [ ] **RS-086** [Tests For No Page-Load External Fetches](../../BACKLOG.md#L1596) — not implemented.
- [ ] **RS-087** [Tests For No Heavy Source Running Without Explicit Config](../../BACKLOG.md#L1605) — not implemented.
- [ ] **RS-088** [Tests For No Token/Account Source Running Without Config](../../BACKLOG.md#L1613) — not implemented.

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

- **2026-10-15:** Advanced RS-013. Corrected LOCAL and REGIONAL SQLite registry cleanup to delete only stale keys; the old REGIONAL query could delete current rows when any stale key existed. A repeat-scan regression verifies the full current REGIONAL key set survives and the obsolete key is removed. Full pytest passed (223 tests); Ruff passed. Next: inspect the remaining REGIONAL registry acceptance details, then move to the next missing scope foundation.
- **2026-10-15:** Integration state: [PR #28](https://github.com/joeszilagyi/Console-1701/pull/28) has passing required CI and is ready for review. A normal `gh pr merge 28 --merge` call was rejected by the automatic PreToolUse hook, which requires `CODEX_ALLOW_PR_MERGE=28` or an audited project merge steward. No bypass was attempted. [PR #29](https://github.com/joeszilagyi/Console-1701/pull/29) is stacked on #28 for the NATIONAL config/USGS slice. Continue independent first-pass work while integration waits for the required authority path.
- **2026-10-15:** Advanced RS-037 and RS-034. Added a NATIONAL USGS fixture and coarse U.S./territory coordinate relevance filter with configurable magnitude threshold, stored geographic basis, and end-to-end fixture ingest coverage. Regional USGS parsing remains unchanged. Full pytest passed (222 tests); Ruff passed. Nuanced cross-border and multi-state impact routing is still open.
- **2026-10-15:** Completed RS-032 on a stacked branch while PR #28 awaits the project merge gate. Added the disabled NATIONAL policy config and example, validated source and threshold settings, rejected unapproved social candidates, and connected the policy gate for future exact-allowlisted live sources. Full pytest passed (220 tests); Ruff passed. No NATIONAL live source was enabled.
- **2026-10-15:** Completed RS-035 and advanced RS-034. Added a NATIONAL NWS fixture with Washington and Puerto Rico alerts, UGC-derived state/territory evidence, official instruction-link validation, parser tests, and an end-to-end fixture `news-scan` regression. Full pytest passed (219 tests); Ruff passed. NATIONAL live HTTP remains disabled.
- **2026-10-15:** Completed RS-026. Expanded the REGIONAL source-state regression to include robots-blocked, auth-required, rate-limited, and unsupported states through the SQLite-only page/API path. Focused pytest passed. Next: inspect the remaining REGIONAL config/fixture and official-source gaps, then take the smallest verified slice.
- **2026-10-15:** Goal contract saved. Selection frozen at 150 selected / 45 deferred / 7 host-console entries. Next: inspect shared news code and choose the smallest unfinished foundation or LOCAL/REGIONAL slice; implement and verify it.
