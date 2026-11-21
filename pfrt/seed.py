"""Seed import: load past rate changes from a batch CSV (plan section 7, Stage 5).

A batch is a CSV in seed/ that follows seed/import_template.csv, one row per
rate item. Rows with the same state, product and effective date are merged into
one record. Three commands use this module:

  seed validate FILE   parse, merge and check every row (plan 7.4); writes nothing
  seed import FILE     create one candidate (origin "seed") per merged record
  seed scan FOLDER     search for blocklisted terms before anything is committed

Seed candidates are reviewed like any other, or confirmed together with
`review confirm --batch NAME` (only those with no warnings).

The blocklist (internal/blocklist.txt) is private. This module never prints a
term from it: a match is reported by file name and place only.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import re
from dataclasses import dataclass, field
from pathlib import Path

from pfrt import candidates, documents, records

# Columns of seed/import_template.csv, in order (plan 7.1).
COLUMNS = ("state", "product", "change_type", "effective_date", "date_communicated", "source_url",
           "source_title", "plan", "basis", "old_rate", "new_rate", "rate_table_note", "summary",
           "legal_basis", "public_document_file", "notes")
# Fields that belong to the whole record, not to one rate item. Merged rows must agree on them.
RECORD_FIELDS = ("change_type", "date_communicated", "source_url", "source_title", "rate_table_note",
                 "summary", "legal_basis", "public_document_file", "notes")
DOCUMENTS_FOLDER = "documents"   # public documents sit in seed/documents/, next to the CSV
DEFAULT_BLOCKLIST = Path("internal") / "blocklist.txt"


class SeedError(Exception):
    """The batch file cannot be read or imported."""


@dataclass
class SeedRow:
    row: int                      # line number in the CSV; the header is line 1
    values: dict[str, str]        # every column, as text, trimmed


@dataclass
class Draft:
    """One merged record from the batch, before it becomes a candidate."""
    rows: list[int]
    record: dict
    item_rows: list[int] = field(default_factory=list)    # CSV row of each rate item, in order
    issues: list[tuple[str, records.Issue]] = field(default_factory=list)   # (rows text, issue)


@dataclass(frozen=True)
class SeedIssue:
    rows: str                     # "row 4" or "rows 4-6"
    issue: records.Issue

    def __str__(self) -> str:
        return f"{self.rows}: {self.issue}"


@dataclass(frozen=True)
class Hit:
    """A file that failed the scan. `where` says what matched; it never holds the term."""
    path: str
    where: str


# --- parse and merge ---------------------------------------------------------------------

def batch_name(path: str | Path) -> str:
    """seed/batch_01.csv -> batch_01."""
    return Path(path).stem


def parse(path: str | Path) -> list[SeedRow]:
    """Read a batch CSV. Raises SeedError if a template column is missing."""
    text = Path(path).read_text(encoding="utf-8-sig")       # -sig: Excel adds a byte-order mark
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise SeedError(f"{Path(path).name}: missing column(s) {', '.join(missing)}; see seed/import_template.csv")
    rows = []
    for n, raw in enumerate(reader, start=2):
        values = {c: (raw.get(c) or "").strip() for c in COLUMNS}
        if any(values.values()):                             # skip fully blank lines
            rows.append(SeedRow(n, values))
    return rows


def _number(text: str):
    """'0.45' -> 0.45; '' -> None; anything else is kept as text so validation reports it."""
    if text == "":
        return None
    try:
        return float(text.replace("$", "").replace(",", ""))
    except ValueError:
        return text


def _rows_text(rows: list[int]) -> str:
    rows = sorted(set(rows))
    if len(rows) == 1:
        return f"row {rows[0]}"
    if rows == list(range(rows[0], rows[-1] + 1)):
        return f"rows {rows[0]}-{rows[-1]}"
    return "rows " + ", ".join(map(str, rows))


def merge(rows: list[SeedRow]) -> list[Draft]:
    """Group rows on state, product and effective date into one draft record each.

    Record fields (summary, source and so on) may be written on the first row of a
    group only; if two rows give different non-blank values, that is an error.
    Example: three CL rows for ZZ effective 2019-01-01 give one draft with three rate items.
    """
    groups: dict[tuple[str, str, str], list[SeedRow]] = {}
    for r in rows:
        v = r.values
        groups.setdefault((v["state"].upper(), v["product"].upper(), v["effective_date"]), []).append(r)
    drafts = []
    for (state, product, eff), group in groups.items():
        rec = {"state": state, "product": product, "effective_date": eff, "origin": "seed", "rate_items": []}
        draft = Draft([r.row for r in group], rec)
        for f in RECORD_FIELDS:
            given = [(r.row, r.values[f]) for r in group if r.values[f]]
            rec[f] = given[0][1] if given else ""
            if len({val for _, val in given}) > 1:
                draft.issues.append((_rows_text([n for n, _ in given]), records.Issue(
                    "error", f, "rows of the same record give different values")))
        for r in group:
            v = r.values
            if not any(v[k] for k in ("plan", "basis", "old_rate", "new_rate")):
                continue                                     # a no_change row may carry no rate
            if not v["plan"]:
                draft.issues.append((_rows_text([r.row]), records.Issue("error", "plan", "required when a rate is given")))
            rec["rate_items"].append({"plan": v["plan"], "basis": v["basis"],
                                      "old_rate": _number(v["old_rate"]), "new_rate": _number(v["new_rate"])})
            draft.item_rows.append(r.row)
        rec["change_type"] = rec["change_type"].lower()
        rec["verified"] = False if rec["source_url"] == "NONE" else None   # None: decided at import
        drafts.append(draft)
    return drafts


# --- validate ------------------------------------------------------------------------------

def _issue_rows(draft: Draft, issue: records.Issue) -> str:
    """The CSV rows an issue belongs to: one rate item's row, or every row of the record."""
    m = re.match(r"rate_items\[(\d+)\]", issue.field)
    if m and int(m.group(1)) <= len(draft.item_rows):
        return _rows_text([draft.item_rows[int(m.group(1)) - 1]])
    return _rows_text(draft.rows)


def document_names(rec: dict) -> list[str]:
    """public_document_file may name several files separated by ";".

    The first is the saved copy of source_url; the others (for example a separate
    rate table) are saved too and listed in the rate table note.
    Example: "Bulletin2014.html;CredRate14.pdf" -> ["Bulletin2014.html", "CredRate14.pdf"]
    """
    return [n.strip() for n in (rec.get("public_document_file") or "").split(";") if n.strip()]


def _seed_checks(draft: Draft, documents_dir: Path) -> list[records.Issue]:
    """Checks the template needs beyond plan 7.4: required text fields and the document file."""
    rec, out = draft.record, []
    for f in ("summary", "legal_basis"):
        if not rec.get(f):
            out.append(records.Issue("error", f, "required"))
    names = document_names(rec)
    if names:
        for name in names:
            if Path(name).name != name or not (documents_dir / name).is_file():
                out.append(records.Issue("error", "public_document_file", f"'{name}' is not a file in seed/{DOCUMENTS_FOLDER}/"))
    elif rec.get("source_url") != "NONE":
        out.append(records.Issue("warning", "public_document_file",
                                 "no saved copy; the record will be unverified until one is added"))
    if rec.get("source_url") == "NONE":
        out.append(records.Issue("warning", "source_url", "NONE: no public source; the record will be unverified"))
    return out


def validate(path: str | Path, root: str | Path) -> tuple[list[Draft], list[SeedIssue]]:
    """Every check in plan 7.4, row by row. Writes nothing.

    Records are checked in effective-date order, and each one is then treated as
    existing, so the continuity check also runs between records of the same batch.
    Returns the drafts and the issues, each naming its CSV row(s).
    """
    root = Path(root)
    drafts = merge(parse(path))
    ctx = records.load_context(root)
    # Open candidates count as existing too, so a batch cannot be imported twice.
    open_keys = {(c.get("state"), c.get("product"), c.get("effective_date")) for c in candidates.load_all(root)}
    documents_dir = Path(path).parent / DOCUMENTS_FOLDER
    found = []
    for d in sorted(drafts, key=lambda d: (d.record["state"], d.record["product"], d.record["effective_date"])):
        rec = d.record
        check_copy = dict(rec, rate_items=records.fill_pct_changes([dict(i) for i in rec["rate_items"]]))
        for rows, issue in d.issues:
            found.append(SeedIssue(rows, issue))
        for issue in records.validate(check_copy, ctx) + _seed_checks(d, documents_dir):
            found.append(SeedIssue(_issue_rows(d, issue), issue))
        if (rec["state"], rec["product"], rec["effective_date"]) in open_keys:
            found.append(SeedIssue(_rows_text(d.rows), records.Issue(
                "error", "effective_date", "an open candidate already exists for this state, product and effective date")))
        ctx.existing.append(dict(check_copy, status="confirmed", record_id=f"batch {_rows_text(d.rows)}"))
    return drafts, sorted(found, key=lambda s: (int(re.search(r"\d+", s.rows).group()), s.issue.level, s.issue.field))


# --- import --------------------------------------------------------------------------------

def import_batch(path: str | Path, root: str | Path, now: str, blocklist: str | Path | None = None) -> list[dict]:
    """Create one candidate per merged record, with origin "seed" and the batch name.

    Refuses (and writes nothing) if validation finds an error, or if the CSV or any
    document it names fails the blocklist scan. Each named public document is saved
    to archive/{state}/ exactly as monitor documents are.
    """
    root, path = Path(root), Path(path)
    drafts, issues = validate(path, root)
    errors = [i for i in issues if i.issue.level == "error"]
    if errors:
        raise SeedError(f"{len(errors)} error(s); run seed validate. Nothing was imported.")
    docs_dir = path.parent / DOCUMENTS_FOLDER
    files = [path] + sorted({docs_dir / n for d in drafts for n in document_names(d.record)})
    hits = scan_files(files, load_blocklist(blocklist or root / DEFAULT_BLOCKLIST), base=root)
    if hits:
        raise SeedError("scan failed for " + ", ".join(f"{h.path} ({h.where})" for h in hits) + ". Nothing was imported.")
    batch = batch_name(path)
    today = dt.date.fromisoformat(now[:10])
    known_ids = [c.get("candidate_id", "") for c in candidates.load_all(root) + records.load_all(root)]
    created = []
    for d in drafts:
        rec = d.record
        saved = [(n, documents.archive((docs_dir / n).read_bytes(), rec["source_url"] if i == 0 else n,
                                       rec["state"], today, root=root))
                 for i, n in enumerate(document_names(rec))]
        archived = saved[0][1] if saved else None
        if len(saved) > 1:
            also = "; ".join(f"{a.path} ({n})" for n, a in saved[1:])
            rec["rate_table_note"] = (rec["rate_table_note"] + " " if rec["rate_table_note"] else "") + f"Also saved: {also}."
        cand = _candidate(d, batch, archived, now, known_ids)
        known_ids.append(cand["candidate_id"])
        created.append(cand)
    for cand in created:
        candidates.save(root, cand)
    return created


def _candidate(d: Draft, batch: str, archived, now: str, known_ids: list[str]) -> dict:
    """A candidate with its record fields already filled from the batch."""
    rec = d.record
    url = "" if rec["source_url"] == "NONE" else rec["source_url"]
    return {
        "candidate_id": candidates.next_id(rec["state"], now[:10].replace("-", ""), known_ids),
        "status": "candidate", "origin": "seed", "batch": batch, "seed_rows": _rows_text(d.rows),
        "state": rec["state"], "source_id": "seed", "products_hint": rec["product"],
        "detected_at": now, "run_id": batch, "rule": "seed_import", "priority": "seed",
        "document_url": url, "anchor_text": rec["source_title"], "matched_keywords": [],
        "archived_copy": archived.path if archived else "", "archived_sha256": archived.sha256 if archived else "",
        "archived_too_large": bool(archived and archived.too_large), "retrieved_at": now if archived else "",
        "unreadable_document": False, "text_excerpt": "", "text_diff": "", "ai": None,
        "seed_notes": rec["notes"],
        # Record fields, from the batch.
        "product": rec["product"], "change_type": rec["change_type"], "effective_date": rec["effective_date"],
        "date_communicated": rec["date_communicated"], "date_communicated_estimated": False,
        "source_url": rec["source_url"], "source_title": rec["source_title"],
        "rate_items": [{k: v for k, v in i.items() if v not in (None, "")} for i in rec["rate_items"]],
        "rate_table_note": rec["rate_table_note"], "summary": rec["summary"], "legal_basis": rec["legal_basis"],
        "history": [{"at": now, "event": "candidate_created", "by": "seed-import", "batch": batch}],
    }


# --- scan ------------------------------------------------------------------------------------

def load_blocklist(path: str | Path) -> list[str]:
    """Terms from the private blocklist, one per line; blank lines and # comments skipped."""
    p = Path(path)
    if not p.is_file():
        raise SeedError(f"blocklist not found at {p.as_posix()}; the scan cannot run")
    terms = [" ".join(line.split()).lower() for line in p.read_text(encoding="utf-8-sig").splitlines()]
    terms = [t for t in terms if t and not t.startswith("#")]
    if not terms:
        raise SeedError(f"{p.as_posix()} has no terms; the scan cannot run")
    return terms


def _flat(text: str) -> str:
    """Lowercase with whitespace runs collapsed, so a term broken over two lines still matches."""
    return " ".join(text.split()).lower()


def _pdf_parts(content: bytes) -> dict[str, str] | None:
    """Searchable parts of a PDF: page text, metadata, and comment (annotation) text.

    Text is extracted from every page; raw bytes are never searched, because
    compressed streams give false matches on short terms (Stage 2 note).
    Returns None if the PDF cannot be opened.
    """
    from pypdf import PdfReader
    try:
        reader = PdfReader(io.BytesIO(content))
        text = " ".join(p.extract_text() or "" for p in reader.pages)
        meta = " ".join(str(v) for v in (reader.metadata or {}).values())
        try:
            xmp = reader.xmp_metadata
            meta += " " + (xmp.rdf_root.toxml() if xmp is not None else "")
        except Exception:      # XMP is optional and often malformed; the info dictionary is still searched
            pass
        notes = []
        for page in reader.pages:
            for annot in page.get("/Annots") or []:
                obj = annot.get_object()
                notes += [str(obj.get(k, "")) for k in ("/Contents", "/T", "/Subj")]
        return {"PDF text": text, "PDF metadata": meta, "PDF comments": " ".join(notes)}
    except Exception:
        return None


_HTML_CHARSET = re.compile(rb"""charset\s*=\s*["']?([A-Za-z0-9_-]+)""", re.I)


def _decode_text(content: bytes) -> str | None:
    """Text of a plain-text or HTML file: UTF-8, or the charset an HTML page declares itself.

    Some official pages are saved in windows-1252 (Nevada's NAC, New Hampshire's rules) and say
    so in a meta tag. Decoding is strict: bytes the declared charset does not define, or a file
    with no declaration, leave the file unsearchable (None).
    """
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    m = _HTML_CHARSET.search(content[:4096])
    if not m or b"<html" not in content[:4096].lower():
        return None
    try:
        return content.decode(m.group(1).decode("ascii"))
    except (LookupError, UnicodeDecodeError):
        return None


def scan_file(path: Path, terms: list[str], shown: str) -> list[Hit]:
    """Check one file's name and contents. A file that cannot be searched is a hit too."""
    hits = []
    # `shown` is the path from the scanned folder, so folder names are checked too.
    if any(t in _flat(shown.replace("_", " ").replace("-", " ")) or t in _flat(shown) for t in terms):
        hits.append(Hit(shown, "file name"))
    content = path.read_bytes()
    if content[:4] == b"%PDF":
        parts = _pdf_parts(content)
        if parts is None:
            return hits + [Hit(shown, "PDF could not be opened; check it by hand or remove it")]
        if len(parts["PDF text"].strip()) < 200 and len(content) > 20 * 1024:
            hits.append(Hit(shown, "PDF has no extractable text (scanned image); check it by hand"))
        hits += [Hit(shown, where) for where, text in parts.items() if any(t in _flat(text) for t in terms)]
        return hits
    if content[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":     # Word 97-2003 .doc (Florida rules)
        from pfrt import documents
        text = documents.doc_text(content)
        if len(text) < 200:
            return hits + [Hit(shown, "Word file has no readable text; check it by hand or remove it")]
        # doc_text also returns the file's properties (author, title), so they are searched too.
        if any(t in _flat(text) for t in terms):
            hits.append(Hit(shown, "Word text or properties"))
        return hits
    text = _decode_text(content)
    if text is None:
        return hits + [Hit(shown, "file cannot be searched (not text or PDF); convert to PDF or remove it")]
    if any(t in _flat(text) for t in terms):
        hits.append(Hit(shown, "text"))
    return hits


def scan_files(files: list[Path], terms: list[str], base: Path | None = None) -> list[Hit]:
    out = []
    for f in files:
        try:
            shown = f.resolve().relative_to(Path(base).resolve()).as_posix() if base else f.as_posix()
        except ValueError:
            shown = f.as_posix()
        out += scan_file(f, terms, shown)
    return out


def scan(folder: str | Path, blocklist_path: str | Path) -> list[Hit]:
    """Plan 7.3: search every file under `folder` (names, CSV text, PDF text, metadata and comments).

    Case-insensitive. Returns the files that failed; an empty list means the folder passed.
    """
    folder = Path(folder)
    if not folder.exists():
        raise SeedError(f"{folder.as_posix()} does not exist")
    terms = load_blocklist(blocklist_path)
    files = [folder] if folder.is_file() else sorted(p for p in folder.rglob("*") if p.is_file())
    return scan_files(files, terms, base=folder if folder.is_dir() else folder.parent)
