# Decisions

Each decision with its date and reason. References (Q, A) point to docs/plan.md.

| Date | Ref | Decision | Reason |
|---|---|---|---|
| 2026-11-16 | Q1 | Email after every run, even when no candidates are found | Silence must never be ambiguous; a dead job must not look like a quiet month |
| 2026-11-16 | Q2 | Hybrid AI on Claude Sonnet 5.5, annotate only, as a trial; review after three months | Expected cost under $1 a month; AI never decides what is a candidate, so rules-only mode still works |
| 2026-11-16 | Q10 | All saved source documents are public in the repository (publisher-hosted codes are still not fetched or copied) | Simplest audit trail; owner accepts the exposure described in plan 9.5 |
| 2026-11-16 | n/a | The marker "NEEDS TROY'S DECISION" stays in the plan for now | Owner's choice |
| 2026-11-20 | Stage 0 | Repository name `Prima-Facie-Rate-Tracker`, public from the first commit | Public data only; a public repo gets free GitHub Actions and Pages |
| 2026-11-20 | Q5 | `confirmed_by` is the literal word `owner` | Keeps personal names out of the public data |
| 2026-11-20 | Stage 0 | Commits use the owner's name and the GitHub no-reply email; GitHub email-privacy settings on | Public commit history shows no personal or work email address |
| 2026-11-20 | A9 | Confirmed: GitHub Actions is free for standard runners on public repositories (checked by owner 2026-11-20). Caveat: scheduled workflows are disabled after 60 days without repository activity | Plan handles the caveat by committing a run log every run; to be tested in Stage 8 |
| 2026-11-20 | Stage 0 | Use Python 3.15 locally and in workflows, instead of the 3.12 written in the plan | Owner's choice. Checked 2026-11-20: all pinned requirements install on 3.15, and actions/setup-python v7.1.0 provides 3.15.2 on Ubuntu runners |
| 2026-11-20 | Stage 0 | Workflows pin official actions to exact release tags: actions/checkout v7.0.1, actions/setup-python v7.1.0 | Plan 9.7: pinned official actions only, versions looked up at build time |
| 2026-11-20 | Stage 0 | Every source in `config/sources.csv` starts with `enabled=no` | No source has been fetched yet; sources are enabled in Stage 1 and Stage 6 only after verification |
| 2026-11-20 | Stage 0 | `config.load_sources` takes the set of known state codes as a second argument | Needed to check that each source's state is in states.csv without reading that file twice |
| 2026-11-20 | Stage 0 | Plausibility ranges in `config/plausibility.csv` are the plan's placeholders | Owner to set them (Q9); used from Stage 2 |
| 2026-11-20 | Stage 0 | Acceptance test 5 (blocklist search) is pending | `internal/blocklist.txt` has not been written yet; no terms are invented |
