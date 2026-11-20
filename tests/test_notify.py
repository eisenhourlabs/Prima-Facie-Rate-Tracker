"""Run summary and notification tests (plan 9.1: Notify). No network; SMTP and HTTP are faked."""

import datetime as dt
import shutil
from types import SimpleNamespace

import pytest

from pfrt import notify
from pfrt.__main__ import main
from tests.conftest import FIXTURES, REPO

SECRETS = {"SMTP_USER": "project.mailbox@example.com", "SMTP_APP_PASSWORD": "abcd efgh ijkl mnop",
           "ALERT_TO": "one@example.com, two@example.com"}


def entry(sid, state, status="unchanged", role="leading", failures=0, **kw):
    return {"source_id": sid, "state": state, "status": status, "role": role, "error": kw.get("error", ""),
            "consecutive_failures": failures, "notes": kw.get("notes", []), "new_anchors": kw.get("anchors", [])}


def run_log(**over):
    log = {"run_id": "run-20261203-1317",
           "sources": [entry("IN-bulletins", "IN"), entry("WI-bulletins-index", "WI", "failed", failures=1, error="HTTP 404"),
                       entry("IL-reg", "IL", notes=["changed_no_match"], anchors=["Bulletin 9 - Ownership"])],
           "totals": {"sources": 3, "candidates": 2, "not_ok": 1},
           "states_not_fully_checked": ["WI"], "not_monitored": ["ID", "VA"], "monitored_state_count": 3}
    log.update(over)
    return log


def cand(cid, state="IN"):
    return {"candidate_id": cid, "state": state, "rule": "R1_new_matching_link", "priority": "high",
            "anchor_text": "Bulletin 278 - Credit Life Rates", "document_url": "https://www.in.gov/b278.pdf",
            "matched_keywords": ["credit life"], "unreadable_document": False}


def test_acceptance_1_two_candidates_one_failed_state():
    email = notify.compose(run_log(), [cand("c-20261203-IN-01"), cand("c-20261203-IN-02")], [], 2)
    assert email.subject == "[PFRT] 2 candidates; 1 state not checked (2026-12-03)"
    order = ["== States not fully checked ==", "== Expected notice not seen ==", "== Candidates ==",
             "== Other page changes ==", "== Not monitored", "== Run =="]
    positions = [email.body.index(h) for h in order]
    assert positions == sorted(positions)
    first = email.body.split("== Expected notice")[0]
    assert "WI WI-bulletins-index: failed (HTTP 404)" in first     # the failed state comes first
    assert "Bulletin 9 - Ownership" in email.body                   # other page changes listed


@pytest.mark.parametrize("n_cands, n_gaps, expected", [
    (0, 0, "[PFRT] No candidates; all 3 monitored states checked (2026-12-03)"),
    (0, 3, "[PFRT] ACTION: 3 states not checked (2026-12-03)"),
    (1, 0, "[PFRT] 1 candidate; all 3 monitored states checked (2026-12-03)"),
    (2, 1, "[PFRT] 2 candidates; 1 state not checked (2026-12-03)"),
])
def test_subject_patterns(n_cands, n_gaps, expected):
    assert notify.subject(n_cands, n_gaps, 3, "2026-12-03") == expected


def test_action_flag_after_two_failures():
    log = run_log(sources=[entry("WI-bulletins-index", "WI", "blocked", failures=2)])
    assert "ACTION: check this state by hand" in notify.compose(log, [], [], 0).body


def test_quiet_run_says_none_in_each_section():
    log = run_log(sources=[entry("IN-bulletins", "IN")], states_not_fully_checked=[], not_monitored=[],
                  totals={"sources": 1, "candidates": 0, "not_ok": 0})
    body = notify.compose(log, [], [], 0).body
    assert body.count("None.") == 5


# --- Expected notices -------------------------------------------------------------

def state(code, due):
    return SimpleNamespace(state=code, next_notice_expected_by=due)


def test_expected_notice_past_due_and_unseen_is_listed():
    assert notify.expected_not_seen([state("WI", "2029-10-01")], [], [], dt.date(2029, 10, 2)) == [("WI", "2029-10-01")]


def test_late_notice_still_counts():
    # Wisconsin 2026: due October 1, communicated October 16.
    recs = [{"state": "WI", "date_communicated": "2026-10-16"}]
    assert notify.expected_not_seen([state("WI", "2026-10-01")], recs, [], dt.date(2026, 11, 20)) == []


def test_open_candidate_counts_and_future_or_blank_dates_are_ignored():
    cands = [{"state": "WI", "detected_at": "2029-09-15T13:00:00Z"}]
    assert notify.expected_not_seen([state("WI", "2029-10-01")], [], cands, dt.date(2029, 10, 5)) == []
    assert notify.expected_not_seen([state("WI", "2029-10-01"), state("IN", "")], [], [], dt.date(2029, 9, 1)) == []


# --- Delivery -------------------------------------------------------------------------

class FakeSMTP:
    sent, fail = [], None

    def __init__(self, host, port, timeout):
        self.host = host

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def starttls(self, context):
        pass

    def login(self, user, password):
        if FakeSMTP.fail:
            raise FakeSMTP.fail

    def send_message(self, msg):
        FakeSMTP.sent.append(msg)


def test_not_configured_sends_nothing():
    assert notify.deliver(notify.Email("s", "b"), {}, True) == ["email not configured", "issue not enabled"]


def test_email_goes_to_every_alert_address():
    FakeSMTP.sent, FakeSMTP.fail = [], None
    assert notify.deliver(notify.Email("s", "b"), SECRETS, False, smtp_factory=FakeSMTP)[0] == "email sent"
    assert FakeSMTP.sent[0]["To"] == "one@example.com, two@example.com"


def test_send_failure_never_reveals_the_password():
    FakeSMTP.fail = Exception(f"535 bad credentials for {SECRETS['SMTP_APP_PASSWORD']}")
    with pytest.raises(notify.NotifyError) as err:
        notify.deliver(notify.Email("s", "b"), SECRETS, False, smtp_factory=FakeSMTP)
    FakeSMTP.fail = None
    assert SECRETS["SMTP_APP_PASSWORD"] not in str(err.value) and "Exception" in str(err.value)


def test_issue_opens_only_when_enabled_and_there_is_news():
    calls = []
    post = lambda url, **kw: calls.append((url, kw)) or SimpleNamespace(status_code=201)  # noqa: E731
    env = {"PFRT_OPEN_ISSUES": "yes", "GITHUB_TOKEN": "t0ken", "GITHUB_REPOSITORY": "o/r"}
    assert notify.deliver(notify.Email("s", "b"), env, False, post=post)[-1] == "issue not needed"
    assert notify.deliver(notify.Email("s", "b"), env, True, post=post)[-1] == "issue opened"
    assert calls[0][0] == "https://api.github.com/repos/o/r/issues"


# --- Through the command line, with no secrets -----------------------------------------------

def test_real_run_saves_summary_and_reports_email_not_configured(tmp_path, capsys, monkeypatch):
    for k in list(SECRETS) + ["PFRT_OPEN_ISSUES", "GITHUB_STEP_SUMMARY"]:
        monkeypatch.delenv(k, raising=False)
    shutil.copytree(REPO / "config", tmp_path / "config")
    code = main(["--root", str(tmp_path), "check", "--offline", "--fixtures", str(FIXTURES), "--states", "IN,WI"])
    out = capsys.readouterr().out
    assert code == 0 and "Notify: email not configured" in out
    [txt] = (tmp_path / "data" / "runs").glob("run-*.txt")
    text = txt.read_text(encoding="utf-8")
    assert text.startswith("[PFRT] No candidates; all 2 monitored states checked")
    assert "== States not fully checked ==\nNone." in text


def test_step_summary_written_in_github_actions(tmp_path, capsys, monkeypatch):
    summary = tmp_path / "step_summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    shutil.copytree(REPO / "config", tmp_path / "repo" / "config")
    main(["--root", str(tmp_path / "repo"), "check", "--dry-run", "--offline", "--fixtures", str(FIXTURES), "--states", "IN"])
    assert summary.read_text(encoding="utf-8").startswith("## [PFRT] No candidates")
