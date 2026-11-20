"""Candidate tests: ids and duplicate detection."""

from types import SimpleNamespace

from pfrt import candidates
from pfrt.detect import Finding
from pfrt.documents import ArchivedFile

SRC = SimpleNamespace(state="IN", source_id="IN-bulletins", products="CL;CD",
                      citation="760 IAC 1-5.1-9", url="https://www.in.gov/idoi/list/")
NOW = "2026-12-03T13:17:42Z"


def test_next_id_plan_example():
    assert candidates.next_id("IN", "20261203", ["c-20261203-IN-01"]) == "c-20261203-IN-02"
    assert candidates.next_id("IN", "20261203", ["c-20261203-WI-01"]) == "c-20261203-IN-01"


def make(url="https://www.in.gov/b277.pdf", sha="aa11", known=None, rule="R1_new_matching_link"):
    finding = Finding(rule, url if rule != "R2_content_changed" else "", "Bulletin 277", ("credit life",))
    archived = ArchivedFile(url, "archive/IN/2026-12-03_aa11.pdf", sha, 100, "application/pdf")
    return candidates.create(finding, SRC, archived, "run-20261203-1317", "text", known or [], NOW)


def test_create_fills_detection_fields():
    c = make()
    assert c["candidate_id"] == "c-20261203-IN-01"
    assert c["status"] == "candidate" and c["origin"] == "monitor" and c["priority"] == "high"
    assert c["document_url"] == "https://www.in.gov/b277.pdf"
    assert c["legal_basis"] == "760 IAC 1-5.1-9" and c["ai"] is None
    assert c["history"][0]["event"] == "candidate_created"


def test_same_url_is_not_raised_twice():
    assert make(known=[{"document_url": "https://www.in.gov/b277.pdf"}]) is None


def test_same_file_at_new_url_is_not_raised_twice():
    assert make(url="https://www.in.gov/moved.pdf", known=[{"archived_sha256": "aa11"}]) is None


def test_any_change_page_can_change_again():
    # R2 sources keep their URL; a second change (new hash) must still be raised.
    first = make(rule="R2_content_changed", sha="v1")
    second = make(rule="R2_content_changed", sha="v2", known=[first])
    assert second is not None and second["candidate_id"] == "c-20261203-IN-02"
