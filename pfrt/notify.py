"""Run summary and (optional) notifications (plan section 6, modified 2026-11-20).

Every run composes a summary in the plan 6.3 order and saves it next to the
run log, so it can be read on GitHub and, from Stage 4, on the site.

Sending is OFF until it is configured. Nothing here needs changing to turn it on:
  Email   set the GitHub secrets SMTP_USER, SMTP_APP_PASSWORD and ALERT_TO
          (ALERT_TO may list several addresses separated by commas).
  Issue   set the repository variable PFRT_OPEN_ISSUES to "yes" (uses the
          workflow's built-in token) to open an issue when a run has
          candidates or unchecked states.
Secret values are never printed or written; errors name only the error class.
"""

from __future__ import annotations

import datetime as dt
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage

SMTP_HOST, SMTP_PORT = "smtp.gmail.com", 587
EXPECTED_WINDOW_DAYS = 120
ACTION_AFTER_FAILURES = 2
REVIEW_COMMANDS = ("git pull", "python -m pfrt review list", "python -m pfrt review show ID")


class NotifyError(Exception):
    """Sending failed. The message never contains a secret value."""


@dataclass(frozen=True)
class Email:
    subject: str
    body: str


# --- Expected notices (plan 3.5) -------------------------------------------------

def expected_not_seen(states, records: list[dict], candidates: list[dict], today: dt.date) -> list[tuple[str, str]]:
    """States whose next_notice_expected_by has passed with no notice seen.

    A notice counts if a record's date_communicated, or an open candidate's
    detection date, falls on or after 120 days before the expected date.
    (Notices can arrive late: Wisconsin's 2026 bulletin came 15 days after the
    October 1 date in its rule, and must still count.)
    """
    out = []
    for s in states:
        if not s.next_notice_expected_by:
            continue
        due = dt.date.fromisoformat(s.next_notice_expected_by)
        if today <= due:
            continue
        since = (due - dt.timedelta(days=EXPECTED_WINDOW_DAYS)).isoformat()
        seen = [r.get("date_communicated") or "" for r in records if r.get("state") == s.state]
        seen += [(c.get("detected_at") or "")[:10] for c in candidates if c.get("state") == s.state]
        if not any(d >= since for d in seen if d):
            out.append((s.state, s.next_notice_expected_by))
    return out


# --- Composing the summary ---------------------------------------------------------

def subject(n_candidates: int, n_gaps: int, n_monitored: int, day: str) -> str:
    """Plan 6.3 subject lines, so the inbox (or the run list) is enough to triage."""
    states = lambda n: f"{n} state{'s' if n != 1 else ''}"  # noqa: E731
    if n_candidates == 0 and n_gaps:
        return f"[PFRT] ACTION: {states(n_gaps)} not checked ({day})"
    cands = f"{n_candidates} candidate{'s' if n_candidates != 1 else ''}" if n_candidates else "No candidates"
    checked = f"{states(n_gaps)} not checked" if n_gaps else f"all {n_monitored} monitored states checked"
    return f"[PFRT] {cands}; {checked} ({day})"


def compose(run_log: dict, new_candidates: list[dict], expected: list[tuple[str, str]],
            open_candidate_count: int, repo_url: str = "") -> Email:
    """Build the summary. Sections appear in the order of plan 6.3."""
    day = run_log["run_id"][4:8] + "-" + run_log["run_id"][8:10] + "-" + run_log["run_id"][10:12]
    gaps = [e for e in run_log["sources"] if e["state"] in run_log["states_not_fully_checked"]
            and e.get("role") == "leading" and e["status"] not in ("ok", "baseline", "unchanged", "changed")]
    n_gap_states = len(run_log["states_not_fully_checked"])
    sections = [
        _section("States not fully checked", [_gap_line(e) for e in gaps]),
        _section("Expected notice not seen", [f"{st}: expected by {d}" for st, d in expected]),
        _section("Candidates", [_candidate_lines(c) for c in new_candidates]),
        _section("Other page changes", [f"{e['state']} {e['source_id']}: new link titles {e.get('new_anchors', [])[:8]}"
                                        for e in run_log["sources"] if "changed_no_match" in e.get("notes", [])]),
        _section("Not monitored (no enabled leading source)", [", ".join(run_log["not_monitored"])] if run_log["not_monitored"] else []),
    ]
    if run_log.get("link_check"):
        sections.append(_section("Link check results", run_log["link_check"]))
    sections.append(_footer(run_log, open_candidate_count, repo_url))
    n_monitored = run_log.get("monitored_state_count", 0)
    return Email(subject(len(new_candidates), n_gap_states, n_monitored, day), "\n\n".join(sections) + "\n")


def _section(title: str, lines: list[str]) -> str:
    return f"== {title} ==\n" + ("\n".join(lines) if lines else "None.")


def _gap_line(e: dict) -> str:
    n = e.get("consecutive_failures", 0)
    action = "  ACTION: check this state by hand" if n >= ACTION_AFTER_FAILURES else ""
    why = f" ({e['error']})" if e.get("error") else ""
    return f"{e['state']} {e['source_id']}: {e['status']}{why}; consecutive failures {n}{action}"


def _candidate_lines(c: dict) -> str:
    kw = ", ".join(c.get("matched_keywords") or []) or "-"
    flag = "  [unreadable document: review by hand]" if c.get("unreadable_document") else ""
    return (f"{c['candidate_id']}  {c['state']}  {c['rule']}  priority {c['priority']}{flag}\n"
            f"  {c.get('anchor_text') or '(no title)'}\n  {c['document_url']}\n  keywords: {kw}")


def _footer(run_log: dict, open_count: int, repo_url: str) -> str:
    t = run_log["totals"]
    link = f"{repo_url}/blob/main/data/runs/{run_log['run_id']}.json" if repo_url else f"data/runs/{run_log['run_id']}.json"
    return ("== Run ==\n"
            f"Run {run_log['run_id']}: {t['sources']} sources, {t['candidates']} new candidates, "
            f"{t['not_ok']} not ok, {open_count} open candidates in total.\n"
            f"Run log: {link}\n"
            "Review: " + "; ".join(REVIEW_COMMANDS))


# --- Delivery (off until configured) ---------------------------------------------------

def email_configured(env: dict) -> bool:
    return all(env.get(k) for k in ("SMTP_USER", "SMTP_APP_PASSWORD", "ALERT_TO"))


def send(email: Email, env: dict, smtp_factory=smtplib.SMTP) -> None:
    """Send by Gmail SMTP with STARTTLS. Raises NotifyError naming only the error class."""
    to = [a.strip() for a in env["ALERT_TO"].split(",") if a.strip()]
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = email.subject, env["SMTP_USER"], ", ".join(to)
    msg.set_content(email.body)
    try:
        with smtp_factory(SMTP_HOST, SMTP_PORT, timeout=30) as s:
            s.starttls(context=ssl.create_default_context())
            s.login(env["SMTP_USER"], env["SMTP_APP_PASSWORD"])
            s.send_message(msg)
    except Exception as err:  # never let the server's message (which may echo input) through
        raise NotifyError(f"email not sent: {type(err).__name__}") from None


def open_issue(email: Email, env: dict, post=None) -> None:
    """Open a GitHub issue with the summary, using the workflow's built-in token."""
    import requests
    post = post or requests.post
    url = f"https://api.github.com/repos/{env['GITHUB_REPOSITORY']}/issues"
    try:
        r = post(url, json={"title": email.subject, "body": "```\n" + email.body + "```"},
                 headers={"Authorization": f"Bearer {env['GITHUB_TOKEN']}",
                          "Accept": "application/vnd.github+json"}, timeout=30)
        if r.status_code >= 300:
            raise NotifyError(f"issue not opened: HTTP {r.status_code}")
    except NotifyError:
        raise
    except Exception as err:
        raise NotifyError(f"issue not opened: {type(err).__name__}") from None


def deliver(email: Email, env: dict, has_news: bool, smtp_factory=smtplib.SMTP, post=None) -> list[str]:
    """Send through whatever is configured. Returns one status line per channel.

    Email goes after every run once configured (decision Q1). The issue, when
    enabled, opens only for runs with candidates or unchecked states.
    Raises NotifyError after trying every channel if any configured one failed.
    """
    status, failures = [], []
    if email_configured(env):
        try:
            send(email, env, smtp_factory)
            status.append("email sent")
        except NotifyError as err:
            failures.append(str(err))
    else:
        status.append("email not configured")
    if env.get("PFRT_OPEN_ISSUES", "").lower() == "yes" and has_news:
        if env.get("GITHUB_TOKEN") and env.get("GITHUB_REPOSITORY"):
            try:
                open_issue(email, env, post)
                status.append("issue opened")
            except NotifyError as err:
                failures.append(str(err))
        else:
            failures.append("issue not opened: no workflow token")
    else:
        status.append("issue not enabled" if env.get("PFRT_OPEN_ISSUES", "").lower() != "yes" else "issue not needed")
    if failures:
        raise NotifyError("; ".join(failures))
    return status
