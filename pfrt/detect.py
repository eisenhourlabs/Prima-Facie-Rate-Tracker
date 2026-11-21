"""Decide what changed on a source since the last check (plan section 3.2).

Rules:
  R1  new_links source: a new link whose anchor text pre-matches the keywords.
  R2  any_change source: the content hash changed.
  R3  new_links source: the hash changed but no R1/R4 finding. Logged, no candidate.
  R4  new_links source: a new link to a PDF or file download (LinkClick.aspx, /download)
      with no (or 3-character) anchor text.
  suspect_redesign: more than 25 new links at once. No candidates; keep old snapshot.

The functions here only compare. Downloading a document and testing its text
(text_test) is done by the caller, so these rules can be tested without a network.
Every threshold favors a false alarm over a missed change.
"""

from __future__ import annotations

import csv
import difflib
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

REDESIGN_LIMIT = 25            # more new links than this in one run = probable redesign
SHORT_ANCHOR = 3               # anchor text of this many characters or fewer counts as bare
UNREADABLE_MAX_CHARS = 200     # under this much text ...
UNREADABLE_MIN_BYTES = 20_000  # ... in a file over this size = probably a scanned image

KEYWORD_CLASSES = ("strong", "product", "rate")


@dataclass(frozen=True)
class Match:
    """Keywords found in a text, by class."""
    strong: tuple[str, ...] = ()
    product: tuple[str, ...] = ()
    rate: tuple[str, ...] = ()

    @property
    def matches(self) -> bool:
        """Full text test: a product term plus a strong or rate term."""
        return bool(self.product) and bool(self.strong or self.rate)

    @property
    def prematches(self) -> bool:
        """Anchor-text test: any product term or any strong term."""
        return bool(self.product or self.strong)

    @property
    def terms(self) -> list[str]:
        return [*self.strong, *self.product, *self.rate]


@dataclass(frozen=True)
class Finding:
    rule: str                 # R1_new_matching_link, R2_content_changed, R3_changed_no_match,
                              # R4_new_bare_pdf_link, suspect_redesign
    url: str = ""
    anchor_text: str = ""
    matched_keywords: tuple[str, ...] = ()
    new_anchors: tuple[str, ...] = field(default=())  # R3 and redesign: titles of new links


def load_keywords(path: str | Path) -> dict[str, list[str]]:
    """Read config/keywords.csv into {class: [terms]} with terms lowercased."""
    out: dict[str, list[str]] = {c: [] for c in KEYWORD_CLASSES}
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            cls = row["class"].strip()
            if cls not in out:
                raise ValueError(f"{path}: unknown keyword class '{cls}'")
            out[cls].append(row["term"].strip().lower())
    return out


def keyword_match(text: str, keywords: dict[str, list[str]]) -> Match:
    """Find which keywords appear in the text, ignoring case and extra whitespace.

    This is a plain substring search: "premium" also matches "premiums", and
    "rate" also matches "separate". That is deliberate; a false alarm costs a
    few minutes of review, a miss costs much more (plan 3.6).
    """
    low = " ".join(text.lower().split())
    found = {c: tuple(t for t in keywords.get(c, []) if t in low) for c in KEYWORD_CLASSES}
    return Match(**found)


def text_test(text: str, byte_count: int, keywords: dict[str, list[str]]) -> tuple[str, Match]:
    """Test a downloaded document's text for R1/R4.

    Returns ("match" | "unreadable" | "no_match", Match). "unreadable" means a
    large file with almost no text, probably a scan; it still becomes a candidate.
    """
    m = keyword_match(text, keywords)
    if m.matches:
        return "match", m
    if len(text.strip()) < UNREADABLE_MAX_CHARS and byte_count > UNREADABLE_MIN_BYTES:
        return "unreadable", m
    if not text.strip():
        return "unreadable", m  # no text at all (for example a DOC or RTF in version 1)
    return "no_match", m


DIFF_MAX_LINES = 60


def text_diff(old_text: str, new_text: str, max_lines: int = DIFF_MAX_LINES) -> str:
    """Line diff of old against new for an R2 candidate, at most 60 lines.

    Normalized text is one long line, so it is first split into sentences.
    """
    def sentences(t: str) -> list[str]:
        return [s for s in re.split(r"(?<=[.!?;:])\s+", t or "") if s]
    lines = list(difflib.unified_diff(sentences(old_text), sentences(new_text),
                                      "old", "new", n=1, lineterm=""))
    if len(lines) > max_lines:
        lines = lines[:max_lines] + [f"... diff cut at {max_lines} lines"]
    return "\n".join(lines)


def _is_pdf_url(url: str) -> bool:
    """True for a link to a PDF or to a file download that hides its type.

    Some sites (DotNetNuke's LinkClick.aspx?fileticket=..., Drupal's /media/N/download)
    link documents without a .pdf ending and often with an icon instead of link text.
    Such links are downloaded and their text decides (R4), so a notice is not missed.
    """
    parts = urlsplit(url)
    path, query = parts.path.lower(), parts.query.lower()
    return (path.endswith(".pdf") or path.endswith("/linkclick.aspx") or "fileticket=" in query
            or path.endswith("/download"))


def compare(watch_mode: str, old_snapshot: dict | None, new_hash: str,
            new_links: dict[str, str], keywords: dict[str, list[str]]) -> list[Finding]:
    """Compare a fresh fetch with the last snapshot and return the findings.

    old_snapshot is None on a source's first run: that run is a baseline and
    returns no findings.
    """
    if not old_snapshot or "content_sha256" not in old_snapshot:
        return []   # no good fetch yet (a snapshot may hold only failure counts)
    changed = new_hash != old_snapshot.get("content_sha256")
    if watch_mode == "any_change":
        return [Finding("R2_content_changed")] if changed else []
    return _compare_links(old_snapshot.get("links", {}), new_links, changed, keywords)


def _compare_links(old_links: dict[str, str], new_links: dict[str, str],
                   changed: bool, keywords: dict[str, list[str]]) -> list[Finding]:
    """R1, R3, R4 and the redesign rule for a new_links source."""
    added = {u: t for u, t in new_links.items() if u not in old_links}
    if len(added) > REDESIGN_LIMIT:
        return [Finding("suspect_redesign", new_anchors=tuple(list(added.values())[:10]))]
    findings: list[Finding] = []
    for url, anchor in sorted(added.items()):
        m = keyword_match(anchor, keywords)
        if m.prematches:
            findings.append(Finding("R1_new_matching_link", url, anchor, tuple(m.terms)))
        elif len(anchor.strip()) <= SHORT_ANCHOR and _is_pdf_url(url):
            findings.append(Finding("R4_new_bare_pdf_link", url, anchor))
    if changed and not findings:
        findings.append(Finding("R3_changed_no_match", new_anchors=tuple(added.values())))
    return findings
