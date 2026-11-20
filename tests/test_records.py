"""Record tests: pct_change, ids, and every validation check in plan 7.4."""

import datetime as dt

import pytest

from pfrt import records


@pytest.mark.parametrize("old, new, same, expected", [
    (0.50, 0.45, True, -10.0),
    (None, 0.45, True, None),
    (0.50, 0.45, False, None),
    (0.0, 0.45, True, None),
    (1.34, 1.20, True, -10.4),
])
def test_pct_change(old, new, same, expected):
    assert records.pct_change(old, new, same) == expected


def test_make_id():
    assert records.make_id("ZZ", "CL", "2027-01-01", []) == "ZZ-CL-2027-01-01-1"
    assert records.make_id("ZZ", "CL", "2027-01-01", {"ZZ-CL-2027-01-01-1"}) == "ZZ-CL-2027-01-01-2"


def test_fill_pct_changes_respects_old_basis():
    items = records.fill_pct_changes([
        {"basis": "per $100 per year", "old_rate": 0.5, "new_rate": 0.45},
        {"basis": "per $100 per year", "old_basis": "per $1,000 per month", "old_rate": 0.5, "new_rate": 0.45},
    ])
    assert [i["pct_change"] for i in items] == [-10.0, None]


def test_is_official_includes_subdomains():
    assert records.is_official("https://www.in.gov/dA/x.pdf", {"in.gov"})
    assert not records.is_official("https://in.gov.example.com/x", {"in.gov"})


# --- validation -----------------------------------------------------------------

def ctx(existing=None):
    return records.Context(states={"ZZ"}, official_domains={"example.gov"}, existing=existing or [],
                           build_date=dt.date(2026, 11, 20),
                           plausibility=[("", ["per $100", "per year"], 0.10, 2.00)])


def good(**over):
    rec = {"record_id": "ZZ-CL-2027-01-01-1", "state": "ZZ", "product": "CL", "change_type": "change",
           "effective_date": "2027-01-01", "date_communicated": "2026-10-01",
           "source_url": "https://www.example.gov/b.pdf", "verified": True, "status": "confirmed",
           "summary": "Revised prima facie credit life rates for the next three years.",
           "rate_items": [{"plan": "SP decreasing", "basis": "per $100 per year",
                           "old_rate": 0.5, "new_rate": 0.45, "pct_change": -10.0}]}
    rec.update(over)
    return rec


def fields(issues, level):
    return sorted(i.field for i in issues if i.level == level)


def test_good_record_has_no_issues():
    assert records.validate(good(), ctx()) == []


@pytest.mark.parametrize("over, field", [
    ({"state": "QQ"}, "state"),
    ({"product": "XX"}, "product"),
    ({"change_type": "maybe"}, "change_type"),
    ({"effective_date": "2027-02-30"}, "effective_date"),
    ({"effective_date": "1989-12-31"}, "effective_date"),
    ({"effective_date": "2029-11-21"}, "effective_date"),
    ({"date_communicated": "2026-13-01"}, "date_communicated"),
    ({"source_url": ""}, "source_url"),
    ({"source_url": "NONE", "verified": True}, "verified"),
    ({"rate_items": []}, "rate_items"),
    ({"rate_items": [{"plan": "p", "basis": "b", "new_rate": -1}]}, "rate_items[1].new_rate"),
    ({"rate_items": [{"plan": "p", "basis": "", "new_rate": 0.4}]}, "rate_items[1].basis"),
])
def test_each_error(over, field):
    assert field in fields(records.validate(good(**over), ctx()), "error")


@pytest.mark.parametrize("over, field", [
    ({"source_url": "https://other.com/b.pdf"}, "source_url"),
    ({"rate_items": [{"plan": "p", "basis": "per $100 per year", "new_rate": 4.5}]}, "rate_items[1].new_rate"),
    ({"rate_items": [{"plan": "p", "basis": "b", "old_rate": 1, "new_rate": 2, "pct_change": 100.0}]},
     "rate_items[1].pct_change"),
    ({"date_communicated": "2027-02-01"}, "date_communicated"),
    ({"summary": "short"}, "summary"),
])
def test_each_warning(over, field):
    issues = records.validate(good(**over), ctx())
    assert field in fields(issues, "warning") and not fields(issues, "error")


def test_no_change_needs_no_rate_items():
    assert records.validate(good(change_type="no_change", rate_items=[]), ctx()) == []


def test_source_none_with_verified_false_is_allowed():
    assert "source_url" not in fields(records.validate(good(source_url="NONE", verified=False), ctx()), "error")


def test_duplicate_state_product_effective_date_is_error():
    other = good(record_id="ZZ-CL-2027-01-01-9")
    assert "effective_date" in fields(records.validate(good(), ctx([other])), "error")


def test_continuity_check_warns_when_old_rate_differs_from_previous_new_rate():
    prev = good(record_id="ZZ-CL-2024-01-01-1", effective_date="2024-01-01",
                rate_items=[{"plan": "SP decreasing", "basis": "per $100 per year", "new_rate": 0.55}])
    issues = records.validate(good(), ctx([prev]))
    assert "rate_items[1].old_rate" in fields(issues, "warning")


def test_continuity_check_quiet_when_rates_chain():
    prev = good(record_id="ZZ-CL-2024-01-01-1", effective_date="2024-01-01",
                rate_items=[{"plan": "SP decreasing", "basis": "per $100 per year", "new_rate": 0.5}])
    assert records.validate(good(), ctx([prev])) == []


def test_save_json_is_sorted_and_indented(tmp_path):
    p = tmp_path / "a" / "x.json"
    records.save_json(p, {"b": 1, "a": [1]})
    assert p.read_text(encoding="utf-8") == '{\n  "a": [\n    1\n  ],\n  "b": 1\n}\n'
