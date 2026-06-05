# Seattle City Light Outage Endpoint Research

This note captures the current verified status for Seattle City Light outage research.

## Verified public surface

- Seattle City Light outages page: `https://www.seattle.gov/city-light/outages`

## Research result

- The public outage page and map web app are the verified surfaces currently available for LOCAL
  outage awareness.
- A stable machine-readable endpoint has not yet been verified.
- The LOCAL registry entry for `city_light_outages_home` remains `source_health_probe_only` and now
  points at the public outage page and map web app.

## Remaining work

- Verify whether an official API or feature service exists behind the public map.
- If no machine-readable endpoint exists, keep the source in a probe-only or manual-review state.
- Do not scrape dashboard HTML or experience-map pages.
