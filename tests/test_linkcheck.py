"""Link check tests (plan 9.6). No network: sessions, throttle and robots are fakes."""

import datetime as dt
import json

import requests

from pfrt import config, linkcheck

TODAY = dt.date(2026, 12, 3)


class Resp:
    """A streamed response: usable in `with`, body never read."""
    def __init__(self, status, url):
        self.status_code, self.url = status, url

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Session:
    """Answers each URL from a table: (status, final_url) or an exception."""
    def __init__(self, table):
        self.table, self.calls = table, []

    def get(self, url, **kw):
        assert kw.get("stream") is True          # the body is never downloaded
        self.calls.append(url)
        out = self.table[url]
        if isinstance(out, list):
            out = out.pop(0)
        if isinstance(out, Exception):
            raise out
        status, final = out
        return Resp(status, final or url)


class NoWait:
    def __init__(self):
        self.urls = []

    def wait(self, url):
        self.urls.append(url)


class Robots:
    def __init__(self, disallowed=()):
        self.disallowed = set(disallowed)

    def check(self, url):
        return ("disallowed", "robots.txt disallows this path") if url in self.disallowed else ("allowed", "")


def src(source_id, url, enabled="yes", state="WI"):
    return config.Source(source_id=source_id, state=state, products="CL", role="leading",
                         watch_mode="new_links", url=url, format="html", selector="", must_contain="",
                         citation="", enabled=enabled, verification="fetched", verified_on="", notes="")


def run(sources, records, table, disallowed=()):
    session = Session(table)
    res = linkcheck.run(sources, records, TODAY, session, NoWait(), Robots(disallowed),
                        sleep=lambda s: None, echo=lambda *a: None)
    return res, session


def test_collect_enabled_sources_and_confirmed_records_only_and_shares_urls():
    sources = [src("WI-a", "https://oci.wi.gov/a"), src("WI-off", "https://oci.wi.gov/off", enabled="no"),
               src("AL-aam", "https://x.gov/api/aam/{prev_month}", state="AL")]
    records = [{"record_id": "WI-CL-2027-01-01-1", "status": "confirmed", "source_url": "https://oci.wi.gov/a"},
               {"record_id": "WI-CL-2009-01-01-1", "status": "retracted", "source_url": "https://oci.wi.gov/r"}]
    urls = linkcheck.collect(sources, records, TODAY)
    assert urls == {"https://oci.wi.gov/a": ["WI-a", "WI-CL-2027-01-01-1"],
                    "https://x.gov/api/aam/2026-11": ["AL-aam"]}   # placeholder filled in


def test_interleave_hosts_round_robin():
    urls = ["https://a.gov/1", "https://a.gov/2", "https://b.gov/1", "https://a.gov/3", "https://c.gov/1"]
    assert linkcheck.interleave_hosts(urls) == ["https://a.gov/1", "https://b.gov/1", "https://c.gov/1",
                                                "https://a.gov/2", "https://a.gov/3"]


def test_classify_each_outcome():
    u = "https://oci.wi.gov/a"
    assert linkcheck.classify(u, 200, u) == ("ok", "")
    assert linkcheck.classify(u, 200, "https://oci.wi.gov/b") == ("ok", "")             # same host
    assert linkcheck.classify("http://oci.wi.gov/a", 200, "https://oci.wi.gov/a")[0] == "ok"
    # "www." added or dropped is the same site (www.aldoi.gov -> aldoi.gov, seen 2026-11-22)
    assert linkcheck.classify("https://www.aldoi.gov/a", 200, "https://aldoi.gov/a")[0] == "ok"
    # A real move to another host is reported (gencourt.state.nh.us -> gc.nh.gov, seen 2026-11-22)
    assert linkcheck.classify("https://gencourt.state.nh.us/r", 200, "https://gc.nh.gov/r")[0] == "moved_host"
    assert linkcheck.classify(u, 200, "https://www.wi.gov/a") == ("moved_host", "redirects to https://www.wi.gov/a")
    assert linkcheck.classify(u, 404, u) == ("http_error", "HTTP 404")
    assert linkcheck.classify(u, 403, u) == ("blocked", "HTTP 403")
    assert linkcheck.classify(u, None, "", "ConnectionError") == ("failed", "ConnectionError")


def test_run_reports_problems_and_obeys_robots():
    sources = [src("WI-a", "https://oci.wi.gov/a"), src("WI-b", "https://oci.wi.gov/b"),
               src("IN-c", "https://www.in.gov/c", state="IN"), src("VA-d", "https://scc.virginia.gov/d", state="VA")]
    records = [{"record_id": "IN-CL-2024-12-19-1", "status": "confirmed", "source_url": "https://www.in.gov/gone.pdf"}]
    table = {"https://oci.wi.gov/a": (200, None), "https://oci.wi.gov/b": (200, "https://new.example.gov/b"),
             "https://www.in.gov/c": (200, None), "https://www.in.gov/gone.pdf": (404, None)}
    res, session = run(sources, records, table, disallowed={"https://scc.virginia.gov/d"})
    by = {r.url: r for r in res}
    assert by["https://oci.wi.gov/a"].status == "ok"
    assert by["https://oci.wi.gov/b"].status == "moved_host"
    assert by["https://www.in.gov/gone.pdf"].status == "http_error"
    assert by["https://scc.virginia.gov/d"].status == "robots"
    assert "https://scc.virginia.gov/d" not in session.calls       # never requested
    lines = linkcheck.summary_lines(res)
    assert lines[0] == "5 links checked; 3 problems."
    assert any(l.startswith("IN-CL-2024-12-19-1: http_error (HTTP 404)") for l in lines)
    assert lines[-1].startswith("A broken record link is not changed automatically")


def test_retries_connection_error_then_succeeds():
    table = {"https://oci.wi.gov/a": [requests.ConnectionError(), (200, None)]}
    res, session = run([src("WI-a", "https://oci.wi.gov/a")], [], table)
    assert res[0].status == "ok" and len(session.calls) == 2


def test_all_ok_summary_has_count_only():
    res, _ = run([src("WI-a", "https://oci.wi.gov/a")], [], {"https://oci.wi.gov/a": (200, None)})
    assert linkcheck.summary_lines(res) == ["1 links checked; 0 problems."]


def test_due_once_per_month(tmp_path):
    assert linkcheck.due(tmp_path, TODAY)                                     # no runs yet
    (tmp_path / "run-20261203-1317.json").write_text(json.dumps({"run_id": "x"}), encoding="utf-8")
    assert linkcheck.due(tmp_path, TODAY)                                     # a run, no link check
    (tmp_path / "run-20261203-1330.json").write_text(json.dumps({"link_check": ["1 links checked; 0 problems."]}),
                                                     encoding="utf-8")
    assert not linkcheck.due(tmp_path, dt.date(2026, 12, 18))                 # done this month
    assert linkcheck.due(tmp_path, dt.date(2027, 1, 3))                       # new month


def test_summary_section_in_composed_email():
    from pfrt import notify
    log = {"run_id": "run-20261203-1317", "sources": [], "states_not_fully_checked": [], "not_monitored": [],
           "totals": {"sources": 0, "candidates": 0, "not_ok": 0}, "monitored_state_count": 33,
           "link_check": ["2 links checked; 0 problems."]}
    body = notify.compose(log, [], [], 0).body
    assert "== Link check results ==\n2 links checked; 0 problems." in body
    assert body.index("Link check results") < body.index("== Run ==")


def test_check_command_runs_link_check_only_when_wanted(tmp_path):
    from types import SimpleNamespace
    from pfrt.__main__ import link_check_wanted
    (tmp_path / "data" / "runs").mkdir(parents=True)
    a = lambda **kw: SimpleNamespace(**{"link_check": "auto", "dry_run": False, "offline": False, **kw})  # noqa: E731
    assert link_check_wanted(a(), tmp_path, TODAY, some_states=False)              # first full run of month
    assert not link_check_wanted(a(dry_run=True), tmp_path, TODAY, False)
    assert not link_check_wanted(a(offline=True), tmp_path, TODAY, False)
    assert not link_check_wanted(a(), tmp_path, TODAY, some_states=True)
    assert link_check_wanted(a(link_check="yes", dry_run=True), tmp_path, TODAY, True)
    assert not link_check_wanted(a(link_check="no"), tmp_path, TODAY, False)
