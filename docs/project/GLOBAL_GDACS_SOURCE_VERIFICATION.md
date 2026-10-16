# GDACS RSS and API source verification

Verified 2026-10-15 against GDACS's official [feed reference](https://www.gdacs.org/feed_reference.aspx),
[RSS endpoint](https://www.gdacs.org/xml/rss.xml), [API documentation](https://www.gdacs.org/gdacsapi/swagger/index.html),
and [API quick start](https://www.gdacs.org/Documents/2025/GDACS_API_quickstart_v2.pdf).

The RSS endpoint returned XML with `gdacs:eventtype`, `gdacs:eventid`, `gdacs:episodeid`,
`gdacs:alertlevel`, `gdacs:alertscore`, `gdacs:severity` attributes, country/ISO3, publication
and modification dates, `geo:Point`, and `gdacs:bbox`. The bounding-box comment defines
`lonmin lonmax latmin latmax`; the parser converts ordinary boxes to GeoJSON order and retains
the raw source value for antimeridian cases.

A later bounded direct RSS read returned HTTP 200, 702,751 bytes, and 229 items; six items had a
nonempty `gdacs:glide` value such as `DR-2026-000117-ETH`. The RSS parser now retains this optional
identifier. ReliefWeb's official [field tables](https://apidoc.reliefweb.int/fields-tables)
document `glide` for disasters and `disaster.glide` for reports. Strictly shaped matching GLIDE
values support a fixture-only GDACS/ReliefWeb correlation path, including linked reports.

The documented API Search endpoint returned a GeoJSON `FeatureCollection` with point geometry,
`bbox`, and properties including event/episode IDs, alert level, `severitydata`, country,
`affectedcountries`, `fromdate`, `datemodified`, and `url.report`. The parser uses the official
report URL as the item URL and rejects non-GDACS report hosts.

Fixtures in `tests/fixtures/news/` are reduced examples based on those observed shapes. Tests
read local files only. There is no GDACS HTTP allowlist or live ingest path in this change;
registry design-document URLs remain disabled references.
