"""Monthly link check (plan section 9.6).

On the first full run of each month, request every url of an enabled source in
sources.csv and every source_url of a confirmed record, with the same politeness as
the check (robots.txt obeyed, 5 seconds between requests to one host). Anything other
than HTTP 200, and any redirect to a different host, is listed in the run summary.

A broken record link is never edited automatically: the saved copy remains, and the
owner updates the URL with `review amend`. Disabled sources are left out on purpose:
most are disabled because their host refuses the tool, and listing them every month
would bury the new problems (decision 2026-11-22).

Only the status line and headers are read (a streamed GET, closed at once), so a
large PDF is not downloaded. Many state servers answer HEAD requests wrongly.
"""

from __future__ import annotations

import datetime as dt
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

import requests

from pfrt import config, fetch

OK = "ok"


@dataclass
class LinkResult:
    url: str
    used_by: list[str] = field(default_factory=list)   # source ids and record ids
    status: str = ""        # ok, moved_host, http_error, blocked, failed, robots
    http_status: int | None = None
    final_url: str = ""
    note: str = ""


# --- What to check -------------------------------------------------------------------

def collect(sources, records: list[dict], today: dt.date) -> dict[str, list[str]]:
    """{url: [source ids and record ids that use it]} for enabled sources and confirmed records."""
    urls: dict[str, list[str]] = defaultdict(list)
    for s in sources:
        if s.is_enabled and s.url:
            urls[config.resolve_url(s.url, today)].append(s.source_id)
    for r in records:
        if r.get("status") == "confirmed" and r.get("source_url"):
            urls[r["source_url"]].append(r.get("record_id", "?"))
    return dict(urls)


def interleave_hosts(urls: list[str]) -> list[str]:
    """Order URLs round-robin by host, so the 5-second gap per host costs little waiting."""
    by_host: dict[str, list[str]] = defaultdict(list)
    for u in sorted(urls):
        by_host[urlsplit(u).netloc.lower()].append(u)
    queues = [by_host[h] for h in sorted(by_host)]
    out = []
    while any(queues):
        for q in queues:
            if q:
                out.append(q.pop(0))
    return out


# --- One request ---------------------------------------------------------------------

def same_host(a: str, b: str) -> bool:
    """True if both URLs are on the same host. http to https is fine, and so is "www."
    added or dropped (www.aldoi.gov to aldoi.gov): the same site, so not worth a line
    every month (decision 2026-11-22)."""
    def host(u: str) -> str:
        h = urlsplit(u).netloc.lower()
        return h[4:] if h.startswith("www.") else h
    return host(a) == host(b)


def classify(url: str, http_status: int | None, final_url: str, error: str = "") -> tuple[str, str]:
    """Status and note for one link. Pure: no network."""
    if error:
        return "failed", error
    if http_status in (403, 429):
        return "blocked", f"HTTP {http_status}"
    if http_status != 200:
        return "http_error", f"HTTP {http_status}"
    if final_url and not same_host(url, final_url):
        return "moved_host", f"redirects to {final_url}"
    return OK, ""


def probe(url: str, session, throttle, sleep: Callable[[float], None] = time.sleep) -> tuple[int | None, str, str]:
    """GET with the body not read. Retries timeouts, connection errors and 5xx like the check.
    Returns (http_status, final_url, error)."""
    status, final, error = None, "", ""
    for attempt in range(len(fetch.RETRY_WAITS) + 1):
        if attempt:
            sleep(fetch.RETRY_WAITS[attempt - 1])
        throttle.wait(url)
        try:
            with session.get(url, timeout=fetch.TIMEOUT_SECONDS, allow_redirects=True, stream=True) as r:
                status, final, error = r.status_code, r.url, ""
        except (requests.Timeout, requests.ConnectionError) as err:
            status, final, error = None, "", type(err).__name__
            continue
        except requests.RequestException as err:
            return None, "", type(err).__name__
        if status < 500:
            break
    return status, final, error


def check_one(url: str, used_by: list[str], session, throttle, robots,
              sleep: Callable[[float], None] = time.sleep) -> LinkResult:
    verdict, reason = robots.check(url)
    if verdict != "allowed":
        return LinkResult(url, used_by, "robots", note=f"not requested: {reason}")
    http_status, final, error = probe(url, session, throttle, sleep)
    status, note = classify(url, http_status, final, error)
    return LinkResult(url, used_by, status, http_status, final, note)


# --- The run -------------------------------------------------------------------------

def run(sources, records: list[dict], today: dt.date, session=None, throttle=None, robots=None,
        sleep: Callable[[float], None] = time.sleep, echo=print) -> list[LinkResult]:
    """Check every link once. Prints one line per problem as it goes."""
    if session is None:
        session, throttle = fetch.new_session(), fetch.Throttle()
        robots = fetch.RobotsCache(session, throttle)
    wanted = collect(sources, records, today)
    results = []
    for url in interleave_hosts(list(wanted)):
        res = check_one(url, wanted[url], session, throttle, robots, sleep)
        if res.status != OK:
            echo(f"  link {res.status}: {url} ({res.note}) used by {', '.join(res.used_by)}")
        results.append(res)
    return results


def summary_lines(results: list[LinkResult]) -> list[str]:
    """Lines for the run summary: a count, then one line per problem."""
    bad = [r for r in results if r.status != OK]
    lines = [f"{len(results)} links checked; {len(bad)} problem{'s' if len(bad) != 1 else ''}."]
    for r in sorted(bad, key=lambda r: (r.used_by[0] if r.used_by else "", r.url)):
        lines.append(f"{', '.join(r.used_by)}: {r.status} ({r.note})\n  {r.url}")
    if any(r.used_by and not _is_source_id(r.used_by[0]) for r in bad):
        lines.append("A broken record link is not changed automatically: update it with review amend.")
    return lines


def _is_source_id(name: str) -> bool:
    """Record ids are STATE-PRODUCT-DATE-N (e.g. WI-CL-2027-01-01-1); source ids are not."""
    parts = name.split("-")
    return not (len(parts) >= 5 and parts[1] in ("CL", "CD", "IUI") and parts[2].isdigit())


# --- When to run ---------------------------------------------------------------------

def due(runs_dir: Path, today: dt.date) -> bool:
    """True if no saved run log from this month has link check results (plan 9.6: the
    first run of each month). The schedule runs on the 3rd and 18th, so this is normally
    the run of the 3rd; if that run failed, the run of the 18th does it."""
    prefix = f"run-{today:%Y%m}"
    for path in sorted(Path(runs_dir).glob(f"{prefix}*.json")):
        try:
            if json.loads(path.read_text(encoding="utf-8")).get("link_check"):
                return False
        except (OSError, ValueError):
            continue
    return True
