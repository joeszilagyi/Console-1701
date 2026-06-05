# ArcGIS Dashboard Underlying Endpoint Research

This note captures the current official-source research for Seattle dashboard endpoints.

## Verified official surfaces

- SPD Online Crime Maps: `https://www.seattle.gov/police/information-and-data/online-crime-maps`
- SPD Crime Data Dashboard: `https://spdblotter.seattle.gov/2015/10/21/seattle-police-department-launches-crime-data-dashboard/`
- SPD Calls for Service Dashboard: `https://spdblotter.seattle.gov/2018/10/02/spd-launches-new-data-dashboard-for-911-calls-officer-response-times/`
- Seattle City Light outages page: `https://www.seattle.gov/city-light/outages`
- SDOT Traffic Cameras dataset: `https://data.seattle.gov/dataset/Traffic-Cameras/mvth-ptq3`
- Seattle GIS ArcGIS folder for SDOT: `https://gisdata.seattle.gov/server/rest/services/SDOT`

## Research result

- SDOT traffic cameras clearly have an official ArcGIS/open-data surface and a published dataset
  entry.
- The SPD public dashboard pages are official, but the inspected ArcGIS folder listing does not
  expose a corresponding public service.
- The City Light outage map remains a verified public surface, but a machine-readable backend has
  not yet been verified.

## Remaining work

- Verify stable underlying feature services for any dashboard that can support them.
- Keep unresolved dashboard surfaces in probe-only or manual-review states.
- Do not screen scrape dashboard HTML when a direct endpoint is not verified.
