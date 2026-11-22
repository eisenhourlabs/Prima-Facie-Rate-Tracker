# Onboarding a state (Stage 6) and seeding its history

The method used for every state so far. Read this before onboarding the next state. Decisions
and their reasons are in `docs/decisions.md`; open items in `docs/gaps.md`; progress in
`docs/status.md`.

## Owner's standing instructions for this work

- Complete each state (research, monitoring, seed records, docs) and commit it **without
  checking in on each value**. Stop and ask only for an important decision that cannot be
  given a clear recommendation. This is the owner's explicit instruction to run `review
  confirm` for seed batches (CLAUDE.md requires one).
- Still ask "Shall I push?" before every push.
- One state per commit. Report each state briefly when done (what is monitored, what was
  seeded, decisions made, gaps).

## Steps for one state

1. **Read what is known.** `grep "^XX" config/sources.csv config/states.csv`, plan sections 1.2
   and Appendix A/B. Rows marked `search_seen` were seen in search on 2026-11-16, not fetched.
2. **Find how rates are set and published.** Read the rule or statute on an official host and
   find: where the rates are; whether they are adjusted by bulletin, order, memo or rule
   amendment; the cycle; the history line (amendment dates). Search
   (`WebSearch`, standard first) for the publications. Fetch with `tools/polite_get.py`.
3. **Check access for every host.** Before fetching from a new host, read its terms of use
   or web policy: terms against robots, data mining or reproduction rule the host out even
   when robots.txt allows (Colorado's Secretary of State, 2026-11-20). `polite_get` reports
   robots.txt verdicts. If blocked:
   - robots.txt "disallow" only, no other barrier, and no terms of use against automated
     access: the owner may approve an override in `config/robots_overrides.csv` (done for New
     Mexico). Check the site's terms first and ask.
   - HTTP 403, a CAPTCHA or challenge page, a login, or 404 for every page: a refusal. Never
     work around it (no disguised user agent). The state becomes a manual check in
     `docs/gaps.md`.
   - A robots.txt request redirected to an ordinary page, or answered with a page identical
     to the home page (an app), means no robots.txt (rules of 2026-11-20).
4. **Choose sources** and add them to `config/sources.csv` (use the csv module; quote values
   with commas):
   - At least one **leading** source: the index where a new bulletin/order/memo/proposed rule
     would appear, usually `new_links`. Check that a new item's link text would contain a
     keyword (R1); if links are icons, R4 downloads PDF and download-style links
     (LinkClick.aspx, `fileticket=`, `/download`). If the link text names a document only by
     number (Nebraska "IGD - - A2"), add that text to `config/keywords.csv` as `strong`.
   - If the index lists items by title with no usable links (ASP.NET postbacks, as in
     California), use `new_text`: the added words are tested against the keywords (R5).
   - **Lagging** sources: the rule text (`any_change`). Prefer undated, current-version URLs.
   - Set `must_contain` to a phrase specific to the page.
5. **Dry run:** `.venv\Scripts\python.exe -m pfrt check --dry-run --states XX --include-disabled`.
   Every source must show `baseline` with HTTP 200. Then set `enabled=yes`,
   `verification=fetched`, `verified_on`, and a note. Add new hosts to
   `config/official_domains.csv`.
6. **Seed records** from saved public documents only:
   - Copy each document into `seed/documents/` (git-ignored); give it a clear name.
   - Write `seed/batch_NN.csv` with a small script (keeps repeated plan/basis text identical).
     Next batch number: see `seed/` (batch_27 is the last used).
   - Headline rates (A5): credit life per-annum and outstanding-balance rates as published;
     12- and 60-month rates where the state publishes rates by term (for credit disability,
     and for credit life where a term table exists). Never compute a rate (formulas,
     joint percentages, unemployment factors stay in the note).
   - `basis` is the unit only, in the state's words; the term and coverage go in `plan`.
   - A change with no stated effective date uses the bulletin date (said in the summary); a
     required "no later than" date is used where given (Indiana 277, Minnesota 2010).
   - "Reviewed, no change" notices are `no_change` records (old = new).
   - Where no change was found in the 15-year window, add **rates in force** records
     (`change_type` `initial`), only if the effective date can be stated truthfully.
   - Note every oddity in the record (one-cent table/letter differences, typos, garbled
     extraction) and use the table or figure printed in the governing document.
7. **Check before import:** `seed scan seed/` must pass (scanned PDFs fail by design);
   `seed validate seed/batch_NN.csv` must show 0 errors; then check every rate against the
   saved document by script (table rows for terms 12 and 60; "$x.xx" strings for life rates).
8. **Import and confirm:** `seed import seed/batch_NN.csv`, then `review confirm --batch
   batch_NN`; confirm any record left open by warnings on its own with
   `review confirm ID --values FILE` when the warnings are genuine.
9. **Set `next_notice_expected_by`** in `config/states.csv` when the state has a regular
   cycle (`review.set_next_expected`); leave it blank when it does not (it would warn
   every year).
10. **Document:** a row per decision in `docs/decisions.md`; any gap in `docs/gaps.md`;
    the state in the Stage 6 line of `docs/status.md`.
11. **Check and commit:** `config check`, `validate`, `pytest` — **check pytest's real exit
    code** (do not pipe it through `tail` and continue on success of `tail`), `build`.
    Stage files by name; confirm `internal/` is not staged; commit; ask "Shall I push?".

## Lessons from this session

- A page that shows a few hundred characters to the tool is not necessarily built by
  JavaScript: Minnesota's was a CAPTCHA, Ohio's a 404 for all automated requests, and West
  Virginia's an archive behind a login. Look at the page text before diagnosing. A headless
  browser (plan Q7 option B) was tested and not adopted.
- In several states the rule's own tables are only base rates and the rates in force are set
  elsewhere: Iowa (bulletin), Ohio (actuarial memo), Minnesota IUI (unemployment factor).
  Find the publication that governs.
- Rule history lines show when rate sections were last amended; compare the proposal text
  with the current text before calling an amendment a rate change (North Dakota 2021 changed
  formulas only).
- Read the definitions section: Alabama's insurance rule names the "Superintendent" (of Banks)
  as the source of its prima facie rates, which settled which agency's rule holds them.
- Some agencies are exempt from their state's administrative procedure act (Alabama's
  Department of Insurance) and post revised rules only on their own site, under a new file
  name; their own list of rules is then the leading source.
- Third-party copies (Justia, Cornell, Casetext mirrors, trade bulletins) are only for finding
  official documents; never a record's source.
- In this Git Bash shell, long inline Python with quotes can fail to parse; write the script
  to a file in the scratch folder and run it.
- Read a host's terms before the first fetch (`tools/terms_links.py` lists the policy links).
  Colorado's rules site allows robots in robots.txt but forbids them in its terms. When a
  policy page itself refuses all readers (Delaware, Florida), say so in the source note.
- When the official host of the rule text cannot be used (a commercial publisher, a refusal,
  no answer), look for a final rule or notice on the agency's or register's own site; if
  none, record no rates-in-force record and log the gap (California, Delaware, Georgia).
- Rulemaking pages often link notices only by number or by postback: watch the page text
  with `new_text` (California's list, Florida's rule pages), or add the notice title as a
  strong keyword (Georgia's "new rules and regulations") so the notice is downloaded and
  tested. Test the rule on the real page with the new notice removed.
- Some states publish rule text only as Word (.doc) files (Florida); the tool reads them
  (`documents.doc_text`). Table cells come out as " | " columns; read rate rows by band.
- Rate tables printed by term band ("7-12", "49-60") give the 12- and 60-month headline
  rates; name the band in `plan`.
- `polite_get.py` names each saved file after the last part of the URL path, so pages like
  `ruleNo.asp?id=...` overwrite each other: give each its own OUT_DIR.
- A host that does not answer from the build computer (Georgia's rules site, Idaho) may
  answer from GitHub's network; test it there before calling it blocked.
- Some states publish one set of terms for every state site (Hawaii: any address containing
  "hawaii.gov"); an archive's policy can forbid robots while the agencies' own sites do not
  (Maryland State Archives). Read the terms the agency site links, and the portal's terms.
- A redirected former agency site can still serve old copies (Kansas, insurance.ks.gov,
  posted 2015). Use such a copy for a rates-in-force record, saying so, but do not watch a
  frozen page: it would show the state as monitored while seeing nothing.
- Rates-in-force records may be dated from 1950 (the rule text's effective date); change
  records keep the 1990 floor.
- A rule may print rates without their unit (Maryland COMAR 31.13.01.15E): say so in
  `basis` and quote the unit from the announcing document in the note.
- A state may name a rate rulemaking only by chapter or citation (Nevada "NAC 690A", New
  Hampshire "Ins 1200", New Jersey "11:2-3.17"): add it as a strong keyword and test it
  against real unrelated items on the page.
- Some official pages are saved in windows-1252 (Nevada NAC, New Hampshire rules);
  `seed scan` reads them in the charset the page declares.
- An official text PDF can still print rate tables as images (Michigan's appendices): those
  rates wait for a hand-checked import.
- A listing that shows only the latest issue (New Hampshire's Rulemaking Register) can miss a
  notice between two runs; say so in the gaps.
- Keywords are global. On a `new_text` page a strong keyword makes a candidate directly, so
  test a new keyword against the ordinary text of every `new_text` page it could appear on
  ("rule changes" was dropped because South Dakota's page says "rule changes pending").
- A host that refuses the build computer but answers GitHub (Idaho, New York) is probed with the
  `probe` workflow (GitHub > Actions > probe, or `gh workflow run probe.yml -f urls="..."`); its
  artifact holds the copies and logs. Put terms pages first, and hold back content pages of hosts
  whose terms are unknown or doubtful. Dry-run such sources offline on the probe copies
  (`check --dry-run --offline --fixtures DIR`, files named SOURCE_ID.ext).
- robots.txt wildcards (`Disallow: /gac/*-.*`, Georgia) are honored by the fetcher: test a URL
  against the saved robots.txt before planning a source.
- A state may make a posted web document the governing publication (Idaho 18.03.05.014: "The
  Director will post on the Department's website the prima facie rates"): watch that file itself.
- A document published under a new address each month (Alabama Administrative Monthly,
  `/api/aam/YYYY-MM`) is watched with the url placeholder `{prev_month}` (`config.resolve_url`);
  watch it as `new_text`, so each new issue's whole text is tested, and test the keywords on a few
  past issues first. The size floor is skipped when the address changed.
- Single-page apps: look in the app's JavaScript for plain document addresses and feeds (Delaware's
  `register/regs-rss.xml`) before anything else; a GraphQL interface limited to the app's own
  queries ("PersistedQueryOnly") is not imitated.
- UTF-16 pages (South Dakota) pass a UTF-8 decode with zero bytes between letters;
  `seed scan` now checks for UTF-16 first.

## Helper scripts

- `tools/polite_get.py`: polite downloads through the project fetcher (see its docstring).
- `tools/grep_pages.py`: search saved HTML/PDF text for phrases.
- `tools/terms_links.py`: fetch a host's pages politely and list its terms, policy and
  disclaimer links, to read before onboarding the host.
