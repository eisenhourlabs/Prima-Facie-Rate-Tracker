# Build status

Where the build stands, for the next session. The design is in `docs/plan.md` (stages in
section 10); every decision and its reason is in `docs/decisions.md`. Update this file at each
stage gate.

Last updated: 2026-11-20.

## Stages

| Stage | State | Notes |
|---|---|---|
| 0. Repository and configuration | Done, pushed | |
| 1. Fetch and detect, pilot states | Done, pushed | 7 sources enabled (IL, IN, VA, WI) |
| 2. Candidates, records, review | Done, pushed | First records: WI-CL and WI-CD, effective 2027-01-01 |
| 3. Run summary and check workflow | Done, pushed | Notifications built but off (owner choice) |
| 4. The page | Done, pushed, gate approved | Live at https://eisenhourlabs.github.io/Prima-Facie-Rate-Tracker/ |
| 5. Seed import | Done, pushed, gate approved | Batch 1 (Wisconsin, effective 2009-2024): 12 records; WI-CD-2027 amended to 12/60-month rates. Page: each change is a collapsed line; links open in a new tab |
| 6. All states | **Next** (or more seed batches first) | |
| 7. AI annotation | Not started | Optional; after Q2 |
| 8. Scheduled production run | Not started | The schedule in `check.yml` is commented out until then |

## Notes carried forward

Stage 5 (seed import):
- Built: `seed validate`, `seed import`, `seed scan`, `review confirm --batch`, `review list --batch`.
  Q9, A5 and A6 decided (see decisions.md, 2026-11-20).
- Batch 1 (Wisconsin, effective 2009-2024) was drafted by Claude Code from public bulletins and
  tables downloaded from oci.wi.gov, approved by the owner, imported and confirmed (11 by
  `--batch`, WI-CD-2024 on its own because of its genuine +102% 30-day changes). The 2009 records
  are outside the 15-year window and hidden on the page. Wisconsin now has 14 confirmed records.
- WI-CD-2027-01-01-1 amended to the 12- and 60-month rates (A5).
- Next batches: one state at a time, same method (Indiana's numbered bulletins are a good next one).
- `internal/blocklist.txt` is private: report only the names of matching files, never the terms.

Stage 6 (all states):
- Idaho: both sources return HTTP 200 from GitHub Actions (run 44773368940) but fail TLS from
  the build computer. Enable after choosing `must_contain` markers from a copy fetched on
  GitHub's network (for example, saved as a workflow artifact).
- Virginia: the leading source is a manual check because the regulator's robots.txt blocks
  automated fetching. Revisit.

Deferred:
- Email and the backup GitHub issue (`pfrt/notify.py`) are built but off. They turn on with the
  secrets `SMTP_USER`, `SMTP_APP_PASSWORD`, `ALERT_TO` and the variable `PFRT_OPEN_ISSUES=yes`.
  Stage 3 acceptance tests 2 and 5 wait for this.

## Working rules (also in CLAUDE.md)

- Run tools with `.venv\Scripts\python.exe -m pfrt ...` (Python 3.15.2).
- Explain each command before running it. Ask "Shall I push?" before every push, even when a
  later step depends on it. Wait for approval on deleting files and anything with secrets.
- Before every commit, check `git status` to make sure nothing from `internal/` is staged.
- Look up action and package versions when building; never write them from memory.
