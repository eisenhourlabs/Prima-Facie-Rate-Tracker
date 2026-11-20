"""The check run: fetch each source, compare with its last snapshot, report (plan 2.4).

Stage 1 supports --dry-run only: nothing is written to data/ or archive/, and
nothing is sent. Snapshots are read from data/snapshots/ if they exist; a
source with no snapshot is a baseline and produces no findings.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from pfrt import detect, documents, fetch, normalize
from pfrt.config import Source

NEEDS_BROWSER_CHARS = 500   # an HTML page with less visible text than this probably needs JavaScript
OK_STATUSES = {"ok", "baseline", "unchanged", "changed"}


@dataclass
class SourceResult:
    source: Source
    status: str                       # fetch status, or baseline/unchanged/changed when ok
    http_status: int | None = None
    byte_count: int = 0
    link_count: int = 0
    content_sha256: str = ""
    elapsed_ms: int = 0
    error: str = ""
    final_url: str = ""
    findings: list[detect.Finding] = field(default_factory=list)


def load_snapshot(source_id: str, root: Path) -> dict | None:
    path = root / "data" / "snapshots" / f"{source_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def read_fixture(source: Source, fixture_dir: Path) -> fetch.FetchResult:
    """--offline: read tests/fixtures/{source_id}.* instead of the network."""
    matches = sorted(fixture_dir.glob(f"{source.source_id}.*"))
    if not matches:
        return fetch.FetchResult(status="failed", error="no fixture file")
    content = matches[0].read_bytes()
    text = documents.content_text(content, url=matches[0].name)
    status, err = fetch.classify(200, "", text, source.must_contain, len(content), None)
    return fetch.FetchResult(status=status, http_status=200, final_url=source.url,
                             content=content, byte_count=len(content), error=err, text=text)


def fingerprint(source: Source, fr: fetch.FetchResult) -> tuple[str, dict[str, str]]:
    """Content hash and link set as in plan 3.1. HTML: hash of the normalized
    (selected) text. Documents: hash of the raw bytes, no links."""
    if documents.guess_ext(fr.content, fr.content_type, source.url) != "html":
        return normalize.sha256_hex(fr.content), {}
    base = fr.final_url or source.url
    text = normalize.html_to_text(fr.content, source.selector)
    links = normalize.extract_links(fr.content, base, source.selector)
    return normalize.sha256_hex(text), links


def check_source(source: Source, fr: fetch.FetchResult, snapshot: dict | None,
                 keywords: dict[str, list[str]]) -> SourceResult:
    """Turn a classified fetch into a result with findings."""
    res = SourceResult(source, fr.status, fr.http_status, fr.byte_count,
                       error=fr.error, final_url=fr.final_url)
    if fr.status != "ok":
        return res
    is_html = documents.guess_ext(fr.content, fr.content_type, source.url) == "html"
    if is_html and len(fr.text) < NEEDS_BROWSER_CHARS:
        res.status, res.error = "needs_browser", f"only {len(fr.text)} characters of visible text"
        return res
    try:
        res.content_sha256, links = fingerprint(source, fr)
    except normalize.SelectorNotFound as err:
        res.status, res.error = "suspect", f"selector '{err}' matched nothing; layout may have changed"
        return res
    res.link_count = len(links)
    res.findings = detect.compare(source.watch_mode, snapshot, res.content_sha256, links, keywords)
    if snapshot is None:
        res.status = "baseline"
    elif any(f.rule == "suspect_redesign" for f in res.findings):
        res.status = "suspect_redesign"
    else:
        res.status = "changed" if res.content_sha256 != snapshot.get("content_sha256") else "unchanged"
    return res


def run(sources: list[Source], keywords: dict[str, list[str]], root: Path,
        offline: bool = False, fixture_dir: Path | None = None,
        echo=print) -> list[SourceResult]:
    """Check each source in state order and print one line per source as it goes."""
    session, throttle = fetch.new_session(), fetch.Throttle()
    robots = fetch.RobotsCache(session, throttle)
    results = []
    for source in sorted(sources, key=lambda s: (s.state, s.source_id)):
        snapshot = load_snapshot(source.source_id, root)
        start = time.monotonic()
        if offline:
            fr = read_fixture(source, fixture_dir or root / "tests" / "fixtures")
        else:
            fr = fetch.get(source, session, (snapshot or {}).get("byte_count"), robots, throttle)
        res = check_source(source, fr, snapshot, keywords)
        res.elapsed_ms = int((time.monotonic() - start) * 1000)
        echo(format_line(res))
        for f in res.findings:
            echo("      " + format_finding(f))
        results.append(res)
    return results


def format_line(r: SourceResult) -> str:
    http = f"HTTP {r.http_status}" if r.http_status else "no response"
    sha = r.content_sha256[:8] or "-"
    extra = f"  ({r.error})" if r.error else ""
    return (f"{r.source.state}  {r.source.source_id:<22} {r.status:<15} {http:<11} "
            f"{r.byte_count:>8} bytes {r.link_count:>4} links  sha {sha}  "
            f"{r.elapsed_ms / 1000:.1f}s{extra}")


def format_finding(f: detect.Finding) -> str:
    if f.rule in ("R3_changed_no_match", "suspect_redesign"):
        return f"{f.rule}: new link titles {list(f.new_anchors)[:5]}"
    kw = f" [{', '.join(f.matched_keywords)}]" if f.matched_keywords else ""
    return f"{f.rule}: {f.anchor_text or '(no text)'} -> {f.url}{kw}"


def not_fully_checked(results: list[SourceResult]) -> dict[str, list[SourceResult]]:
    """States where an enabled leading source was not ok (plan 3.4)."""
    out: dict[str, list[SourceResult]] = {}
    for r in results:
        if r.source.role == "leading" and r.source.is_enabled and r.status not in OK_STATUSES:
            out.setdefault(r.source.state, []).append(r)
    return out
