"""Fetch a source politely and classify the result (plan sections 2.4 and 9.4).

Statuses:
  ok              HTTP 200, the must_contain marker is present, size looks normal.
  failed          network error, timeout, or an HTTP error other than 403/429.
  blocked         HTTP 403 or 429, or a known "are you a robot" challenge page.
  suspect         HTTP 200 but the marker is missing, or the page is under 40% of
                  its last good size. Counts as NOT checked.
  blocked_robots  the site's robots.txt does not allow this path. Not fetched.

Politeness: robots.txt is obeyed; requests to one host are at least 5 seconds
apart (longer if robots.txt asks for a longer Crawl-delay); one request at a time.
"""

from __future__ import annotations

import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib import robotparser
from urllib.parse import urlsplit

import certifi
import requests

from pfrt import documents

USER_AGENT = ("PrimaFacieRateTracker/0.1 "
              "(+https://github.com/eisenhourlabs/Prima-Facie-Rate-Tracker)")
TIMEOUT_SECONDS = 30
RETRY_WAITS = (10, 30)      # seconds to wait before retry 1 and retry 2
MIN_HOST_GAP = 5.0          # seconds between requests to the same host
SIZE_FLOOR = 0.40           # under 40% of the last good byte count is suspect

# Phrases seen on bot-challenge and block pages. Only used when must_contain
# is also missing, so a real page that mentions one of these is not misread.
CHALLENGE_MARKERS = ("just a moment", "attention required", "access denied",
                     "captcha", "cf-chl", "request unsuccessful", "are you a robot")

# Extra intermediate certificates for sites that send an incomplete chain.
# Verification stays on: these only fill the gap up to a root Python trusts.
CERTS_DIR = Path(__file__).parent / "certs"


@dataclass
class FetchResult:
    status: str
    http_status: int | None = None
    final_url: str = ""
    content: bytes = b""
    content_type: str = ""
    byte_count: int = 0
    error: str = ""
    text: str = ""          # full visible text (HTML) or extracted text (PDF)


# --- Certificates -----------------------------------------------------------

_bundle_path: str | None = None


def ca_bundle() -> str:
    """Path to a CA file: Python's standard roots (certifi) plus pfrt/certs/*.pem."""
    global _bundle_path
    if _bundle_path is None:
        parts = [Path(certifi.where()).read_text(encoding="utf-8")]
        parts += [p.read_text(encoding="utf-8") for p in sorted(CERTS_DIR.glob("*.pem"))]
        f = tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False, encoding="utf-8")
        f.write("\n".join(parts))
        f.close()
        _bundle_path = f.name
    return _bundle_path


def new_session() -> requests.Session:
    """A requests session with the project User-Agent and the extended CA bundle."""
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    s.verify = ca_bundle()
    return s


# --- Waiting between requests ----------------------------------------------

class Throttle:
    """Keeps requests to the same host at least `gap` seconds apart."""

    def __init__(self, sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], float] = time.monotonic):
        self._last: dict[str, float] = {}
        self._extra_gap: dict[str, float] = {}
        self._sleep, self._clock = sleep, clock

    def set_crawl_delay(self, host: str, seconds: float) -> None:
        self._extra_gap[host] = seconds

    def wait(self, url: str) -> None:
        host = urlsplit(url).netloc.lower()
        gap = max(MIN_HOST_GAP, self._extra_gap.get(host, 0.0))
        if host in self._last:
            remaining = gap - (self._clock() - self._last[host])
            if remaining > 0:
                self._sleep(remaining)
        self._last[host] = self._clock()


# --- robots.txt -------------------------------------------------------------

def parse_robots(http_status: int | None, content_type: str, text: str,
                 error: str = "") -> tuple[robotparser.RobotFileParser | None, str]:
    """Turn a robots.txt response into a parser, or None with a reason.

    None with reason starting "allow" means no robots.txt (everything allowed).
    None with any other reason means the file could not be read: do not fetch.
    """
    if error:
        return None, f"robots.txt unavailable: {error}"
    if http_status is not None and http_status >= 500:
        return None, f"robots.txt unavailable: HTTP {http_status}"
    if http_status is not None and http_status >= 400:
        return None, "allow: no robots.txt"
    # An HTML page served instead of robots.txt (block page, redirect page) is not
    # a real robots file. Reading it as "no rules" would wrongly allow everything.
    if "html" in content_type.lower() or text.lstrip()[:1] == "<":
        return None, "robots.txt unreadable: server returned a web page"
    rp = robotparser.RobotFileParser()
    rp.parse(text.splitlines())
    return rp, "robots.txt read"


OVERRIDES_FILE = Path(__file__).resolve().parent.parent / "config" / "robots_overrides.csv"


def load_overrides(path: str | Path = OVERRIDES_FILE) -> dict[str, str]:
    """config/robots_overrides.csv as {host: "approved_on: reason"}.

    Each row is a host whose robots.txt disallow the owner has decided to override
    (the site has no other barrier and no terms against automated access). The tool
    keeps its honest name and its polite pace there. A missing file means no overrides.
    """
    import csv
    p = Path(path)
    if not p.is_file():
        return {}
    with open(p, encoding="utf-8", newline="") as f:
        return {r["host"].strip().lower(): f"{r['approved_on'].strip()}: {r['reason'].strip()}"
                for r in csv.DictReader(f) if (r.get("host") or "").strip()}


class RobotsCache:
    """Reads each host's robots.txt once per run and answers can-I-fetch questions.

    `overrides` ({host: note}) lists hosts where a robots.txt disallow is overridden by
    the owner's decision; by default it is read from config/robots_overrides.csv.
    Only "disallowed" is overridden: an unreadable robots.txt still stops the fetch.
    """

    def __init__(self, session: requests.Session, throttle: Throttle, overrides: dict[str, str] | None = None):
        self._session, self._throttle = session, throttle
        self._cache: dict[str, tuple[robotparser.RobotFileParser | None, str]] = {}
        self._overrides = load_overrides() if overrides is None else overrides

    def check(self, url: str) -> tuple[str, str]:
        """Return ("allowed" | "disallowed" | "unavailable", reason)."""
        parts = urlsplit(url)
        host = parts.netloc.lower()
        if host not in self._cache:
            self._cache[host] = self._load(f"{parts.scheme}://{host}/robots.txt")
            rp = self._cache[host][0]
            delay = rp.crawl_delay(USER_AGENT) if rp else None
            if delay:
                self._throttle.set_crawl_delay(host, float(delay))
        rp, reason = self._cache[host]
        if rp is None:
            return ("allowed" if reason.startswith("allow") else "unavailable"), reason
        if rp.can_fetch(USER_AGENT, url):
            return "allowed", reason
        if host in self._overrides:
            return "allowed", f"robots.txt disallows this path; fetched under owner override ({self._overrides[host]})"
        return "disallowed", "robots.txt disallows this path"

    def _load(self, robots_url: str):
        self._throttle.wait(robots_url)
        try:
            r = self._session.get(robots_url, timeout=TIMEOUT_SECONDS)
            return parse_robots(r.status_code, r.headers.get("Content-Type", ""), r.text)
        except requests.RequestException as err:
            return parse_robots(None, "", "", error=type(err).__name__)


def robots_allowed(url: str, user_agent: str = USER_AGENT) -> bool:
    """Plan 1.4 helper: True if robots.txt allows the URL. Uses a one-off session."""
    session = new_session()
    session.headers["User-Agent"] = user_agent
    return RobotsCache(session, Throttle()).check(url)[0] == "allowed"


# --- Classification ---------------------------------------------------------

def classify(http_status: int | None, error: str, page_text: str,
             must_contain: str, byte_count: int, last_byte_count: int | None) -> tuple[str, str]:
    """Decide the status of one fetch. Returns (status, reason). Pure: no network."""
    if error:
        return "failed", error
    if http_status in (403, 429):
        return "blocked", f"HTTP {http_status}"
    if http_status != 200:
        return "failed", f"HTTP {http_status}"
    low = page_text.lower()
    if must_contain and must_contain.lower() not in low:
        if any(m in low for m in CHALLENGE_MARKERS):
            return "blocked", "challenge or block page"
        return "suspect", f"marker '{must_contain}' not found"
    if last_byte_count and byte_count < SIZE_FLOOR * last_byte_count:
        return "suspect", f"size {byte_count} is under 40% of last good size {last_byte_count}"
    return "ok", ""


# --- Fetching ---------------------------------------------------------------

def download(url: str, session: requests.Session, throttle: Throttle,
             sleep: Callable[[float], None] = time.sleep) -> FetchResult:
    """GET a URL with retries on timeouts, connection errors and 5xx. Not classified yet."""
    last = FetchResult(status="failed")
    for attempt in range(len(RETRY_WAITS) + 1):
        if attempt:
            sleep(RETRY_WAITS[attempt - 1])
        throttle.wait(url)
        try:
            r = session.get(url, timeout=TIMEOUT_SECONDS, allow_redirects=True)
        except (requests.Timeout, requests.ConnectionError) as err:
            last = FetchResult(status="failed", error=f"{type(err).__name__}")
            continue
        except requests.RequestException as err:
            return FetchResult(status="failed", error=f"{type(err).__name__}")
        last = FetchResult(status="fetched", http_status=r.status_code, final_url=r.url,
                           content=r.content, content_type=r.headers.get("Content-Type", ""),
                           byte_count=len(r.content))
        if r.status_code < 500:
            break
    return last


def get(source, session: requests.Session, last_byte_count: int | None,
        robots: RobotsCache, throttle: Throttle,
        sleep: Callable[[float], None] = time.sleep) -> FetchResult:
    """Fetch one source (a config.Source) and classify it, as in plan 2.4 step 3."""
    verdict, reason = robots.check(source.url)
    if verdict == "disallowed":
        return FetchResult(status="blocked_robots", error=reason)
    if verdict == "unavailable":
        return FetchResult(status="failed", error=reason)
    result = download(source.url, session, throttle, sleep)
    if result.status == "fetched" and result.http_status == 200:
        result.text = documents.content_text(result.content, result.content_type)
    result.status, result.error = classify(
        result.http_status, result.error, result.text, source.must_contain,
        result.byte_count, last_byte_count)
    return result
