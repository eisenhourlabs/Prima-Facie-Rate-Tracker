# Build status

Where the build stands, for the next session. The design is in `docs/plan.md` (stages in
section 10); every decision and its reason is in `docs/decisions.md`; open items in
`docs/gaps.md`; the method for onboarding a state in `docs/onboarding.md`. Update this file
at each stage gate and at the end of each session.

Last updated: 2026-11-21 (third session; regulation-fixed states AL to TN done).

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

Totals after Tennessee: 74 confirmed records; 53 of 89 sources enabled; 208 tests pass.

## Where each state stands

Monitored = at least one enabled **leading** source. Records = confirmed records on the page.

| State | Group | Records | Monitoring | Notes |
|---|---|---|---|---|
| WI | notice | 14 | Yes (4) | Batch 1; next notice expected 2029-10-01 |
| IN | notice | 12 | Yes | Batch 2; next 2027-12-31; official copy of 760 IAC 1-5.1 still to save |
| NE | notice | 10 | Yes (3) | Batch 5; IGD-A2 steps 2025, 2026, 2027; next 2027-12-31 |
| NM | notice | 4 | **No: sources not yet enabled** | Batch 4; robots.txt override approved for www.osi.state.nm.us; next 2027-12-31 |
| SC | notice | 2 | **No: sources not yet enabled** | Batch 3 (rates for 2026 and 2027); next 2027-09-30 |
| OH | notice | 4 | Lagging only | Batch 6 (memos 2023, 2026); insurance.ohio.gov 404s the tool; next 2028-09-30 |
| IA | notice | 2 (in force) | Yes | Batch 7: Bulletin 00-04 rates in force since 2001 |
| OR | notice | 2 (in force) | Yes | Batch 8: rules in force since 2001 |
| ND | notice | 2 (in force) | Yes | Batch 8: rule in force since 2003 |
| MN | notice | 2 (in force) | Lagging only | Batch 8: rules in force since 2010; bulletins page is a CAPTCHA; IUI factor history is a gap |
| UT | notice | 0 | Yes | No change found; rates-in-force date not found (gap) |
| WV | notice | 0 | Yes | No change since 2011; rule file is a scanned image (gap) |
| AL | regulation | 3 (in force) | Yes (3) | Batch 9: Banking rule 155-2-2-.12 (CL, CD; June 1, 2018) and ALDOI 482-1-093 Exhibit B (IUI; 2003); Q4 settled from the rules; Administrative Monthly not readable (gap) |
| CA | regulation | 0 | Yes (1) | Proposed-regulations list (`new_text`, R5); rates fixed in 10 CCR 2248.47 (2002) and 2670.6 (2006); official code host is the publisher's, so no saved copy and no records (gap) |
| CO | regulation | 0 | Manual | Division site 403s the tool; SOS rule site's terms prohibit robots and reproduction; rates changed 2013, 2016, 2022 (gaps) |
| DE | regulation | 0 | Manual | Department site and delaware.gov reject the tool; new rules system's robots.txt is an app page (owner question); archive frozen; rates unchanged since 1971 (gaps) |
| FL | regulation | 2 | Yes (2) | Batch 10: CL in force since 2003; CD change effective 2019-08-15. Rule pages on flrules.org watched with `new_text`; rule files are Word (.doc), now read; IUI not researched |
| GA | regulation | 0 | Yes (1) | Press releases (hearing notices; strong keyword "new rules and regulations"); CL rule unchanged since 1993 but rules.sos.ga.gov does not answer the tool (gap); no CD table in the insurance rules |
| HI | regulation | 0 | Manual | State terms of use prohibit automated access to every hawaii.gov site (as Colorado); rates in HAR 16-6-11 and 16-6-12 (exhibit 1988); no records (gap) |
| KS | regulation | 2 (in force) | Manual | Batch 11: K.A.R. 40-5-107 (May 1, 1988) from the frozen former Department site; new site 403, rules.ks.gov human check, Kansas Register disallowed by robots.txt |
| ME | regulation | 0 | Manual | maine.gov refuses the tool (CloudFront 403), including the Rule 220 Word file; no records (gap) |
| MD | regulation | 4 | Yes (2) | Batch 12: CL (2001), CD single premium (2001), CD outstanding balance change 2016-06-01 (no old rates; gap), IUI (2003); MIA L&H bulletins (`new_links`) and Regulatory Activity (`new_text`); COMAR subtitle 31.13 (lagging) |
| MI | regulation | 1 (in force) | Yes (1) | Batch 13: CL rates of R 550.211 (September 1, 1989); CD appendices are images (gap); ARS rulemaking list (`new_text`); DIFS site 403 |
| NV | regulation | 3 (in force) | Yes (1) | Batch 14: NAC 690A CL, CD, IUI (R145-08, September 18, 2008); Division regulations page (`new_text`, strong keyword "nac 690a") |
| NH | regulation | 2 (in force) | Yes (1) | Batch 15: actual premium rates by class, Table 1200-2 (February 2, 2018); Rulemaking Register (latest week only; gap); Insurance Department 403 |
| NJ | regulation | 0 | Yes (1) | Department open proposals (`new_text`, strong keyword "11:2-3."); code text only on the publisher's host: no records (gap) |
| NY | regulation | 0 | No | All ny.gov hosts fail to connect from the build computer; retry from GitHub's network; NYCRR on a publisher's host |
| OK | regulation | 1 (in force) | Yes (1) | Batch 16: CL rates of OAC 365:10-5-64 (July 1, 1997); OID bulletins (strong keyword "bulletin no."); Appendix E (CD) not saved; rules.ok.gov bot challenge |
| SD | regulation | 2 (in force) | Yes (1) | Batch 17: ARSD 20:06:06:03 and :04 (July 1, 2000); Division hearings page (`new_text`); IUI "no" |
| TN | regulation | 0 | Manual | tn.gov and Secretary of State hosts 403; 2026 rulemaking on 0780-01-04 unread (gap) |
| IL | regulation | 0 | Lagging only (pilot) | Leading source still to add |
| VA | notice | 0 | Manual | SCC robots.txt admits search engines only; not overridden |
| AZ | notice | 0 | Manual | 403 / Cloudflare bot check |
| ID | notice | 0 | No | Fetches from GitHub Actions only; markers to choose (see below) |
| PA | notice | 0 | No | Not started |
| All others | regulation / statute / unclear | 0 | No | Not started: KY, LA, MS, MO, MT, NC, TX, WA, WY |

## Next steps, in order

1. **Regulation-fixed states**, alphabetically (AL, CA, CO, DE, FL, GA, HI, KS, ME, MD, MI, NV, NH, NJ, NY, OK, SD, TN done), next **Texas**, then
   WA, WY.
2. **Statute-fixed** (LA, MS, MO, NC) and **unclear** (KY, MT).
3. **Loose ends from the notice group:** enable monitoring for NM and SC (sources exist but are
   disabled); Pennsylvania; Idaho (choose `must_contain` from a copy fetched on GitHub's
   network, for example a workflow artifact); a leading source for Illinois.
4. **Follow-up to the robots decision of 2026-11-20** (an app page equal to the home page
   means no robots.txt): read the terms of admincode.legislature.state.al.us and
   regulations.delaware.gov, then add sources there (Alabama Administrative Monthly;
   Delaware Register and Regulation 1701). Both are single-page apps with /api/ addresses.
5. **Hosts to retry from GitHub's network** (a workflow run, as for Idaho): rules.sos.ga.gov
   (Georgia rule 120-2-27, for a rates-in-force record and a lagging source); every ny.gov host
   (New York DFS regulatory activity and the State Register).
6. **Owner choices that would add records** (see `docs/gaps.md`): Colorado (written
   permission from the Secretary of State, or another host; rates changed 2013, 2016, 2022);
   California (Department copy of the 2002 and 2006 rules saved by hand, or the Westlaw text);
   Delaware (2008 final order or current text, once regulations.delaware.gov sources exist).
7. Gaps in `docs/gaps.md` (scanned documents need a hand-checked import; `review add --file`
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

## Notes carried forward

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
