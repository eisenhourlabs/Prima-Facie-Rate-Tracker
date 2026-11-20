"""Candidates: possible rate changes waiting for the owner's review (plan 2.2).

One JSON file per open candidate in data/candidates/{candidate_id}.json.
The check job can create candidates; it can never confirm them.
"""

from __future__ import annotations

from pathlib import Path

from pfrt import records
from pfrt.detect import Finding
from pfrt.documents import ArchivedFile

EXCERPT_CHARS = 1500


def candidates_dir(root: Path) -> Path:
    return Path(root) / "data" / "candidates"


def candidate_path(root: Path, candidate_id: str) -> Path:
    return candidates_dir(root) / f"{candidate_id}.json"


def load_all(root: Path) -> list[dict]:
    return [records.load_json(p) for p in sorted(candidates_dir(root).glob("*.json"))]


def save(root: Path, candidate: dict) -> Path:
    path = candidate_path(root, candidate["candidate_id"])
    records.save_json(path, candidate)
    return path


def next_id(state: str, today: str, existing_ids: set[str] | list[str]) -> str:
    """c-{YYYYMMDD}-{state}-{nn}. today is YYYYMMDD.

    Example: with c-20261203-IN-01 present, returns c-20261203-IN-02.
    """
    prefix = f"c-{today}-{state}-"
    used = [int(i[len(prefix):]) for i in existing_ids
            if i.startswith(prefix) and i[len(prefix):].isdigit()]
    return f"{prefix}{max(used, default=0) + 1:02d}"


def already_known(document_url: str, sha256: str, known: list[dict]) -> bool:
    """True if any candidate or record has the same document URL or the same file hash.

    A document re-linked at a new URL is caught by the hash; a URL that now
    serves a new version is caught by the URL, so the same notice is never raised twice.
    """
    for item in known:
        if document_url and document_url == item.get("document_url"):
            return True
        if sha256 and sha256 == item.get("archived_sha256"):
            return True
    return False


def create(finding: Finding, source, archived: ArchivedFile, run_id: str, text: str,
           known: list[dict], now: str, unreadable: bool = False, text_diff: str = "",
           origin: str = "monitor") -> dict | None:
    """Build a candidate dict, or None if this document is already a candidate or record.

    `known` is every existing candidate and record. Record fields are left empty
    for the reviewer to fill; legal_basis starts as the source's citation as a draft.
    """
    document_url = finding.url or source.url
    # An any_change (R2) source keeps its URL when it changes, so only the hash
    # identifies a repeat; matching on its URL would hide every later change.
    if already_known(finding.url, archived.sha256, known):
        return None
    ids = [k.get("candidate_id", "") for k in known]
    cid = next_id(source.state, now[:10].replace("-", ""), ids)
    return {
        "candidate_id": cid, "status": "candidate", "origin": origin,
        "state": source.state, "source_id": source.source_id, "products_hint": source.products,
        "detected_at": now, "run_id": run_id, "rule": finding.rule, "priority": "high",
        "document_url": document_url, "anchor_text": finding.anchor_text,
        "matched_keywords": list(finding.matched_keywords),
        "archived_copy": archived.path, "archived_sha256": archived.sha256,
        "archived_too_large": archived.too_large, "retrieved_at": now,
        "unreadable_document": unreadable,
        "text_excerpt": text[:EXCERPT_CHARS], "text_diff": text_diff, "ai": None,
        # Record fields, filled in at review.
        "product": "", "change_type": "", "effective_date": "", "date_communicated": "",
        "date_communicated_estimated": False, "source_url": document_url,
        "source_title": finding.anchor_text, "rate_items": [], "rate_table_note": "",
        "summary": "", "legal_basis": source.citation,
        "history": [{"at": now, "event": "candidate_created", "by": "check-job" if origin == "monitor" else "owner"}],
    }
