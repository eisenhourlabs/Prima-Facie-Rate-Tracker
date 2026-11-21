"""Fetch classification, robots and retry tests (plan 9.1: Fetch classification). No network."""

import requests

from pfrt import fetch
from pfrt.config import Source


def classify(status=200, error="", text="Credit life bulletins", marker="bulletins",
             size=1000, last=None):
    return fetch.classify(status, error, text, marker, size, last)[0]


def test_200_with_marker_is_ok():
    assert classify() == "ok"


def test_200_without_marker_is_suspect():
    assert classify(text="We are redesigning our site") == "suspect"


def test_200_challenge_page_without_marker_is_blocked():
    assert classify(text="Access Denied | Illinois General Assembly") == "blocked"


def test_403_and_429_are_blocked():
    assert classify(status=403) == "blocked"
    assert classify(status=429) == "blocked"


def test_404_and_500_are_failed():
    assert classify(status=404) == "failed"
    assert classify(status=500) == "failed"


def test_timeout_is_failed():
    assert classify(status=None, error="ReadTimeout") == "failed"


def test_size_under_40_percent_is_suspect():
    assert classify(size=399, last=1000) == "suspect"
    assert classify(size=400, last=1000) == "ok"


def test_marker_match_ignores_case():
    assert classify(text="CREDIT LIFE BULLETINS") == "ok"


# --- robots.txt -----------------------------------------------------------------

def test_robots_missing_means_allowed():
    rp, reason = fetch.parse_robots(404, "text/html", "Not found")
    assert rp is None and reason.startswith("allow")


def test_robots_server_error_means_not_allowed():
    rp, reason = fetch.parse_robots(503, "", "")
    assert rp is None and "unavailable" in reason


def test_robots_html_page_is_not_read_as_empty_rules():
    rp, reason = fetch.parse_robots(200, "text/html", "<!DOCTYPE html><title>Access Denied</title>")
    assert rp is None and "unreadable" in reason


def test_robots_disallow_all_but_search_engines_blocks_us():
    text = "User-agent: googlebot\nAllow: /\n\nUser-agent: *\nDisallow: /\n"
    rp, _ = fetch.parse_robots(200, "text/plain", text)
    assert not rp.can_fetch(fetch.USER_AGENT, "https://www.example.gov/getdoc/x")


def test_robots_crawl_delay_is_read():
    rp, _ = fetch.parse_robots(200, "text/plain", "User-agent: *\nCrawl-delay: 10\nDisallow: /api\n")
    assert rp.crawl_delay(fetch.USER_AGENT) == 10
    assert rp.can_fetch(fetch.USER_AGENT, "https://x.gov/ftp/a.html")
    assert not rp.can_fetch(fetch.USER_AGENT, "https://x.gov/api/a")


# --- Throttle and retries ----------------------------------------------------------

class FakeClock:
    def __init__(self):
        self.now, self.slept = 0.0, []

    def sleep(self, s):
        self.slept.append(round(s, 3))
        self.now += s

    def __call__(self):
        return self.now


def test_throttle_spaces_same_host_and_honors_crawl_delay():
    clock = FakeClock()
    t = fetch.Throttle(sleep=clock.sleep, clock=clock)
    t.wait("https://a.gov/1"); t.wait("https://b.gov/1"); t.wait("https://a.gov/2")
    assert clock.slept == [5.0]          # a.gov waited; b.gov had no earlier request
    t.set_crawl_delay("c.gov", 10)
    t.wait("https://c.gov/1"); t.wait("https://c.gov/2")
    assert clock.slept[-1] == 10.0       # robots Crawl-delay longer than 5 s is honored


class FakeResponse:
    def __init__(self, status, content=b"ok", ctype="text/html"):
        self.status_code, self.content, self.url = status, content, "https://a.gov/x"
        self.headers = {"Content-Type": ctype}
        self.text = content.decode()


class FakeSession:
    def __init__(self, *outcomes):
        self.outcomes, self.calls = list(outcomes), 0

    def get(self, url, **kw):
        self.calls += 1
        out = self.outcomes.pop(0)
        if isinstance(out, Exception):
            raise out
        return out


def no_wait_throttle():
    clock = FakeClock()
    return fetch.Throttle(sleep=clock.sleep, clock=clock)


def test_download_retries_timeouts_and_5xx_then_succeeds():
    waits = []
    s = FakeSession(requests.Timeout(), FakeResponse(503), FakeResponse(200))
    r = fetch.download("https://a.gov/x", s, no_wait_throttle(), sleep=waits.append)
    assert r.http_status == 200 and s.calls == 3 and waits == [10, 30]


def test_download_gives_up_after_two_retries():
    s = FakeSession(requests.ConnectionError(), requests.ConnectionError(), requests.ConnectionError())
    r = fetch.download("https://a.gov/x", s, no_wait_throttle(), sleep=lambda _: None)
    assert r.status == "failed" and r.error == "ConnectionError" and s.calls == 3


def test_download_does_not_retry_404():
    s = FakeSession(FakeResponse(404))
    assert fetch.download("https://a.gov/x", s, no_wait_throttle(), sleep=lambda _: None).http_status == 404
    assert s.calls == 1


def source(url="https://a.gov/x", must="bulletins"):
    return Source("ZZ-x", "ZZ", "CL", "leading", "new_links", url, "html", "", must, "", "yes",
                  "fetched", "", "")


def test_get_reports_blocked_robots_without_fetching_page():
    s = FakeSession(FakeResponse(200, b"User-agent: *\nDisallow: /\n", "text/plain"))
    t = no_wait_throttle()
    r = fetch.get(source(), s, None, fetch.RobotsCache(s, t), t)
    assert r.status == "blocked_robots" and s.calls == 1


def test_get_classifies_a_good_page_as_ok():
    page = b"<html><body><p>Credit life bulletins</p></body></html>"
    s = FakeSession(FakeResponse(404), FakeResponse(200, page))
    t = no_wait_throttle()
    r = fetch.get(source(), s, None, fetch.RobotsCache(s, t), t, sleep=lambda _: None)
    assert r.status == "ok" and r.text == "Credit life bulletins"


# --- robots.txt overrides (owner decision, config/robots_overrides.csv) ---------------

class _FakeRobotsSession:
    """Answers every robots.txt request with the given status, type and text."""
    def __init__(self, status, content_type, text):
        self.reply = type("R", (), {"status_code": status, "headers": {"Content-Type": content_type}, "text": text})

    def get(self, url, timeout=None):
        return self.reply


def _cache(status, ctype, text, overrides):
    return fetch.RobotsCache(_FakeRobotsSession(status, ctype, text), fetch.Throttle(sleep=lambda s: None), overrides)


def test_override_allows_only_the_listed_host_and_says_why():
    over = {"www.osi.example.gov": "2026-11-20: owner decision"}
    c = _cache(200, "text/plain", "User-agent: *\nDisallow: /\n", over)
    verdict, reason = c.check("https://www.osi.example.gov/wp-content/uploads/Bulletin.pdf")
    assert verdict == "allowed" and "owner override" in reason and "2026-11-20" in reason
    assert c.check("https://other.example.gov/x.pdf")[0] == "disallowed"


def test_override_does_not_bypass_an_unreadable_robots_file():
    over = {"blocked.example.gov": "2026-11-20: owner decision"}
    c = _cache(200, "text/html", "<html><title>Just a moment...</title></html>", over)
    assert c.check("https://blocked.example.gov/a.pdf")[0] == "unavailable"


def test_load_overrides_reads_the_real_config():
    over = fetch.load_overrides()
    assert "www.osi.state.nm.us" in over and over["www.osi.state.nm.us"].startswith("2026-11-20")
    assert fetch.load_overrides("does/not/exist.csv") == {}


def test_robots_redirected_to_an_ordinary_page_means_no_robots_file():
    """Oregon's rules site sends /robots.txt to its home page: there is no robots file."""
    rp, reason = fetch.parse_robots(200, "text/html", "<html><title>Welcome Page</title></html>",
                                    redirected_to="https://sos.example.gov/Pages/default.aspx")
    assert rp is None and reason.startswith("allow") and "redirected" in reason


def test_robots_redirect_to_a_challenge_page_still_stops():
    rp, reason = fetch.parse_robots(200, "text/html", "<html><title>Just a moment...</title></html>",
                                    redirected_to="https://x.example.gov/challenge")
    assert rp is None and "unreadable" in reason


def test_robots_html_at_robots_path_without_redirect_still_stops():
    c = _cache(200, "text/html", "<html><title>Home</title></html>", {})
    assert c.check("https://x.example.gov/a.pdf")[0] == "unavailable"
