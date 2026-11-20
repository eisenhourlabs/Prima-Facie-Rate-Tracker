# CLAUDE.md - Prima Facie Rate Tracker

Read this first in every session. This file is published in a PUBLIC repository, so it must
never name an employer or contain internal data or secrets. Private context lives in
`internal/` (git-ignored): read `internal/README.md` and `internal/project_instructions.md`
at the start of a session if they exist.

## What we are building
A simple one-page site with two boxes. Recent: prima facie rate changes communicated in the
last 12 months, sorted by effective date. Historical: 15 years of changes by state, in alphabetical
order, expandable per state. Products: credit life, credit disability, IUI (where a prima facie
rate exists). The primary purpose is to detect NEW changes soon after publication; the
historical log is secondary.

## How it works
A scheduled GitHub Actions job runs twice a month, checks each state's registered source
page (config/sources.csv), creates CANDIDATE records, and emails a summary. The owner approves
or rejects candidates in a Claude Code session. Only confirmed records appear on the site.

## Rules
- Public data only. Every record links to a primary source and keeps a saved copy.
- Never fill a rate or date from memory; unverified values are labeled unverified.
- A state that could not be checked is reported as a gap, never skipped silently.
- Secrets only in GitHub secrets. Never in files, commits or logs.
- Add states and sources in config/, not in code.
- Log each decision and its reason in docs/decisions.md.
- Keep code simple and well commented; the owner is new to Python, Git and VS Code. Explain
  each command before running it and wait for approval on anything with push, delete or secrets.

## Review protocol (candidates and records)
- Claude Code never runs `review confirm`, `review reject`, `review amend`, `review retract`
  or `git push` without an explicit instruction from the owner in the current session.
- Rates and dates come only from the saved document in `archive/`. For every value, quote
  the sentence it comes from and give the page number. Never fill a value from memory.
- Propose values first and wait. The owner states or approves each value before confirm.
- Run commands from the repository folder with the project Python: `.venv\Scripts\python.exe -m pfrt ...`

Short prompts the owner may use:
- "Pull the latest changes and list open candidates." -> `git pull`, then `review list`
- "Show me candidate ID and open its saved source document." -> `review show ID`, open the file
- "Read the saved document and propose values for every record field. Quote the sentence each
  rate and date comes from, with the page number. Do not confirm anything."
- "Confirm ID with these values: ..." -> write the values to a JSON file in the scratchpad,
  then `review confirm ID --values FILE [--next-expected YYYY-MM-DD]`
- "Reject ID, reason: ..." -> `review reject ID --reason "..."`
- "Validate, build the site, show me the diff, and wait for my go-ahead before committing."
- "Commit and push." (push only on this explicit instruction)

Values file for confirm: `{"records": [{"product": "CL", "change_type": "change",
"effective_date": "YYYY-MM-DD", "date_communicated": "YYYY-MM-DD", "legal_basis": "...",
"summary": "...", "rate_table_note": "...", "rate_items": [{"plan": "...", "basis": "...",
"old_rate": 0.0, "new_rate": 0.0}]}], "next_notice_expected_by": "YYYY-MM-DD"}`.
One candidate may give several records (for example CL and CD from one bulletin).

## Status and next steps
See docs/plan.md. Start by reading it.