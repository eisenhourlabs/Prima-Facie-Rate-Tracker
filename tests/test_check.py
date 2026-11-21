"""Check-run tests using saved pages (--offline). No network."""

import datetime as dt

from pfrt import check, fetch
from tests.conftest import FIXTURES

PILOT_FIXTURES = ["IN-bulletins", "WI-bulletins-index", "WI-bulletin-2026", "WI-bulletin-2023",
                  "WI-rate-filing-guide", "VA-code-3730", "IL-reg-1051-50"]
NOW = dt.datetime(2026, 12, 3, 13, 17, tzinfo=dt.timezone.utc)


def ctx(root, keywords, dry_run=True, lines=None):
    return check.RunContext(root=root, keywords=keywords, now=NOW, dry_run=dry_run, offline=True,
                            fixture_dir=FIXTURES, echo=(lines.append if lines is not None else lambda _: None))


def test_offline_dry_run_over_pilot_fixtures_is_all_baseline(sources, keywords, tmp_path):
    lines = []
    results = check.run([sources[s] for s in PILOT_FIXTURES], ctx(tmp_path, keywords, lines=lines))
    assert [r.status for r in results] == ["baseline"] * len(PILOT_FIXTURES), lines
    assert all(not r.findings for r in results)
    assert not (tmp_path / "data").exists()   # dry run wrote nothing


def test_offline_real_run_writes_snapshots_only_on_baseline(sources, keywords, tmp_path):
    check.run([sources[s] for s in PILOT_FIXTURES], ctx(tmp_path, keywords, dry_run=False))
    snaps = sorted(p.stem for p in (tmp_path / "data" / "snapshots").glob("*.json"))
    assert snaps == sorted(PILOT_FIXTURES)
    assert not (tmp_path / "data" / "candidates").exists()
    assert not (tmp_path / "archive").exists()


def test_every_pilot_marker_is_present_in_its_fixture(sources):
    for sid in PILOT_FIXTURES:
        fr = check.read_fixture(sources[sid], FIXTURES)
        assert fr.status == "ok", (sid, fr.error)


def test_selector_that_no_longer_matches_is_suspect(sources, keywords):
    src = sources["IN-bulletins"]
    page = b"<html><body><p>" + b"Credit Life and Accident and Health Rates " * 20 + b"</p></body></html>"
    fr = fetch.FetchResult(status="ok", http_status=200, content=page, byte_count=len(page),
                           text=page.decode())
    res = check.check_source(src, fr, None, keywords)
    assert res.status == "suspect" and "selector" in res.error


def test_tiny_html_page_needs_browser(sources, keywords):
    src = sources["IN-bulletins"]
    fr = fetch.FetchResult(status="ok", http_status=200, content=b"<div id='app'></div>",
                           byte_count=20, text="Loading")
    assert check.check_source(src, fr, None, keywords).status == "needs_browser"


def test_unchanged_and_changed_against_a_snapshot(sources, keywords):
    src = sources["WI-bulletin-2026"]
    fr = check.read_fixture(src, FIXTURES)
    first = check.check_source(src, fr, None, keywords)
    snap = {"content_sha256": first.content_sha256, "links": {}}
    assert check.check_source(src, fr, snap, keywords).status == "unchanged"
    changed = check.check_source(src, fr, {"content_sha256": "different", "links": {}}, keywords)
    assert changed.status == "changed" and changed.findings[0].rule == "R2_content_changed"


def _page(titles):
    body = "<p>Currently Proposed Regulations. Can't find the regulation you are looking for?</p>" * 12
    items = "".join(f"<li><a href=\"javascript:__doPostBack('x{i}','')\">{t}</a></li>"
                    for i, t in enumerate(titles))
    html = f"<html><body>{body}<ul>{items}</ul></body></html>".encode()
    from pfrt import documents
    return fetch.FetchResult(status="ok", http_status=200, content=html, byte_count=len(html),
                             text=documents.content_text(html, "text/html"))


def test_new_text_source_makes_r5_candidate_with_saved_page(sources, keywords, tmp_path):
    import dataclasses
    src = dataclasses.replace(sources["IN-bulletins"], watch_mode="new_text", selector="", must_contain="")
    first = _page(["LONG-TERM SOLVENCY PLANNING*"])
    base = check.check_source(src, first, None, keywords)
    snap = {"content_sha256": base.content_sha256, "links": base.links, "text": base.text}
    second = _page(["LONG-TERM SOLVENCY PLANNING*", "CREDIT INSURANCE PRIMA FACIE RATES*"])
    res = check.check_source(src, second, snap, keywords)
    assert [f.rule for f in res.findings] == ["R5_new_matching_text"], (res.status, res.error)
    check.act_on_findings(res, second, snap, ctx(tmp_path, keywords, dry_run=False))
    assert len(res.candidates_created) == 1
    assert list((tmp_path / "archive").rglob("*.htm*"))   # the page is the saved copy
    other = _page(["LONG-TERM SOLVENCY PLANNING*", "NET COST OF REINSURANCE*"])
    assert [f.rule for f in check.check_source(src, other, snap, keywords).findings] == ["R3_changed_no_match"]


def test_failure_keeps_old_content_and_counts(sources, keywords, tmp_path):
    src = sources["IN-bulletins"]
    c = ctx(tmp_path, keywords, dry_run=False)
    old = {"source_id": src.source_id, "content_sha256": "abc", "links": {"u": "t"}, "consecutive_failures": 1}
    check.update_snapshot(check.SourceResult(src, "failed"), old, c)
    snap = check.load_snapshot(src.source_id, tmp_path)
    assert snap["content_sha256"] == "abc" and snap["consecutive_failures"] == 2


def test_failed_leading_source_makes_state_not_fully_checked(sources):
    src = sources["IN-bulletins"]
    gaps = check.not_fully_checked([check.SourceResult(src, "failed")])
    assert list(gaps) == ["IN"]   # IN-bulletins is enabled and leading


def test_run_logs_older_than_24_months_are_pruned(tmp_path):
    folder = tmp_path / "runs"
    folder.mkdir()
    for name in ("run-20241119-0900", "run-20241120-0900", "run-20261120-0900"):
        (folder / f"{name}.json").write_text("{}")
    check.prune_run_logs(folder, dt.date(2026, 11, 20))
    assert sorted(p.stem for p in folder.glob("*.json")) == ["run-20241120-0900", "run-20261120-0900"]
