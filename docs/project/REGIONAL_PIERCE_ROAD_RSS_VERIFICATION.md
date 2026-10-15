# Pierce County Road Alert RSS fixture verification

Reviewed 2026-10-15 for RS-016. The [official county RSS directory](https://www.piercecountywa.gov/rss.aspx)
links the [Road Alert category feed](https://www.piercecountywa.gov/RSSFeed.aspx?CID=Road-Alert-29&ModID=63).
A single bounded direct GET with an identifying user agent returned HTTP 200, `text/xml`, 3,900
bytes, and five RSS items. The same directory's extreme-weather and flood category feeds returned
valid but empty RSS; the PPW Fire feed had one burn-ban-lift notice. The Road Alert channel title
was `Pierce County, WA - Alert Center - Road Alert` and its items supplied title, HTTPS Alert Center
link, publication time, description and revision GUID.

The observed five Road Alert items represented only two Alert Center AIDs: sidewalk repairs and
four revisions of one September weather advisory. AID is the stable public notice identity; the
GUID suffix changes per revision. The fixture parser retains the latest dated revision per AID,
stores no item description or body, and labels its county as publisher jurisdiction rather than
claiming countywide impact. Routine roadwork gets no public-impact bonus. A weather advisory gets
a small bonus; explicit closures/hazards can score higher. These are classification rules for
fixture evaluation, not a claim that either observed notice is a current emergency.

The checked-in fixture is a short metadata sample matching the observed XML shape, with shortened
descriptions. The registry entry is disabled and the parser accepts local files only. No live
allowlist, schedule, page-load fetch, or automatic county coverage is added. Before live admission,
review the county's published access/terms and update cadence, document retention and revised-item
handling, test a fresh closure/hazard sample, and run a controlled exact-URL `news-scan`.
