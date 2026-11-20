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

## Status and next steps
See docs/plan.md. Start by reading it.