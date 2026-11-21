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

### Maine (ME)
| Host | Result |
|---|---|
| www.maine.gov | 403 CloudFront "Request blocked" (/pfr/insurance and /sos/, read by `terms_links.py`) |
| www11.maine.gov | 403 CloudFront "Request blocked" (031c220.doc, the Rule Chapter 220 Word file) |

- No terms page could be read. Manual check.

### Maryland (MD)
| Host | Result |
|---|---|
| insurance.maryland.gov | 200; robots.txt allows; no terms page (accessibility only). Bulletins.aspx, LifeHealthBulletins.aspx (newest Bulletin 26-27, October 30, 2026), 2026-Bulletins.aspx, laws-and-regulations.aspx, RegulatoryActivity.aspx; bulletins 00-25 and LH 02-15 and 06-20 (text), 16-11 (scanned), 31.13 regulation review report (scanned) |
| dsd.maryland.gov | 200; regulation pages (`/regulations/Pages/31.13.01.10.aspx`) redirect to regs.maryland.gov; /MDRIssues/4305/Assembled.aspx 404 (older Register issues not online) |
| regs.maryland.gov | 200; robots.txt allows; COMAR sections, chapter pages with administrative history, and /us/md/exec/comar/31.13/index.full.html; content offered under CC BY-NC-SA 4.0 and CC0 |
| www.maryland.gov | 200; terms-use: agency sites maintained separately; no rule against automated access |
| msa.maryland.gov | 200 (home page and Acceptable Use Policy only); the policy prohibits scripts and robots; not used |

- COMAR 31.13.01 history: chapter revised effective March 1, 2001 (27:22 Md. R. 2062); .15A and E amended effective June 1, 2016 (43:5 Md. R. 387); .10 not amended since 2001. 31.13.03 effective January 1, 2003 (29:12 Md. R. 934); .10 not amended since.
- Bulletin 16-11 (scanned, read as an image): proposal in the Register December 28, 2015; final March 4, 2016; effective June 1, 2016; composite monthly outstanding balance rates reduced; "Prima facie rates for credit health insurance have not been revised since 2001". It cites "45:5 Md. R 387" (the chapter history says 43:5).

### Michigan (MI)
| Host | Result |
|---|---|
| www.michigan.gov (DIFS) | 403 Akamai "Access Denied" |
| dtmb.state.mi.us | 403 |
| ars.apps.lara.state.mi.us | 200; no robots.txt; no terms found. Home page (pending/recent rulemaking transactions); /AdminCode/DeptBureauAdminCode?Department=Insurance+and+Financial+Services&Bureau=Insurance (rule-set list); DownloadAdminCodeFile for "R 550.201 to R 550.221.pdf" (text PDF; Appendices A to E are images). The Admin Code search itself is a POST form |

### Nevada (NV)
| Host | Result |
|---|---|
| doi.nv.gov | 200; robots.txt allows; Credit-Insurance (annual data call), News-Notices/Regulations (proposed regulations by LCB file) |
| www.leg.state.nv.us | 200; NAC-690A.html (windows-1252); no terms found |
| nv.gov | robots.txt disallows all robots: privacy policy not read |

### New Hampshire (NH)
| Host | Result |
|---|---|
| www.insurance.nh.gov, www.nh.gov | 403 Akamai "Access Denied" (robots.txt included) |
| gencourt.state.nh.us | 200; rules/State_Agencies/ins1200.html (windows-1252; formulas as images); rules/register/ (latest week's notices linked); nholsrulesdbsearch (form) |

### New Jersey (NJ)
| Host | Result |
|---|---|
| www.nj.gov/dobi | 200 (redirect stub to www.state.nj.us/dobi, which serves www.nj.gov pages); legal statement nj.gov/nj/legal.shtml allows copying; lrnurulz.htm (open proposals, empty on 2026-11-21), proposed.htm, legsregs.htm; readoption notices pn05_241.pdf, prn10_227.pdf, re250707njac11_2.pdf (no 11:2-3.17 text) |

### New York (NY)
| Host | Result |
|---|---|
| www.dfs.ny.gov, dos.ny.gov, www.ny.gov | ConnectionError from the build computer (robots.txt included) |

### Oklahoma (OK)
| Host | Result |
|---|---|
| www.oid.ok.gov | 200; robots.txt allows. Bulletins page (legal-division/bulletins), notices page, statutes-and-rules page (built by script); C10S5P7.pdf (2019 upload; 365:10-5-64 source line ends "eff 7-1-97"); 2020 subchapter 5 adopted text (forms and appendices F to O) |
| www.ok.gov / oklahoma.gov | policy pages linked from OID are 404s; oklahoma.gov policy page lists only links |
| rules.ok.gov | 403 "Just a moment..." (bot challenge) |

### South Dakota (SD)
| Host | Result |
|---|---|
| sdlegislature.gov | 200; robots.txt allows /api/Rules/; rule pages are UTF-16 HTML at /api/Rules/20:06:06:NN.html; chapter page lists sections |
| dlr.sd.gov | 200; insurance/admin_rules/public_hearings.aspx ("No public hearings scheduled" on 2026-11-21) |
| rules.sd.gov | 200 (state rules portal); not used |
| sd.gov | disclaimer and privacy pages built by script (no readable text) |

### Tennessee (TN)
| Host | Result |
|---|---|
| www.tn.gov | 403 (robots.txt included) |
| sharetngov.tnsosfiles.com, publications.tnsosfiles.com, sos.tn.gov, tnsos.org | 403 CloudFront "request could not be satisfied" |

### Texas (TX)
| Host | Result |
|---|---|
| www.tdi.texas.gov | 200; robots.txt allows; privacy page grants copying for noncommercial use. rules/index.html; rules/YYYY/index.html for 2004 to 2026 (2014 via parules.html); rules/2004/0519-059.html (adoption, May 18, 2005) and figures T28S3-5206EXH21, 22-3 to 22-6; bulletins/2005/b-0069-05.html |
| www.sos.state.tx.us | 405 |

### Washington (WA)
| Host | Result |
|---|---|
| www.insurance.wa.gov | 200; privacy policy (no terms against automated access); laws-rules/legislation-and-rulemaking/rulemaking |
| app.leg.wa.gov | 403 |
| lawfilesext.leg.wa.gov | 200; no robots.txt; WAC 284-34-150, -170, -210 section files |

### Wyoming (WY)
| Host | Result |
|---|---|
| doi.wyo.gov | 200 (Google Sites); /legal lists memos and bulletins linked to Google Drive |
| rules.wyo.gov | 200; no robots.txt (404); Search.aspx pages return "No Results Found" without a form postback |
| wyoleg.gov | 200; ARules archive (ARR14-052 is chapter 43, not 52) |

### Louisiana (LA)
| Host | Result |
|---|---|
| legis.la.gov | 200; home is a redirect stub; Law.aspx?d=106294 (6:969.25), 107634 (9:3542), 107637 (9:3545), 107515 (9:3332) |
| www.ldi.la.gov | 403 "Just a moment..." (bot challenge) |

### Mississippi (MS)
| Host | Result |
|---|---|
| www.mid.ms.gov | 200; website disclaimer (no terms against automated access); legal/bulletins, legal/regulations, legal/mississippi-code; 94103reg.pdf (refunds; no rates); creditsubrequirements.pdf (cites 83-53-23 without figures) |
| healthrates.mid.ms.gov | 200; creditsubmissionReq.aspx (same text as the PDF) |
| www.sos.ms.gov | 200; Mississippi law page links LexisNexis (publisher's host, not fetched) |

### Missouri (MO)
| Host | Result |
|---|---|
| insurance.mo.gov | 429 on every request, with page content |
| www.sos.mo.gov | 200; privacy policy only; 20 CSR 600-2 PDF (600-2.110 amended effective July 30, 2019) |
| revisor.mo.gov | 200; OneSection.aspx?section=385.070 (effective 28 Aug 1992) |

### North Carolina (NC)
| Host | Result |
|---|---|
| www.ncleg.gov | 200; disclaimer (no terms against automated access); G.S. 58-57-35, -40, -45 PDFs; S.L. 1993-226 (HTML and PDF) |
| www.ncdoi.gov | 200; documents-bulletins; nc.gov disclaimer and terms of use (no rule against automated access) |
