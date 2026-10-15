# REGIONAL WSF Alerts Fixture Verification

Reviewed 2026-10-15. This is a documented synthetic fixture, not an observed
authenticated response or a live source signoff.

- The official [WSF Schedule API REST documentation](https://www.wsdot.wa.gov/ferries/api/schedule/documentation/rest.html)
  names `/alerts`, accepts JSON/XML, and says a WSDOT Traveler API access code is required.
  The [operation example](https://www.wsdot.wa.gov/ferries/api/schedule/rest/help/operations/GetAllAlerts)
  shows a JSON array with `BulletinID`, `BulletinFlag`, `BulletinText`, `PublishDate`,
  `DisruptionDescription`, `AlertType`, `AlertFullTitle`, `AffectedRouteIDs`, and flags.
  Publication dates use the WCF `/Date(milliseconds-offset)/` representation.
- The fixture uses synthetic IDs and text in that documented shape. No authenticated
  API response was fetched, and no live WSF request is allowlisted. The registry
  URL names the documented operation without placing any credential in config.
- The parser accepts only the local fixture tied to that exact operation. It
  retains numeric bulletin ID, affected route IDs, WCF publication time, bounded
  title and description, and a cancellation/delay/notice classification from
  explicit bulletin text. It skips non-bulletins and entries without a route or
  all-routes flag. Public-impact ranking is 25 for cancellation, 15 for delay,
  and zero for a general notice.
- The API alert model does not provide structured terminal, vessel, start or end
  fields. Those remain null; text mentions do not become verified identity.
  The [public WSF bulletin page](https://www.wsdot.com/ferries/schedule/bulletin.aspx)
  is the display source URL. No per-bulletin URL was verified. A clearly labeled
  local canonical query key is used solely to avoid collapsing separate fixture
  bulletins in storage.
- Any live promotion requires a supplied API access code, explicit credential
  handling, exact endpoint policy, bounded transport, real response validation,
  and separate source signoff. The current parser rejects HTTP use.
