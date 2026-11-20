"""Check-run tests using saved pages (--offline). No network, no writes."""

from pfrt import check, fetch
from tests.conftest import FIXTURES, REPO

PILOT_FIXTURES = ["IN-bulletins", "WI-bulletins-index", "WI-bulletin-2026", "WI-bulletin-2023",
                  "WI-rate-filing-guide", "VA-code-3730", "IL-reg-1051-50"]


def test_offline_run_over_pilot_fixtures_is_all_baseline(sources, keywords, tmp_path):
    lines = []
    results = check.run([sources[s] for s in PILOT_FIXTURES], keywords, tmp_path,
                        offline=True, fixture_dir=FIXTURES, echo=lines.append)
    assert [r.status for r in results] == ["baseline"] * len(PILOT_FIXTURES), lines
    assert all(not r.findings for r in results)
    assert not (tmp_path / "data").exists()   # dry run wrote nothing


def test_every_pilot_marker_is_present_in_its_fixture(sources, keywords, tmp_path):
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


def test_failed_leading_source_makes_state_not_fully_checked(sources):
    src = sources["IN-bulletins"]
    enabled = src.__class__(**{**src.__dict__, "enabled": "yes"})
    gaps = check.not_fully_checked([check.SourceResult(enabled, "failed")])
    assert list(gaps) == ["IN"]
