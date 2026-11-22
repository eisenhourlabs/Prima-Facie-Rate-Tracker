# Prima Facie Rate Tracker

An unofficial, personal compilation of state prima facie rate changes for credit life,
credit disability and involuntary unemployment insurance, built from public sources only.

A scheduled job checks state insurance department and regulation pages twice a month and
flags possible rate changes for review. Only reviewed, confirmed records are published.
Every record links to its official source, and the linked source governs. This is not
legal or actuarial advice.

Status: under construction. See [docs/plan.md](docs/plan.md) for the design and build plan
and [docs/decisions.md](docs/decisions.md) for decisions made.

## The page

The site is one HTML page built from the confirmed records in `data/records/` by
`python -m pfrt build`, and published on GitHub Pages by `.github/workflows/pages.yml`.
It shows recent changes (communicated in the last 12 months) and a 15-year history by state,
with a link to the official source and a saved copy of each document. The "Last checked"
line shows when the sources were last checked; checks run twice a month, so a date more than
20 days old means the checks have stopped.

## Quick start (local)

```
python -m venv .venv
.venv\Scripts\activate          # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m pfrt config check
pytest
python -m pfrt build             # then open site/index.html in a browser
```

## Operations

### The schedule

`.github/workflows/check.yml` runs on the 3rd and 18th of each month at 13:17 UTC
(7:17 a.m. Central Standard Time, 8:17 a.m. Central Daylight Time). Each run checks every enabled
source, saves the snapshots, the run log and the summary in `data/runs/`, commits them, and
sends the summary by email once email is set up. The first run of each month also runs the
link check (below).

What GitHub's documentation says (read 2026-11-22; check again if something looks wrong):

- "By default, scheduled workflows run in UTC." ([workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onschedule))
- "The `schedule` event can be delayed during periods of high loads of GitHub Actions workflow
  runs. High load times include the start of every hour. If the load is sufficiently high
  enough, some queued jobs may be dropped." This is why the minute is 17, not 0.
  ([events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule))
- "Scheduled workflows run on the latest commit on the default branch" (`main`).
- "In a public repository, scheduled workflows are automatically disabled when no repository
  activity has occurred in 60 days." GitHub does not say what counts as activity. Each scheduled
  run commits its run log, which should keep the repository active, but if runs stop, check
  this first. ([disabling and enabling a workflow](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/disabling-and-enabling-a-workflow))
- Failure emails from GitHub for scheduled runs go to the user who last changed the `cron`
  line, or to the user who re-enabled a disabled workflow.
  ([notifications for workflow runs](https://docs.github.com/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs))

**A missed or dropped run** is visible in three places: the page's "Last checked" line (more
than 20 days old means the checks have stopped), the Actions tab (no run on the 3rd or 18th),
and the email (none arrives). Start the check by hand: GitHub > Actions > check > Run workflow.

**Re-enabling a disabled workflow.** GitHub > Actions > click "check" in the left list >
Enable workflow. Or from the repository folder: `gh workflow enable check.yml`. Then start
one run by hand to confirm it works.

### Reading the run summary

Each run's summary is saved as `data/runs/run-YYYYMMDD-HHMM.txt`, shown on the run's page in
the Actions tab, and (once set up) emailed. The subject line gives the triage:
`[PFRT] 2 candidates; 1 state not checked (DATE)`, or `[PFRT] ACTION: ...` when states could not be checked.
Sections, in order:

| Section | Meaning | What to do |
|---|---|---|
| States not fully checked | A leading source of a monitored state did not give a usable page. "ACTION: check this state by hand" after 2 failures in a row | Open the source URL in a browser. If the page moved, update `config/sources.csv`; if the site blocks the tool, check the state by hand until fixed |
| Expected notice not seen | A state's `next_notice_expected_by` date has passed with no record or candidate communicated in the 120 days before it | Look for the notice on the state's site; the regulator may have moved its bulletins to a page that is not watched |
| Manual checks due this month | The by-hand checks in `config/manual_checks.csv` (statute states, May and September) | Do the check; log anything found with `review add` |
| Candidates | Possible new rate documents found this run | In Claude Code: "Pull the latest changes and list open candidates." Then review each (CLAUDE.md, review protocol) |
| Other page changes | A watched page changed, but no new item matched the keywords | Skim the listed titles; if one is a rate notice, add a keyword to `config/keywords.csv` |
| Not monitored | States with no enabled leading source | Nothing each run; read the list every six months |
| Link check results | First run of the month: source and record links that did not answer HTTP 200, or that redirect to another host | Fix a source URL in `config/sources.csv`; fix a record link with `review amend` (the saved copy stays) |
| Run | Totals and the run log's location | |

### Source statuses

| Status | Meaning | Counts as checked |
|---|---|---|
| `ok`, `unchanged`, `changed`, `baseline` | Page fetched and read. `baseline` is the first good fetch of a source; it never creates candidates | Yes |
| `failed` | Network error, timeout, or an HTTP error other than 403 and 429 | No |
| `blocked` | HTTP 403 or 429, or a bot-challenge page | No |
| `blocked_robots` | The site's robots.txt does not allow the page; not fetched | No |
| `suspect` | HTTP 200, but the `must_contain` marker is missing or the page is under 40% of its last size | No |
| `suspect_redesign` | More than 25 new links at once; no candidates made, old snapshot kept | No |
| `needs_browser` | Under 500 characters of visible text (page built by script) | No |

Link check statuses: `http_error` (not 200), `moved_host` (redirects to another host), `blocked`
(403 or 429), `failed` (no answer), `robots` (robots.txt does not allow it; not requested). A
one-off `failed` can be a slow server; a link that fails in two months running needs a look.
To run the link check by hand at any time (writes nothing): `python -m pfrt linkcheck`.

### Adding or changing a source

Sources live in `config/sources.csv`, never in code. Follow `docs/onboarding.md`. In short:
read the site's terms and robots.txt; add the row with `enabled` = `no`; run
`python -m pfrt check --dry-run --states XX --include-disabled`; when the page is fetched and
the marker found, set `verification` = `fetched`, `verified_on`, and `enabled` = `yes`; run two
dry runs at least a day apart to make sure the page does not change by itself (if it does, add a
`selector` or a pattern in `pfrt/normalize.py`, with a test); then `python -m pfrt config check`
and `pytest`. Record the reason in `docs/decisions.md` and the fetch in `docs/research_log.md`.

### Email (off until set up)

The summary is emailed through Gmail SMTP when three repository secrets exist:
`SMTP_USER` (the sending Gmail address), `SMTP_APP_PASSWORD` (a Google app password, not the
account password) and `ALERT_TO` (one or more addresses, separated by commas). Set them in
GitHub > Settings > Secrets and variables > Actions. Test with Actions > check > Run workflow,
ticking "Send a test email". The optional backup GitHub issue is turned on with the repository
variable `PFRT_OPEN_ISSUES` = `yes`.

**Rotating the app password.** In the sending Google account, create a new app password
(Google Account > Security > 2-Step Verification > App passwords; Google may move this page).
In GitHub, update the secret `SMTP_APP_PASSWORD` with the new value. Run the check workflow with
"Send a test email". When the test arrives, delete the old app password in the Google account.
The password is never written to a file, a commit or a log.
