# Regional County Emergency Source Review

Reviewed 2026-10-15 for RS-021. This is a source and access review, not a live-ingest
authorization. No county feed is enabled by this review. The presence of an RSS link does not
establish that its item shape, update cadence, or policy is suitable for the scanner.

| County | Official source and ownership | Public access found | First-pass decision |
| --- | --- | --- | --- |
| Snohomish | [County emergency response](https://snohomishcountywa.gov/2240/Response); [county Alert Center](https://snohomishcountywa.gov/AlertCenter.aspx) | County publishes emergency information and offers SnoCoAlerts registration. Alert Center advertises RSS, but its category/endpoint and event coverage were not verified. | Disabled; alert center is a candidate for a bounded RSS check. SnoCoAlerts is a subscription service, not a public ingest API. |
| Pierce | [County Alert Center](https://www.piercecountywa.gov/AlertCenter.aspx); [county RSS directory](https://www.piercecountywa.gov/rss.aspx) | Category RSS includes extreme weather, flooding, road, ferry and fire notices. Emergency Management also offers [ALERT signup](https://www.piercecountywa.gov/List.aspx). The general center contains routine park and administrative notices, so an all-category feed would need filtering. | Disabled; verify one relevant category feed's XML, freshness and terms before adding an exact URL. |
| Thurston | [County Emergency Information](https://www.thurstoncountywa.gov/departments/emergency-management/emergency-information); [Alert and Notification](https://www.thurstoncountywa.gov/departments/emergency-management/emergency-information/alert-and-notification) | TC Alert is the official registration service. Current alerts and incident news are shown on county pages; no public emergency RSS/API was established from the reviewed pages. | Manual review/source health only; do not automate the signup service or scrape alert pages. |
| Whatcom | [County RSS directory](https://www.whatcomcounty.us/Rss.aspx); [Sheriff emergency alert subscription](https://www.whatcomcounty.us/list.aspx?Mode=Subscribe) | The official RSS directory offers a Sheriff's Office Emergency Alert category, county general alerts, and emergency management updates. The sheriff describes the emergency list as notifications for disasters or emergencies. | Disabled; targeted category RSS is a candidate after bounded XML, freshness and policy checks. |
| Skagit | [County RSS information](https://www.skagitcounty.net/Departments/Home/RSS.htm); [Department of Emergency Management](https://skagitcounty.net/Departments/EmergencyManagement/Main.htm) | The county says its news RSS includes emergency alerts and press releases; the emergency department also offers alert signup. The RSS information page redirects to a newer county domain, and its exact feed was not verified here. | Disabled; verify the redirected official feed and whether alert items are distinguishable before parsing. |
| Kitsap | [Kitsap County Department of Emergency Management, KitsapALERT](https://www.kitsapdem.com/programs/kitsapalert/) | KitsapALERT sends critical safety notifications by text, phone or email and may post them on the DEM site and social accounts. The reviewed official page does not publish a public alert feed/API. | Manual review/source health only. Do not use registration credentials, private vendor APIs or social scraping. |
| Clallam | [County RSS directory](https://clallamcountywa.gov/rss.aspx); [county alert registration](https://clallamcountywa.gov/260/Wireless-Emergency-Alert-Information) | County RSS directory lists Clallam County Alerts and Inclement Weather/Road Closures. The county also operates a separate subscriber alert service. | Disabled; candidate category RSS needs bounded shape/freshness review, with tests and drill identification. |
| Jefferson | [County Emergency Management alerts](https://www.co.jefferson.wa.us/1066/5280/Alerts-Warnings); [county Alert Center](https://www.co.jefferson.wa.us/AlertCenter.aspx) | Emergency Management advertises text/email signup. The county Alert Center advertises RSS, but categories also include administrative and public-health notices; it is not an established DEM emergency feed. | Manual review for DEM alerts; any county Alert Center RSS must be category scoped and separately verified. |

## Access, policy, privacy and health rules

- **Ownership:** Each linked page is operated on an official county domain or, for Kitsap,
  the county Department of Emergency Management site. Third-party signup providers are delivery
  services, not a license to access their internal APIs.
- **Feed/API availability:** RSS is advertised by Snohomish, Pierce, Whatcom, Skagit, Clallam
  and Jefferson. This review does not certify item XML, stable endpoint URLs, redirects, or a
  published rate limit for any of them. No public API was established for Thurston or Kitsap.
- **Parser risk:** medium for the advertised RSS candidates until category filtering, GUID/link,
  publication times, empty feeds, test messages and stale records are checked. High for generic
  HTML or signup paths; those are not parser inputs.
- **Policy and privacy:** ingest only public alert metadata after an exact-source signoff. Do not
  use recipient lists, phone numbers, addresses, subscriber profiles, private notifications, or
  authenticated vendor services. Avoid storing article bodies or unnecessary personal details.
- **Health and fallback:** keep each source disabled. An empty feed is `no_items` or stale according
  to observed fetch/publication times, never proof of no emergency. A fetch/parser failure is
  reported as failing and retains the last good data under normal retention. For signup-only
  sources, show an official external link and `manual_review_only`; do not imply live coverage.
- **Activation gate:** for each exact public feed, record robots/terms, a bounded HTTP and XML
  observation, refresh interval, category scope, fixture, parser and scan tests, and a controlled
  opt-in `news-scan`. No page render, host scan or test may fetch it.

The first useful follow-up is a dedicated Whatcom or Clallam category-feed signoff, since their
official RSS directories identify emergency categories. The cross-county review itself does not
select a feed for production.
