"""The check run: fetch each source, compare with its last snapshot, act (plan 2.4).

With dry_run=True nothing is written and nothing is downloaded beyond the
source pages; findings are only printed. Otherwise the run:
  - downloads each new matching document, saves it to archive/ and creates a candidate,
  - saves a new snapshot for each source that was checked,
  - writes a run log to data/runs/.
A source's first good check is a baseline: it stores a snapshot and creates nothing.
"""

from __future__ import annotations

import datetime as dt
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlsplit

from pfrt import candidates, detect, documents, fetch, normalize, records
from pfrt.config import Source

NEEDS_BROWSER_CHARS = 500   # an HTML page with less visible text than this probably needs JavaScript
OK_STATUSES = {"ok", "baseline", "unchanged", "changed"}
RUN_LOG_MONTHS = 24


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
    links: dict[str, str] = field(default_factory=dict)
    text: str = ""
    candidates_created: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    consecutive_failures: int = 0


@dataclass
class RunContext:
    """Everything one run shares: where to write, how to fetch, and the clock."""
    root: Path
    keywords: dict[str, list[str]]
    now: dt.datetime
    dry_run: bool = True
    offline: bool = False
    fixture_dir: Path | None = None
    session: object = None
    throttle: fetch.Throttle | None = None
    robots: fetch.RobotsCache | None = None
    echo: object = print

    @property
    def stamp(self) -> str:
        return self.now.strftime("%Y-%m-%dT%H:%M:%SZ")

    @property
    def run_id(self) -> str:
        return f"run-{self.now:%Y%m%d-%H%M}"

    @property
    def fixtures(self) -> Path:
        return self.fixture_dir or self.root / "tests" / "fixtures"


# --- Snapshots and fixtures --------------------------------------------------------

def snapshot_path(root: Path, source_id: str) -> Path:
    return Path(root) / "data" / "snapshots" / f"{source_id}.json"


def load_snapshot(source_id: str, root: Path) -> dict | None:
    path = snapshot_path(root, source_id)
    return records.load_json(path) if path.exists() else None


def read_fixture(source: Source, fixture_dir: Path) -> fetch.FetchResult:
    """--offline: read {fixture_dir}/{source_id}.* instead of the network."""
    matches = sorted(p for p in fixture_dir.glob(f"{source.source_id}.*") if p.is_file())
    if not matches:
        return fetch.FetchResult(status="failed", error="no fixture file")
    content = matches[0].read_bytes()
    text = documents.content_text(content, url=matches[0].name)
    status, err = fetch.classify(200, "", text, source.must_contain, len(content), None)
    return fetch.FetchResult(status=status, http_status=200, final_url=source.url,
                             content=content, byte_count=len(content), error=err, text=text)


def read_document_fixture(url: str, fixture_dir: Path) -> fetch.FetchResult:
    """--offline: a linked document is read from {fixture_dir}/documents/{file name in the URL}."""
    path = fixture_dir / "documents" / unquote(Path(urlsplit(url).path).name)
    if not path.is_file():
        return fetch.FetchResult(status="failed", error=f"no document fixture {path.name}")
    content = path.read_bytes()
    return fetch.FetchResult(status="fetched", http_status=200, final_url=url,
                             content=content, byte_count=len(content))


# --- One source -------------------------------------------------------------------

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
    """Turn a classified fetch into a result with findings. Writes nothing."""
    res = SourceResult(source, fr.status, fr.http_status, fr.byte_count,
                       error=fr.error, final_url=fr.final_url, text=fr.text)
    if fr.status != "ok":
        return res
    is_html = documents.guess_ext(fr.content, fr.content_type, source.url) == "html"
    if is_html and len(fr.text) < NEEDS_BROWSER_CHARS:
        res.status, res.error = "needs_browser", f"only {len(fr.text)} characters of visible text"
        return res
    try:
        res.content_sha256, res.links = fingerprint(source, fr)
    except normalize.SelectorNotFound as err:
        res.status, res.error = "suspect", f"selector '{err}' matched nothing; layout may have changed"
        return res
    res.link_count = len(res.links)
    res.findings = detect.compare(source.watch_mode, snapshot, res.content_sha256, res.links, keywords)
    if not snapshot or "content_sha256" not in snapshot:
        res.status = "baseline"
    elif any(f.rule == "suspect_redesign" for f in res.findings):
        res.status = "suspect_redesign"
    else:
        res.status = "changed" if res.content_sha256 != snapshot.get("content_sha256") else "unchanged"
    return res


def act_on_findings(res: SourceResult, fr: fetch.FetchResult, snapshot: dict | None,
                    ctx: RunContext) -> None:
    """Create candidates for R1, R2 and R4 findings (not in a dry run)."""
    if ctx.dry_run or res.status == "suspect_redesign":
        return
    known = candidates.load_all(ctx.root) + records.load_all(ctx.root)
    for f in res.findings:
        if f.rule == "R2_content_changed":
            diff = detect.text_diff((snapshot or {}).get("text", ""), res.text)
            archived = documents.archive(fr.content, res.source.url, res.source.state,
                                         ctx.now.date(), fr.content_type, ctx.root)
            _save_candidate(res, f, archived, res.text, known, ctx, text_diff=diff)
        elif f.rule in ("R1_new_matching_link", "R4_new_bare_pdf_link"):
            _act_on_new_link(res, f, known, ctx)
        elif f.rule == "R3_changed_no_match":
            res.notes.append("changed_no_match")


def _act_on_new_link(res: SourceResult, f: detect.Finding, known: list[dict], ctx: RunContext) -> None:
    """R1/R4: download the linked document, test its text, and make a candidate if it fits."""
    if candidates.already_known(f.url, "", known):
        res.notes.append(f"already known: {f.url}")
        return
    doc = (read_document_fixture(f.url, ctx.fixtures) if ctx.offline
           else fetch.download(f.url, ctx.session, ctx.throttle))
    if doc.http_status != 200:
        res.notes.append(f"document download failed ({doc.error or doc.http_status}): {f.url}")
        # The new link is still reported: a candidate with no saved copy is better than a miss.
        archived = documents.ArchivedFile(f.url, "", "", 0, "")
        _save_candidate(res, f, archived, "", known, ctx, unreadable=True)
        return
    text = documents.content_text(doc.content, doc.content_type, f.url)
    verdict, _ = detect.text_test(text, doc.byte_count, ctx.keywords)
    if verdict == "no_match":
        res.notes.append(f"new_link_no_match: {f.anchor_text}")
        return
    archived = documents.archive(doc.content, f.url, res.source.state, ctx.now.date(),
                                 doc.content_type, ctx.root)
    _save_candidate(res, f, archived, text, known, ctx, unreadable=(verdict == "unreadable"))


def _save_candidate(res, f, archived, text, known, ctx, **kw) -> None:
    cand = candidates.create(f, res.source, archived, ctx.run_id, text, known, ctx.stamp, **kw)
    if cand is None:
        res.notes.append(f"duplicate of an existing candidate or record: {f.url or res.source.url}")
        return
    candidates.save(ctx.root, cand)
    known.append(cand)
    res.candidates_created.append(cand["candidate_id"])


def update_snapshot(res: SourceResult, snapshot: dict | None, ctx: RunContext) -> None:
    """Save the new state of a source. A failed or suspect check keeps the old content."""
    failures = (snapshot or {}).get("consecutive_failures", 0)
    res.consecutive_failures = 0 if res.status in OK_STATUSES else failures + 1
    if ctx.dry_run:
        return
    snap = dict(snapshot or {"source_id": res.source.source_id})
    snap["last_checked"] = ctx.stamp
    snap["last_status"] = res.status
    if res.status in OK_STATUSES:
        snap.update(last_ok=ctx.stamp, consecutive_failures=0, content_sha256=res.content_sha256,
                    byte_count=res.byte_count, links=res.links, text=res.text)
    else:
        snap["consecutive_failures"] = snap.get("consecutive_failures", 0) + 1
    records.save_json(snapshot_path(ctx.root, res.source.source_id), snap)


# --- The run --------------------------------------------------------------------------

def run(sources: list[Source], ctx: RunContext) -> list[SourceResult]:
    """Check each source in state order and print one line per source as it goes."""
    if not ctx.offline and ctx.session is None:
        ctx.session, ctx.throttle = fetch.new_session(), fetch.Throttle()
        ctx.robots = fetch.RobotsCache(ctx.session, ctx.throttle)
    results = []
    for source in sorted(sources, key=lambda s: (s.state, s.source_id)):
        snapshot = load_snapshot(source.source_id, ctx.root)
        start = time.monotonic()
        if ctx.offline:
            fr = read_fixture(source, ctx.fixtures)
        else:
            fr = fetch.get(source, ctx.session, (snapshot or {}).get("byte_count"), ctx.robots, ctx.throttle)
        res = check_source(source, fr, snapshot, ctx.keywords)
        act_on_findings(res, fr, snapshot, ctx)
        update_snapshot(res, snapshot, ctx)
        res.elapsed_ms = int((time.monotonic() - start) * 1000)
        ctx.echo(format_line(res))
        for f in res.findings:
            ctx.echo("      " + format_finding(f))
        for note in res.notes:
            ctx.echo("      note: " + note)
        if res.candidates_created:
            ctx.echo("      candidates created: " + ", ".join(res.candidates_created))
        results.append(res)
    return results


def build_run_log(results: list[SourceResult], all_sources: list[Source], states_in_scope: set[str],
                  ctx: RunContext, started: str) -> dict:
    """The run log (plan 2.2): one entry per source, totals and the unchecked states."""
    gaps = not_fully_checked(results)
    unmonitored = not_monitored(all_sources, states_in_scope)
    return {
        "run_id": ctx.run_id, "started_at": started, "finished_at": records.now_utc(),
        "offline": ctx.offline, "dry_run": ctx.dry_run,
        "sources": [_log_entry(r) for r in results],
        "totals": {"sources": len(results), "candidates": sum(len(r.candidates_created) for r in results),
                   "not_ok": sum(r.status not in OK_STATUSES for r in results)},
        "states_in_scope": sorted(states_in_scope),
        "monitored_state_count": len(states_in_scope) - len(unmonitored),
        "states_not_fully_checked": sorted(gaps),
        "not_monitored": unmonitored,
    }


def _log_entry(r: SourceResult) -> dict:
    anchors = [a for f in r.findings if f.rule == "R3_changed_no_match" for a in f.new_anchors]
    return {"source_id": r.source.source_id, "state": r.source.state, "role": r.source.role,
            "enabled": r.source.is_enabled, "status": r.status, "http_status": r.http_status,
            "elapsed_ms": r.elapsed_ms, "rule_fired": sorted({f.rule for f in r.findings}),
            "candidates_created": r.candidates_created, "error": r.error, "notes": r.notes,
            "consecutive_failures": r.consecutive_failures, "new_anchors": anchors}


def write_run_log(log: dict, summary_text: str, ctx: RunContext) -> Path | None:
    """Save data/runs/{run_id}.json and the readable summary {run_id}.txt; prune old logs."""
    if ctx.dry_run:
        return None
    folder = Path(ctx.root) / "data" / "runs"
    path = folder / f"{ctx.run_id}.json"
    records.save_json(path, log)
    (folder / f"{ctx.run_id}.txt").write_text(summary_text, encoding="utf-8", newline="\n")
    prune_run_logs(folder, ctx.now.date())
    return path


def prune_run_logs(folder: Path, today: dt.date) -> None:
    """Delete run logs older than 24 months, judged by the date in the file name."""
    cutoff = f"run-{today.year - RUN_LOG_MONTHS // 12:04d}{today:%m%d}"
    for p in list(folder.glob("run-*.json")) + list(folder.glob("run-*.txt")):
        if p.stem[:12] < cutoff:
            p.unlink()


# --- Reporting -------------------------------------------------------------------------

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


def not_monitored(all_sources: list[Source], states_in_scope: set[str]) -> list[str]:
    """States with no enabled leading source (plan 3.4)."""
    monitored = {s.state for s in all_sources if s.is_enabled and s.role == "leading"}
    return sorted(states_in_scope - monitored)
