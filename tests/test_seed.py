"""Seed import tests: parse, merge, validate, scan, import and batch confirm (Stage 5).

Each test works in a temporary repository: a copy of config/ and of the confirmed
Wisconsin records, so the real data/ is never touched. Scan tests use a made-up
blocklist term, never the real internal/blocklist.txt.
"""

import shutil
import zlib

import pytest
from pypdf import PdfWriter

from pfrt import candidates, records, review, seed
from pfrt.__main__ import main
from tests.conftest import FIXTURES, REPO

FAKE_TERM = "Zebracorp Holdings"      # stands in for a blocklisted name
NOW = "2026-11-20T12:00:00Z"
HEADER = ",".join(seed.COLUMNS)


@pytest.fixture
def repo(tmp_path):
    shutil.copytree(REPO / "config", tmp_path / "config")
    shutil.copytree(REPO / "data" / "records" / "WI", tmp_path / "data" / "records" / "WI")
    (tmp_path / "internal").mkdir()
    (tmp_path / "internal" / "blocklist.txt").write_text(f"# test terms\n{FAKE_TERM}\n\n", encoding="utf-8")
    (tmp_path / "seed" / "documents").mkdir(parents=True)
    return tmp_path


def text_pdf(text: str, title: str = "Public bulletin") -> bytes:
    """A one-page PDF whose page text is in a compressed stream, so the raw bytes do not show it."""
    stream = zlib.compress(f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1"))
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
            b"/Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(stream) + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            f"<< /Title ({title}) >>".encode("latin-1")]
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for n, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % n + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R /Info 6 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return bytes(out)


def write_batch(repo, name, rows):
    path = repo / "seed" / f"{name}.csv"
    path.write_text(HEADER + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return path


def row(state="IN", product="CL", eff="2019-01-01", plan="Test plan", basis="per $100 per year",
        old="", new="0.45", doc="", summary="TEST VALUES ONLY. A test record for the seed tests.",
        url="https://www.in.gov/idoi/files/test.pdf", change="change", comm="2018-10-01"):
    values = dict(state=state, product=product, change_type=change, effective_date=eff, date_communicated=comm,
                  source_url=url, source_title="Test", plan=plan, basis=basis, old_rate=old, new_rate=new,
                  rate_table_note="", summary=summary, legal_basis="Test cite", public_document_file=doc, notes="")
    return ",".join(f'"{values[c]}"' for c in seed.COLUMNS)


# --- parse and merge --------------------------------------------------------------------

def test_parse_rows_numbers_and_types():
    rows = seed.parse(FIXTURES / "seed_good.csv")
    assert [r.row for r in rows] == [2, 3, 4, 5, 6]
    assert rows[0].values["state"] == "IN" and rows[0].values["new_rate"] == "0.45"


def test_parse_refuses_missing_column(tmp_path):
    p = tmp_path / "b.csv"
    p.write_text("state,product\nIN,CL\n", encoding="utf-8")
    with pytest.raises(seed.SeedError, match="missing column"):
        seed.parse(p)


def test_acceptance_4_three_rows_merge_into_one_record():
    drafts = seed.merge(seed.parse(FIXTURES / "seed_good.csv"))
    cl = [d for d in drafts if (d.record["product"], d.record["effective_date"]) == ("CL", "2019-01-01")]
    assert len(cl) == 1 and cl[0].rows == [2, 3, 4]
    assert [i["new_rate"] for i in cl[0].record["rate_items"]] == [0.45, 0.75, 0.60]
    assert cl[0].record["summary"].startswith("TEST VALUES ONLY")       # given on the first row only


def test_merge_flags_rows_that_disagree():
    rows = seed.parse(FIXTURES / "seed_good.csv")
    rows[1].values["summary"] = "TEST VALUES ONLY. A different summary on the second row."
    [draft] = [d for d in seed.merge(rows) if d.rows == [2, 3, 4]]
    assert any(i.field == "summary" and i.level == "error" for _, i in draft.issues)


# --- validate (acceptance 2 and 3) -----------------------------------------------------------

def test_acceptance_2_good_file_has_no_errors(repo, capsys):
    assert main(["--root", str(repo), "seed", "validate", str(FIXTURES / "seed_good.csv")]) == 0
    assert "0 error(s)" in capsys.readouterr().out


EXPECTED_ERRORS = {
    2: "state", 3: "product", 4: "effective_date", 5: "effective_date", 6: "source_url",
    7: "rate_items[1].new_rate", 8: "rate_items[1].basis", 9: "effective_date",
    10: "date_communicated", 11: "change_type", 12: "rate_items[1].new_rate", 13: "plan",
    14: "summary", 15: "legal_basis", 16: "public_document_file",
}


def test_acceptance_3_bad_file_reports_each_error_on_its_row(repo, capsys):
    assert main(["--root", str(repo), "seed", "validate", str(FIXTURES / "seed_bad.csv")]) == 1
    out = capsys.readouterr().out
    _, issues = seed.validate(FIXTURES / "seed_bad.csv", repo)
    errors = [i for i in issues if i.issue.level == "error"]
    found = {}
    for e in errors:
        found.setdefault(int(e.rows.split()[1]), []).append(e.issue.field)
    assert set(found) == set(EXPECTED_ERRORS)
    for n, fld in EXPECTED_ERRORS.items():
        assert fld in found[n], (n, found[n])
        assert f"row {n}: ERROR: {fld}" in out
    # The specific 7.4 messages.
    text = "\n".join(map(str, errors))
    for phrase in ("not in states.csv", "must be one of CL, CD, IUI", "not a real YYYY-MM-DD date",
                   "outside 1990-01-01", "missing; write NONE", "must be a number greater than 0",
                   "required when a rate is given", "already exists for this state, product and effective date"):
        assert phrase in text, phrase


def test_validate_warns_outside_plausible_range_including_iui(repo):
    path = write_batch(repo, "b", [row(new="4.50"), row(product="IUI", basis="per $100 of monthly benefit", new="12.00")])
    _, issues = seed.validate(path, repo)
    ranges = [i for i in issues if "plausible range" in i.issue.message]
    assert len(ranges) == 2 and "0.5 to 10.0 for IUI" in str(ranges[1])


def test_validate_continuity_within_batch(repo):
    path = write_batch(repo, "b", [row(eff="2016-01-01", new="0.50"), row(eff="2019-01-01", old="0.55", new="0.45")])
    _, issues = seed.validate(path, repo)
    assert any("differs from 0.5" in i.issue.message and i.rows == "row 3" for i in issues)


def test_validate_warns_when_no_saved_copy_or_no_source(repo):
    path = write_batch(repo, "b", [row(), row(eff="2016-01-01", url="NONE")])
    _, issues = seed.validate(path, repo)
    fields = {(i.rows, i.issue.field) for i in issues if i.issue.level == "warning"}
    assert ("row 2", "public_document_file") in fields and ("row 3", "source_url") in fields
    assert not [i for i in issues if i.issue.level == "error"]


# --- scan (acceptance 5) ------------------------------------------------------------------

def test_acceptance_5_scan_fails_and_names_file_but_never_the_term(repo, capsys):
    folder = repo / "seed"
    (folder / "documents" / "clean.pdf").write_bytes(text_pdf("Revised prima facie credit life rates"))
    (folder / "documents" / "bulletin.pdf").write_bytes(text_pdf(f"Prepared by {FAKE_TERM.upper()}"))
    code = main(["--root", str(repo), "seed", "scan", str(folder)])
    out = capsys.readouterr().out
    assert code == 1
    assert "documents/bulletin.pdf: PDF text" in out and "clean.pdf" not in out
    assert FAKE_TERM.lower() not in out.lower() and "zebracorp" not in out.lower()


def test_scan_reads_extracted_text_not_raw_bytes(repo):
    pdf = text_pdf(f"note {FAKE_TERM}")
    assert FAKE_TERM.encode() not in pdf                       # only extraction can find it
    (repo / "seed" / "a.pdf").write_bytes(pdf)
    hits = seed.scan(repo / "seed", repo / "internal/blocklist.txt")
    assert [h.where for h in hits] == ["PDF text"]


def test_scan_finds_metadata_csv_text_and_file_names(repo):
    w = PdfWriter()
    w.add_blank_page(612, 792)
    w.add_metadata({"/Author": "zebracorp   holdings"})       # case and spacing differ
    with open(repo / "seed" / "documents" / "meta.pdf", "wb") as f:
        w.write(f)
    write_batch(repo, "batch_01", [row(summary=f"TEST VALUES ONLY. Copied from {FAKE_TERM}.")])
    (repo / "seed" / "documents" / "zebracorp_holdings_notes.txt").write_text("plain", encoding="utf-8")
    hits = {(h.path, h.where) for h in seed.scan(repo / "seed", repo / "internal/blocklist.txt")}
    assert hits == {("documents/meta.pdf", "PDF metadata"), ("batch_01.csv", "text"),
                    ("documents/zebracorp_holdings_notes.txt", "file name")}


def test_scan_fails_on_files_it_cannot_search(repo):
    (repo / "seed" / "sheet.xlsx").write_bytes(b"PK\x03\x04\x00\xff\xfe binary")
    [hit] = seed.scan(repo / "seed", repo / "internal/blocklist.txt")
    assert hit.path == "sheet.xlsx" and "cannot be searched" in hit.where


def fake_doc(body: str, author: str = "Rules Clerk") -> bytes:
    """Bytes shaped like a Word 97 file: the OLE signature, binary padding, 8-bit body text
    and a UTF-16 property string (as Florida's rule files store them)."""
    return (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + bytes(range(32)) * 32 + body.encode("cp1252")
            + b"\x00\x01\x02" * 50 + author.encode("utf-16-le") + b"\x00\xff" * 40)


DOC_BODY = ("69O-163.011 Credit Disability Insurance Rates.\r(a) If premiums are payable on a "
            "single-premium basis:\rTABLE I\r7-12\x07 0.90\x07 0.58\x07 1.41\x07 1.26\x07 1.09\x07\x07\r"
            "49-60\x07 2.53\x07 2.38\x07 2.95\x07 2.70\x07 2.62\x07\x07\r" + "Rulemaking Authority 624.308(1). " * 4)


def test_scan_passes_a_readable_word_file(repo):
    (repo / "seed" / "documents" / "rule.doc").write_bytes(fake_doc(DOC_BODY))
    assert seed.scan(repo / "seed", repo / "internal/blocklist.txt") == []


def test_scan_finds_a_term_in_word_properties_without_naming_it(repo):
    (repo / "seed" / "documents" / "rule.doc").write_bytes(fake_doc(DOC_BODY, author=f"{FAKE_TERM} staff"))
    [hit] = seed.scan(repo / "seed", repo / "internal/blocklist.txt")
    assert hit.path == "documents/rule.doc" and "Word" in hit.where and FAKE_TERM not in hit.where


def test_scan_fails_a_word_file_with_no_text(repo):
    (repo / "seed" / "documents" / "empty.doc").write_bytes(fake_doc("", author="x"))
    [hit] = seed.scan(repo / "seed", repo / "internal/blocklist.txt")
    assert "no readable text" in hit.where


def test_scan_needs_a_blocklist(repo):
    with pytest.raises(seed.SeedError, match="not found"):
        seed.scan(repo / "seed", repo / "internal/none.txt")


# --- import ---------------------------------------------------------------------------------

def test_import_creates_seed_candidates_and_archives_document(repo, capsys):
    (repo / "seed" / "documents" / "bulletin.pdf").write_bytes(text_pdf("Revised prima facie credit life rates"))
    path = write_batch(repo, "batch_01", [row(doc="bulletin.pdf"), row(plan="Second plan", doc="bulletin.pdf"),
                                          row(plan="Third plan"), row(product="CD", doc="bulletin.pdf",
                                                                      basis="per $100, 12 months", new="1.20")])
    assert main(["--root", str(repo), "seed", "import", str(path)]) == 0
    cands = candidates.load_all(repo)
    assert len(cands) == 2
    cl = next(c for c in cands if c["product"] == "CL")
    assert (cl["origin"], cl["batch"], cl["seed_rows"], len(cl["rate_items"])) == ("seed", "batch_01", "rows 2-4", 3)
    assert cl["archived_copy"].startswith("archive/IN/2026-") and (repo / cl["archived_copy"]).exists()
    assert "pct_change" not in cl["rate_items"][0]
    # A second import of the same batch is refused.
    assert main(["--root", str(repo), "seed", "import", str(path)]) == 1
    assert len(candidates.load_all(repo)) == 2


def test_import_saves_several_documents_for_one_record(repo):
    docs = repo / "seed" / "documents"
    docs.joinpath("bulletin.pdf").write_bytes(text_pdf("Revised prima facie credit disability rates"))
    docs.joinpath("table.pdf").write_bytes(text_pdf("Single premium rates per $100"))
    path = write_batch(repo, "b", [row(product="CD", basis="per $100, 12 months", new="1.20", doc="bulletin.pdf;table.pdf")])
    [cand] = seed.import_batch(path, repo, NOW)
    assert cand["archived_copy"].endswith(".pdf") and "Also saved: archive/IN/" in cand["rate_table_note"]
    assert "(table.pdf)" in cand["rate_table_note"] and len(list((repo / "archive" / "IN").iterdir())) == 2
    missing = write_batch(repo, "m", [row(eff="2010-01-01", doc="bulletin.pdf;nope.pdf")])
    _, issues = seed.validate(missing, repo)
    assert any("'nope.pdf' is not a file" in i.issue.message for i in issues)


def test_import_refuses_errors_and_blocklisted_text(repo):
    bad = write_batch(repo, "bad", [row(state="ZZ")])
    with pytest.raises(seed.SeedError, match="error"):
        seed.import_batch(bad, repo, NOW)
    (repo / "seed" / "documents" / "x.pdf").write_bytes(text_pdf(FAKE_TERM))
    flagged = write_batch(repo, "flagged", [row(doc="x.pdf")])
    with pytest.raises(seed.SeedError, match="scan failed for seed/documents/x.pdf") as err:
        seed.import_batch(flagged, repo, NOW)
    assert "zebracorp" not in str(err.value).lower()
    assert not candidates.load_all(repo) and not (repo / "archive").exists()


# --- confirm --batch (acceptance 6) ------------------------------------------------------------

def test_acceptance_6_batch_confirms_only_rows_without_warnings(repo, capsys):
    (repo / "seed" / "documents" / "b.pdf").write_bytes(text_pdf("Revised prima facie credit life rates"))
    path = write_batch(repo, "batch_01", [
        row(eff="2016-01-01", comm="2015-10-01", new="0.50", doc="b.pdf"),   # clean
        row(eff="2019-01-01", old="0.50", new="0.45", doc="b.pdf"),     # clean, continuity holds
        row(product="CD", basis="per $100, 12 months", new="40.00", doc="b.pdf"),   # outside the range
        row(product="IUI", basis="per $100 of monthly benefit", new="2.00"),      # no saved copy
    ])
    assert seed.import_batch(path, repo, NOW)
    assert main(["--root", str(repo), "review", "confirm", "--batch", "batch_01"]) == 0
    out = capsys.readouterr().out
    confirmed = sorted(r["record_id"] for r in records.load_all(repo) if r["record_id"].startswith("IN-"))
    assert confirmed == ["IN-CL-2016-01-01-1", "IN-CL-2019-01-01-1"]
    rec = records.load_json(records.record_path(repo, "IN", "IN-CL-2019-01-01-1"))
    assert rec["verified"] and rec["origin"] == "seed" and rec["rate_items"][0]["pct_change"] == -10.0
    left = {c["product"] for c in candidates.load_all(repo)}
    assert left == {"CD", "IUI"} and "2 confirmed, 2 left open." in out


def test_batch_needs_id_or_batch_not_both(repo, capsys):
    assert main(["--root", str(repo), "review", "confirm"]) == 1
    assert main(["--root", str(repo), "review", "confirm", "c-1", "--batch", "b"]) == 1
    with pytest.raises(review.ReviewError, match="no open seed candidates"):
        review.confirm_batch(repo, "nothing", NOW)


def test_seed_record_may_leave_date_communicated_blank(repo):
    (repo / "seed" / "documents" / "b.pdf").write_bytes(text_pdf("Revised prima facie credit life rates"))
    path = write_batch(repo, "batch_02", [row(eff="2012-01-01", comm="", doc="b.pdf")])
    seed.import_batch(path, repo, NOW)
    written, skipped = review.confirm_batch(repo, "batch_02", NOW)
    assert len(written) == 1 and written[0]["date_communicated"] == "" and not skipped


def test_list_filters_by_batch(repo):
    seed.import_batch(write_batch(repo, "batch_03", [row()]), repo, NOW)
    assert len(review.list_open(repo, "seed", "batch_03")) == 1
    assert review.list_open(repo, "seed", "other") == []
