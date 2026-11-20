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
| 2026-11-20 | Stage 0 | Acceptance test 5 (blocklist search) was pending, then run after the owner wrote `internal/blocklist.txt`: no matches in file contents, file names or commit messages | No terms were invented; the owner will add terms over time and the search is rerun before commits that bring in outside material |
| 2026-11-20 | Stage 1 | Virginia SCC orders (`www.scc.virginia.gov`) are not fetched: robots.txt disallows all but named search engines. VA-order-2024 stays disabled and is reported `blocked_robots`. Owner approved 2026-11-20: Virginia's leading source is a manual check for now, to be revisited later | Plan 3.4 and 9.5: obey robots.txt, never work around it |
| 2026-11-20 | Stage 1 | Wisconsin is watched through the "Bulletins Issued" index (new source WI-bulletins-index, `new_links`). Approved by owner 2026-11-20 | The index lists each new bulletin as a link, which is what R1 needs; a single bulletin page cannot show the next one |
| 2026-11-20 | Stage 1 | Idaho sources stay disabled and `failed`; retry from GitHub Actions in Stage 3 | doi.idaho.gov did not complete a secure connection from the build computer |
| 2026-11-20 | Stage 1 | Add the missing Sectigo OV R40 intermediate certificate (`pfrt/certs/`) to the CA bundle used by the job | www.ilga.gov sends an incomplete certificate chain. This fills the gap to a trusted root; certificate verification stays on |
| 2026-11-20 | Stage 1 | Honor a robots.txt Crawl-delay longer than 5 seconds | Illinois asks for 10 seconds; plan 9.4 requires polite fetching |
| 2026-11-20 | Stage 1 | A robots.txt answer that is a web page (HTML) is treated as unreadable, so the site is not fetched that run | An error page read as robots.txt looks like "no rules" and would wrongly allow everything |
| 2026-11-20 | Stage 1 | A source whose CSS selector matches nothing is `suspect` (not checked), instead of silently watching the whole page | A selector that stops matching means the layout changed; silent fallback could hide a missed change |
| 2026-11-20 | Stage 1 | `<form>` is no longer stripped during normalization (plan 3.1 lists it) | SharePoint sites such as oci.wi.gov wrap the whole page in one form; stripping it removed all content |
| 2026-11-20 | Stage 1 | Keyword matching is a plain substring search, as in the plan | Whole-word matching would miss "premiums" for "premium"; a false alarm is cheaper than a miss |
| 2026-11-20 | Stage 1 | `detect.compare` takes the new content hash (not the text) and the keyword list | Lets one function handle HTML (hash of normalized text) and documents (hash of raw bytes) |
| 2026-11-20 | Stage 1 | The check run lives in `pfrt/check.py`; `__main__.py` only parses commands | Keeps the entry point short and the run testable |
| 2026-11-20 | Stage 1 | `check` accepts `--include-disabled` to try a source before enabling it | Plan 9.2: every new source is exercised with a dry run before it is enabled |
| 2026-11-20 | Stage 1 | Stage 1 acceptance test 4 uses the Wisconsin 2023 bulletin PDF instead of the Idaho PDF | Idaho could not be fetched; the WI PDF is the same kind of source (single PDF, `any_change`) |
| 2026-11-20 | Stage 1 | Seven pilot sources that passed are `fetched`, `verified_on` 2026-11-20 and enabled | Plan 1.4 step 6 and Stage 1 acceptance 6. No scheduled job exists yet, so enabling has no effect until Stage 3 |
| 2026-11-20 | Stage 1 | `must_contain` markers approved by owner: IN "Credit Life and Accident and Health Rates"; WI index "Bulletins Issued"; WI 2026 and 2023 bulletins "Revised Prima Facie Credit Life"; WI filing guide "Rate Filings"; VA "38.2-3730"; IL "1051.50" | Each is specific to the page and appeared in every fetch; a block page or redesign would lack it |
| 2026-11-20 | Stage 1 | Owner acknowledged the Wisconsin by-hand read: the October 16, 2026 bulletin is the notice already recorded in plan 1.5 | Stage 1 gate item; the candidate is confirmed from the saved PDF in Stage 2 |
| 2026-11-20 | Stage 1 | Stage 1 gate approved by owner | All six acceptance tests passed (test 4 with the WI PDF substitute) |
| 2026-11-20 | Stage 1 | Saved pilot pages are committed as test fixtures in `tests/fixtures/` | Tests need real pages and must not use the network; all are public state documents (Q10) |
