# Build status

Where the build stands, for the next session. The design is in `docs/plan.md` (stages in
section 10); every decision and its reason is in `docs/decisions.md`; open items in
`docs/gaps.md`; the method for onboarding a state in `docs/onboarding.md`. Update this file
at each stage gate and at the end of each session.

Last updated: 2026-11-21 (fifth session; probe workflow; Idaho and New York monitored; Georgia and Illinois Register results).

## Stages

| Stage | State | Notes |
|---|---|---|
| 0. Repository and configuration | Done, pushed | |
| 1. Fetch and detect, pilot states | Done, pushed | |
| 2. Candidates, records, review | Done, pushed | |
| 3. Run summary and check workflow | Done, pushed | Notifications built but off (owner choice) |
| 4. The page | Done, pushed, gate approved | Live at https://eisenhourlabs.github.io/Prima-Facie-Rate-Tracker/ |
| 5. Seed import | Done, pushed, gate approved | Seed tools; batches 1 to 8 (see below) |
| 6. All states | **In progress** | Combined onboarding and seeding, state by state (`docs/onboarding.md`) |
| 7. AI annotation | Not started | Optional; after Q2 |
| 8. Scheduled production run | Not started | The schedule in `check.yml` is commented out until then |

Totals after status item 6 (2026-11-22): 92 confirmed records; 84 of 104 sources enabled; 224 tests pass.

## Where each state stands

Monitored = at least one enabled **leading** source. Records = confirmed records on the page.

| State | Group | Records | Monitoring | Notes |
|---|---|---|---|---|
| WI | notice | 14 | Yes (4) | Batch 1; next notice expected 2029-10-01 |
| IN | notice | 12 | Yes | Batch 2; next 2027-12-31; official copy of 760 IAC 1-5.1 still to save |
| NE | notice | 10 | Yes (3) | Batch 5; IGD-A2 steps 2025, 2026, 2027; next 2027-12-31 |
| NM | notice | 4 | Yes (1) | Batch 4; OSI bulletins list (`new_text`; posts link a staging host) and 13.18.2 NMAC; robots.txt override for www.osi.state.nm.us; next 2027-12-31 |
| SC | notice | 2 | Yes (2) | Batch 3 (rates for 2026 and 2027); alerts list and LAH page; next 2027-09-30 |
| OH | notice | 4 | Lagging only | Batch 6 (memos 2023, 2026); insurance.ohio.gov 404s the tool; next 2028-09-30 |
| IA | notice | 2 (in force) | Yes | Batch 7: Bulletin 00-04 rates in force since 2001 |
| OR | notice | 2 (in force) | Yes | Batch 8: rules in force since 2001 |
| ND | notice | 2 (in force) | Yes | Batch 8: rule in force since 2003 |
| MN | notice | 2 (in force) | Lagging only | Batch 8: rules in force since 2010; bulletins page is a CAPTCHA; IUI factor history is a gap |
| UT | notice | 0 | Yes | No change found; rates-in-force date not found (gap) |
| WV | notice | 0 | Yes | No change since 2011; rule file is a scanned image (gap) |
| AL | regulation | 3 (in force) | Yes (4) | Batch 9: Banking rule 155-2-2-.12 (CL, CD; June 1, 2018) and ALDOI 482-1-093 Exhibit B (IUI; 2003); Q4 settled from the rules; Administrative Monthly watched since 2026-11-22 (AL-aam, previous month's issue, `new_text`) |
| CA | regulation | 0 | Yes (1) | Proposed-regulations list (`new_text`, R5); rates fixed in 10 CCR 2248.47 (2002) and 2670.6 (2006); official code host is the publisher's, so no saved copy and no records (gap) |
| CO | regulation | 0 | Manual | Division site 403s the tool; SOS rule site's terms prohibit robots and reproduction; rates changed 2013, 2016, 2022 (gaps) |
| DE | regulation | 2 (in force) | Yes (1) | Batch 26: Regulation 1701 CL and CD rates in force since February 15, 1971 (decreasing term single premium misprinted "650", not recorded); Register RSS feed (`new_text`) and the rule PDF on regulations.delaware.gov; Department site and delaware.gov reject the tool |
| FL | regulation | 2 | Yes (2) | Batch 10: CL in force since 2003; CD change effective 2019-08-15. Rule pages on flrules.org watched with `new_text`; rule files are Word (.doc), now read; IUI not researched |
| GA | regulation | 0 | Yes (1) | Press releases (hearing notices; strong keyword "new rules and regulations"); CL rule unchanged since 1993. rules.sos.ga.gov answers GitHub's network but its robots.txt disallows every rule page (`/gac/*-.*`): no saved copy, no records (owner question in gaps); no CD table in the insurance rules |
| HI | regulation | 0 | Manual | State terms of use prohibit automated access to every hawaii.gov site (as Colorado); rates in HAR 16-6-11 and 16-6-12 (exhibit 1988); no records (gap) |
| KS | regulation | 2 (in force) | Manual | Batch 11: K.A.R. 40-5-107 (May 1, 1988) from the frozen former Department site; new site 403, rules.ks.gov human check, Kansas Register disallowed by robots.txt |
| ME | regulation | 0 | Manual | maine.gov refuses the tool (CloudFront 403), including the Rule 220 Word file; no records (gap) |
| MD | regulation | 4 | Yes (2) | Batch 12: CL (2001), CD single premium (2001), CD outstanding balance change 2016-06-01 (no old rates; gap), IUI (2003); MIA L&H bulletins (`new_links`) and Regulatory Activity (`new_text`); COMAR subtitle 31.13 (lagging) |
| MI | regulation | 1 (in force) | Yes (1) | Batch 13: CL rates of R 550.211 (September 1, 1989); CD appendices are images (gap); ARS rulemaking list (`new_text`); DIFS site 403 |
| NV | regulation | 3 (in force) | Yes (1) | Batch 14: NAC 690A CL, CD, IUI (R145-08, September 18, 2008); Division regulations page (`new_text`, strong keyword "nac 690a") |
| NH | regulation | 2 (in force) | Yes (1) | Batch 15: actual premium rates by class, Table 1200-2 (February 2, 2018); Rulemaking Register (latest week only; gap); Insurance Department 403 |
| NJ | regulation | 0 | Yes (1) | Department open proposals (`new_text`, strong keyword "11:2-3."); code text only on the publisher's host: no records (gap) |
| NY | regulation | 0 | Yes (1) | NY-dfs-reg-activity (DFS insurance regulatory activity, `new_text`, strong keywords "11 nycrr 185" and "11 nycrr 187"); ny.gov hosts answer GitHub's network only (local dry runs fail); rates are the 185.7(d) formula; NYCRR on a publisher's host: no records |
| OK | regulation | 1 (in force) | Yes (1) | Batch 16: CL rates of OAC 365:10-5-64 (July 1, 1997); OID bulletins (strong keyword "bulletin no."); Appendix E (CD) not saved; rules.ok.gov bot challenge |
| SD | regulation | 2 (in force) | Yes (1) | Batch 17: ARSD 20:06:06:03 and :04 (July 1, 2000); Division hearings page (`new_text`); IUI "no" |
| TN | regulation | 0 | Manual | tn.gov and Secretary of State hosts 403; 2026 rulemaking on 0780-01-04 unread (gap) |
| TX | regulation | 2 (in force) | Yes (2) | Batch 18: 28 TAC 3.5206 Exhibits 21, 22-4, 22-6 (January 1, 2006; Class E and other classes); TDI yearly rules list (`new_text`; URL changes each January) and rules index |
| WA | regulation | 2 (in force) | Yes (1) | Batch 19: WAC 284-34-150, -170 (April 1, 2005); OIC rulemaking list; WAC section files lagging |
| WY | regulation | 0 | Yes (1) | Department memos and bulletins (`new_text`, "ch. 52"); rules.wyo.gov needs a form postback: no records (gap) |
| LA | statute | 2 (in force) | Lagging only | Batch 20: R.S. 9:3542 (CL January 1, 1999; CD schedule from the 1998 text); LDI bot challenge |
| MS | statute | 0 | Yes (2) | Department bulletins and regulations (`new_text`); code on the publisher's host: no records |
| MO | statute | 2 (in force) | Lagging only | Batch 21: RSMo 385.070 (August 28, 1992); Department site 429 |
| NC | statute | 2 (in force) | Yes (1) | Batch 22: G.S. 58-57-40 (January 1, 1997), 58-57-45 (January 1, 1994); NCDOI bulletins |
| KY | statute | 2 (in force) | Yes (1) | Batch 23: KRS 304.19-080 (rates of the 2010 version, re-enacted unchanged July 15, 2026); Department home page bulletins; manual check |
| MT | regulation | 0 | Yes (1) | CSI rule notices (`new_text`); ARM 6.6.1101 CL rate $.80 known but undated; rules.mt.gov refuses the tool (gap) |
| IL | regulation | 1 | Yes (1) | Batch 24: credit life prima facie rates lowered effective May 22, 2025 (1051.50); date communicated October 11, 2024 (proposal, 48 Ill. Reg. 14484, per JCAR's Flinn Report; amended 2026-11-21); old rates not recorded: the Illinois Register answers neither the build computer nor GitHub (manual check); Company Bulletins 2026 JSON (`new_text`; address changes each January) and rule 1051.50 (lagging) |
| VA | notice | 0 | Manual | SCC robots.txt admits search engines only; not overridden |
| AZ | notice | 0 | Manual | 403 / Cloudflare bot check |
| ID | notice | 2 (in force) | Yes (3) | Batch 25: CL and CD rates in force since July 1, 1993, posted by the Director since 2022 (IDAPA 18.03.05.014; attachment dated 6/1/2022); rates PDF and rules page (doi.idaho.gov, GitHub's network only; local dry runs fail) and the rule on adminrules.idaho.gov; triennial review (next 2028) |
| PA | notice | 1 (in force) | Yes (1) | Batch 27: CL outstanding balance rates $.705 and $.844 per $1,000 (31 Pa. Code 73.106(d), 1998); Bulletin robots override approved 2026-11-22; A&H and IUI notices after 1998 not found; Department notice library on pa.gov (`new_text`) |

## Next steps, in order

1. **Regulation-fixed states**, alphabetically (AL, CA, CO, DE, FL, GA, HI, KS, ME, MD, MI, NV, NH, NJ, NY, OK, SD, TN, TX, WA, WY done).
2. **Statute-fixed** (LA, MS, MO, NC done; Q11 option A built: `config/manual_checks.csv`, May and September).
   **KY and MT done (2026-11-21, fourth session):** KY statute-fixed (batch 23; manual check added); MT monitored, records a gap (see `docs/gaps.md`). All regulation-, statute- and unclear-group states are onboarded; next are the loose ends below
   (Pennsylvania and Idaho of the notice group are among them).
3. **Loose ends from the notice group:** NM, SC and PA monitoring enabled 2026-11-21 (PA records need an owner decision on the Pennsylvania Bulletin); Illinois leading source added 2026-11-21.
   **Idaho done (2026-11-21, fifth session):** monitored (3 sources); batch 25 confirmed (2 records).
4. **Follow-up to the robots decision of 2026-11-20: done 2026-11-22.** Alabama: AL-aam watches the
   Administrative Monthly issue PDF at `/api/aam/{prev_month}` (new url placeholder); the site's
   GraphQL interface is limited to the app's own queries and is not used. Delaware: DE-register-rss
   (Register RSS feed) and DE-reg-1701 (current rule PDF) enabled; batch 26 (rates in force since
   February 15, 1971) confirmed.
5. **Hosts to retry from GitHub's network: done 2026-11-21** with the probe workflow (`probe.yml`; runs
   44960357704 and 44961254333). doi.idaho.gov and the ny.gov hosts answer (Idaho and New York monitored);
   rules.sos.ga.gov answers but robots.txt disallows its rule pages (Georgia owner question); www.ilsos.gov
   does not answer (Illinois Register: manual check). Batch 25 confirmed and IL-CL-2025-05-22-1 amended;
   `check` dry run on GitHub for ID and NY (run 44962368413): all 4 sources baseline, HTTP 200.
6. **Owner choices: done 2026-11-22.** Colorado: no permission request (manual check). California and
   Georgia: no hand saves for now (gaps kept). Delaware: done under item 4. Pennsylvania: robots override
   for the Bulletin approved; batch 27 (credit life outstanding balance rates of 31 Pa. Code 73.106(d))
   confirmed; A&H and IUI notices after 1998 not found (gap; owner chose to scan the 2001-2019 Bulletin
   issue contents later).
7. **Gaps without hand saves: worked 2026-11-22** (see the decision of that date; no new records).
   Remaining gaps in `docs/gaps.md` (scanned documents need a hand-checked import; `review add --file`
   for blocked states).
8. Stage 6 gate, then Stage 8.

## Seed batches

| Batch | State | Records | Notes |
|---|---|---|---|
| 01 | WI | 12 | 2009 to 2024; WI-CD-2027 amended to 12/60-month rates |
| 02 | IN | 12 | Bulletins 173 to 277; disability basis per $100 (owner) |
| 03 | SC | 2 | Orders for 2026 and 2027 |
| 04 | NM | 4 | 2021-0028 and 2025-002 |
| 05 | NE | 10 | IGD-A2 2022 restatement and 2025 steps |
| 06 | OH | 4 | Memos for 2023 and 2026 |
| 07 | IA | 2 | Rates in force (pilot) |
| 08 | OR, ND, MN | 6 | Rates in force |
| 09 | AL | 3 | Rates in force (CL, CD, IUI) |
| 10 | FL | 2 | CL in force (2003); CD change 2019 |
| 11 | KS | 2 | Rates in force (CL, CD; 1988) |
| 12 | MD | 4 | Rates in force (CL, CD 2001; IUI 2003); CD outstanding balance change 2016 |
| 13 | MI | 1 | Rates in force (CL; 1989) |
| 14 | NV | 3 | Rates in force (CL, CD, IUI; 2008) |
| 15 | NH | 2 | Rates in force (actual premium rates by class; 2018) |
| 16 | OK | 1 | Rates in force (CL; 1997) |
| 17 | SD | 2 | Rates in force (CL, CD; 2000) |
| 18 | TX | 2 | Rates in force (CL, CD; 2006) |
| 19 | WA | 2 | Rates in force (CL, CD; 2005) |
| 20 | LA | 2 | Rates in force (CL 1999, CD 1998; statute) |
| 21 | MO | 2 | Rates in force (CL, CD; 1992; statute) |
| 22 | NC | 2 | Rates in force (CL 1997, CD 1994; statute) |
| 23 | KY | 2 | Rates in force (CL, CD; 2010 text; statute) |
| 24 | IL | 1 | CL change effective 2025-05-22 (no old rates) |

## Notes carried forward

- Each January: move TX-rules-2026 to TDI's new yearly rules page (rules/YYYY/index.html);
  TX-rules-index reports the new year's link as a page change. Also move IL-bulletins-2026 to the
  new year's Company Bulletins JSON (address in the bulletins page source, `data-cf-table-api`).
- Page: each record is a collapsed line; links open in a new tab; Recent shows changes
  communicated in the last 12 months or not yet in effect; "rates in force" records always
  show in History.
- Detection: links written as `javascript:window.open('url')` are read (Alabama); watch mode
  `new_text` (R5) tests the words added to a page, for lists without links (California);
  R4 covers icon links to PDFs and to download-style links; "igd - - a2" is a
  strong keyword (Nebraska).
- robots.txt: owner-approved overrides in `config/robots_overrides.csv` (New Mexico only);
  a robots.txt redirected to an ordinary page, or answered with the site's home page, means none.
- Option B (headless browser) was tested and not adopted; Playwright was removed from the
  build computer.
- `internal/blocklist.txt` is private: report only the names of matching files, never the terms.
- Deferred: email and the backup GitHub issue (`pfrt/notify.py`) are built but off. They turn on
  with the secrets `SMTP_USER`, `SMTP_APP_PASSWORD`, `ALERT_TO` and the variable
  `PFRT_OPEN_ISSUES=yes`. Stage 3 acceptance tests 2 and 5 wait for this.

## Working rules (also in CLAUDE.md)

- Run tools with `.venv\Scripts\python.exe -m pfrt ...` (Python 3.15.2).
- Explain each command before running it. Ask "Shall I push?" before every push, even when a
  later step depends on it. Wait for approval on deleting files and anything with secrets.
- Before every commit, check `git status` to make sure nothing from `internal/` is staged.
- Check pytest's real exit code before committing.
- Look up action and package versions when building; never write them from memory.
