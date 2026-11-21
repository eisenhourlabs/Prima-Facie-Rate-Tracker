# Prima Facie Rate Tracker: Spec and Build Plan

Version 0.2, 2026-11-16 (second research pass, owner decisions recorded, Wisconsin bulletin read). Save as `docs/plan.md`. This is a personal, public project. It uses public data only.

## Summary

**What this is.** A scheduled job checks state insurance department and regulation pages twice a month, flags possible prima facie rate changes for credit life, credit disability and involuntary unemployment insurance (IUI) as candidates, and emails the owner. The owner confirms or rejects each candidate in Claude Code. Confirmed records appear on a one-page static site with a Recent box and a Historical box.

**Main findings from the research (details in section 1).**

1. States fall into three groups, and they need different monitoring.
   - **Notice-driven** (rates change by bulletin, order or published notice, usually on a three-year cycle, without the regulation text changing): AZ, ID, IN, IA, NM, PA, SC, VA, WI, and probably MN and OH. These are where a missed change is most likely, and also where detection is most reliable, because each has a small set of pages or documents to watch.
   - **Regulation-fixed** (rates are written into the administrative code and change only by rulemaking): AL, CA, CO, DE, FL, GA, HI, IL, KS, ME, MD, MI, NJ, NY, TX.
   - **Statute-fixed** (rates are written into statute): LA, MS, MO, NC.
2. For regulation-fixed and statute-fixed states, watching the codified text is a **lagging** signal: the text may update on or after the effective date. Each such state also needs a **leading** source (department bulletins, proposed-rule notices). This changes `config/sources.csv` from one row per state to several.
3. Three official codes (CA, NJ, NY) appear to be hosted by commercial publishers. The job should not scrape or copy those; it should watch the department's own pages instead.
4. AI cost is negligible in every mode (under $4 a month at verified current prices even with the larger model on every page). The choice of mode is about reliability, and the recommendation is hybrid, with AI allowed to annotate candidates but never to suppress them.
5. The job emails after every run, including runs with nothing to report, so that a dead job cannot look like a quiet month (decided 2026-11-16).

**Decisions recorded 2026-11-16.** These supersede the matching open questions and stage gates below; copy them into `docs/decisions.md` in Stage 0.

| Ref | Decision | Reason |
|---|---|---|
| Q1 | Email after every run, even when no candidates are found | Silence must never be ambiguous |
| Q2 | Hybrid AI on Claude Sonnet 5.5, annotate only; to be tried and reviewed | Expected cost under $1 a month; rules-only mode still works |
| Q10 | All saved source documents are public in the repository | Simplest audit trail; owner accepts the exposure described in 9.5 |
| n/a | The marker "NEEDS TROY'S DECISION" stays for now | Owner's choice |

**Research coverage.** All 44 states have now been researched at least once. 36 have at least one official URL located; 8 have a citation only (CA, GA, MI, MT, NJ, NY, PA, WY). Only one page has been read in full (the Wisconsin bulletin below). Every other URL was seen in search results on 2026-11-16 with a matching excerpt and is marked `search_seen`. Stage 1 and Stage 6 fetch and confirm each one.

**Wisconsin has a live change.** The Commissioner's bulletin dated October 16, 2026 sets revised prima facie credit life and credit accident and sickness rates for the three-year period beginning January 1, 2027. Details are in section 1.5. This is the project's first real candidate and it needs action outside the project now: insurers using these rates must file before January 1, 2027.

**Two other items to look at by hand.** Tennessee published a rulemaking hearing notice dated August 26, 2026 that lists chapter 0780-01-04 (credit life and credit accident and health); the listed rules did not include the premium rule .06, but the text was not read. Nebraska's guidance document IGD-A2, issued January 14, 2025, sets prima facie rates for 2025, 2026 and 2027 per a third-party summary, which means a rate step may take effect on January 1, 2027.

**Build plan.** Nine stages (0 to 8), each with a review gate, in section 10.

## Assumptions

These were not asked as clarifying questions because none changes the architecture. Correct any that are wrong.

| # | Assumption |
|---|---|
| A1 | The GitHub repository does not exist yet, and will be public from the first commit. |
| A2 | Alerts go to a personal address, sent from a dedicated project mailbox, never a work address. |
| A3 | "Date communicated" means the date printed on the bulletin, order or notice, or the publication date of the register notice. If neither exists, the date the job first saw the document, flagged as estimated. |
| A4 | One record is one state, one product, one effective date. A bulletin that changes life and disability rates produces two records with the same source. |
| A5 | A record holds a few headline rates (for example single-premium decreasing life, and monthly outstanding balance), not full disability tables. The saved source document holds the full table. |
| A6 | A notice that says "rates reviewed, no change" is recorded, with `change_type` set to `no_change`, because it resets the clock on the next review. It is shown in Historical and not in Recent. See open question Q6. |
| A7 | The 15-year window is by effective date: records with an effective date on or after 15 years before the build date are shown. Older records stay in the data and are hidden. |
| A8 | The Recent box sorts by effective date ascending, so the next rates to install are at the top, with an "Upcoming" tag on dates in the future. |
| A9 | GitHub Actions on standard runners is free for public repositories. Not verified in this session; confirm in Stage 0. |
| A10 | "Twice a month" means the 3rd and 18th at a fixed UTC hour. |

## 1. Research and verification plan

### 1.1 Method and evidence levels

Each source carries a verification level.

| Level | Meaning |
|---|---|
| `fetched` | The job fetched the URL, got HTTP 200, and the text contains the expected marker string. Set only by code in Stage 1. |
| `search_seen` | An official URL and a relevant excerpt appeared in web search results on 2026-11-16. Not fetched. Everything located in this draft is at this level. |
| `unverified` | Citation known from a search excerpt on a third-party site, or state not researched. No official URL recorded. |

No rate value appears in this document. Rates and effective dates enter the project only from a fetched primary source or a seed document.

### 1.2 What the research found, by group

**Notice-driven states.** The rule or statute tells the regulator to review experience and publish adjusted rates.

| State | Mechanism (from search excerpts) | Published as | Detection reliability |
|---|---|---|---|
| AZ | Director sets prima facie rates by order at least every three years (A.A.C. R20-6-604.03, .04). 2025 dockets seen for life, disability, property. Credit unemployment rates set by order under A.R.S. 20-1621.05. | PDF orders on difi.az.gov; hearing notice on publicmeetings.az.gov | Medium. Order PDFs seen, but no index page located. File names look hand-assigned. |
| ID | Director posts prima facie rates on the Department website (IDAPA 18.03.05.014). | One PDF attachment, dated 6/1/2022 in the excerpt | High. One document to hash. |
| IN | Commissioner reviews on a triennial basis and issues a bulletin (760 IAC 1-5.1-9). Bulletins 144, 173, 194, 222, 246, 262, 277 seen. | Numbered PDF bulletins linked from an HTML list | High. New bulletin equals new link with a descriptive title. |
| IA | Adjusted rates are published by bulletin, reviewed no later than triennially (191 IAC 28.10). | PDF bulletins on iid.iowa.gov | Medium. Bulletin index URL not located. |
| MN | Commissioner reviews triennially and adjusts (Minn. R. 2760.0080). | Not found. Where adjusted rates are published is unknown. | Low until the publication channel is found. |
| NM | Superintendent adjusts presumptively acceptable rates by bulletin (13.18.2 NMAC; Bulletins 2019-018, 2021-025, 2021-028, 2025-002 seen). Rule repealed and replaced 3/11/2025. | PDF bulletins, with HTML news posts | High. News posts have descriptive titles. |
| OH | A state rule-review document says the department studies experience every three years (OAC 3901-1-14). Excerpt was cut off; publication channel not confirmed. | Rule text on codes.ohio.gov | Medium. |
| PA | Prima facie rates for life, A&H and IUI are published in the Pennsylvania Bulletin and reviewed at least every three years (31 Pa. Code 73.106, 73.109, 73.112). | Notices in the Pennsylvania Bulletin | Medium. Official URLs not located. |
| SC | Department issues tentative credit A&H rates by bulletin by August 1 each year, then a final order (Reg. 69-11.1; Bulletin 2025-06 seen). Credit life mechanism not found. | PDF bulletins and orders; HTML alert list | High for A&H. |
| VA | Commission adjusts rates on a triennial basis by order (Va. Code 38.2-3725, 38.2-3730); order for the triennium commencing January 1, 2025 seen, plus administrative letters. | PDF orders and administrative letters on scc.virginia.gov | Medium. Documents seen, index page not located. |
| WI | Commissioner gives written notice every three years, on or before October 1 (Ins 3.25(13)(c)); bulletins for 2008, 2011, 2014, 2017, 2020, 2023 seen. | HTML and PDF bulletins on oci.wi.gov | High once the bulletin index is located. |

**Regulation-fixed states.** The rate is in the administrative code. A change needs rulemaking, which is announced in advance.

| State | Citation (from search excerpts) | Notes |
|---|---|---|
| AL | Ala. Admin. Code ch. 482-1-117 (life, disability); ch. 482-1-093 (IUI, property); Banking Dept. r. 155-2-2-.12 | Two agencies publish rate rules. Which one governs a given product is a question for the owner (Q4). |
| CA | 10 CCR 2248.30 to 2248.47; Ins. Code 779.36; credit unemployment in 10 CCR 2670 series (one article shown as repealed) | Official code host not located; likely a commercial publisher. |
| CO | Regulation 4-9-2 (3 CCR 702-4) | Department regulations page located. |
| DE | 18 DE Admin. Code 1701, section 2.0 | State launched a new regulations system in May 2025; old archive URLs may redirect. |
| FL | Rules 69O-163.010 and 69O-163.011; s. 627.6785, F.S. | Rule notices appear on flrules.org with numeric IDs. |
| GA | Ga. Comp. R. & Regs. 120-2-27-.03 and -.07 | Official host not located. |
| HI | HAR 16-6-11 and 16-6-12; HRS 431:10B-108 | Official HAR host not located. |
| IL | 50 Ill. Adm. Code 1051.50 (life), amended effective May 22, 2025 per the official page; a third-party site reports Company Bulletin 2025-14. A&H appears to be Part 1052. | Good test case: a recent real change exists. |
| KS | K.A.R. 40-5-107 | Department hosts its own copy of regulations. |
| ME | 02-031 C.M.R. ch. 220, sections 9 and 10 | Word document on a state host. |
| MD | COMAR 31.13.01.10 (life), 31.13.01.15 (health), 31.13.03.10 (IUI); Bulletins 00-25 and L&H 02-15 | Official COMAR host not located. |
| MI | Mich. Admin. Code R 550.211 and R 550.212; Bulletin 87-07 | Official code host not located. |
| NJ | N.J.A.C. 11:2-3.17 | Official code host not located; likely a commercial publisher. |
| NY | 11 NYCRR 185.7 (Reg. 27-A); 11 NYCRR 187 (Reg. 27-C, credit unemployment) | Official code host not located; likely a commercial publisher. |
| TX | 28 TAC ch. 3, subch. FF; Ins. Code ch. 1153. Presumptive rates were set by order through 2000 and by rule since. Bulletin B-0069-05 announced rates effective January 1, 2006. | Texas calls them presumptive premium rates. Keyword list must include "presumptive". |

**Statute-fixed states.**

| State | Citation | Notes |
|---|---|---|
| LA | La. R.S. 6:969.25, 9:3332, 9:3542 | Rate schedules in consumer credit statutes. No insurance regulation with rates found. |
| MS | Miss. Code 83-53-23 | Department regulations and bulletins pages located. |
| MO | RSMo 385.070; 20 CSR 600-2.110 | IUI rule 20 CSR 600-2.300 is shown as rescinded. |
| NC | G.S. 58-57-40, 58-57-45; credit unemployment rates are filed and approved, so no prima facie rate | |

**Located but mechanism unclear.** KY (KRS ch. 304 subtitle 19; 806 KAR ch. 19 has no rate regulation in the excerpts) and MT (MCA 33-21-205; no rate rule found). Both need a closer look in Stage 1.

**Second research pass, 2026-11-16.** The twelve states left out of the first pass. They were left out only because the first pass was capped for session size; nothing about these states made them harder.

| State | Group | Mechanism (from search excerpts) | Official location seen | Detection reliability |
|---|---|---|---|---|
| NE | notice | Department guidance document IGD-A2 carries the prima facie rates; reissued January 14, 2025 (earlier version December 23, 2021). A hearing notice page for proposed rate adjustments exists. Rule is 210 NAC ch. 22. | doi.nebraska.gov PDF and notice page | High. One document to hash, plus a notice page. One document may hold rates for several years. |
| NV | regulation | Rates in NAC 690A.105 to 690A.155, including credit unemployment. Commissioner reviews experience annually and adopts new rates if needed (NAC 690A.175). | Legislature NAC page; Division credit insurance page | Medium. Change needs rulemaking; Division page is a good leading source. |
| NH | regulation | Rule uses "nominal rates" (Ins 1201.08, 1201.09) and "actual premium rates" in Table 1200-2 (Ins 1201.10), with a formula for new actual rates adopted by the commissioner. | General Court rules page | Medium. Terminology differs from every other state. |
| ND | notice | Rates in N.D. Admin. Code 45-07-01.1-04 to -06 (life, A&H, unemployment). Commissioner reviews triennially from January 1, 2006 (45-07-01.1-09). Bulletins page exists; no recent credit rate bulletin seen. | ndlegis.gov PDF; Department bulletins page | Medium. Publication channel for adjustments not confirmed. |
| OK | regulation | "Presumptively acceptable" life rates in OAC 365:10-5-64 and "presumptively reasonable" A&H rates in Appendix E (365:10-5-65). | Department copy of Part 7 (PDF) | Medium. |
| OR | notice | Rates in OAR 836-060-0026 and -0031, "as adjusted periodically" under 836-060-0041; Director reviews every four years and may publish adjusted rates. | Secretary of State rule viewer; Division rates-and-forms documents | Medium. Channel for published adjustments not found. |
| SD | regulation | "Prima facie acceptable" rates in ARSD 20:06:06:02 to :04; chapter title covers credit life, health and unemployment. | sdlegislature.gov rule pages | Medium. |
| TN | regulation | Rates in Tenn. Comp. R. & Regs. 0780-01-04-.06, plus "such premium rates as may be promulgated from time to time by the Commissioner". A 2026 rulemaking hearing notice lists this chapter. | Secretary of State rule PDF (1999 revision seen); Department hearing notice PDF | Medium. Active rulemaking; read the notice. |
| UT | notice | Rates in R590-91-7 and -8, with the disability table in an attachment on the Department website. Commissioner revises by order after hearing before September 1, effective January 1 of the following year (R590-91-10). | Department rules page and attachment PDF | High. Attachment to hash; fixed annual window. |
| WA | regulation | Rates in WAC 284-34-150 and -170; WAC 284-34-210 covers when the commissioner adjusts them. Chapter last updated 1/4/05 per the archive. | Legislature WAC pages | Medium. Adjustment channel not confirmed. |
| WV | notice | Rates in W. Va. Code R. 114-6-6 (life, A&S) and 114-6-7 (credit unemployment). Commissioner reviews triennially and publishes adjusted rates (114-6-8). Informational letters were replaced by insurance bulletins in 2020. | Commissioner's rules page and letters index | Medium. Bulletins index URL not seen. |
| WY | regulation | Rates deemed acceptable in ch. 52, section 6 of the Insurance Department rules. | Not located | Low until an official URL is found. |

### 1.3 IUI coverage

Search excerpts show a prima facie or presumptive IUI rate mechanism in AL, AZ, MD, NV, NY, ND, PA and WV. CA and SD are unclear (SD's chapter title covers unemployment; no rate section was seen). NC and MO appear not to set one. All other states are unknown. `config/states.csv` carries an `iui` column with `yes`, `no` or `unknown`.

### 1.4 Verification procedure (run in Stage 1 and Stage 6)

For each state, Claude Code does the following and records the result in `config/sources.csv` and `docs/research_log.md`.

1. Fetch each `search_seen` URL. Record HTTP status, final URL after redirects, content type and byte count.
2. Confirm the page contains the `must_contain` marker.
3. Read `robots.txt` for the host and record whether the path is allowed.
4. Find the index page that links to the document (the bulletin list, order list or rule page). The index page, not the single document, is what the job should watch.
5. For regulation-fixed and statute-fixed states, find one leading source: the department's bulletin list and, where it exists, its proposed-rules page.
6. Set `verification` to `fetched` only when steps 1 and 2 pass. Otherwise leave it and write the reason in `notes`.
7. Never write a URL that was not returned by a search or a fetch.

Draft `config/sources.csv` is in Appendix A. Draft `config/states.csv` is in Appendix B.

### 1.5 First candidate: Wisconsin, bulletin of October 16, 2026

Read on 2026-11-16 through an assisted page fetch, which returns a summary and not the raw page. Every value below must be checked against the bulletin PDF before the record is confirmed.

| Field | Value as reported by the fetch |
|---|---|
| Source | https://oci.wi.gov/Pages/Regulation/Bulletin20261016PrimaFacieRates.aspx |
| PDF | https://oci.wi.gov/Documents/Regulation/Bulletin20261016PrimaFacieRates.pdf |
| A&S rate table | https://oci.wi.gov/Documents/Regulation/2027%20New%20Rates%20Table.pdf |
| Date communicated | 2026-10-16 |
| Effective | Three-year period beginning 2027-01-01 |
| Legal basis | Wis. Adm. Code Ins 3.25(13)(c); s. 424.209(1), Wis. Stat. |
| Basic loss ratio, credit life | 41% |
| Credit life, single premium decreasing, single life | $0.39 per annum per $100 of initial insured indebtedness |
| Credit life, single premium level, single life | $0.72 per annum per $100 of initial insured indebtedness |
| Credit life, monthly outstanding balance, single life | $0.60 per month per $1,000 of outstanding insured indebtedness |
| Joint life | 167% of single: $0.65, $1.20 and $1.00 on the same three bases |
| Credit A&S | Adjustment factors applied to existing prima facie rates, rounded to the nearest cent: 0.85 for 14-day retroactive and nonretroactive; 1.35 for 30-day retroactive and nonretroactive |
| Filing | Insurers using these rates must make a rate filing adopting them before January 1; no documentation required; filing recommended at least 30 days before the requested effective date |

Old rates were not read. A search excerpt of the September 28, 2023 bulletin shows joint level life at $1.34 per annum per $100 and joint monthly outstanding balance at $1.106 per month per $1,000. Against those two figures the new joint rates are lower by about 10.4% and 9.6%. Take all old rates from the 2023 bulletin itself when the record is made.

Use of this candidate in the build: it becomes the Stage 1 live test for Wisconsin and the first record confirmed in Stage 2. It produces two records, `WI-CL-2027-01-01-1` and `WI-CD-2027-01-01-1`. The credit A&S record is a case where the notice gives factors and a separate table, so `rate_items` holds the factors and `rate_table_note` points to the table. The page name follows the pattern `Bulletin{YYYYMMDD}{Topic}.aspx`, with a matching PDF under `/Documents/Regulation/`; the bulletins index that links these pages still has to be located and is what the job should watch. Set Wisconsin's `next_notice_expected_by` to 2029-10-01.

## 2. Architecture

### 2.1 Repository layout

```
.
├── .github/workflows/
│   ├── check.yml            scheduled check, twice a month
│   ├── pages.yml            build and deploy the site on push to main
│   └── tests.yml            run tests on every push
├── config/
│   ├── states.csv
│   ├── sources.csv
│   ├── keywords.csv
│   └── official_domains.csv
├── data/
│   ├── records/             one JSON file per confirmed or rejected record
│   ├── candidates/          one JSON file per open candidate
│   ├── snapshots/           one JSON file per source: last hash and link set
│   └── runs/                one JSON log per run
├── archive/                 saved source documents, by state
├── seed/
│   ├── import_template.csv
│   └── README.md
├── pfrt/                    Python package
│   ├── __init__.py
│   ├── __main__.py          command-line entry point
│   ├── config.py
│   ├── fetch.py
│   ├── normalize.py
│   ├── detect.py
│   ├── documents.py
│   ├── candidates.py
│   ├── records.py
│   ├── review.py
│   ├── notify.py
│   ├── ai.py
│   ├── seed.py
│   ├── build_site.py
│   └── linkcheck.py
├── templates/index.html.j2
├── site/                    generated page; git-ignored
├── tests/
│   ├── fixtures/
│   └── test_*.py
├── docs/
│   ├── plan.md
│   ├── decisions.md
│   └── research_log.md
├── internal/                git-ignored; private notes and unscrubbed files
├── CLAUDE.md
├── README.md
├── requirements.txt
└── .gitignore
```

Dependencies: `requests`, `beautifulsoup4`, `pypdf`, `jinja2`, `pytest`, and optionally `anthropic`. Python 3.12.

### 2.2 Data model

All data files are JSON with two-space indentation and sorted keys, so Git diffs are readable.

**Product codes.** `CL` credit life, `CD` credit disability (A&H), `IUI` involuntary unemployment.

**Record** (`data/records/{state}/{record_id}.json`). The example uses a fictional state `ZZ` and invented rates.

```json
{
  "record_id": "ZZ-CL-2027-01-01-1",
  "state": "ZZ",
  "product": "CL",
  "change_type": "change",
  "effective_date": "2027-01-01",
  "date_communicated": "2026-10-01",
  "date_communicated_estimated": false,
  "source_url": "https://example.gov/bulletins/2026-07.pdf",
  "source_title": "Bulletin 2026-07",
  "archived_copy": "archive/ZZ/2026-10-03_3fa9c1d2.pdf",
  "archived_sha256": "3fa9c1d2...",
  "retrieved_at": "2026-10-03T13:17:42Z",
  "rate_items": [
    {
      "plan": "Single premium, decreasing term, single life",
      "basis": "per $100 of initial insured indebtedness per year",
      "old_rate": 0.50,
      "new_rate": 0.45,
      "pct_change": -10.0
    }
  ],
  "rate_table_note": "Full disability table is in the source document.",
  "summary": "Plain-English summary, two to four sentences, with any uncertainty stated.",
  "legal_basis": "Statute or regulation citation",
  "verified": true,
  "status": "confirmed",
  "confirmed_by": "owner",
  "confirmed_on": "2026-10-05",
  "origin": "monitor",
  "candidate_id": "c-20261003-ZZ-01",
  "history": [
    {"at": "2026-10-03T13:17:42Z", "event": "candidate_created", "by": "check-job"},
    {"at": "2026-10-05T01:10:00Z", "event": "confirmed", "by": "owner"}
  ]
}
```

Field rules.

- `record_id` is `{state}-{product}-{effective_date}-{n}`, where `n` starts at 1 and increases only if two records share the first three parts.
- `change_type` is `change`, `no_change` or `initial`.
- `pct_change` is `round((new_rate - old_rate) / old_rate * 100, 1)`. It is `null` when `old_rate` is missing or zero, or when the old and new bases differ. Example: old 0.50, new 0.45 gives -10.0.
- `verified` is `true` only when `source_url` is on a domain in `config/official_domains.csv` and an archived copy exists. Otherwise `false`, and the site labels the record "Unverified".
- `origin` is `monitor`, `seed` or `manual`.
- `confirmed_by` is the literal string `owner`. No personal name in the public repository (see Q5).

**Candidate** (`data/candidates/{candidate_id}.json`). Same fields as a record, most of them empty, plus detection fields.

```json
{
  "candidate_id": "c-20261003-ZZ-01",
  "state": "ZZ",
  "source_id": "ZZ-bulletins",
  "detected_at": "2026-10-03T13:17:42Z",
  "run_id": "run-20261003-1317",
  "rule": "R1_new_matching_link",
  "priority": "high",
  "document_url": "https://example.gov/bulletins/2026-07.pdf",
  "anchor_text": "Bulletin 2026-07: Revised Prima Facie Credit Insurance Rates",
  "matched_keywords": ["prima facie", "credit insurance", "rates"],
  "archived_copy": "archive/ZZ/2026-10-03_3fa9c1d2.pdf",
  "text_excerpt": "First 1,500 characters of extracted text",
  "ai": null,
  "status": "candidate"
}
```

`candidate_id` is `c-{YYYYMMDD}-{state}-{nn}`. When AI is on, `ai` holds `{"model": "...", "relevance": "likely|unlikely|unclear", "draft_summary": "...", "draft_rate_items": [...], "draft_effective_date": "..."}`. Every AI field is a draft for the reviewer.

**Snapshot** (`data/snapshots/{source_id}.json`).

```json
{
  "source_id": "ZZ-bulletins",
  "last_checked": "2026-10-03T13:17:42Z",
  "last_ok": "2026-10-03T13:17:42Z",
  "consecutive_failures": 0,
  "content_sha256": "…",
  "byte_count": 48211,
  "links": {"https://example.gov/bulletins/2026-07.pdf": "Bulletin 2026-07: Revised Prima Facie Credit Insurance Rates"}
}
```

**Run log** (`data/runs/{run_id}.json`). One entry per source with `status`, `http_status`, `elapsed_ms`, `rule_fired`, `candidates_created`, `error`. Plus totals and the list of states not fully checked. Run logs older than 24 months are deleted by the job.

**Archive.** `archive/{state}/{YYYY-MM-DD}_{sha8}.{ext}`, where the date is the retrieval date and `sha8` is the first eight hex characters of the SHA-256 of the file bytes. A file is never overwritten. Maximum saved size is 20 MB; larger files are recorded by hash and URL only and flagged.

### 2.3 Configuration files

`config/sources.csv` columns:

| Column | Meaning |
|---|---|
| `source_id` | Unique, `{state}-{short name}` |
| `state` | Two-letter code |
| `products` | `CL`, `CD`, `IUI` separated by `;` |
| `role` | `leading` (bulletins, orders, notices) or `lagging` (codified text) |
| `watch_mode` | `new_links` for index pages; `any_change` for a single document or rule section; `new_text` for an index page whose items have no usable links (added 2026-11-20, rule R5) |
| `url` | Exact URL |
| `format` | `html`, `pdf`, `doc`, `rtf` |
| `selector` | Optional CSS selector for the part of the page to watch |
| `must_contain` | A string that must appear in the page text, to catch block pages and redesigns |
| `citation` | Legal basis |
| `enabled` | `yes` or `no` |
| `verification` | `fetched`, `search_seen`, `unverified` |
| `verified_on` | ISO date |
| `notes` | Free text |

`config/states.csv` columns: `state, name, cl, cd, iui, group, cycle_years, next_notice_expected_by, notes`.

`config/keywords.csv` columns: `term, class`. Classes are `strong`, `product`, `rate`. Starting list:

- strong: `prima facie`, `presumptive`, `presumptively acceptable`, `presumptively reasonable`, `nominal rate`, `actual premium rate` (the last two are New Hampshire's terms)
- product: `credit life`, `credit accident`, `credit disability`, `credit health`, `credit unemployment`, `involuntary unemployment`, `credit insurance`, `consumer credit insurance`
- rate: `rate`, `rates`, `premium`

`config/official_domains.csv`: one domain per row, built from the hosts of fetched sources. Subdomains of a listed domain are official.

### 2.4 The check job, step by step

Command: `python -m pfrt check [--dry-run] [--offline] [--states IN,WI] [--ai off|hybrid|all]`.

1. Load and validate config. Abort with a clear message if a required column is missing or a `source_id` repeats.
2. Create `run_id` as `run-{YYYYMMDD}-{HHMM}` in UTC.
3. For each enabled source, in state order:
   1. Check `robots.txt` for the host (cached per run). If disallowed, set status `blocked_robots` and skip.
   2. Wait so that requests to one host are at least 5 seconds apart.
   3. Fetch with a 30-second timeout and up to 2 retries (waits of 10 and 30 seconds) on timeouts and 5xx responses.
   4. Classify the fetch: `ok`, `failed` (network error or 4xx or 5xx), `blocked` (403, 429, or a known challenge page), `suspect` (HTTP 200 but `must_contain` missing, or byte count under 40% of the last good byte count).
   5. If not `ok`, increase `consecutive_failures`, keep the old snapshot unchanged, and go to the next source.
   6. Normalize the content and extract links (section 3.1).
   7. Apply detection rules R1 to R4 (section 3.2) against the previous snapshot.
   8. For each new document a rule selects, download it, save it to `archive/`, extract text, and create a candidate unless a candidate or record already has the same `archived_sha256` or `document_url`.
   9. Write the new snapshot.
4. If this is the first run of the calendar month, run the link check (section 9.6).
5. Check expected-notice dates (section 3.5).
6. If AI mode is not `off` and an API key is present, annotate the new candidates (section 4).
7. Write the run log.
8. Build the site from confirmed records.
9. Send the email (section 6).
10. Commit `data/`, `archive/` and nothing else. The workflow then pushes.

A source's first-ever run stores a baseline and creates no candidates. The run log marks it `baseline`.

With `--dry-run`, steps 3.8, 3.9, 7, 9 and 10 write nothing and send nothing; the job prints what it would have done. With `--offline`, fetches read from `tests/fixtures/` instead of the network.

### 2.5 Site generation

Command: `python -m pfrt build`.

1. Load every file in `data/records/`. Keep those with `status` equal to `confirmed`.
2. Historical set: `effective_date >= build_date - 15 years`. Group by state, sort states by name, sort records within a state by effective date descending.
3. Recent set: `date_communicated >= build_date - 365 days` and `change_type` not equal to `no_change`. Sort by effective date ascending.
4. Read the latest run log for the "Last checked" date and the list of states not fully checked.
5. Render `templates/index.html.j2` to `site/index.html`. Copy referenced archive files to `site/archive/`.

The site is one HTML file with inline CSS and no JavaScript.

## 3. Change detection design

### 3.1 Normalization and link extraction

`normalize.html_to_text(html, selector)`:

1. Parse with BeautifulSoup. If `selector` is set and matches, keep only that element.
2. Remove `script`, `style`, `noscript`, `nav`, `header`, `footer`, `form` and `iframe` elements.
3. Take the visible text. Collapse runs of whitespace to one space. Trim.
4. Remove volatile fragments by regular expression: "Last updated …", "Page generated …", copyright year lines, and visitor counters. The pattern list lives in `normalize.py` and each pattern has a test.
5. Return the text. The content hash is the SHA-256 of its UTF-8 bytes, as lowercase hex.

`normalize.extract_links(html, base_url, selector)` returns a dictionary of absolute URL to anchor text. URLs are made absolute, fragments are dropped, scheme and host are lowercased, and query parameters named `utm_*`, `sessionid`, `sid` and `_ga` are removed. Anchor text is whitespace-collapsed.

Example. Input anchor `<a href="/idoi/files/Bulletin-277.pdf">Bulletin 277 - Credit Life and Accident and Health Rates</a>` on base `https://www.in.gov/idoi/2591.htm` yields key `https://www.in.gov/idoi/files/Bulletin-277.pdf` and value `Bulletin 277 - Credit Life and Accident and Health Rates`.

For PDF, DOC and RTF sources watched directly, the hash is taken over the raw file bytes, and text is extracted only for keyword matching.

### 3.2 Detection rules

`detect.keyword_match(text)` lowercases the text and returns the matched terms by class. A text **matches** when it contains at least one `product` term and at least one `strong` or `rate` term. An anchor text alone **pre-matches** when it contains at least one `product` term or one `strong` term.

| Rule | Applies to | Fires when | Result |
|---|---|---|---|
| R1 | `new_links` sources | A link is in the new link set and not in the old one, and its anchor text pre-matches | Download the document. If its text matches, or its text cannot be extracted, create a candidate with priority `high`. If its text is readable and does not match, log `new_link_no_match`. |
| R2 | `any_change` sources | The content hash differs from the snapshot | Create a candidate with priority `high`. Save the new version. The candidate includes a text diff of old against new, limited to 60 lines. |
| R3 | `new_links` sources | The content hash differs, and R1 created no candidate | No candidate. Log `changed_no_match` with the list of new anchors. The email lists these in a short "Other page changes" section. |
| R4 | `new_links` sources | A new link has no anchor text, or anchor text of 3 characters or fewer, and points to a PDF | Download it and apply the text test from R1. This covers pages that link bulletins as bare icons. |
| R5 | `new_text` sources (added 2026-11-20) | The content hash differs, and the words added since the last snapshot pre-match the keywords (the R1 anchor test) | Create a candidate with priority `high`, saving the page and a text diff as R2 does. If the added words do not pre-match, log R3 with the added text. For lists of titles with no document links (California's proposed regulations). |

Examples, using titles seen on a real bulletin list:

- New anchor "Bulletin 277 - Credit Life and Accident and Health Rates": pre-match on `credit life`; document downloaded; text contains `prima facie` and `credit life`; candidate created.
- New anchor "Bulletin 278 - Reporting of Ownership Information": no pre-match; logged under R3; no candidate.

### 3.3 PDFs and other documents

`documents.extract_text(path)` uses `pypdf` for PDF. DOC (Word 97-2003) text is read from its text runs since 2026-11-20 (`documents.doc_text`); RTF returns an empty string in version 1 (see Q8).

- If extracted text is under 200 characters for a file over 20 KB, treat it as a scanned image. Under R1 this creates a candidate marked `unreadable_document` for manual review. No OCR in version 1.
- Text extraction reads at most the first 30 pages.
- The saved copy is the original bytes, never a conversion.

### 3.4 Blocked scripts, layout changes and failures

- **Block pages and soft failures.** A page that returns HTTP 200 with a challenge or an error message would otherwise look like "content changed" or, worse, "unchanged". `must_contain` and the 40% size floor classify it as `suspect`, which counts as not checked.
- **Layout changes.** A redesign changes the hash and usually every link. If more than 25 links are new in one run for one source, the job creates no candidates from that source, sets status `suspect_redesign`, keeps the old snapshot, and reports the state as needing a manual look. Without this rule, a redesign would reset the baseline silently.
- **JavaScript-rendered pages.** If the fetched HTML has under 500 characters of visible text, mark the source `needs_browser` in the run log. Version 1 does not run a headless browser. Such sources are reported every run until a different URL is registered or the owner approves a browser-based fetcher (Q7).
- **Robots or terms disallow.** The job does not work around it. The source is reported as `blocked_robots`, and the state goes on the manual-check list.
- **Per-state reporting.** A state is "fully checked" only when every enabled `leading` source for that state has status `ok` or `baseline`. Otherwise the email's first section names the state, the source, the status, and the number of consecutive failures. After 2 consecutive failures the line is marked "ACTION: check this state by hand".
- **States with no enabled leading source** are listed in every email under "Not monitored", so an unverified state is never mistaken for a quiet one.

### 3.5 Expected-notice check

Notice-driven states publish on a known cycle. `config/states.csv` holds `next_notice_expected_by`. If the run date is later than that date and no record or open candidate for the state has `date_communicated` in the 120 days before it, the email includes "Expected notice not seen" for that state. When a record is confirmed, the review command asks for the next expected date and updates the file.

This catches a class of miss that hashing cannot: the regulator moved the bulletin to a page the job does not watch.

### 3.6 False positives and false negatives

A missed change (false negative) is the costly error: the rates are not installed by the effective date. A false positive costs a few minutes of review. Every threshold above is set to favor a false positive.

| Source of false negatives | Control |
|---|---|
| Notice posted on an unwatched page | Several sources per state; expected-notice check; "Not monitored" list |
| Notice title has none of the keywords | R2 on single-document sources; "Other page changes" list in the email; keyword list reviewed after each miss |
| Scanned PDF with no text | Unreadable documents become candidates |
| Block page read as valid content | `must_contain`, size floor, redesign rule |
| Job did not run at all | Email after every run; GitHub's own failure email; workflow keeps the repository active by committing each run |
| Codified text updates after the effective date | A `leading` source for every regulation-fixed and statute-fixed state |
| Statute changed by a bill | Not covered in version 1 (risk R4) |
| First run stores a baseline that already contains an unseen change | Stage 6 gate: owner reviews each state's current documents once at onboarding |

| Source of false positives | Control |
|---|---|
| Page chrome, dates, counters | Normalization; optional `selector` |
| Unrelated bulletins | Keyword pre-match before download |
| Same document re-linked at a new URL | De-duplication on `archived_sha256` |
| Credit property, GAP or deviation notices that mention prima facie rates | Not filtered. These reach review and are rejected with a reason. Rejections are kept so the pattern can be tuned later. |

Expected volume, as an assumption: 2 to 6 candidates a month across 44 states, most of them rejected.

## 4. AI in the job

### 4.1 Prices (verified 2026-11-16)

From the Claude Platform pricing and model pages, seen in search results:

| Model | Input per million tokens | Output per million tokens |
|---|---|---|
| Claude Haiku 5.5, prompts up to 100,000 tokens | $0.10 | $0.50 |
| Claude Sonnet 5.5 | $2.00 | $10.00 |

Batch processing is listed at 50% off; it is not needed at this volume. Sources: https://platform.claude.com/docs/en/about-claude/pricing and https://www.anthropic.com/claude/haiku. Re-check before Stage 7; prices change.

### 4.2 Assumptions

| Item | Value |
|---|---|
| States | 44 |
| Sources per state, average | 2.5, so 110 sources |
| Runs per month | 2, so 220 page checks |
| Tokens per page after normalization, average | 6,000 input |
| Output per page classification | 400 tokens |
| Changed documents read per month in hybrid mode | 20 |
| Tokens per changed document | 10,000 input, 800 output |

### 4.3 Cost per month

| Mode | Token volume per month | Haiku 5.5 | Sonnet 5.5 |
|---|---|---|---|
| Rules only | none | $0.00 | $0.00 |
| Hybrid | 200,000 in, 16,000 out | $0.03 | $0.56 |
| AI on every page | 1,320,000 in, 88,000 out | $0.18 | $3.52 |

Arithmetic, hybrid on Sonnet: 0.2 × $2 + 0.016 × $10 = $0.40 + $0.16. Every page on Sonnet: 1.32 × $2 + 0.088 × $10 = $2.64 + $0.88. Token counts per page are estimates and could be off by a factor of three without changing the conclusion.

### 4.4 Comparison

| | Rules only | Hybrid | AI on every page |
|---|---|---|---|
| Cost | $0 | Under $1 | Under $4 |
| Detects a change | Deterministic; same input gives same output | Same as rules; AI adds nothing to detection | Could catch a notice with unusual wording that keywords miss |
| Risk of a miss caused by AI | None | None, if AI cannot suppress | Present if AI output is used to decide what is a candidate |
| Reviewer effort | Reads each source document cold | Starts from a draft summary and draft rates | Same as hybrid |
| Extra parts that can fail | None | API key, one API call per candidate | API call per page; a provider outage would stop detection unless rules still run |
| Reproducible in tests | Yes | Detection yes; drafts no | No |

### 4.5 Recommendation

**Hybrid, with Sonnet 5.5, under one firm rule: AI annotates and never filters.** Rules alone decide what becomes a candidate. For each new candidate, the model receives the extracted document text and returns a relevance label, a draft summary, draft rate items with their bases, and a draft effective date. A label of `unlikely` changes nothing except the order of candidates in the email.

Reasons: cost is not a constraint in any mode; the drafts save real review time on rate tables; and keeping detection in rules means the alert works identically with AI off, during an API outage, or with no key configured.

"AI on every page" is not recommended for version 1. Its one advantage, catching oddly worded notices, is better tested later as a second opinion that can only add candidates. Defer until there is a record of what rules missed.

Safeguards for AI use:

- The job runs with `--ai off` if `ANTHROPIC_API_KEY` is absent or the call fails. A failure is logged and never stops the run.
- Fetched pages are untrusted input. The prompt tells the model to treat document text as data, and the model's output is only ever stored as text fields for a human to read. It is never executed and never changes status.
- Draft rates are labeled "AI draft, verify against source" in the email and the review command. The review command requires the owner to type or accept each rate before confirming.
- Input is capped at 60,000 characters per document.

DECIDED 2026-11-16 (Q2): hybrid on Sonnet 5.5, as a trial. Set a spending limit on the API account, and review after three months whether the drafts are saving review time.

## 5. Review and approval workflow in Claude Code

### 5.1 Status transitions

```
(detected) ──> candidate ──> confirmed
                   │
                   └────────> rejected
```

- `candidate` to `confirmed`: owner only, through `pfrt review confirm`. Requires state, product, effective date, date communicated, source URL, at least one rate item or `change_type` of `no_change`, a summary and a legal basis.
- `candidate` to `rejected`: owner only, through `pfrt review reject`, with a reason. Rejected candidates move to `data/records/` with status `rejected`, so the same document is not raised again.
- `confirmed` to corrected: `pfrt review amend` edits fields and appends a `history` entry. There is no silent edit.
- `confirmed` to `rejected`: `pfrt review retract`, with a reason, for a record confirmed in error.
- Nothing else changes status. The scheduled job can create candidates and cannot confirm.

### 5.2 Commands

Run from the repository folder in the VS Code terminal.

| Step | Command | What it does |
|---|---|---|
| Get the latest data | `git pull` | Downloads the candidates the job committed |
| List | `python -m pfrt review list` | Table of open candidates: id, state, detected date, rule, priority, title |
| Inspect | `python -m pfrt review show c-20261003-ZZ-01` | Prints all fields, the text excerpt, AI drafts if any, the source URL and the path of the saved copy |
| Open the saved copy | `code archive/ZZ/2026-10-03_3fa9c1d2.pdf` | Opens the file in VS Code; or paste the source URL into a browser |
| Confirm | `python -m pfrt review confirm c-20261003-ZZ-01` | Prompts for each required field, showing the draft value to accept or replace; computes `pct_change`; if the document covers two products, asks whether to create a second record; asks for the state's next expected notice date |
| Reject | `python -m pfrt review reject c-20261003-ZZ-01 --reason "credit property only"` | Records the rejection |
| Check | `python -m pfrt validate` | Runs all record validations |
| Preview | `python -m pfrt build` then open `site/index.html` | Builds the page locally |
| Publish | `git add data archive config` then `git commit -m "Confirm ZZ credit life change effective 2027-01-01"` then `git push` | The push triggers the Pages workflow |

### 5.3 Prompts for Claude Code

`CLAUDE.md` holds the review protocol so these short prompts work in a fresh session.

- "Pull the latest changes and list open candidates."
- "Show me candidate c-20261003-ZZ-01 and open its saved source document."
- "Read the saved document and propose values for every record field. Quote the sentence each rate and date comes from, with the page number. Do not confirm anything."
- "Confirm c-20261003-ZZ-01 with these values: …" (owner states or approves each value)
- "Reject c-20261003-ZZ-02, reason: annual experience report call, no rate change."
- "Validate, build the site, show me the diff, and wait for my go-ahead before committing."
- "Commit and push."

Protocol rules written into `CLAUDE.md`: Claude Code never runs `confirm`, `reject`, `amend`, `retract` or `git push` without an explicit instruction in the current session; it takes rates and dates only from the saved document; and it states the page it read each value from.

## 6. Email notification

### 6.1 Recommended method

**A dedicated Gmail account that sends through Gmail's SMTP server with an app password, called from Python's standard `smtplib`.** No third-party GitHub Action and no email service account are needed, and the sender address is a project address, not a work or personal one.

Backup channel, recommended: the job also opens a GitHub issue titled with the run date when there are candidates or unchecked states. GitHub then sends its own notification, which still works if the mailbox credentials expire. The issue is public; it contains only public data.

Alternatives considered: a transactional email service (more setup, an extra account, a domain to verify); GitHub issue notifications alone (no secrets at all, but formatting is limited and delivery depends on notification settings). See Q3.

### 6.2 Setup steps

1. Create a new Google account for the project, for example a name based on the project title. Do not reuse a personal or work account.
2. Turn on 2-Step Verification for that account. Google requires it before app passwords can be created (verify this at setup; Google changes these screens).
3. Create an app password and copy the 16-character value.
4. In the GitHub repository, open Settings, then Secrets and variables, then Actions. Add three repository secrets: `SMTP_USER` (the new address), `SMTP_APP_PASSWORD` (the app password), `ALERT_TO` (the personal address that receives alerts).
5. Never put these values in a file, a commit message or a workflow log. `notify.py` reads them from environment variables and prints only "email sent" or the error class.
6. Run the workflow by hand with the "send test email" input and confirm arrival, including the spam folder. Add the sender to contacts.
7. In GitHub account settings, set the commit email to the GitHub-provided no-reply address so the public commit history shows no personal or work address.

### 6.3 Email content

Subject line patterns, so the inbox view is enough to triage:

- `[PFRT] 2 candidates; 1 state not checked (2026-12-03)`
- `[PFRT] No candidates; all 44 states checked (2026-12-03)`
- `[PFRT] ACTION: 3 states not checked (2026-12-03)`

Body, plain text, in this order:

1. **States not fully checked.** State, source, status, consecutive failures, and "ACTION" where failures are 2 or more.
2. **Expected notice not seen.** State and expected-by date.
3. **Candidates.** For each: id, state, rule, document title, document URL, matched keywords, and when AI is on, the draft summary, draft effective date and draft rates, each marked "AI draft, verify against source". Sorted with high priority first.
4. **Other page changes.** Sources that changed with no keyword match, with new link titles.
5. **Not monitored.** States with no enabled leading source.
6. **Link check results**, on the first run of the month.
7. **Footer.** Run id, counts, a link to the run log in the repository, and the review commands.

If the SMTP call fails, the job still opens the GitHub issue and exits with a non-zero status so GitHub sends its failure notice.

## 7. Seed data

### 7.1 Import template

`seed/import_template.csv`, one row per rate item. Rows that share `state`, `product` and `effective_date` are merged into one record.

| Column | Required | Format and example |
|---|---|---|
| `state` | yes | `ZZ` |
| `product` | yes | `CL`, `CD` or `IUI` |
| `change_type` | yes | `change`, `no_change` or `initial` |
| `effective_date` | yes | `2019-01-01` |
| `date_communicated` | no | `2018-09-28`; blank allowed for old records |
| `source_url` | yes | Primary-source URL; write `NONE` if no public source is known |
| `source_title` | no | `Bulletin 2018-04` |
| `plan` | yes unless `no_change` | `Single premium, decreasing term, single life` |
| `basis` | yes unless `no_change` | `per $100 of initial insured indebtedness per year` |
| `old_rate` | no | `0.50` |
| `new_rate` | yes unless `no_change` | `0.45` |
| `rate_table_note` | no | Free text |
| `summary` | yes | Plain English |
| `legal_basis` | yes | Citation |
| `public_document_file` | no | File name in `seed/documents/` of a public document to archive |
| `notes` | no | Not published |

### 7.2 Process

1. Put original work documents in `internal/seed_raw/`. This folder is git-ignored. They never leave it.
2. Copy only the facts into a new CSV in `seed/`, following the template. Do not copy sentences from internal documents.
3. For each row, find the public primary source and put its URL in `source_url`. If a public copy of the bulletin or order exists, download it from the official site into `seed/documents/`.
4. Run the scrubbing checklist (7.3) on the CSV and on every file in `seed/documents/`.
5. `python -m pfrt seed validate seed/batch_01.csv` prints errors and warnings and writes nothing.
6. `python -m pfrt seed import seed/batch_01.csv` creates candidates with `origin` set to `seed`. Rows with `source_url` of `NONE` get `verified` set to `false`.
7. Review `python -m pfrt review list --origin seed`, then `python -m pfrt review confirm --batch batch_01` to confirm all rows of a batch that passed validation with no warnings. Rows with warnings are confirmed one at a time.
8. Build, preview, commit, push.

### 7.3 Scrubbing checklist

Before any seed file is committed:

- [ ] No employer, affiliate, client, vendor or colleague names, in text or in file names.
- [ ] No internal rates: deviated rates, filed company rates, account rates, commissions, loss ratios or experience data. Only state prima facie or presumptive rates.
- [ ] No filing identifiers, tracking numbers, system names, product codes or form numbers.
- [ ] No borrower, account or policy data.
- [ ] No internal commentary, opinions, deadlines or project names.
- [ ] `notes` column reviewed; it is not published on the site but is public in the repository.
- [ ] Documents in `seed/documents/` were downloaded from the official public site, not taken from internal copies, so they carry no annotations, stamps, routing marks or highlights.
- [ ] Document properties checked: author, company, comments and tracked changes are absent. For PDFs, check File, Properties. For spreadsheets, check hidden sheets, hidden columns, cell comments and named ranges.
- [ ] `python -m pfrt seed scan seed/` passes. This command searches the CSV text, file names and extractable PDF text and metadata for terms listed in `internal/blocklist.txt` (git-ignored, written by the owner) and fails if any is found.
- [ ] A final read of `git diff --staged` before committing.

### 7.4 Validation checks

`pfrt validate` and `pfrt seed validate` apply the same rules. Errors block; warnings are listed.

| Check | Level |
|---|---|
| `state` is in `config/states.csv` | error |
| `product` is `CL`, `CD` or `IUI` | error |
| Dates parse as ISO `YYYY-MM-DD` and are real calendar dates | error |
| `effective_date` is between 1990-01-01 and build date plus 3 years | error |
| `source_url` is present, or `NONE` with `verified` false | error |
| `source_url` host is in `config/official_domains.csv` | warning; record is `verified` false until resolved |
| `source_url` responds with HTTP 200 | warning |
| Rates are numbers greater than 0 | error |
| `basis` is not blank when a rate is present | error |
| Rate is inside the plausible range for its basis (table below) | warning |
| Absolute `pct_change` is over 50 | warning |
| `date_communicated` is later than `effective_date` | warning |
| Duplicate of an existing record on state, product, effective date | error |
| `old_rate` differs from the `new_rate` of the previous record for the same state, product, plan and basis | warning; this is the continuity check and it finds missing history |
| `summary` is 20 to 600 characters | warning |

Plausible ranges are starting assumptions for the owner to set (Q9). They exist to catch a misplaced decimal or a wrong basis, and they are stored in `config/plausibility.csv`.

| Basis contains | Low | High |
|---|---|---|
| `per $100` and `per year` (single premium life) | 0.10 | 2.00 |
| `per $1,000` and `per month` (outstanding balance life) | 0.10 | 3.00 |
| `per $100` with a term in months (single premium disability) | 0.50 | 15.00 |
| anything else | no range check | |

## 8. Page design

### 8.1 Wireframe in words

Top of page: the title "Prima Facie Rate Tracker", then one sentence saying what the page is, then a line "Last checked: 3 December 2026. 43 of 44 states checked." A state that was not checked in the last run is named there.

**Box 1, "Recent changes".** Heading, then a subheading "Communicated in the last 12 months, soonest effective date first". A table with one row per record:

| Effective | State | Product | Change | Communicated | Source |
|---|---|---|---|---|---|
| 1 Jan 2027, tagged "Upcoming" | State name | Credit life | Headline rate old to new with the percent change, or "See source" when there are several | 1 Oct 2026 | Link to the official document, and "saved copy" |

Under each row, the plain-English summary in smaller text. If there are no records, the box says "No changes communicated in the last 12 months."

**Box 2, "History by state".** Heading, then "Changes with effective dates in the last 15 years". A list of states in alphabetical order. Each state is a row showing a caret, the state name and a count, for example "Indiana (4)". Selecting the row or the caret opens it in place. A state with no records shows "(0)" and opens to "No changes recorded."

Inside an open state: records newest first. Each record shows the effective date, product, each rate item as plan, basis, old rate, new rate and percent change, the date communicated, the legal basis, the summary, the source link and the saved-copy link. A record with `verified` false carries the label "Unverified: no primary source located". A `no_change` record reads "Reviewed, no change".

Footer: a disclaimer that the page is an unofficial personal compilation, may be incomplete or out of date, is not legal or actuarial advice, and that the linked official source governs. A link to the repository. No names.

### 8.2 Expanding a state

Each state is a native HTML `details` element with a `summary`. The browser supplies the caret, keyboard operation and screen-reader state with no JavaScript. All states start closed.

### 8.3 Mobile

Single column at any width; maximum content width about 50 rem. Under 640 px, the Recent table turns into stacked cards, each field on its own line with its label. Tap targets are at least 44 px high. Long URLs are never shown as text; links use the document title.

### 8.4 Accessibility basics

- One `h1`, an `h2` for each box, in order. `lang="en"` on the page.
- Table has a caption and `th` cells with `scope`.
- Text contrast at least 4.5 to 1. Meaning never carried by color alone: "Upcoming" and "Unverified" are words.
- Links describe their target ("Bulletin 2026-07 (official PDF)"), and say when they open a PDF.
- Dates written with the month as a word. Rates shown with their basis every time.
- Visible keyboard focus. Page works with CSS off.
- Honors the reader's dark-mode setting through a small media query.

## 9. Quality and safety

### 9.1 Tests

Run with `pytest`. Tests use saved fixtures and never touch the network.

| Area | Test cases |
|---|---|
| Normalize | Volatile date removed; nav removed; selector applied; same content with different whitespace gives the same hash |
| Links | Relative to absolute; fragment and tracking parameters dropped; anchor text collapsed |
| Keywords | Each example in 3.2; case differences; "credit union" alone does not pre-match |
| Detect | Baseline creates nothing; new matching link fires R1; hash change on `any_change` fires R2; change with no match gives R3; 26 new links gives `suspect_redesign` |
| Fetch classification | 200 with marker is `ok`; 200 without marker is `suspect`; 403 is `blocked`; timeout is `failed`; size under 40% is `suspect` |
| Documents | Text PDF extracts; image-only PDF gives `unreadable_document` |
| Records | `pct_change` formula, including null cases; id generation; validation table in 7.4 |
| Review | Each allowed transition; each forbidden transition raises an error |
| Build | Recent filter boundary at exactly 365 days; 15-year boundary; sort orders; unverified label; zero-record state |
| Notify | Subject line for each pattern; unchecked states listed first; no secret value appears in output |
| Seed | Template round trip; merge of rows into one record; each error and warning |

### 9.2 Dry run and local modes

`--dry-run` makes no writes, sends no email, opens no issue, and prints the email it would send. `--offline` reads fixtures. `--states` limits the run. Every new source is exercised with `--dry-run --states XX` before it is enabled.

### 9.3 Logging

Human-readable lines to the console, one per source. The full structured log goes to `data/runs/`. The workflow also writes a short table to the GitHub Actions run summary. Logs never contain secrets or the alert address.

### 9.4 Polite fetching

- At least 5 seconds between requests to one host. One connection at a time.
- A descriptive `User-Agent` naming the project, the repository URL and the project mailbox.
- Conditional requests (`If-Modified-Since`, `If-None-Match`) when the server supports them.
- Total load is about 2 requests per source per month plus document downloads, which is far below any reasonable threshold.
- No login, no form submission, no CAPTCHA solving, no rotating addresses, no headless browser in version 1.

### 9.5 Robots and terms of use by source type

| Source type | Position |
|---|---|
| State insurance department pages, bulletins, orders | Public notices issued for the industry. Check `robots.txt` per host and obey it. Record the result in `sources.csv` notes. |
| State legislature and secretary of state sites hosting statutes and administrative code | Same. Some publish terms for bulk reuse; fetching one section twice a month is not bulk. Read each site's terms once in Stage 6 and record anything restrictive. |
| Official codes hosted by a commercial publisher (expected for CA, NJ, NY) | Do not fetch by script and do not archive copies. Link to the official page in records. Monitor the department's bulletin and rulemaking pages instead. |
| Third-party legal sites and compliance news sites | Never used as a source of record and never fetched by the job. Useful to a human for finding the official document. |
| State registers (for example a bulletin of proposed and adopted rules) | Fetch the table of contents or search result for the agency only; obey `robots.txt`. |

**Saved copies in a public repository.** A saved copy is a republication. Federal works are in the public domain, but state works are not uniformly so, and some states assert copyright in their codes. DECIDED 2026-11-16 (Q10): all saved copies are public in the repository. The exception in the table above still applies: codes hosted by a commercial publisher are not fetched or copied at all. If a state or publisher objects to a saved copy, remove it and keep the hash and link. This is not legal advice.

### 9.6 Link check

On the first run of each month, `linkcheck.py` requests every `url` in `sources.csv` and every `source_url` in confirmed records, with the same rate limit. Any result other than HTTP 200, and any redirect to a different host, is listed in the email. A broken record link is not edited automatically; the saved copy remains, and the owner updates the URL with `review amend`.

### 9.7 Workflow safety

- `check.yml` has `permissions: contents: write, issues: write` and nothing more. `pages.yml` has only the Pages permissions.
- A `concurrency` group prevents two check runs from overlapping.
- Secrets are passed as environment variables to the single step that needs them.
- Third-party Actions are avoided; official `actions/*` are pinned to a version. Claude Code must look up the current versions at build time and not write them from memory.
- GitHub may disable scheduled workflows in a repository with no recent activity (commonly described as 60 days; verify in GitHub's documentation in Stage 8). The job commits a run log every run, which keeps the repository active.
- Scheduled runs can start late under load. The cron minute is set off the hour.

## 10. Build plan

Each stage ends at a gate. Claude Code stops at the gate, shows the acceptance test results, and waits. Each stage adds an entry to `docs/decisions.md` for every decision made.

Conventions for every task: Python 3.12; type hints; functions under 50 lines; no network in tests; no employer name, internal data or personal name anywhere; explain each terminal command in one line before running it.

### Stage 0. Repository and configuration

**Create:** `README.md`, `.gitignore` (must include `internal/`, `site/`, `__pycache__/`, `.venv/`, `.env`), `requirements.txt`, `CLAUDE.md`, `docs/plan.md` (this file), `docs/decisions.md`, `docs/research_log.md`, `config/states.csv` (Appendix B), `config/sources.csv` (Appendix A), `config/keywords.csv`, `config/official_domains.csv` (empty with header), `config/plausibility.csv`, `pfrt/__init__.py`, `pfrt/__main__.py`, `pfrt/config.py`, `tests/test_config.py`, `.github/workflows/tests.yml`.

**Behavior.**
- `config.load_states(path) -> list[State]` and `config.load_sources(path) -> list[Source]` read the CSVs into dataclasses and raise `ConfigError` naming the file, row number and column on: missing column, duplicate `source_id`, `state` not in `states.csv`, `role` not in the allowed set, `watch_mode` not in the allowed set, `enabled` not `yes` or `no`, or `enabled` equal to `yes` with a blank `url`.
- `python -m pfrt config check` prints "44 states, N sources (M enabled)" or the errors.

**Acceptance tests.**
1. `pytest` passes.
2. `python -m pfrt config check` prints 44 states.
3. A copy of `sources.csv` with a duplicated `source_id` produces an error naming the row.
4. `git status` shows nothing from `internal/` after a file is placed there.
5. A search of the repository for the blocklist terms returns nothing.

**Owner decides or approves:** repository name and public visibility; Q5 (`confirmed_by` value); commit email set to the GitHub no-reply address; confirms A9.

### Stage 1. Fetch and detect for five pilot states

Pilot states and why: **IN** (HTML bulletin list with PDF bulletins), **WI** (bulletins; a notice may be due now), **VA** (order PDFs; no index located yet), **ID** (single PDF, `any_change`), **IL** (regulation text as a lagging source, plus a recent real change to test against).

**Create:** `pfrt/fetch.py`, `pfrt/normalize.py`, `pfrt/detect.py`, `pfrt/documents.py`, `tests/fixtures/` (saved pages for the five states), `tests/test_fetch.py`, `tests/test_normalize.py`, `tests/test_detect.py`, `tests/test_documents.py`. **Change:** `config/sources.csv`, `config/official_domains.csv`, `docs/research_log.md`, `pfrt/__main__.py`.

**Behavior.**
- `fetch.get(source, session, last_byte_count) -> FetchResult` with fields `status`, `http_status`, `final_url`, `content`, `content_type`, `byte_count`, `error`. Classification as in 2.4 step 3.4.
- `fetch.robots_allowed(url, user_agent) -> bool` using `urllib.robotparser`; a missing `robots.txt` means allowed; a `robots.txt` that cannot be fetched because of a server error means not allowed for this run.
- `normalize.html_to_text`, `normalize.extract_links`, `normalize.sha256_hex` as in 3.1.
- `detect.keyword_match(text, keywords) -> Match` and `detect.compare(source, old_snapshot, new_text, new_links) -> list[Finding]` implementing R1 to R4 and the redesign rule. `Finding` has `rule`, `url`, `anchor_text`, `matched_keywords`.
- `documents.download(url, state, today) -> ArchivedFile` and `documents.extract_text(path) -> str` as in 2.2 and 3.3.
- `python -m pfrt check --dry-run --states IN,WI,VA,ID,IL` prints one line per source and the findings.
- Run the verification procedure in 1.4 for the five states. For WI and VA, locate the index page.

**Acceptance tests.**
1. `pytest` passes, including every case in 9.1 for normalize, links, keywords, detect, fetch classification and documents.
2. Fixture test: the IN bulletin list fixture with one bulletin link removed is the "old" page; the full fixture is the "new" page. Expected: exactly one R1 finding, for the removed bulletin.
3. Fixture test: the same page twice. Expected: no findings.
4. Fixture test: the ID PDF and a copy with one byte changed. Expected: one R2 finding.
5. Live dry run for the five states completes with each source `ok` or with a stated reason, in under 3 minutes, with no writes to `data/`.
6. `sources.csv` shows `fetched` and a `verified_on` date for each pilot source that passed.

**Owner decides or approves:** the located index pages for WI and VA; whether the pilot sources' `must_contain` strings look right; reads the WI page by hand for a possible current notice.

### Stage 2. Candidate queue, records and review commands

**Create:** `pfrt/candidates.py`, `pfrt/records.py`, `pfrt/review.py`, `tests/test_candidates.py`, `tests/test_records.py`, `tests/test_review.py`. **Change:** `pfrt/__main__.py`, `pfrt/detect.py`, `CLAUDE.md`.

**Behavior.**
- `candidates.create(finding, source, archived, run_id) -> Candidate`; returns `None` when a candidate or record already has the same `archived_sha256` or `document_url`.
- `candidates.next_id(state, today, existing_ids) -> str`. Example: with `c-20261203-IN-01` present, returns `c-20261203-IN-02`.
- `records.pct_change(old, new, same_basis) -> float | None`. Examples: `(0.50, 0.45, True)` gives `-10.0`; `(None, 0.45, True)` gives `None`; `(0.50, 0.45, False)` gives `None`; `(0.0, 0.45, True)` gives `None`.
- `records.make_id(state, product, effective_date, existing_ids) -> str`.
- `records.validate(record, context) -> list[Issue]` implementing 7.4.
- `review` commands `list`, `show`, `confirm`, `reject`, `amend`, `retract` as in section 5. `confirm` refuses when a required field is empty. Every command appends to `history`.
- `check` without `--dry-run` now writes snapshots, archives, candidates and a run log.
- `CLAUDE.md` gains the review protocol from 5.3.

**Acceptance tests.**
1. `pytest` passes, including all transition tests.
2. Using fixtures and `--offline`: first run creates baselines and no candidates; second run against the "new" fixture creates one candidate file with the expected id and fields.
3. A third identical run creates no new candidate.
4. `review confirm` on that candidate with test values writes a record with status `confirmed` and removes the candidate file; `review list` is then empty.
5. `review confirm` on a rejected record exits with an error and changes nothing.

**Owner decides or approves:** does one end-to-end confirm and one reject by hand on test data; approves the wording of the prompts.

### Stage 3. Email and the scheduled workflow in test mode

**Create:** `pfrt/notify.py`, `tests/test_notify.py`, `.github/workflows/check.yml`. **Change:** `pfrt/__main__.py`.

**Behavior.**
- `notify.compose(run_log, candidates, states, sources) -> Email(subject, body)` as in 6.3.
- `notify.send(email, env) -> None` using `smtplib` with TLS; raises `NotifyError` with no secret in the message.
- `notify.open_issue(email, env) -> None` using the workflow's built-in token.
- `check.yml`: triggers `schedule` (commented out until Stage 8) and `workflow_dispatch` with inputs `states`, `dry_run`, `send_test_email`. Steps: check out, set up Python, install requirements, run tests, run the check, commit `data/` and `archive/` if changed, push.

**Acceptance tests.**
1. `pytest` passes; a test asserts the composed body for a run with 2 candidates and 1 failed state has the sections in the order in 6.3 and the subject `[PFRT] 2 candidates; 1 state not checked (DATE)`.
2. A manual workflow run with `send_test_email` delivers a message to the alert address.
3. A manual run for the five pilot states with `dry_run` false commits snapshots and a run log, and sends a correctly formed email.
4. Temporarily pointing one pilot source at a URL that returns 404 produces an email whose first section names that state and source. The URL is then restored.
5. The workflow log contains none of the three secret values.

**Owner decides or approves:** Q3 (issue as backup channel); creates the mailbox and the three secrets.

### Stage 4. The page

**Create:** `pfrt/build_site.py`, `templates/index.html.j2`, `tests/test_build.py`, `.github/workflows/pages.yml`. **Change:** `pfrt/__main__.py`, `README.md`.

**Behavior.**
- `build_site.select_recent(records, today) -> list[Record]` and `build_site.select_history(records, today) -> dict[str, list[Record]]` as in 2.5.
- `build_site.render(recent, history, states, last_run, out_dir) -> Path`.
- `pages.yml` builds and deploys `site/` on push to `main` using GitHub's official Pages actions.

**Acceptance tests.**
1. `pytest` passes, including boundaries: a record communicated exactly 365 days before the build date is in Recent, 366 days is not; an effective date exactly 15 years before is in History, one day earlier is not.
2. With four test records (two states, one unverified, one `no_change`), the page shows: Recent with the expected rows in ascending effective-date order; all 44 states in History in alphabetical order with correct counts; the "Unverified" label once; "Reviewed, no change" once.
3. The HTML has no `script` element, one `h1`, and passes an HTML validator with no errors.
4. Keyboard only: Tab reaches each state; Enter or Space opens it.
5. At 375 px width nothing scrolls sideways.
6. The public URL loads after a push.

**Owner decides or approves:** wording of the intro sentence and the disclaimer; A8 sort order; the look on a phone.

### Stage 5. Seed import

**Create:** `pfrt/seed.py`, `seed/import_template.csv`, `seed/README.md` (process 7.2 and checklist 7.3), `tests/test_seed.py`, `tests/fixtures/seed_good.csv`, `tests/fixtures/seed_bad.csv`. **Change:** `pfrt/__main__.py`, `pfrt/review.py` (add `--origin` and `--batch`).

**Behavior.**
- `seed.parse(path) -> list[SeedRow]`; `seed.merge(rows) -> list[Candidate]` grouping on state, product, effective date.
- `seed.validate(path, context) -> list[Issue]`.
- `seed.scan(folder, blocklist_path) -> list[Hit]`: case-insensitive search of CSV text, file names, extractable PDF text and PDF metadata.
- `seed import` writes candidates with `origin` of `seed` and a `batch` name taken from the file name.

**Acceptance tests.**
1. `pytest` passes.
2. `seed validate tests/fixtures/seed_good.csv` reports 0 errors.
3. `seed validate tests/fixtures/seed_bad.csv` reports one of each error in 7.4, each naming its row.
4. Three rows with the same state, product and effective date import as one candidate with three rate items.
5. `seed scan` on a folder containing a file with a blocklisted term exits non-zero and names the file.
6. `review confirm --batch` confirms only rows with no warnings.

**Owner decides or approves:** supplies the first scrubbed batch; Q9 (plausible ranges); A5 (headline rates only); A6 (no-change notices).

### Stage 6. All states

Work in four batches of about ten states, each with its own gate. Order: remaining notice-driven states first (AZ, IA, MN, NM, OH, PA, SC), then regulation-fixed, then statute-fixed and unclear, then the twelve states from the second research pass (NE and UT first).

**Change:** `config/sources.csv`, `config/states.csv`, `config/official_domains.csv`, `docs/research_log.md`, fixtures and tests for any new page pattern.

**Per state, Claude Code:**
1. Runs the verification procedure in 1.4.
2. Registers at least one `leading` source, or records in `notes` why none exists and leaves the state on the "Not monitored" list.
3. Runs `check --dry-run --states XX` twice, at least a day apart, and confirms the second run reports no change. A source that changes with no real update gets a `selector` or a normalization pattern, with a test.
4. Lists the state's current bulletins or orders that match the keywords, so the owner can look for anything already issued and not yet in the log.
5. Sets `iui`, `group`, `cycle_years` and `next_notice_expected_by` from what the primary source says, citing the URL, or leaves them `unknown`.

**Acceptance tests, per batch.**
1. Every state in the batch has a row in `research_log.md` with URLs fetched, status, robots result and open issues.
2. `config check` passes; `pytest` passes.
3. Two consecutive dry runs for the batch show no noise changes.
4. No source row has `enabled` of `yes` with `verification` other than `fetched`.

**Owner decides or approves:** per state, the source list and the review of current documents; Q4 (Alabama); Q7 for any `needs_browser` source; Q11 (statute-fixed states).

### Stage 7. AI annotation (optional; after Q2)

**Create:** `pfrt/ai.py`, `tests/test_ai.py`. **Change:** `pfrt/__main__.py`, `pfrt/notify.py`, `pfrt/review.py`, `check.yml`, `requirements.txt`.

**Behavior.**
- `ai.annotate(candidate, text, client, model) -> dict | None` returns the `ai` object in 2.2 or `None` on any failure. Input capped at 60,000 characters. The prompt and the expected JSON shape live in `ai.py` with a test that a malformed reply yields `None`.
- Model name and current price are looked up at build time from the provider's documentation, not written from memory.
- `--ai off` is the default locally. The workflow passes `--ai hybrid` only when the secret exists.

**Acceptance tests.**
1. `pytest` passes with the API client mocked.
2. With no API key, the run completes and candidates have `ai` of `null`.
3. With the key set, a manual run on a known bulletin fixture stores a draft; the email marks every draft value "AI draft, verify against source".
4. Removing the key afterward produces the same candidates as before.

**Owner decides or approves:** sets a monthly spending limit on the API account; adds the secret.

### Stage 8. Scheduled production run

**Create:** `pfrt/linkcheck.py`, `tests/test_linkcheck.py`. **Change:** `check.yml` (enable the schedule), `pfrt/__main__.py`, `README.md` (operations section), `docs/decisions.md`.

**Behavior.**
- Enable `schedule` on the 3rd and 18th at an off-the-hour minute, in UTC.
- `linkcheck.run(sources, records) -> list[LinkResult]` as in 9.6.
- Expected-notice check as in 3.5.
- `README.md` operations section: what each email section means, what to do for each status, how to add or change a source, how to rotate the app password, how to re-enable a disabled workflow.

**Acceptance tests.**
1. Two consecutive scheduled runs start within an hour of the scheduled time and send an email each.
2. The first run of a month includes link check results.
3. Setting one state's `next_notice_expected_by` to a past date produces the "Expected notice not seen" line; the value is then restored.
4. Disabling a source for one run moves its state to "Not monitored" in the email.
5. Owner completes one real candidate from email to published page using only section 5.

**Owner decides or approves:** go-live; a calendar reminder every six months to read the "Not monitored" list and the keyword list.

## 11. Risks and open questions

### 11.1 Risks, ranked

| # | Risk | Likelihood | Impact | Recommendation |
|---|---|---|---|---|
| R1 | The job stops running, or its email stops arriving, and silence is read as "no changes" | Medium | High | Email after every run (decided). Issue as second channel. Commit each run. |
| R2 | A state is unmonitored or blocked for months and nobody acts on it | High | High | "Not monitored" and "ACTION" sections at the top of every email. Stage 6 gate per state. Accept that some states will need a manual quarterly check, and list them on the page's "Last checked" line. |
| R3 | A notice appears on a page the job does not watch, or with a title that matches no keyword | Medium | High | Several sources per state; expected-notice check; R2 on dedicated documents; review "Other page changes". |
| R4 | A statute-fixed state changes rates by legislation; the codified text updates late | Low | High | Q11. At minimum, a twice-yearly manual check of LA, MS, MO and NC during and after session. |
| R5 | Baseline hides a change already published before monitoring started | Medium | High | Owner reviews each state's current documents at onboarding (Stage 6 step 4). Wisconsin first. |
| R6 | A government site blocks GitHub's servers | Medium | Medium | Report as blocked; try the state's alternate host if one exists; otherwise manual. Running the job from a home computer is a fallback that changes the hosting decision, so it is not adopted now. |
| R7 | Detection lag: up to about 15 days between publication and the next run, plus review time | Certain | Low to medium | Lead times seen in excerpts were months. A weekly schedule would cost nothing extra and halve the lag; this is a fixed decision, so it is noted and not changed. |
| R8 | Eight states have a citation and no official URL (CA, GA, MI, MT, NJ, NY, PA, WY), and several notice-driven states have no confirmed publication channel (MN, ND, OH, OR, WA, WV) | Medium | Medium | Stage 6. Expect two or three to end up manual. |
| R9 | Internal information reaches the public repository through seed data | Low | High | Facts-only CSV; official copies only; `seed scan` with a private blocklist; staged-diff review; `internal/` git-ignored from the first commit. |
| R10 | Republishing saved copies of state documents raises a copyright or terms question | Low | Medium | Accepted by the owner (Q10). Remove a copy on objection; keep hash and link. |
| R11 | A wrong rate or date is confirmed and published | Low | Medium | Values typed or accepted by the owner from the saved document; continuity check; plausibility ranges; disclaimer; `amend` with history. |
| R12 | Page redesigns break sources over time | High | Low | `must_contain`, redesign rule, monthly link check. Budget an hour a quarter for source upkeep. |
| R13 | AI draft is trusted without checking | Low | Medium | Drafts labeled; confirm step requires accepting each value; AI cannot change status. |
| R14 | Mailbox app password expires or the account is locked for inactivity | Medium | Medium | Issue as backup; job exits non-zero on send failure so GitHub emails the account. |

### 11.2 Open questions

**Q1. DECIDED 2026-11-16: Option A, email after every run.**
The fixed decision is to email when candidates are found or a state could not be checked. The problem: if the workflow is disabled, the schedule is dropped, or the mailbox fails, no email arrives, which is exactly what a quiet month looks like.
- Option A (recommended): a short email after every run, 24 a year. The subject line says "No candidates; all 44 states checked", so it can be read without opening.
- Option B: keep the fixed decision and add a monthly "still alive" email on the first run of the month.
- Option C: keep the fixed decision unchanged and rely on GitHub's failure emails. Does not cover a disabled schedule.

**Q2. DECIDED 2026-11-16: Option A, hybrid on Sonnet 5.5, as a trial.**
- Option A (recommended): hybrid on Sonnet 5.5, annotate only, expected under $1 a month.
- Option B: hybrid on Haiku 5.5, a few cents a month, weaker on dense rate tables.
- Option C: rules only. The system is complete without AI.

**Q3. NEEDS TROY'S DECISION. Notification channels.**
- Option A (recommended): dedicated Gmail by SMTP, plus a GitHub issue per run that has candidates or failures.
- Option B: email only.
- Option C: GitHub issues only, with no mailbox and no secrets.

**Q4. SETTLED BY THE RULES 2026-11-20 (owner may revisit): both agencies are monitored; the Banking rule 155-2-2-.12 holds the credit life and disability prima facie rates, because 482-1-117-.04(r) defines "Superintendent" as the Superintendent of Banks and -.10 makes the Superintendent's maximum rates the prima facie rates; IUI rates are the Department of Insurance's 482-1-093 Exhibit B. See `docs/decisions.md`.** Original question: Alabama. Search excerpts show rate rules from both the Department of Insurance (ch. 482-1-117, which refers to maximum rates promulgated by the Superintendent) and the State Banking Department (r. 155-2-2-.12). Which is the prima facie rate for this log: insurance only, banking only, or both as separate sources? Recommendation: monitor both and decide at the first candidate.

**Q5. NEEDS TROY'S DECISION. What goes in `confirmed_by` in a public repository?**
- Option A (recommended): the word `owner`.
- Option B: initials.
- Option C: the GitHub username.

**Q6. NEEDS TROY'S DECISION. Are "reviewed, no change" notices recorded?** Recommendation: yes, shown in History only (A6). They prove the cycle was checked and set the next expected date.

**Q7. NEEDS TROY'S DECISION, when it first arises. Pages that need a browser to render.**
- Option A (recommended): find a different official URL; if none, mark the state manual.
- Option B: add a headless browser to the job. More moving parts, slower runs, and some sites treat it as unwelcome automation.

**Q8. DOC and RTF sources** (updated 2026-11-20: DOC text is now extracted, because Florida publishes its rules only as Word files; RTF unchanged) (Maine's rule is a Word file; Iowa offers RTF). Version 1 hashes the bytes and does not extract text, which is enough for `any_change`. Recommendation: accept this, and prefer a PDF or HTML version of the same rule where the state offers one.

**Q9. NEEDS TROY'S DECISION. Plausible rate ranges** in 7.4 are placeholders. Set them from professional judgment, or switch the check off.

**Q10. DECIDED 2026-11-16: Option B, everything saved publicly** (publisher-hosted codes are still not copied).
- Option A (recommended): bulletins, orders and notices saved publicly; codified text saved as hash plus excerpt publicly, full copy kept privately.
- Option B: everything saved publicly.
- Option C: nothing saved publicly; hash and link only. Weakest audit trail, lowest exposure.

**Q11. NEEDS TROY'S DECISION. Statute-fixed states** (LA, MS, MO, NC, possibly others).
- Option A (recommended for version 1): watch the codified section as a lagging source and the department's bulletins as a leading source, and add a manual check twice a year, listed in the email footer when due.
- Option B: add legislative bill-search monitoring per state. More reliable and much more work; each legislature's site is different.

**Q12. Where does Minnesota publish adjusted rates?** Not found. Until it is, Minnesota is only partly monitored. Recommendation: owner supplies the last known notice, if one exists, so the channel can be identified.

**Q13. Kentucky and Montana.** No prima facie rate rule appeared in the excerpts. They may regulate by filed rates and a loss-ratio standard. Recommendation: confirm in Stage 6; if there is no state-set rate, mark `cl` and `cd` as `no` in `states.csv` and say so on the page.

**Q14. Terminology.** Texas uses "presumptive premium rate"; New Mexico uses "presumptively acceptable". The site title says "prima facie". Recommendation: keep the title and show the state's own term in each record's summary.

## Appendix A. Draft `config/sources.csv`

Every URL below was seen in search results on 2026-11-16 and has not been fetched. All rows start with `enabled` set to `no`; Stage 1 and Stage 6 turn them on after fetching. Rows with a blank URL record a citation whose official location still has to be found. `must_contain` and `selector` are left for Stage 1.

```csv
source_id,state,products,role,watch_mode,url,format,selector,must_contain,citation,enabled,verification,verified_on,notes
AL-reg-117,AL,CL;CD,lagging,any_change,https://admincode.legislature.state.al.us/api/chapter/482-1-117,html,,,Ala. Admin. Code ch. 482-1-117,no,search_seen,2026-11-16,"URL path contains /api/; confirm it is the public page. See Q4."
AL-reg-093,AL,IUI,lagging,any_change,https://admincode.legislature.state.al.us/api/chapter/482-1-093,html,,,Ala. Admin. Code ch. 482-1-093,no,search_seen,2026-11-16,"Credit property and involuntary unemployment."
AL-banking-12,AL,CL;CD,lagging,any_change,https://banking.alabama.gov/wp-content/uploads/2023/06/155_2_2_12.pdf,pdf,,,Ala. Admin. Code r. 155-2-2-.12,no,search_seen,2026-11-16,"Banking Department maximum rates. See Q4. Leading source not located."
AZ-order-life,AZ,CL,leading,any_change,https://difi.az.gov/sites/default/files/Credit%20Life%20Insurance.pdf,pdf,,,A.A.C. R20-6-604.03 and R20-6-604.04,no,search_seen,2026-11-16,"2025 docket 25A-005-INS. Order at least every three years. Find the index page that links orders."
AZ-order-dis,AZ,CD,leading,any_change,https://difi.az.gov/sites/default/files/Credit%20Disability%20Insurance_1.pdf,pdf,,,A.A.C. R20-6-604.05,no,search_seen,2026-11-16,"2025 docket 25A-003-INS."
AZ-hearings,AZ,CL;CD;IUI,leading,any_change,https://publicmeetings.az.gov/content/loss-ratio-and-prima-facie-rates-hearings-credit-insurance,html,,,A.R.S. 20-1621.05,no,search_seen,2026-11-16,"2025 hearing notice covering life, disability, property and unemployment. Credit unemployment order URL not located."
CA-reg,CA,CL;CD,lagging,any_change,,html,,,10 CCR 2248.30 to 2248.47; Ins. Code 779.36,no,unverified,,"Official code host not located; may be a commercial publisher. Do not scrape. Find the Department's rulemaking page as leading source."
CA-reg-iui,CA,IUI,lagging,any_change,,html,,,10 CCR 2670 series,no,unverified,,"One article shown as repealed in excerpt. Status unclear."
CO-regs,CO,CL;CD,leading,new_links,https://doi.colorado.gov/statutes-regulations-bulletins/colorado-insurance-regulations,html,,,Regulation 4-9-2 (3 CCR 702-4),no,search_seen,2026-11-16,"Department regulations and rulemaking page."
DE-reg-1701,DE,CL;CD,lagging,any_change,https://regulations.delaware.gov/api/AdminCode/title18/1701/ebbb48fd-878b-47de-b873-fe058a9705fe,html,,,18 DE Admin. Code 1701 s. 2.0,no,search_seen,2026-11-16,"New state regulations system since May 2025; confirm stable URL. Leading source not located."
FL-rule-notices,FL,CL;CD,leading,any_change,https://flrules.org/Gateway/View_notice.asp?id=7137859,html,,,Rules 69O-163.010 and 69O-163.011; s. 627.6785 F.S.,no,search_seen,2026-11-16,"This is one 2009 notice, kept as a pointer. Find the chapter 69O-163 page that lists notices."
GA-reg,GA,CL;CD,lagging,any_change,,html,,,Ga. Comp. R. & Regs. 120-2-27-.03 and 120-2-27-.07,no,unverified,,"Official host not located."
HI-statute,HI,CL;CD,lagging,any_change,https://data.capitol.hawaii.gov/hrscurrent/Vol09_Ch0431-0435H/HRS0431/HRS_0431-0010B-0108.htm,html,,,HRS 431:10B-108,no,search_seen,2026-11-16,"Authority to adopt prima facie rates by rule. Rates are in HAR 16-6-11 and 16-6-12; official HAR host not located."
ID-rates-pdf,ID,CL;CD,leading,any_change,https://doi.idaho.gov/wp-content/uploads/info/rules/18-03-05-Credit-Prima-Facie-Rates.pdf,pdf,,,IDAPA 18.03.05.014,no,search_seen,2026-11-16,"Rates posted on Department website; attachment dated 6/1/2022 in excerpt. Pilot."
ID-rules-index,ID,CL;CD,leading,new_links,https://doi.idaho.gov/?p=26206,html,,,IDAPA 18.03.05,no,search_seen,2026-11-16,"Page that links the attachment. Confirm canonical URL."
IL-reg-1051-50,IL,CL,lagging,any_change,https://www.ilga.gov/ftp/JCAR/AdminCode/050/050010510000500R.html,html,,,50 Ill. Adm. Code 1051.50,no,search_seen,2026-11-16,"Shows amendment effective May 22, 2025. Pilot. A&H appears to be Part 1052; URL not located. Company bulletins page not located."
IN-bulletins,IN,CL;CD,leading,new_links,https://www.in.gov/idoi/2591.htm,html,,,760 IAC 1-5.1-9,no,search_seen,2026-11-16,"Bulletin list. Triennial bulletins titled Credit Life and Accident and Health Rates. Pilot."
IA-rule-28-10,IA,CL;CD,lagging,any_change,https://www.legis.iowa.gov/docs/iac/rule/02-05-2025.191.28.10.pdf,pdf,,,191 IAC 28.10,no,search_seen,2026-11-16,"URL is date-stamped; find the undated current-rule URL. Adjusted rates are published by bulletin; bulletin index not located."
KS-regs,KS,CL;CD,lagging,new_links,https://insurance.ks.gov/department/LegalIssues/all-adopted-regulations.php,html,,,K.A.R. 40-5-107,no,search_seen,2026-11-16,"Department list of adopted regulations. Leading source not located."
KY-kar-19,KY,CL;CD,lagging,new_links,https://apps.legislature.ky.gov/law/kar/titles/806/019,html,,,806 KAR ch. 19; KRS 304.19-080,no,search_seen,2026-11-16,"No rate regulation seen in this chapter. See Q13."
LA-rs-6-969-25,LA,CL;CD,lagging,any_change,https://legis.la.gov/Legis/Law.aspx?d=106294,html,,,La. R.S. 6:969.25,no,search_seen,2026-11-16,"Motor vehicle credit transactions. Other schedules cited at R.S. 9:3332 and 9:3542. Statute-fixed; see Q11."
ME-rule-220,ME,CL;CD,lagging,any_change,https://www11.maine.gov/sos/sites/maine.gov.sos/files/content/assets/031c220.doc,doc,,,02-031 C.M.R. ch. 220 ss. 9 and 10,no,search_seen,2026-11-16,"Word file; hash only. Confirm host. Leading source not located."
MD-bulletin-00-25,MD,CL;CD,leading,any_change,https://insurance.maryland.gov/insurer/documents/bulletins/00-25.pdf,pdf,,,COMAR 31.13.01.10 and 31.13.01.15,no,search_seen,2026-11-16,"Year-2000 bulletin kept as a pointer. Find the bulletin index. COMAR host not located. IUI at COMAR 31.13.03.10."
MI-reg,MI,CL;CD,lagging,any_change,,html,,,Mich. Admin. Code R 550.211 and R 550.212,no,unverified,,"Official code host not located. DIFS bulletins are under michigan.gov/difs/legal/bulletins; index URL not located."
MN-rules-2760,MN,CL;CD,lagging,any_change,https://www.revisor.mn.gov/rules/2760/,html,,,Minn. R. 2760.0050 to 2760.0080,no,search_seen,2026-11-16,"Triennial adjustment under 2760.0080. Where adjusted rates are published is unknown. See Q12."
MS-regs,MS,CL;CD,lagging,new_links,https://www.mid.ms.gov/?p=100,html,,,Miss. Code 83-53-23,no,search_seen,2026-11-16,"Department regulations list. Confirm canonical URL. Statute-fixed; see Q11."
MS-bulletins,MS,CL;CD,leading,new_links,https://www.mid.ms.gov/?p=98,html,,,Miss. Code 83-53-23,no,search_seen,2026-11-16,"Department bulletins list. Confirm canonical URL."
MO-csr-600-2,MO,CL;CD,lagging,any_change,https://www.sos.mo.gov/cmsimages/adrules/csr/current/20csr/20c600-2.pdf,pdf,,,20 CSR 600-2.110; RSMo 385.070,no,search_seen,2026-11-16,"Statute-fixed; see Q11. Leading source not located."
MT-mca-33-21,MT,CL;CD,lagging,any_change,,html,,,MCA 33-21-205,no,unverified,,"No prima facie rate rule seen. See Q13."
NJ-reg,NJ,CL;CD,lagging,any_change,,html,,,N.J.A.C. 11:2-3.17,no,unverified,,"Official code host not located; may be a commercial publisher. Do not scrape."
NM-bulletin-2025-002,NM,CL;CD,leading,any_change,https://www.osi.state.nm.us/en/news/bulletin-2025-002,html,,,13.18.2.18 and 13.18.2.26 NMAC,no,search_seen,2026-11-16,"Single news post kept as a pointer. Find the bulletins index. Updated version posted July 23, 2025 per excerpt."
NM-rule-13-18-2,NM,CL;CD,lagging,any_change,https://www.srca.nm.gov/parts/title13/13.018.0002.pdf,pdf,,,13.18.2 NMAC,no,search_seen,2026-11-16,"Rule repealed and replaced 3/11/2025."
NY-reg,NY,CL;CD;IUI,lagging,any_change,,html,,,11 NYCRR 185.7; 11 NYCRR 187,no,unverified,,"Official code host not located; may be a commercial publisher. Do not scrape. Find DFS regulatory activity page as leading source."
NC-gs-58-57-45,NC,CD,lagging,any_change,https://www.ncleg.gov/EnactedLegislation/Statutes/PDF/BySection/Chapter_58/GS_58-57-45.pdf,pdf,,,G.S. 58-57-45,no,search_seen,2026-11-16,"Statute-fixed; see Q11. Credit life is G.S. 58-57-40; URL not seen, do not guess. No prima facie IUI rate per G.S. 58-57-35."
OH-rule-3901-1-14,OH,CL;CD,lagging,any_change,https://codes.ohio.gov/ohio-administrative-code/rule-3901-1-14,html,,,OAC 3901-1-14,no,search_seen,2026-11-16,"Triennial study mentioned in a rule-review document. Leading source not located."
PA-ch-73,PA,CL;CD;IUI,leading,new_links,,html,,,31 Pa. Code 73.106; 73.109; 73.112,no,unverified,,"Rates are published as notices in the Pennsylvania Bulletin, reviewed at least every three years. Official URLs not located."
SC-alerts,SC,CD,leading,new_links,https://doi.sc.gov/CivicAlerts.aspx?CID=10,html,,,S.C. Reg. 69-11.1,no,search_seen,2026-11-16,"Alert list including notices of tentative credit A&H rates, issued by August 1 each year, then a final order."
SC-lah,SC,CL;CD,leading,new_links,https://doi.sc.gov/431/Life-Accident-Health,html,,,S.C. Reg. 69-11.1,no,search_seen,2026-11-16,"Life, accident and health unit page with a bulletins section. Credit life mechanism not found."
TX-bulletin-2005,TX,CL;CD,leading,any_change,https://www.tdi.texas.gov/bulletins/2005/b-0069-05.html,html,,,28 TAC ch. 3 subch. FF; Ins. Code ch. 1153,no,search_seen,2026-11-16,"2005 bulletin kept as a pointer. Texas term is presumptive premium rate. Find the bulletins index and the rules page."
VA-order-2024,VA,CL;CD,leading,any_change,https://scc.virginia.gov/getdoc/b707b397-4317-4b97-8c52-ac7ae2eeb265/ni240060,pdf,,,Va. Code 38.2-3725 and 38.2-3730,no,search_seen,2026-11-16,"Order for the triennium commencing January 1, 2025, case INS-2024-00060. Find the administrative letters and orders index. Pilot."
VA-code-3730,VA,CL;CD,lagging,any_change,https://law.lis.virginia.gov/vacode/38.2-3730/,html,,,Va. Code 38.2-3730,no,search_seen,2026-11-16,"Statute requiring triennial adjustment."
WI-bulletin-2026,WI,CL;CD,leading,any_change,https://oci.wi.gov/Pages/Regulation/Bulletin20261016PrimaFacieRates.aspx,html,,Prima Facie,Wis. Adm. Code Ins 3.25(13)(c),no,search_seen,2026-11-16,"Read by assisted fetch 2026-11-16; script fetch still required. Bulletin for the period beginning January 1, 2027. First candidate; see 1.5. Find the bulletins index and watch that instead."
WI-bulletin-2023,WI,CL;CD,leading,any_change,https://oci.wi.gov/Documents/Regulation/Bulletin20230928PrimaFacieRates.pdf,pdf,,,Wis. Adm. Code Ins 3.25(13)(c),no,search_seen,2026-11-16,"Bulletin for the period beginning January 1, 2024. Source of old rates for the 2027 record."
WI-rate-filing-guide,WI,CL;CD,leading,any_change,https://oci.wi.gov/Documents/OCIForms/RateFilings.PDF,pdf,,,Wis. Adm. Code Ins 3.25,no,search_seen,2026-11-16,"States the three-year cycle and October publication."
NE-igd-a2,NE,CL;CD,leading,any_change,https://doi.nebraska.gov/sites/default/files/doc/IGD%20--%20A2%202025.pdf,pdf,,,210 NAC ch. 22; Neb. Rev. Stat. 44-1709,no,search_seen,2026-11-16,"Guidance document carrying prima facie rates; issued January 14, 2025. File name includes the year, so a reissue will likely have a new URL; find the guidance documents index."
NE-rate-hearing,NE,CL;CD,leading,any_change,https://doi.nebraska.gov/node/1996,html,,,210 NAC ch. 22,no,search_seen,2026-11-16,"Notice of credit rate hearing with proposed rates. Date of this notice not seen."
NV-nac-690a,NV,CL;CD;IUI,lagging,any_change,https://www.leg.state.nv.us/nac/NAC-690A.html,html,,,NAC 690A.105 to 690A.155; NAC 690A.175,no,search_seen,2026-11-16,"Whole chapter on one page; use a selector for the rate sections."
NV-doi-credit,NV,CL;CD;IUI,leading,any_change,https://doi.nv.gov/Insurers/Life-Health/Credit-Insurance,html,,,NAC 690A.175,no,search_seen,2026-11-16,"Division credit insurance page describing the annual review."
NH-ins-1200,NH,CL;CD,lagging,any_change,https://gencourt.state.nh.us/rules/State_Agencies/ins1200.html,html,,,N.H. Admin. R. Ins 1201.08 to 1201.10,no,search_seen,2026-11-16,"Terms are nominal rates and actual premium rates. Leading source not located."
ND-ch-45-07-01-1,ND,CL;CD;IUI,lagging,any_change,https://ndlegis.gov/api/acdata/pdf/45-07-01.1.pdf,pdf,,,N.D. Admin. Code 45-07-01.1-04 to -06 and -09,no,search_seen,2026-11-16,"Triennial review under -09."
ND-bulletins,ND,CL;CD;IUI,leading,new_links,https://www.insurance.nd.gov/bulletins,html,,,N.D. Admin. Code 45-07-01.1-09,no,search_seen,2026-11-16,"Department bulletins list. Older credit rate bulletins seen (1992, 2002); none recent."
OK-part-7,OK,CL;CD,lagging,any_change,https://www.oid.ok.gov/wp-content/uploads/2019/10/C10S5P7.pdf,pdf,,,OAC 365:10-5-64 and 365:10-5-65; Appendix E,no,search_seen,2026-11-16,"Department copy; upload path dated 2019, may be stale. Terms are presumptively acceptable and presumptively reasonable. Leading source not located."
OR-rule-0026,OR,CL,lagging,any_change,https://secure.sos.state.or.us/oard/view.action?ruleNumber=836-060-0026,html,,,OAR 836-060-0026; 836-060-0041,no,search_seen,2026-11-16,"URL seen as a source citation on a third-party page; confirm. Health rates at 836-060-0031 follow the same URL pattern but that URL was not seen."
OR-dfr-rules,OR,CL;CD,leading,any_change,https://dfr.oregon.gov/rates-forms/Documents/crlhsrls.pdf,pdf,,,OAR 836-060-0000 to 836-060-0060,no,search_seen,2026-11-16,"Division copy of the credit rules. Director reviews every four years and may publish adjusted rates; channel not found."
SD-rule-03,SD,CL,lagging,any_change,https://sdlegislature.gov/api/Rules/5944.html,html,,,ARSD 20:06:06:03,no,search_seen,2026-11-16,"Credit life acceptable rates. URL path contains /api/; confirm it is the public page. Health rates at 20:06:06:04; URL not seen."
TN-rule-0780-01-04,TN,CL;CD,lagging,any_change,https://sharetngov.tnsosfiles.com/sos/rules/0780/0780-01/0780-01-04.pdf,pdf,,,Tenn. Comp. R. & Regs. 0780-01-04-.06,no,search_seen,2026-11-16,"Copy seen is a 1999 revision; confirm this is the current effective rule location."
TN-hearing-2026,TN,CL;CD,leading,any_change,https://www.tn.gov/content/dam/tn/commerce/documents/insurance/hearingnotice/RulemakingHearing_8-26-2026.pdf,pdf,,,Tenn. Comp. R. & Regs. ch. 0780-01-04,no,search_seen,2026-11-16,"2026 rulemaking hearing notice listing this chapter; rule .06 not in the excerpt. Read it. Find the page that lists hearing notices and watch that."
UT-rules,UT,CL;CD,leading,new_links,https://insurance.utah.gov/rules,html,,,Utah Admin. Code R590-91-7; R590-91-8; R590-91-10,no,search_seen,2026-11-16,"Department rules page linking R590-91 and its attachment. Revised rates are published by order before September 1, effective January 1."
UT-attachment,UT,CD,leading,any_change,https://insurance.utah.gov/wp-content/uploads/R590-91AttachmentCDI.pdf,pdf,,,Utah Admin. Code R590-91-8,no,search_seen,2026-11-16,"Credit disability rate attachment; excerpt shows format updated 06/2026 and data 06/2008."
WA-wac-170,WA,CD,lagging,any_change,https://lawfilesext.leg.wa.gov/Law/WAC/WAC%20284%20%20TITLE/WAC%20284%20-%2034%20%20CHAPTER/WAC%20284%20-%2034%20-170.htm,html,,,WAC 284-34-170; WAC 284-34-210,no,search_seen,2026-11-16,"Credit life is WAC 284-34-150; current-version URL not seen. Find the Commissioner's rulemaking page as leading source."
WV-rules,WV,CL;CD;IUI,lagging,new_links,https://www.wvinsurance.gov/Resources_Policy-Legislation_Insurance-Rules,html,,,W. Va. Code R. 114-6-6 to 114-6-8,no,search_seen,2026-11-16,"Commissioner's list of rules; series 114-06 shown effective 7/1/11. Triennial adjustment is published; insurance bulletins index not seen."
WY-ch-52,WY,CL;CD,lagging,any_change,,html,,,Wyo. Ins. Dept. Rules ch. 52 s. 6,no,unverified,,"Official host not located."
```

Every in-scope state now has at least one row.

## Appendix B. Draft `config/states.csv`

`group` is `notice`, `regulation`, `statute`, `unclear` or `unknown`. `iui` reflects search excerpts only. `cycle_years` and `next_notice_expected_by` are left blank unless a primary source stated the cycle; no date is filled from memory.

```csv
state,name,cl,cd,iui,group,cycle_years,next_notice_expected_by,notes
AL,Alabama,yes,yes,yes,regulation,,,Two agencies; see Q4
AZ,Arizona,yes,yes,yes,notice,3,,Order at least every three years; 2025 orders seen
CA,California,yes,yes,unknown,regulation,,,
CO,Colorado,yes,yes,unknown,regulation,,,
DE,Delaware,yes,yes,unknown,regulation,,,
FL,Florida,yes,yes,unknown,regulation,,,
GA,Georgia,yes,yes,unknown,regulation,,,
HI,Hawaii,yes,yes,unknown,regulation,,,
ID,Idaho,yes,yes,unknown,notice,3,,Rates posted on Department website
IL,Illinois,yes,yes,unknown,regulation,,,Life rule amended effective 2025-05-22 per official page
IN,Indiana,yes,yes,unknown,notice,3,,Bulletin 277 dated 2024-12-19 per excerpt
IA,Iowa,yes,yes,unknown,notice,3,,Adjusted rates published by bulletin
KS,Kansas,yes,yes,unknown,regulation,,,
KY,Kentucky,unknown,unknown,unknown,unclear,,,See Q13
LA,Louisiana,yes,yes,unknown,statute,,,
ME,Maine,yes,yes,unknown,regulation,,,
MD,Maryland,yes,yes,yes,regulation,,,
MI,Michigan,yes,yes,unknown,regulation,,,
MN,Minnesota,yes,yes,unknown,notice,3,,Publication channel unknown; see Q12
MS,Mississippi,yes,yes,unknown,statute,,,
MO,Missouri,yes,yes,no,statute,,,IUI rule shown as rescinded
MT,Montana,unknown,unknown,unknown,unclear,,,See Q13
NE,Nebraska,yes,yes,unknown,notice,,,Rates in guidance document IGD-A2; check for a rate step on 2027-01-01
NV,Nevada,yes,yes,yes,regulation,1,,Annual review under NAC 690A.175
NH,New Hampshire,yes,yes,unknown,regulation,,,Terms are nominal and actual premium rates
NJ,New Jersey,yes,yes,unknown,regulation,,,
NM,New Mexico,yes,yes,unknown,notice,,,Bulletins in 2019 and 2021 and 2025 seen; cycle not stated
NY,New York,yes,yes,yes,regulation,,,
NC,North Carolina,yes,yes,no,statute,,,Credit unemployment rates are filed and approved
ND,North Dakota,yes,yes,yes,notice,3,,Triennial review; channel not confirmed
OH,Ohio,yes,yes,unknown,notice,3,,Triennial study; channel not confirmed
OK,Oklahoma,yes,yes,unknown,regulation,,,Terms are presumptively acceptable and presumptively reasonable
OR,Oregon,yes,yes,unknown,notice,4,,Director reviews every four years; channel not found
PA,Pennsylvania,yes,yes,yes,notice,3,,Published in the Pennsylvania Bulletin
SC,South Carolina,unknown,yes,unknown,notice,1,,Tentative A&H rates by August 1 each year
SD,South Dakota,yes,yes,unknown,regulation,,,
TN,Tennessee,yes,yes,unknown,regulation,,,2026 rulemaking notice lists the chapter; read it
TX,Texas,yes,yes,unknown,regulation,,,Term is presumptive premium rate
UT,Utah,yes,yes,unknown,notice,1,,Order before September 1 for January 1 when rates are revised
VA,Virginia,yes,yes,unknown,notice,3,,Order for triennium commencing 2025-01-01 seen
WA,Washington,yes,yes,unknown,regulation,,,
WV,West Virginia,yes,yes,yes,notice,3,,Triennial adjustment is published; channel not confirmed
WI,Wisconsin,yes,yes,unknown,notice,3,2029-10-01,Bulletin dated 2026-10-16 for the period beginning 2027-01-01; see 1.5
WY,Wyoming,yes,yes,unknown,regulation,,,Official URL not located
```

## Appendix C. Sources consulted on 2026-11-16

All were seen as search results with excerpts. Only the Wisconsin bulletin of October 16, 2026 was fetched, through an assisted fetch. Third-party legal sites were used only to find citations and are not listed as sources of record.

State sources: every URL in Appendix A, plus the following supporting pages.

- Arizona: https://difi.az.gov/sites/default/files/Credit%20Property%20Insurance.pdf
- Idaho: https://adminrules.idaho.gov/rules/2022 Archive/18/180305.pdf
- Illinois: https://www.ilga.gov/ftp/JCAR/AdminCode/050/050010510000600R.html
- Indiana: https://www.in.gov/idoi/files/Bulletin-277.pdf and https://secure.in.gov/idoi/insurance-laws-rules-and-bulletins
- Iowa: https://iid.iowa.gov/media/113/download
- Maryland: https://mdinsurance.state.md.us/insurer/documents/bulletins/bulletinlh02-15.pdf
- Michigan: https://www.michigan.gov/difs/legal/bulletins/insurance-bulletins-1984---1989/bulletin-no-87-07
- New Mexico: https://www.osi.state.nm.us/wp-content/uploads/Bulletin-2025-002-Credit-Life-and-Credit-Accident-and-Health-Insurance-Premiums-5.8.25-FINAL-ATK-signed.pdf and https://www.osi.state.nm.us/en/news/updated-bulletin-2025-002/
- North Carolina: https://ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/Chapter_58/GS_58-57-35.html
- Ohio: https://www.registerofohio.state.oh.us/pdfs/3901/0/1/3901-1-14_PH_RV_A_RU_20230919_1116.pdf
- South Carolina: https://doi.sc.gov/DocumentCenter/View/15069/Bulletin-2025-06-Credit-Accident-and-Health-Insurance-Rates
- Texas: https://tdi.texas.gov/orders/co-00-0214.html and https://tdi.texas.gov/rules/2004/0519-059.html
- Virginia: https://scc.virginia.gov/getdoc/6bae2e76-af8d-498f-a802-34b317096581/Notice-Order-INS-2024-00060-Prima-Facie-Rates and https://appspre.scc.virginia.gov/boi/adminlets/12-09.pdf
- Wisconsin (fetched): https://oci.wi.gov/Pages/Regulation/Bulletin20261016PrimaFacieRates.aspx
- Nebraska: https://doi.nebraska.gov/sites/default/files/doc/IGD%20-%20-%20A2.pdf and https://doi.nebraska.gov/sites/default/files/doc/CH%2022.pdf
- North Dakota: https://insurance.nd.gov/node/266
- West Virginia: https://www.wvinsurance.gov/Resources-Informational-Letters
- Wisconsin: https://oci.wi.gov/Pages/Regulation/Bulletin20170721CreditRate.aspx and https://oci.wi.gov/Documents/Regulation/Bulletin20201015Rates.pdf

Pricing: https://platform.claude.com/docs/en/about-claude/pricing, https://platform.claude.com/docs/en/models/overview, https://www.anthropic.com/claude/haiku

Not verified in this session, and flagged where used: GitHub Actions pricing for public repositories; GitHub's rule on disabling inactive scheduled workflows; Google's current app-password requirements; current versions of GitHub's official Actions.
