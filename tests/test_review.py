"""Review tests: every allowed transition, every forbidden one, and Stage 2 acceptance 2-5.

Each test works in a temporary copy of config/ so the real data/ is never touched.
"""

import datetime as dt
import json
import shutil

import pytest
from bs4 import BeautifulSoup

from pfrt import candidates, fetch, records, review
from pfrt.__main__ import main
from tests.conftest import FIXTURES, REPO

TODAY = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")

VALUES = {"records": [{
    "product": "CL", "change_type": "change", "effective_date": "2025-01-01",
    "date_communicated": "2024-12-19", "legal_basis": "760 IAC 1-5.1-9",
    "summary": "TEST VALUES ONLY. Revised credit life rates for the next three years.",
    "rate_items": [{"plan": "Test plan", "basis": "per $100 per year", "old_rate": 0.5, "new_rate": 0.45}],
}]}


@pytest.fixture
def repo(tmp_path):
    """A temporary repository: real config, empty data, and old/new Indiana fixtures."""
    shutil.copytree(REPO / "config", tmp_path / "config")
    full = (FIXTURES / "IN-bulletins.html").read_bytes()
    soup = BeautifulSoup(full, "html.parser")
    soup.find("a", string=lambda t: t and "Bulletin 277" in t).find_parent("li").decompose()
    for name, content in (("old", str(soup).encode("utf-8")), ("new", full)):
        (tmp_path / name / "documents").mkdir(parents=True)
        (tmp_path / name / "IN-bulletins.html").write_bytes(content)
        shutil.copy(FIXTURES / "documents" / "Bulletin-277.pdf", tmp_path / name / "documents")
    return tmp_path


def run_check(repo, which, capsys):
    code = main(["--root", str(repo), "check", "--offline", "--fixtures", str(repo / which), "--states", "IN"])
    assert code == 0
    return capsys.readouterr().out


def tree(root):
    return sorted(p.relative_to(root).as_posix() for p in (root / "data").rglob("*") if p.is_file())


# --- Stage 2 acceptance tests 2 to 5 ---------------------------------------------------

def test_acceptance_end_to_end(repo, capsys, tmp_path):
    # 2. First run: baseline, no candidate. Second run with Bulletin 277 added: one candidate.
    out = run_check(repo, "old", capsys)
    assert "baseline" in out and not candidates.load_all(repo)
    run_check(repo, "new", capsys)
    [cand] = candidates.load_all(repo)
    assert cand["candidate_id"] == f"c-{TODAY}-IN-01"
    assert cand["rule"] == "R1_new_matching_link"
    assert "Bulletin-277.pdf" in cand["document_url"]
    assert cand["anchor_text"] == "Bulletin 277 - Credit Life and Accident and Health Rates"
    assert "credit life" in cand["matched_keywords"]
    assert (repo / cand["archived_copy"]).read_bytes() == (FIXTURES / "documents" / "Bulletin-277.pdf").read_bytes()
    assert "prima facie" in cand["text_excerpt"].lower()
    assert len(list((repo / "data" / "runs").glob("run-*.json"))) >= 1

    # 3. A third identical run creates no new candidate.
    run_check(repo, "new", capsys)
    assert len(candidates.load_all(repo)) == 1

    # 4. Confirm with test values: record written, candidate removed, list empty.
    values = tmp_path / "values.json"
    values.write_text(json.dumps(VALUES), encoding="utf-8")
    assert main(["--root", str(repo), "review", "confirm", cand["candidate_id"], "--values", str(values)]) == 0
    rec = records.load_json(repo / "data/records/IN/IN-CL-2025-01-01-1.json")
    assert rec["status"] == "confirmed" and rec["confirmed_by"] == "owner"
    assert rec["verified"] is True and rec["rate_items"][0]["pct_change"] == -10.0
    assert [h["event"] for h in rec["history"]] == ["candidate_created", "confirmed"]
    capsys.readouterr()
    main(["--root", str(repo), "review", "list"])
    assert capsys.readouterr().out.strip() == "No open candidates."


def test_acceptance_5_confirm_on_rejected_record_errors_and_changes_nothing(repo, capsys, tmp_path):
    run_check(repo, "old", capsys)
    run_check(repo, "new", capsys)
    [cand] = candidates.load_all(repo)
    assert main(["--root", str(repo), "review", "reject", cand["candidate_id"], "--reason", "test reject"]) == 0
    before = {p: (repo / p).read_bytes() for p in tree(repo)}
    values = tmp_path / "values.json"
    values.write_text(json.dumps(VALUES), encoding="utf-8")
    capsys.readouterr()
    code = main(["--root", str(repo), "review", "confirm", cand["candidate_id"], "--values", str(values)])
    assert code == 1 and "rejected record" in capsys.readouterr().err
    assert {p: (repo / p).read_bytes() for p in tree(repo)} == before


def test_rejected_document_is_not_raised_again(repo, capsys):
    run_check(repo, "old", capsys)
    run_check(repo, "new", capsys)
    [cand] = candidates.load_all(repo)
    review.reject(repo, cand["candidate_id"], "test", records.now_utc())
    (repo / "data/snapshots/IN-bulletins.json").unlink()       # forget the page entirely ...
    run_check(repo, "old", capsys)                             # ... re-baseline without 277 ...
    out = run_check(repo, "new", capsys)                       # ... and see 277 appear again
    assert "already known" in out and not candidates.load_all(repo)


# --- Transitions on hand-made data ----------------------------------------------------------

@pytest.fixture
def open_candidate(repo):
    pdf = (FIXTURES / "documents" / "Bulletin-277.pdf").read_bytes()
    doc = fetch.FetchResult(status="fetched", http_status=200, content=pdf, byte_count=len(pdf),
                            content_type="application/pdf")
    return review.add(repo, "IN", "https://www.in.gov/dA/ce9858f869/Bulletin-277.pdf?language_id=1",
                      records.now_utc(), title="Bulletin 277", downloader=lambda u: doc)


def test_add_creates_manual_candidate(repo, open_candidate):
    assert open_candidate["origin"] == "manual" and open_candidate["rule"] == "manual"
    assert (repo / open_candidate["archived_copy"]).exists()
    with pytest.raises(review.ReviewError, match="already"):
        review.add(repo, "IN", open_candidate["document_url"], records.now_utc(),
                   downloader=lambda u: fetch.FetchResult(status="fetched", http_status=200,
                                                          content=(repo / open_candidate["archived_copy"]).read_bytes()))


def test_confirm_refuses_empty_required_field(repo, open_candidate):
    entry = dict(VALUES["records"][0], summary="")
    with pytest.raises(review.ReviewError, match="summary"):
        review.confirm(repo, open_candidate["candidate_id"], [entry], records.now_utc())
    assert candidates.load_all(repo)   # still open


def test_confirm_refuses_unknown_field(repo, open_candidate):
    with pytest.raises(review.ReviewError, match="unknown"):
        review.confirm(repo, open_candidate["candidate_id"], [dict(VALUES["records"][0], status="confirmed")],
                       records.now_utc())


def test_confirm_two_products_and_next_expected(repo, open_candidate):
    cd = dict(VALUES["records"][0], product="CD", rate_items=[], change_type="no_change")
    written, _ = review.confirm(repo, open_candidate["candidate_id"], [VALUES["records"][0], cd],
                                records.now_utc(), next_expected="2027-12-01")
    assert [r["record_id"] for r in written] == ["IN-CL-2025-01-01-1", "IN-CD-2025-01-01-1"]
    assert "IN,Indiana,yes,yes,unknown,notice,3,2027-12-01," in (repo / "config/states.csv").read_text()


def test_amend_and_retract_confirmed_record(repo, open_candidate):
    [rec], _ = review.confirm(repo, open_candidate["candidate_id"], VALUES["records"], records.now_utc())
    amended, _ = review.amend(repo, rec["record_id"], {"summary": "TEST. Corrected summary of the bulletin text."},
                              "typo", records.now_utc())
    assert amended["history"][-1]["event"] == "amended"
    assert amended["history"][-1]["before"]["summary"].startswith("TEST VALUES ONLY")
    retracted = review.retract(repo, rec["record_id"], "confirmed in error", records.now_utc())
    assert retracted["status"] == "rejected" and retracted["history"][-1]["event"] == "retracted"


@pytest.mark.parametrize("action", ["confirm", "reject", "amend", "retract"])
def test_forbidden_transitions_raise(repo, open_candidate, action):
    now = records.now_utc()
    cid = open_candidate["candidate_id"]
    review.reject(repo, cid, "test", now)                 # cid is now a rejected record
    calls = {"confirm": lambda: review.confirm(repo, cid, VALUES["records"], now),
             "reject": lambda: review.reject(repo, cid, "again", now),
             "amend": lambda: review.amend(repo, cid, {"summary": "x" * 30}, "r", now),
             "retract": lambda: review.retract(repo, cid, "r", now)}
    with pytest.raises(review.ReviewError):
        calls[action]()


def test_amend_and_retract_refuse_open_candidate(repo, open_candidate):
    cid = open_candidate["candidate_id"]
    with pytest.raises(review.ReviewError):
        review.amend(repo, cid, {"summary": "x" * 30}, "r", records.now_utc())
    with pytest.raises(review.ReviewError):
        review.retract(repo, cid, "r", records.now_utc())


def test_reasons_are_required(repo, open_candidate):
    with pytest.raises(review.ReviewError, match="reason"):
        review.reject(repo, open_candidate["candidate_id"], "  ", records.now_utc())


def test_interactive_prompts_build_an_entry(repo, open_candidate):
    answers = iter(["CL", "change", "2025-01-01", "2024-12-19", "", "", "", "A twenty character summary here.", "",
                    "y", "Plan A", "per $100 per year", "0.5", "0.45", "n", "n"])
    [entry] = review.prompt_entries(open_candidate, ask=lambda _: next(answers))
    assert entry["product"] == "CL" and entry["rate_items"][0]["new_rate"] == 0.45
    assert entry["legal_basis"] == open_candidate["legal_basis"]   # blank answer keeps the draft
