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
3. **Check access for every host.** `polite_get` reports robots.txt verdicts. If blocked:
   - robots.txt "disallow" only, no other barrier, and no terms of use against automated
     access: the owner may approve an override in `config/robots_overrides.csv` (done for New
     Mexico). Check the site's terms first and ask.
   - HTTP 403, a CAPTCHA or challenge page, a login, or 404 for every page: a refusal. Never
     work around it (no disguised user agent). The state becomes a manual check in
     `docs/gaps.md`.
   - A robots.txt request redirected to an ordinary page means no robots.txt (rule 2026-11-20).
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
     Next batch number: see `seed/` (batch_09 is the last used).
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

## Helper scripts

- `tools/polite_get.py`: polite downloads through the project fetcher (see its docstring).
- `tools/grep_pages.py`: search saved HTML/PDF text for phrases.
