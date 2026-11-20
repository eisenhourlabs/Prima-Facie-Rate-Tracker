# Research log

One entry per state per verification pass (plan section 1.4): URLs fetched, HTTP status,
final URL, `must_contain` result, robots.txt result, and open issues.

User-Agent for all fetches: `PrimaFacieRateTracker/0.1 (+https://github.com/eisenhourlabs/Prima-Facie-Rate-Tracker)`.

## Stage 0, 2026-11-20

No source fetched. Every row in `config/sources.csv` was `search_seen` or `unverified`, with
`enabled` set to `no`.

## Stage 1 pilot, 2026-11-20

Fetched from the build computer. Each source was fetched once by a probe and again by
`python -m pfrt check --dry-run`; the normalized content hash was identical both times.

### Indiana (IN)
| Source | URL fetched | HTTP | Final URL | Marker | Robots |
|---|---|---|---|---|---|
| IN-bulletins | https://www.in.gov/idoi/2591.htm | 200 | https://www.in.gov/idoi/insurance-laws-rules-and-bulletins/ | "Credit Life and Accident and Health Rates" found | allowed |

- The old URL redirects; `sources.csv` now holds the final URL.
- The page lists every bulletin as a link, newest first. Credit rate bulletins seen in the list:
  277, 262, 246, 222 (titled "Credit Life and Accident and Health Rates"), plus older ones.
- Selector `#main` keeps the main content (220 links) and drops the site menu.
- Open: none for monitoring. Bulletin 277 is the most recent credit rate bulletin in the list.

### Wisconsin (WI)
| Source | URL | HTTP | Marker | Robots |
|---|---|---|---|---|
| WI-bulletins-index (new) | https://oci.wi.gov/Pages/Regulation/Bulletins.aspx | 200 | "Bulletins Issued" found | no robots.txt (allowed) |
| WI-bulletin-2026 | https://oci.wi.gov/Pages/Regulation/Bulletin20261016PrimaFacieRates.aspx | 200 | "Revised Prima Facie Credit Life" found | allowed |
| WI-bulletin-2023 | https://oci.wi.gov/Documents/Regulation/Bulletin20230928PrimaFacieRates.pdf | 200 (PDF) | "Revised Prima Facie Credit Life" found in text | allowed |
| WI-rate-filing-guide | https://oci.wi.gov/Documents/OCIForms/RateFilings.PDF | 200 (PDF) | "Rate Filings" found in text | allowed |

- **Index located:** "Bulletins Issued" (link in the 2026 bulletin page's navigation). It lists 65
  bulletins newest first; the October 16, 2026 prima facie bulletin is at the top. Selector
  `#accordionOne` keeps the bulletin list only. Older bulletins move to
  https://oci.wi.gov/Pages/Regulation/BulletinsArchived.aspx; "Bulletins Currently Pending"
  (https://oci.wi.gov/Pages/Regulation/BulletinsPending.aspx) had no bulletins.
- The site is SharePoint: the whole page sits inside one `<form>`, so forms are no longer
  stripped during normalization.
- The 2026 bulletin links an A&S rate table, https://oci.wi.gov/Documents/Regulation/2027%20New%20Rates%20Table.pdf
  (fetched, HTTP 200, PDF). Not registered as a source; it is the document for the CD record.

### Virginia (VA)
| Source | URL | Result | Robots |
|---|---|---|---|
| VA-code-3730 | https://law.lis.virginia.gov/vacode/38.2-3730/ | 200, "38.2-3730" found | allowed |
| VA-order-2024 | https://scc.virginia.gov/getdoc/b707b397-4317-4b97-8c52-ac7ae2eeb265/ni240060 | not fetched | **disallowed** |

- `scc.virginia.gov/robots.txt` redirects to `www.scc.virginia.gov/robots.txt`, which allows only
  named search engines and ends with `User-agent: *` / `Disallow: /`. All SCC orders and
  administrative letters on that host are therefore off limits to the job.
- `appspre.scc.virginia.gov` (older administrative letters 94-9 to 12-09, seen in search) did
  not respond to a robots.txt request.
- Web search (2026-11-20) found no Virginia Register notice for the prima facie orders.
- **No index page usable by the job.** Leading source for Virginia is manual until another
  official channel is found. The statute text is a lagging source only and does not state
  the rates.
- The phrase "September 1" from a search excerpt does not appear in the fetched text of
  38.2-3730, so no expected-notice date is set.

### Idaho (ID)
| Source | URL | Result |
|---|---|---|
| ID-rates-pdf | https://doi.idaho.gov/wp-content/uploads/info/rules/18-03-05-Credit-Prima-Facie-Rates.pdf | not fetched |
| ID-rules-index | https://doi.idaho.gov/?p=26206 | not fetched |

- The TLS handshake with `doi.idaho.gov` gets no reply, or the connection is reset, from the
  build computer, with both Python and curl. robots.txt could not be read, so nothing was
  fetched. Status `failed`.
- Open: retry from GitHub Actions (different network) in Stage 3. No fixture exists; Stage 1
  acceptance test 4 uses the Wisconsin 2023 bulletin PDF in place of the Idaho PDF.
- **2026-11-20, retried from GitHub Actions** (dry run with `include_disabled`, run
  https://github.com/eisenhourlabs/Prima-Facie-Rate-Tracker/actions/runs/44773368940): both
  sources HTTP 200. ID-rates-pdf 213,677 bytes; ID-rules-index 220,775 bytes, 170 links;
  robots.txt allowed. The block is specific to the build computer's network.
- Open (Stage 6): choose `must_contain` markers and a selector from the page text, which needs a
  copy fetched from GitHub's network (for example a dry run that saves the page as a workflow
  artifact); then enable both sources.

### Illinois (IL)
| Source | URL | HTTP | Marker | Robots |
|---|---|---|---|---|
| IL-reg-1051-50 | https://www.ilga.gov/ftp/JCAR/AdminCode/050/050010510000500R.html | 200 | "1051.50" found | allowed; Crawl-delay 10 |

- The server sends its certificate without the Sectigo "Public Server Authentication CA OV R40"
  intermediate, so Python cannot verify it. The intermediate was downloaded from the URL in
  the certificate (http://crt.sectigo.com/SectigoPublicServerAuthenticationCAOVR40.crt),
  verified against the server certificate and Python's trusted roots, and saved as
  `pfrt/certs/sectigo-ov-r40.pem`.
- robots.txt asks for 10 seconds between requests; the job honors it.
- robots.txt asks automated systems to prefer https://ftp.ilga.gov/. Consider switching in
  Stage 6.
- An "Access Denied" page is served to clients with no User-Agent; the project User-Agent is
  served normally.
- Open: A&H rule (Part 1052) URL and a leading source (Company Bulletins page) not located.
