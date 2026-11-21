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

## Stage 6, regulation-fixed states, 2026-11-20 (second session)

Fetched from the build computer with `tools/polite_get.py` and dry runs. Third-party copies
(Cornell LII, Justia, a trade newsletter) were read only to find official documents.

### Alabama (AL)
| Host | Result |
|---|---|
| banking.alabama.gov | 200; robots.txt allows; rule 155-2-2-.12 PDF and July 2026 compilation identical (95 figures) |
| www.aldoi.gov | 200; robots.txt allows; regulations listed by `javascript:window.open` links (now read); 093r-2002.PDF and 117-1999.pdf |
| admincode.legislature.state.al.us | /robots.txt answered with the app's home page; unreadable until the 2026-11-20 rule, now "no robots.txt"; terms not yet read |

- 482-1-117-.04(r) defines "Superintendent" as the Superintendent of Banks (settles Q4).
- The disability table's column headings were read from their page positions (pypdf text
  operators); the extracted text runs the heading lines together.

### California (CA)
| Host | Result |
|---|---|
| legaldocs.insurance.ca.gov | 200; "Currently Proposed Regulations" list of titles with ASP.NET postback links (new_text) |
| www.insurance.ca.gov | 200 |
| leginfo.legislature.ca.gov | 403 to the tool |
| govt.westlaw.com/calregs | official code host, commercial publisher; not fetched (Q10) |

### Colorado (CO)
| Host | Result |
|---|---|
| doi.colorado.gov | 403 "Request blocked" (CloudFront), pages and files |
| www.coloradosos.gov/CCR | 200, robots.txt allows, but terms prohibit robots, data mining and reproduction; 13 research requests made before the terms were read; not used since |

- Series 4-9 rule versions (ruleVersionId): 10240 (eff. 07/15/2022), 6744 (05/15/2016),
  6610 (02/01/2016), 5522 (01/01/2014), 4973 (01/01/2013), 4282 (09/01/2011).

### Delaware (DE)
| Host | Result |
|---|---|
| insurance.delaware.gov, delaware.gov | firewall "Request Rejected" page (also to a plain web reader) |
| regulations.delaware.gov | /robots.txt answered with the app's home page; now "no robots.txt"; terms not yet read |
| archive.regulations.delaware.gov | 200; frozen since May 19, 2025; 11 DE Reg 727 (2007 proposal for 1701) read |
| regulations.justia.com | 403 |

### Florida (FL)
| Host | Result |
|---|---|
| www.flrules.org | 200; robots.txt allows; no terms found; rule files are Word 97 .doc (`notice_Files.asp?ID=`) |
| dos.myflorida.com / dos.fl.gov (policy page) | 403 to the tool and to a plain web reader |
| floir.com | 200, little text; not used |

- Notice IDs: 2791774 (69O-163.010 final, eff. 2/11/2003); 7666606 (69O-163.011 final,
  eff. 9/30/2009); 21097808 (development, 10/30/2018); 21640717 (proposed, 3/21/2019);
  22196527 (final, filed 7/26/2019, eff. 8/15/2019).

### Georgia (GA)
| Host | Result |
|---|---|
| oci.georgia.gov | 200; robots.txt allows; georgia.gov privacy statement has no terms against automated access |
| rules.sos.ga.gov | no answer: connection error, then read timeout after 60 seconds (robots.txt included), three tries |

## Stage 6, regulation-fixed states, 2026-11-21 (third session)

Fetched from the build computer with `tools/polite_get.py` and `tools/terms_links.py`.
Third-party copies (Cornell LII, Justia) were seen only in search results, to find official
documents.

### Hawaii (HI)
| Host | Result |
|---|---|
| cca.hawaii.gov | 200 (home page of the Insurance Division, read by `terms_links.py`); links the State terms of use |
| portal.ehawaii.gov | 200; Terms of Use: no access "through any automated means (including, but not limited to, use of scripts, web crawlers or screen scrapers)"; covers addresses containing "hawaii.gov" |
| data.capitol.hawaii.gov | 200 (home page and privacy page); privacy page says nothing on automated access, but the address is covered by the State terms |
| files.hawaii.gov | not fetched (Division's copy of HAR 16-6, found in search: /dcca/ins/har/ins_har_6-c.pdf) |

- Ruled out by the terms; no further requests. Manual check.

### Kansas (KS)
| Host | Result |
|---|---|
| www.insurance.kansas.gov | 403 Akamai "Access Denied" (home page and a `showpublisheddocument` file) |
| insurance.ks.gov | home page is a meta refresh to the new site; /robots.txt redirects to a 404 page (no robots.txt); old pages and PDFs still 200: all-adopted-regulations.php, proposed-regulations.php (no dates), article-5/40-5-107.pdf (Last-Modified April 7, 2015) |
| sos.ks.gov | 200; no terms page (only a KORA policy); robots.txt disallows /publications/register/Volume-40/ to Volume-45/; kansas-register.html redirects to rules.ks.gov; pubs_kar_inprocess.aspx 403 (CloudFront); future-effective-regulations.html is a leftover page ("no future effective regulations") |
| rules.ks.gov | 405 "Human Verification" (home page and /robots.txt) |

- K.A.R. 40-5-107 history: effective Jan. 1, 1974; amended May 1, 1979, May 1, 1986, May 1, 1988.
