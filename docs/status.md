# Build status

Where the build stands, for the next session. The design is in `docs/plan.md` (stages in
section 10); every decision and its reason is in `docs/decisions.md`; open items in
`docs/gaps.md`; the method for onboarding a state in `docs/onboarding.md`. Update this file
at each stage gate and at the end of each session.

Last updated: 2026-11-20 (end of second session; regulation-fixed states AL to GA done).

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

Totals after Georgia: 59 confirmed records; 39 of 81 sources enabled; 205 tests pass.

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
| IL | regulation | 0 | Lagging only (pilot) | Leading source still to add |
| VA | notice | 0 | Manual | SCC robots.txt admits search engines only; not overridden |
| AZ | notice | 0 | Manual | 403 / Cloudflare bot check |
| ID | notice | 0 | No | Fetches from GitHub Actions only; markers to choose (see below) |
| PA | notice | 0 | No | Not started |
| All others | regulation / statute / unclear | 0 | No | Not started: HI, KS, KY, LA, ME, MD, MI, MS, MO, MT, NV, NH, NJ, NY, NC, OK, SD, TN, TX, WA, WY |

## Next steps, in order

1. **Regulation-fixed states**, alphabetically (AL, CA, CO, DE, FL, GA done), next **Hawaii**, then KS, ME, MD, MI, NV, NH, NJ, NY, OK, SD,
   TN (early: 2026 rulemaking notice for chapter 0780-01-04), TX, WA, WY.
2. **Statute-fixed** (LA, MS, MO, NC) and **unclear** (KY, MT).
3. **Loose ends from the notice group:** enable monitoring for NM and SC (sources exist but are
   disabled); Pennsylvania; Idaho (choose `must_contain` from a copy fetched on GitHub's
   network, for example a workflow artifact); a leading source for Illinois.
4. **Follow-up to the robots decision of 2026-11-20** (an app page equal to the home page
   means no robots.txt): read the terms of admincode.legislature.state.al.us and
   regulations.delaware.gov, then add sources there (Alabama Administrative Monthly;
   Delaware Register and Regulation 1701). Both are single-page apps with /api/ addresses.
5. **Hosts to retry from GitHub's network** (a workflow run, as for Idaho): rules.sos.ga.gov
   (Georgia rule 120-2-27, for a rates-in-force record and a lagging source).
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
