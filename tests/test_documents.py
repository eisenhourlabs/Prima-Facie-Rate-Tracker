"""Document text and archive tests (plan 9.1: Documents)."""

import datetime as dt
import io

from pypdf import PdfWriter

from pfrt import detect, documents
from tests.conftest import FIXTURES


def test_text_pdf_extracts():
    text = documents.extract_text(FIXTURES / "WI-bulletin-2023.pdf")
    assert "Revised Prima Facie Credit Life" in text


def blank_pdf() -> bytes:
    w = PdfWriter()
    w.add_blank_page(612, 792)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def test_image_only_pdf_is_unreadable_document(keywords):
    # A page with no text layer stands in for a scanned image. The size passed
    # is that of a typical scan (over 20 KB).
    content = blank_pdf()
    assert documents.content_text(content) == ""
    assert detect.text_test(documents.content_text(content), 250_000, keywords)[0] == "unreadable"


def test_damaged_pdf_gives_empty_text():
    assert documents.content_text(b"%PDF-1.7 not really a pdf") == ""


def test_guess_ext():
    assert documents.guess_ext(b"%PDF-1.4") == "pdf"
    assert documents.guess_ext(b"{\\rtf1") == "rtf"
    assert documents.guess_ext(b"<html>", "text/html") == "html"
    assert documents.guess_ext(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1rest") == "doc"


def test_word_doc_text_keeps_table_rows_and_both_encodings(keywords):
    body = ("69O-163.011 Credit Disability Insurance Rates.\rTABLE I\r"
            "7-12\x07 0.90\x07 0.58\x07 1.41\x07\x07\r49-60\x07 2.53\x07 2.38\x07 2.95\x07\x07\r")
    content = (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + bytes(range(32)) * 32 + body.encode("cp1252")
               + b"\x00\x01" * 40 + "Notice of Proposed Rule".encode("utf-16-le") + b"\x00\xff" * 40)
    text = documents.content_text(content, "application/msword", "notice_Files.asp?ID=1")
    assert "7-12 | 0.90 | 0.58 | 1.41 |" in text and "49-60 | 2.53 | 2.38 | 2.95 |" in text
    assert "Notice of Proposed Rule" in text and "\xff" not in text
    assert detect.text_test(text, len(content), keywords)[0] == "match"   # credit disability + rates


def test_archive_name_and_never_overwrite(tmp_path):
    day = dt.date(2026, 10, 3)
    a = documents.archive(b"%PDF-1.4 hello", "https://x.gov/a.pdf", "ZZ", day, root=tmp_path)
    assert a.path == f"archive/ZZ/2026-10-03_{a.sha256[:8]}.pdf"
    saved = tmp_path / a.path
    assert saved.read_bytes() == b"%PDF-1.4 hello"
    saved.write_bytes(b"edited by hand")
    documents.archive(b"%PDF-1.4 hello", "https://x.gov/a.pdf", "ZZ", day, root=tmp_path)
    assert saved.read_bytes() == b"edited by hand"   # existing file left alone


def test_oversize_file_recorded_by_hash_only(tmp_path, monkeypatch):
    monkeypatch.setattr(documents, "MAX_SAVE_BYTES", 10)
    a = documents.archive(b"%PDF-1.4 more than ten bytes", "u", "ZZ", dt.date(2026, 1, 1), root=tmp_path)
    assert a.too_large and a.path == "" and not (tmp_path / "archive").exists()
