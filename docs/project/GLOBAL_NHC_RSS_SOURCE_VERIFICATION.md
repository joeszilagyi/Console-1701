# GLOBAL NHC basin RSS verification

Checked 2026-10-15 for RS-071 against the [official NHC/CPHC RSS directory](https://www.nhc.noaa.gov/aboutrss.shtml)
and bounded read-only inspections of the [Atlantic](https://www.nhc.noaa.gov/index-at.xml),
[Eastern Pacific](https://www.nhc.noaa.gov/index-ep.xml), and
[Central Pacific](https://www.nhc.noaa.gov/index-cp.xml) basin feeds. The console's source entry
now points to the exact Eastern Pacific feed. It remains disabled for live HTTP ingest.

## Observed item shape

- Each basin feed was RSS 2.0 with a channel title identifying the basin. Atlantic and Central
  Pacific had outlook and no-active-cyclone placeholder items at inspection. A valid feed with
  only those items should yield zero event items and healthy source state.
- Eastern Pacific contained a basin outlook plus two active storms. Each storm had a summary,
  Public Advisory, Forecast Advisory, Discussion, wind probabilities, and graphics entries.
  These are different products for the same cyclone; the first-pass parser selects Public
  Advisories and uses structured summaries only to fill source-provided identity. A summary is
  retained only when its Public Advisory is absent.
- The summary item had `title`, `guid`, `pubDate`, `link`, `description`, and an
  `nhc:Cyclone` element with `type`, `name`, `wallet`, `atcf`, and other fields. The inspected
  Trudy item identified `EP212026` and wallet `EP1`. The Public Advisory had a title with
  advisory number, official text link, publication time, and advisory body. Its body repeated
  the ATCF ID and explicitly stated a Tropical Storm Watch. These values informed a synthetic
  RSS fixture; the repository does not store a full live advisory body.
- The feed's no-cyclone placeholder showed a future `pubDate` relative to its description in
  this inspection. The parser excludes placeholders and never treats that date as an alert.

## Parser and policy boundary

The fixture parser accepts only recognized NHC/CPHC basin channel titles and official NHC HTTPS
item links. It keeps the basin, ATCF storm ID when explicitly present, name, type, wallet,
advisory number/type, source time, GUID, and bounded plain-text description. A wallet number is
not a permanent storm ID. Watch/warning terms are recorded only from explicit Public Advisory
text, with affected geography left unverified; a basin title alone never proves impact in a
country. Outlooks, graphics, and inactive placeholders are not event items in this first pass.

The source's 10-minute interval is a tentative local policy for future opt-in scans, not an NHC
issuance guarantee. Keep the feed disabled by default, bounded by response size and timeout, and
visible through existing disabled/healthy/empty/parser-failure source states. No page load,
host scan, or test may fetch it. A separate exact URL allowlist and live-source review are needed
before HTTP ingest. The same parser can process verified Atlantic and Central Pacific basin
fixtures in a later source-registration slice.
