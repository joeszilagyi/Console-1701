# WHO Disease Outbreak News source verification

Checked 2026-10-15 against WHO's official [Disease Outbreak News page](https://www.who.int/emergencies/disease-outbreak-news/),
[OData API help](https://www.who.int/api/hubs/diseaseoutbreaknews/sfhelp), and
[article path](https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON620).
The official `api/hubs/diseaseoutbreaknews` endpoint returned a JSON `value` list with
`UrlName`, `Title`, `PublicationDate`, `PublicationDateAndTime`, `LastModified`, `Summary`,
and large full-article fields. The item with `UrlName` `2026-DON620` resolved at the WHO
article path above.

The parser constructs article URLs only from safe slugs, keeps bounded summaries, and omits
full-article fields. Disease/hazard and geography labels are split from the title when it has
a clear separator; geography evidence is explicitly marked as an unverified title suffix.
Case counts are never inferred from narrative text. Tests use a reduced local fixture and
block HTTP; the app still has no WHO DON live-fetch allowlist.
