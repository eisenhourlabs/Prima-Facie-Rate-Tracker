"""Owner review: list, show, confirm, reject, amend, retract, add (plan section 5).

Allowed status changes, and nothing else:
  candidate -> confirmed   (confirm)   one candidate may produce several records
  candidate -> rejected    (reject)
  confirmed -> confirmed   (amend)     fields corrected, change kept in history
  confirmed -> rejected    (retract)
Every command appends to the item's history. Only the owner runs these.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
from pathlib import Path

from pfrt import candidates, records

# Fields the reviewer may set when confirming or amending.
EDITABLE = {"product", "change_type", "effective_date", "date_communicated",
            "date_communicated_estimated", "source_url", "source_title", "rate_items",
            "rate_table_note", "summary", "legal_basis"}
REQUIRED = ("state", "product", "change_type", "effective_date", "date_communicated",
            "source_url", "summary", "legal_basis")
RATE_ITEM_KEYS = {"plan", "basis", "old_rate", "new_rate", "old_basis", "note"}


class ReviewError(Exception):
    """The requested review action is not allowed or the values are incomplete."""


# --- Finding things ---------------------------------------------------------------

def find(root: Path, item_id: str) -> tuple[str, Path, dict]:
    """Return ("candidate" | "record", path, data) for a candidate or record id."""
    path = candidates.candidate_path(root, item_id)
    if path.exists():
        return "candidate", path, records.load_json(path)
    for p in records.records_dir(root).glob(f"*/{item_id}.json"):
        return "record", p, records.load_json(p)
    raise ReviewError(f"no candidate or record with id {item_id}")


def _require_candidate(root: Path, cid: str) -> tuple[Path, dict]:
    kind, path, data = find(root, cid)
    if kind != "candidate":
        raise ReviewError(f"{cid} is a {data.get('status')} record; only open candidates can be "
                          "confirmed or rejected. Nothing was changed.")
    return path, data


def _require_confirmed(root: Path, rid: str) -> tuple[Path, dict]:
    kind, path, data = find(root, rid)
    if kind != "record" or data.get("status") != "confirmed":
        raise ReviewError(f"{rid} is not a confirmed record (it is {data.get('status')}). Nothing was changed.")
    return path, data


# --- list and show ------------------------------------------------------------------

def list_open(root: Path, origin: str = "") -> list[dict]:
    return [c for c in candidates.load_all(root) if not origin or c.get("origin") == origin]


def format_list(items: list[dict]) -> str:
    if not items:
        return "No open candidates."
    lines = [f"{'id':<20} {'state':<5} {'detected':<10} {'rule':<22} {'priority':<8} title"]
    for c in items:
        lines.append(f"{c['candidate_id']:<20} {c['state']:<5} {c['detected_at'][:10]:<10} "
                     f"{c['rule']:<22} {c['priority']:<8} {c.get('anchor_text') or c.get('document_url')}")
    return "\n".join(lines)


def show(root: Path, item_id: str) -> str:
    """Every field, with the text excerpt and diff printed last so they are easy to read."""
    _, path, data = find(root, item_id)
    long = {k: data.get(k) for k in ("text_excerpt", "text_diff")}
    short = {k: v for k, v in data.items() if k not in long}
    out = [f"File: {path.as_posix()}", json.dumps(short, indent=2, sort_keys=True, ensure_ascii=False)]
    for k, v in long.items():
        if v:
            out += [f"\n--- {k} ---", v]
    return "\n".join(out)


# --- confirm ------------------------------------------------------------------------

def _check_entry(entry: dict) -> None:
    unknown = set(entry) - EDITABLE
    if unknown:
        raise ReviewError(f"unknown field(s): {', '.join(sorted(unknown))}")
    for i, item in enumerate(entry.get("rate_items") or [], 1):
        bad = set(item) - RATE_ITEM_KEYS
        if bad:
            raise ReviewError(f"rate_items[{i}]: unknown key(s) {', '.join(sorted(bad))}")


def build_record(cand: dict, entry: dict, existing_ids: set[str], root: Path,
                 domains: set[str], now: str) -> dict:
    """Combine a candidate with the owner's values into a confirmed record (not yet saved)."""
    _check_entry(entry)
    rec = {k: cand.get(k) for k in ("state", "source_url", "source_title", "archived_copy",
                                    "archived_sha256", "retrieved_at", "legal_basis", "origin",
                                    "candidate_id", "document_url", "date_communicated_estimated",
                                    "rate_table_note")}
    rec.update({k: v for k, v in json.loads(json.dumps(entry)).items()})
    rec.setdefault("rate_items", [])
    rec["date_communicated_estimated"] = bool(rec.get("date_communicated_estimated"))
    rec["rate_table_note"] = rec.get("rate_table_note") or ""
    missing = [f for f in REQUIRED if not rec.get(f)]
    if missing:
        raise ReviewError(f"required field(s) empty: {', '.join(missing)}. Nothing was changed.")
    records.fill_pct_changes(rec["rate_items"])
    rec["record_id"] = records.make_id(rec["state"], rec["product"], rec["effective_date"], existing_ids)
    rec["verified"] = records.is_verified(rec, domains, root)
    rec.update(status="confirmed", confirmed_by="owner", confirmed_on=now[:10])
    rec["history"] = list(cand.get("history", [])) + [{"at": now, "event": "confirmed", "by": "owner"}]
    return rec


def confirm(root: Path, cid: str, entries: list[dict], now: str,
            next_expected: str = "") -> tuple[list[dict], list[records.Issue]]:
    """Confirm a candidate as one or more records. All are validated before anything is written.

    Returns (records written, warnings). Raises ReviewError on any error.
    """
    path, cand = _require_candidate(root, cid)
    if not entries:
        raise ReviewError("no record values given. Nothing was changed.")
    ctx = records.load_context(root)
    ids = {r.get("record_id", "") for r in ctx.existing}
    built, warnings = [], []
    for entry in entries:
        rec = build_record(cand, entry, ids, root, ctx.official_domains, now)
        issues = records.validate(rec, ctx)
        errors = [i for i in issues if i.level == "error"]
        if errors:
            raise ReviewError(f"{rec['record_id']}: " + "; ".join(map(str, errors)) + ". Nothing was changed.")
        warnings += issues
        ids.add(rec["record_id"])
        ctx.existing.append(rec)
        built.append(rec)
    for rec in built:
        records.save_json(records.record_path(root, rec["state"], rec["record_id"]), rec)
    path.unlink()
    if next_expected:
        set_next_expected(root, cand["state"], next_expected)
    return built, warnings


# --- reject, amend, retract ------------------------------------------------------------

def reject(root: Path, cid: str, reason: str, now: str) -> Path:
    """Move a candidate to data/records/ with status rejected, so it is not raised again."""
    if not reason.strip():
        raise ReviewError("a reason is required to reject")
    path, cand = _require_candidate(root, cid)
    cand.update(status="rejected", record_id=cid, rejection_reason=reason)
    cand["history"] = cand.get("history", []) + [{"at": now, "event": "rejected", "by": "owner", "reason": reason}]
    out = records.record_path(root, cand["state"], cid)
    records.save_json(out, cand)
    path.unlink()
    return out


def amend(root: Path, rid: str, changes: dict, reason: str, now: str) -> tuple[dict, list[records.Issue]]:
    """Correct fields of a confirmed record. The old and new values go into history."""
    if not reason.strip():
        raise ReviewError("a reason is required to amend")
    _check_entry(changes)
    path, rec = _require_confirmed(root, rid)
    before = {k: rec.get(k) for k in changes}
    rec.update(json.loads(json.dumps(changes)))
    records.fill_pct_changes(rec.get("rate_items") or [])
    ctx = records.load_context(root, exclude_id=rid)
    rec["verified"] = records.is_verified(rec, ctx.official_domains, root)
    issues = records.validate(rec, ctx)
    errors = [i for i in issues if i.level == "error"]
    if errors:
        raise ReviewError("; ".join(map(str, errors)) + ". Nothing was changed.")
    rec["history"] = rec.get("history", []) + [{"at": now, "event": "amended", "by": "owner",
                                                "reason": reason, "before": before}]
    records.save_json(path, rec)
    return rec, issues


def retract(root: Path, rid: str, reason: str, now: str) -> dict:
    """Mark a record confirmed in error as rejected. The record stays, with its history."""
    if not reason.strip():
        raise ReviewError("a reason is required to retract")
    path, rec = _require_confirmed(root, rid)
    rec.update(status="rejected", rejection_reason=reason)
    rec["history"] = rec.get("history", []) + [{"at": now, "event": "retracted", "by": "owner", "reason": reason}]
    records.save_json(path, rec)
    return rec


# --- add a document by hand -------------------------------------------------------------

def add(root: Path, state: str, url: str, now: str, source=None, title: str = "",
        downloader=None) -> dict:
    """Create a candidate (origin "manual") from a document URL the owner names.

    Used when a notice was already published before monitoring began, so the
    baseline will never raise it (plan risk R5). The document is downloaded
    politely, saved to archive/, and the candidate is reviewed like any other.
    `source` is the config.Source it belongs to, if any (for the citation).
    `downloader(url) -> FetchResult` is replaced in tests.
    """
    from types import SimpleNamespace

    from pfrt import config, detect, documents, fetch

    if state not in {s.state for s in config.load_states(Path(root) / "config/states.csv")}:
        raise ReviewError(f"state '{state}' is not in states.csv")
    if downloader is None:
        session, throttle = fetch.new_session(), fetch.Throttle()
        robots = fetch.RobotsCache(session, throttle)
        verdict, reason = robots.check(url)
        if verdict != "allowed":
            raise ReviewError(f"not downloaded: {reason}")
        downloader = lambda u: fetch.download(u, session, throttle)  # noqa: E731
    doc = downloader(url)
    if doc.http_status != 200:
        raise ReviewError(f"download failed: {doc.error or f'HTTP {doc.http_status}'}")
    src = source or SimpleNamespace(state=state, source_id="manual", products="", citation="", url=url)
    archived = documents.archive(doc.content, url, state, dt.date.fromisoformat(now[:10]),
                                 doc.content_type, root)
    text = documents.content_text(doc.content, doc.content_type, url)
    known = candidates.load_all(root) + records.load_all(root)
    cand = candidates.create(detect.Finding("manual", url, title), src, archived, "manual", text,
                             known, now, origin="manual")
    if cand is None:
        raise ReviewError("this document is already a candidate or record")
    candidates.save(root, cand)
    return cand


# --- interactive confirm -----------------------------------------------------------------

def _ask(ask, label: str, draft) -> str:
    shown = "" if draft in (None, "") else f" [{draft}]"
    answer = ask(f"{label}{shown}: ").strip()
    return answer if answer else ("" if draft is None else str(draft))


def prompt_entries(cand: dict, ask=input) -> list[dict]:
    """Ask for each record field in turn, offering any draft value. Returns entries for confirm()."""
    entries = []
    while True:
        e = {k: _ask(ask, k, cand.get(k) if not entries else entries[-1].get(k))
             for k in ("product", "change_type", "effective_date", "date_communicated",
                       "source_url", "source_title", "legal_basis", "summary", "rate_table_note")}
        e["rate_items"] = []
        while e["change_type"] != "no_change" and _ask(ask, "Add a rate item? (y/n)", "y").lower() == "y":
            item = {k: _ask(ask, f"  {k}", "") for k in ("plan", "basis", "old_rate", "new_rate")}
            item = {k: (float(v) if k.endswith("rate") and v else v or None) for k, v in item.items()}
            e["rate_items"].append(item)
        entries.append(e)
        if _ask(ask, "Create another record from this candidate (for a second product)? (y/n)", "n").lower() != "y":
            return entries


# --- states.csv: next expected notice ---------------------------------------------------

def set_next_expected(root: Path, state: str, date: str) -> None:
    """Write next_notice_expected_by for one state in config/states.csv."""
    dt.date.fromisoformat(date)  # raises ValueError on a bad date
    path = Path(root) / "config" / "states.csv"
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        cols, rows = reader.fieldnames, list(reader)
    for r in rows:
        if r["state"] == state:
            r["next_notice_expected_by"] = date
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    path.write_text(buf.getvalue(), encoding="utf-8", newline="")
