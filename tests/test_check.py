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
