# ORBITAL First-Pass Fixture Pack Audit

Checked 2026-10-15 against the frozen RS-092 wording in `BACKLOG.md` and the current test suite. This is a fixture and state acceptance audit, not an approval for live HTTP.

| Frozen requirement | Local evidence |
| --- | --- |
| SWPC alerts, NOAA scales, Kp, aurora JSON | `tests/fixtures/orbital/swpc_alerts.json`, `swpc_noaa_scales.json`, `swpc_kp_planetary.json`, `swpc_kp_1m.json`, `swpc_k_boulder.json`, `swpc_aurora.json`; dedicated parser and offline scan tests. The later GOES flare fixture also covers an additional SWPC product. |
| JPL CAD, fireball, Sentry or Scout JSON | `jpl_cad.json`, `jpl_fireball.json`, and `jpl_scout.json`; dedicated versioned parsers, no-impact framing and offline scans. Scout satisfies the stated Sentry-or-Scout choice. |
| MPC MPEC metadata | `mpc_mpec_2025_a18.json` matches the official MPECs API's observed one-term response; the offline parser retains only notice identity/title/time/link. |
| Launch Library upcoming launch JSON | `launch_library_upcoming.json` and `launch_library_events.json` exercise launch schedule/status and an operational docking; routine press items are suppressed. |
| Spaceflight News API JSON | `spaceflight_news_articles.json` exercises a linked article, routine image, sensitive headline and unlinked story; the aggregator cannot create independent corroboration. |
| NASA and ESA RSS | Dedicated NASA and ESA ORBITAL fixtures and parser/scan tests cover official channel identity and relevance filtering. |
| Tiny allowlisted CelesTrak GP JSON | `celestrak_iss_gp.json` is one public ISS object; the parser drops every orbital element and persists catalog freshness only. The broad catalog source remains blocked. |
| Restricted Space-Track, disabled, stale, auth-required, policy-blocked, parser-failed states | `tests/test_orbital_source_health_states.py` and `tests/test_orbital_safety_gates.py` verify these distinct state and access gates. Malformed-payload tests verify parser failure paths. GET rendering and fixture scans trap network requests. |
| Reentry candidates after verification | RS-102's ESA access review found predictions require an account and no permitted machine-readable endpoint. `esa_reentry` produces `auth_required` health without a fetch. The stated verification condition is unmet, so there is no reentry data fixture to invent. |

The full suite passed with 757 tests, Ruff passed, and `git diff --check` passed when the final MPC fixture was added. All sources remain disabled by default. Separate live-admission, source verification, and event-correlation rows remain open where their own acceptance is not met.
