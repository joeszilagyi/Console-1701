# ORBITAL Launch Provider and Agency Source Verification

Checked 2026-10-15 against each owner's public site. This pass establishes the source identity
and access boundary; it does not authorize HTML extraction or live polling.

| Source | Official page and observed form | First-pass decision |
| --- | --- | --- |
| SpaceX | [Launches](https://www.spacex.com/launches/) shows upcoming and completed mission tables; [Updates](https://www.spacex.com/updates/) returned an HTML shell with no verified item contract. | Both reference/source health only. No official feed or stable permitted selector was verified. |
| Blue Origin | [News](https://www.blueorigin.com/news) is a dated provider article index. | Reference/source health only; no feed shape verified. |
| Rocket Lab | Current [Launches](https://rocketlabcorp.com/missions/launches/index.jsp) shows mission/date/vehicle/customer/site fields. The old `rocketlabusa.com/missions/next-mission/` URL returned 404. | Reference/source health only. Registry URL corrected; table selectors and policy remain unverified. |
| ULA | [Missions](https://www.ulalaunch.com/missions) is a dated mission index. Its [Next Launch](https://www.ulalaunch.com/missions/next-launch) route redirected to a “stay tuned” page at check time. | Reference/source health only. Registry points to the mission index. |
| Arianespace | Current [newsroom](https://newsroom.arianespace.com/en/) presents releases and launch updates; the old `arianespace.com/mission-updates/` URL was unavailable. | Reference/source health only. Registry URL corrected. |
| ISRO | Current [English press index](https://www.isro.gov.in/ISRO_EN/Press.html) lists dated releases, including launch items. | Reference/source health only; no feed or selector contract verified. |
| JAXA | [For Media](https://global.jaxa.jp/media.html) advertises press releases and RSS. | Reference/source health only until an exact feed URL and parser shape are checked. |
| ESA | [Top News RSS](https://www.esa.int/rssfeed/Our_Activities/Space_News) has a verified parser and exact disabled-by-default live opt-in in [ESA source verification](ORBITAL_ESA_RSS_SOURCE_VERIFICATION.md). | Opt-in official agency headlines after ORBITAL action filtering. |
| CSA | [Agency home](https://www.asc-csa.gc.ca/eng/) links general RSS, but direct retrieval of that endpoint failed during this check. | Reference/source health only; no launch-specific feed verified. |
| CNSA | [English agency site](https://www.cnsa.gov.cn/english/) contains dated news, but no RSS or stable parser shape was established. | Reference/source health only. |

All provider and unparsed agency entries remain disabled. Except for the separately reviewed ESA
feed, no exact provider endpoint is in the live HTTP allowlist. No provider HTML selectors are
approved: page layouts, robots and terms, refresh limits, and machine-readable alternatives have
not been established well enough for a stable lawful adapter. Registry cadence is `manual` for
these references; there is no background polling or homepage extraction. Do not infer a feed from
a page labelled “news,” from an RSS icon without a tested exact endpoint, or from a third-party
calendar.

Before promoting a provider page, record its terms/robots and allowed method, exact selectors or
documented API, response and row caps, conditional requests, refresh limit, date/time zones,
mission and launch status semantics, and fixture/parser drift behavior. Provider launch schedules
are tentative. A launch is completed only when a dated official result says so; schedule changes
and scrub notices must update the same mission identity. Duplicate agency/provider stories count
as separate families only when their own event evidence is present. Never extract payload,
vehicle, or orbital data for tactical tracking.
