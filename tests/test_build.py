"""Site build tests (plan 9.1: Build; Stage 4 acceptance 1-3)."""

import datetime as dt

from bs4 import BeautifulSoup

from pfrt import build_site, config
from tests.conftest import REPO

TODAY = dt.date(2026, 11, 20)


def rec(state="WI", product="CL", eff="2027-01-01", comm="2026-10-16", **over):
    r = {"record_id": f"{state}-{product}-{eff}-1", "state": state, "product": product, "status": "confirmed",
         "change_type": "change", "effective_date": eff, "date_communicated": comm, "verified": True,
         "source_url": "https://oci.wi.gov/b.pdf", "source_title": "Bulletin", "archived_copy": "",
         "legal_basis": "Rule 1", "summary": "A summary of the change for the test page.",
         "rate_items": [{"plan": "SP decreasing", "basis": "per $100 per year", "old_rate": 0.43,
                         "new_rate": 0.39, "pct_change": -9.3}]}
    r.update(over)
    return r


# --- Boundaries and sorting (acceptance 1) --------------------------------------------------

def test_recent_boundary_365_in_366_out():
    # Effective dates in the past, so only the communicated date decides.
    in_ = rec(eff="2026-01-01", comm=(TODAY - dt.timedelta(days=365)).isoformat())
    out = rec(state="IN", eff="2026-01-01", comm=(TODAY - dt.timedelta(days=366)).isoformat())
    assert build_site.select_recent([in_, out], TODAY) == [in_]


def test_recent_keeps_upcoming_changes_communicated_long_ago():
    """A multi-year schedule (Nebraska IGD-A2) announced in 2025 for 2027 stays in Recent until
    it takes effect; once effective and over a year old it leaves Recent."""
    upcoming = rec(state="NE", eff="2027-01-01", comm="2025-01-14")
    effective_today = rec(state="NE", product="CD", eff=TODAY.isoformat(), comm="2025-01-14")
    past = rec(state="NE", eff="2026-01-01", comm="2025-01-14")
    no_change = rec(state="NE", product="CD", eff="2027-06-01", comm="2025-01-14", change_type="no_change", rate_items=[])
    assert build_site.select_recent([upcoming, effective_today, past, no_change], TODAY) == [upcoming]


def test_history_boundary_exactly_15_years_in_one_day_earlier_out():
    in_ = rec(eff="2011-11-20")
    out = rec(state="IN", eff="2011-11-19")
    assert build_site.select_history([in_, out], TODAY) == {"WI": [in_]}


def test_recent_sorted_by_effective_date_ascending_and_excludes_no_change():
    a, b = rec(eff="2027-06-01"), rec(state="IN", eff="2027-01-01")
    nc = rec(state="VA", change_type="no_change", rate_items=[])
    assert build_site.select_recent([a, b, nc], TODAY) == [b, a]


def test_history_newest_first_and_only_confirmed():
    old, new = rec(eff="2024-01-01"), rec(eff="2027-01-01")
    rejected = rec(eff="2025-01-01", status="rejected")
    assert build_site.select_history([old, rejected, new], TODAY)["WI"] == [new, old]


# --- Formatting -------------------------------------------------------------------------

def test_formatting():
    assert build_site.long_date("2027-01-01") == "1 January 2027"
    assert [build_site.rate(v) for v in (0.6, 0.662, 1.0, None)] == ["0.60", "0.662", "1.00", "-"]
    assert build_site.pct(-9.3) == "-9.3%" and build_site.pct(None) == "-"
    assert build_site.change_text(rec()) == "0.43 to 0.39 per $100 per year (-9.3%)"
    two = rec(rate_items=[{"new_rate": 1, "pct_change": -9.3}, {"new_rate": 2, "pct_change": -10.4}])
    assert build_site.change_text(two) == "2 rates, changes of -10.4% to -9.3%"


def test_stale_status():
    log = {"monitored_state_count": 2, "states_not_fully_checked": []}
    # TODAY is 20 November: 31 October is 20 days before (fine), 30 October is 21 (stale).
    assert build_site.run_status({**log, "finished_at": "2026-10-31T13:00:00Z"}, TODAY)["stale"] is False
    assert build_site.run_status({**log, "finished_at": "2026-10-30T13:00:00Z"}, TODAY)["stale"] is True
    assert build_site.run_status(None, TODAY)["stale"] is True


# --- The page (acceptance 2 and 3) -----------------------------------------------------------

def build_page(tmp_path, records, last=None):
    states = config.load_states(REPO / "config/states.csv")
    path = build_site.render(build_site.select_recent(records, TODAY), build_site.select_history(records, TODAY),
                             states, last, tmp_path / "site", tmp_path, TODAY)
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def test_acceptance_2_four_records_two_states(tmp_path):
    records = [
        rec("WI", "CL", "2027-01-01", "2026-10-16"),
        rec("WI", "CD", "2026-12-01", "2026-09-01"),
        rec("IN", "CL", "2022-01-01", "2021-09-01", verified=False, source_url="NONE"),   # history only
        rec("IN", "CD", "2025-01-01", "2024-09-01", change_type="no_change", rate_items=[]),
    ]
    page = build_page(tmp_path, records, {"finished_at": "2026-11-18T13:20:00Z", "monitored_state_count": 2,
                                          "states_not_fully_checked": [], "not_monitored": ["VA"]})
    rows = page.select("table.recent tbody tr.row")
    assert [r.find("td").get_text(" ", strip=True) for r in rows] == ["1 December 2026 Upcoming", "1 January 2027 Upcoming"]
    names = [d.summary.get_text() for d in page.select("details.state")]
    assert len(names) == 44 and names == sorted(names)
    assert "Wisconsin (2)" in names and "Indiana (2)" in names and "Alabama (0)" in names
    text = page.get_text(" ")
    assert text.count("Unverified") == 1
    assert text.count("Reviewed, no change") == 1
    assert "Last checked: 18 November 2026. 2 of 2 monitored states checked." in " ".join(text.split())


def test_acceptance_3_no_script_one_h1_and_accessible_table(tmp_path):
    page = build_page(tmp_path, [rec()])
    assert page.find("script") is None and len(page.find_all("h1")) == 1
    assert page.html["lang"] == "en"
    assert page.select_one("table.recent caption") is not None
    assert all(th.get("scope") == "col" for th in page.select("table.recent th"))


def test_zero_records_page(tmp_path):
    page = build_page(tmp_path, [])
    text = " ".join(page.get_text(" ").split())
    assert "No changes communicated in the last 12 months." in text
    assert text.count("No changes recorded.") == 44
    assert "no check has run yet" in text


def test_stale_warning_shown_when_last_run_is_old(tmp_path):
    page = build_page(tmp_path, [], {"finished_at": "2026-10-01T13:00:00Z", "monitored_state_count": 2,
                                     "states_not_fully_checked": ["WI"], "not_monitored": []})
    text = " ".join(page.get_text(" ").split())
    assert "Warning:" in text and "more than 20 days old" in text and "Not checked in the last run: WI." in text


def test_saved_copies_are_copied_and_note_links_escaped(tmp_path):
    (tmp_path / "archive/WI").mkdir(parents=True)
    (tmp_path / "archive/WI/2026-11-20_aaaa1111.pdf").write_bytes(b"%PDF a")
    (tmp_path / "archive/WI/2026-11-20_bbbb2222.pdf").write_bytes(b"%PDF b")
    r = rec(archived_copy="archive/WI/2026-11-20_aaaa1111.pdf",
            rate_table_note="Table <b>x</b>: https://oci.wi.gov/t.pdf, saved copy archive/WI/2026-11-20_bbbb2222.pdf.")
    page = build_page(tmp_path, [r])
    assert (tmp_path / "site/archive/WI/2026-11-20_aaaa1111.pdf").exists()
    assert (tmp_path / "site/archive/WI/2026-11-20_bbbb2222.pdf").exists()
    note = [dd for dd in page.find_all("dd") if "Table" in dd.get_text()][0]
    assert note.find("b") is None                                    # HTML in a note is escaped
    assert [a["href"] for a in note.find_all("a")] == ["https://oci.wi.gov/t.pdf", "archive/WI/2026-11-20_bbbb2222.pdf"]


def test_real_records_build(tmp_path):
    """The real records build; Wisconsin shows every confirmed record inside the 15-year window.

    The count is worked out from the data, so the test does not break when records are added.
    Seed records effective before the window (2009) stay in data/ but are hidden (plan A7).
    """
    from pfrt import records
    since = build_site._years_before(TODAY, build_site.HISTORY_YEARS).isoformat()
    wi = [r for r in records.load_all(REPO) if r.get("state") == "WI" and r.get("status") == "confirmed"]
    shown = sum(r["effective_date"] >= since for r in wi)
    assert shown < len(wi) or not wi                 # the 2009 records are hidden
    out = build_site.build(REPO, tmp_path / "site", TODAY)
    page = BeautifulSoup(out.read_text(encoding="utf-8"), "html.parser")
    assert f"Wisconsin ({shown})" in [d.summary.get_text() for d in page.select("details.state")]


def test_each_change_is_its_own_collapsed_line(tmp_path):
    """Inside a state, every record is a closed <details> whose one-line summary gives
    the effective date, the product and the change, so the list fits on one screen."""
    records = [
        rec("WI", "CL", "2027-01-01", "2026-10-16"),
        rec("WI", "CD", "2024-01-01", "2023-09-28", change_type="no_change", rate_items=[]),
    ]
    page = build_page(tmp_path, records)
    wi = next(d for d in page.select("details.state") if d.summary.get_text().startswith("Wisconsin"))
    lines = wi.select("details.rec")
    assert len(lines) == 2 and not any(d.has_attr("open") for d in lines)
    first, second = (" ".join(d.summary.get_text(" ").split()) for d in lines)
    assert first.startswith("1 January 2027 · Credit life · ")
    assert second == "1 January 2024 · Credit disability · Reviewed, no change"
    assert lines[0].select_one(".record table.items") is not None      # the detail sits inside the line


def test_every_link_opens_in_a_new_tab(tmp_path):
    (tmp_path / "archive/WI").mkdir(parents=True)
    (tmp_path / "archive/WI/2026-11-20_aaaa1111.pdf").write_bytes(b"%PDF a")
    r = rec(archived_copy="archive/WI/2026-11-20_aaaa1111.pdf",
            rate_table_note="Table: https://oci.wi.gov/t.pdf, saved copy archive/WI/2026-11-20_aaaa1111.pdf.")
    links = build_page(tmp_path, [r]).find_all("a")
    assert len(links) >= 5
    for a in links:
        assert a.get("target") == "_blank" and a.get("rel") == ["noopener"], a
        assert "(opens in a new tab)" in a.get_text()


def test_rates_in_force_record_always_in_history_never_in_recent(tmp_path):
    """A 'rates in force' record (change_type initial) set before the 15-year window still
    shows in History, labeled 'Rates in force since', and never in Recent."""
    in_force = rec(state="IA", eff="2001-03-30", comm="2000-12-04", change_type="initial")
    future_in_force = rec(state="IA", product="CD", eff="2027-01-01", comm="2026-10-01", change_type="initial")
    assert build_site.select_recent([in_force, future_in_force], TODAY) == []
    assert build_site.select_history([in_force], TODAY) == {"IA": [in_force]}
    page = build_page(tmp_path, [in_force])
    ia = next(d for d in page.select("details.state") if d.summary.get_text().startswith("Iowa"))
    assert ia.summary.get_text() == "Iowa (1)"
    line = " ".join(ia.select_one("details.rec").summary.get_text(" ").split())
    assert line == "Rates in force since 30 March 2001 · Credit life · 1 rate"
