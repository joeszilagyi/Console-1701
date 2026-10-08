# REGIONAL WSDOT Highway Alerts RSS Source Signoff

Verified 2026-10-08 for a third distinct official live-feed slice.

- Owner and endpoint: Washington State Department of Transportation (WSDOT). Its
  [Traveler Information API index](https://www.wsdot.wa.gov/traffic/api/) explicitly links the
  Highway Alerts RSS feed at
  `https://www.wsdot.wa.gov/traffic/api/HighwayAlerts/rss.aspx`. The separate documented
  [Highway Alerts JSON API](https://apps.wsdot.wa.gov/traffic/api/Documentation/group___highway_alerts.html)
  requires an Access Code; this signoff does **not** enable that API or request a credential.
- Access and shape: a bounded, no-redirect HTTPS GET on 2026-10-08 returned HTTP 200 and
  `application/rss+xml` with 154,671 bytes and 189 items. No authentication, ETag, or
  Last-Modified header was present. RSS items carry a numeric `guid`, legacy WSDOT per-alert link,
  headline, description, and Atom `updated` timestamp. The feed describes current statewide
  highway alerts; some ongoing records have older update timestamps. No homepage scraping or
  per-alert detail requests are needed.
- Parser and geography: `wsdot_highway_alerts_rss` requires the official channel title, unique
  numeric alert IDs, timestamps, and links whose WSDOT `refnum` equals the ID. It strips embedded
  markup before storing bounded text, upgrades the supplied per-alert link to HTTPS, preserves
  the official ID/route/impact evidence, and assigns a distinct REGIONAL event key per alert ID.
  The feed is statewide and has no reliable Seattle-specific location fields; only REGIONAL is
  allowlisted. LOCAL WSDOT remains unverified/disabled to avoid false Seattle matches.
- Link caveat: the legacy per-alert HTTPS URL currently redirects to WSDOT's general alert page.
  Keep the distinct WSDOT URL/ID as an audit identity and explain the redirect in item evidence;
  do not claim a working deep link.
- Policy and schedule: exact REGIONAL source ID, URL, `rss` kind, parser, and verified registry
  status are required. The existing news, REGIONAL, source, and official-HTTP opt-ins still apply.
  The on-machine schedule is 30 minutes, sending a bounded request each time because WSDOT provides
  no validators. HTTP 429 uses the existing backoff. No page load, host scan, or test fetches live.
- Storage and failure: store bounded title/description, URL, alert ID, source update time,
  route/impact evidence, fetch run and source health in local SQLite; never store the raw feed or
  private location. Existing seven-day item, fourteen-day run, and thirty-day health retention
  applies. A successful snapshot retires absent active items. A malformed feed, unexpected media
  type, oversized payload, or empty channel fails soft and retains the prior snapshot. A zero-item
  WSDOT channel is deliberately treated as anomalous because a sudden statewide wipe would be
  more damaging than temporary staleness.
- Enablement: the committed registry/example defaults remain disabled. The exact RSS URL is the
  only new outbound allowlist entry. The legacy access-code JSON API remains a separate candidate,
  and no access code is stored or transmitted by this integration.
