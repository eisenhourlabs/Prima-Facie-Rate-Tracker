"""Save source documents and extract their text (plan sections 2.2 and 3.3).

Saved copies go to archive/{state}/{YYYY-MM-DD}_{sha8}.{ext}: the retrieval
date and the first 8 hex characters of the file's SHA-256. The original bytes
are saved, never a conversion, and an existing file is never overwritten.
"""

from __future__ import annotations

import datetime as dt
import io
import logging
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

from pfrt import normalize

MAX_SAVE_BYTES = 20 * 1024 * 1024   # larger files are recorded by hash and URL only
MAX_PDF_PAGES = 30                  # text extraction reads at most this many pages

# pypdf logs a warning for every small defect in a PDF; they are not useful here.
logging.getLogger("pypdf").setLevel(logging.ERROR)


@dataclass(frozen=True)
class ArchivedFile:
    url: str
    path: str            # repository-relative path, or "" when too large to save
    sha256: str
    byte_count: int
    content_type: str
    too_large: bool = False


def guess_ext(content: bytes, content_type: str = "", url: str = "") -> str:
    """File extension from the bytes first, then the Content-Type, then the URL."""
    if content[:4] == b"%PDF":
        return "pdf"
    if content[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return "doc"
    if content[:5] == b"{\\rtf":
        return "rtf"
    ct, low_url = content_type.lower(), url.lower().split("?")[0]
    for ext in ("pdf", "doc", "rtf"):
        if ext in ct or low_url.endswith("." + ext):
            return ext
    return "html"


def pdf_text(content: bytes) -> str:
    """Text of the first 30 pages of a PDF, or "" if it cannot be read."""
    try:
        reader = PdfReader(io.BytesIO(content))
        pages = reader.pages[:MAX_PDF_PAGES]
        return " ".join(" ".join((p.extract_text() or "").split()) for p in pages).strip()
    except Exception:  # a damaged PDF must not stop the run; it shows up as unreadable
        return ""


def content_text(content: bytes, content_type: str = "", url: str = "") -> str:
    """Searchable text of any fetched content. DOC and RTF give "" in version 1 (Q8)."""
    ext = guess_ext(content, content_type, url)
    if ext == "pdf":
        return pdf_text(content)
    if ext == "html":
        return normalize.html_to_text(content)
    return ""


def extract_text(path: str | Path) -> str:
    """Text of a saved document, as content_text does for fetched bytes."""
    p = Path(path)
    return content_text(p.read_bytes(), url=p.name)


def archive(content: bytes, url: str, state: str, today: dt.date, content_type: str = "",
            root: str | Path = ".") -> ArchivedFile:
    """Save bytes under archive/{state}/ and return where they went.

    If a file with the same name exists it has the same date and hash prefix,
    so it is the same document: it is left untouched.
    """
    sha = normalize.sha256_hex(content)
    if len(content) > MAX_SAVE_BYTES:
        return ArchivedFile(url, "", sha, len(content), content_type, too_large=True)
    ext = guess_ext(content, content_type, url)
    rel = Path("archive") / state / f"{today.isoformat()}_{sha[:8]}.{ext}"
    target = Path(root) / rel
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return ArchivedFile(url, rel.as_posix(), sha, len(content), content_type)


class DownloadError(Exception):
    """A document linked from a source could not be downloaded."""


def download(url: str, state: str, today: dt.date, session, throttle,
             root: str | Path = ".") -> ArchivedFile:
    """Download a document (politely, with retries) and save it with archive()."""
    from pfrt import fetch  # imported here because fetch also imports this module

    r = fetch.download(url, session, throttle)
    if r.http_status != 200:
        raise DownloadError(f"{url}: {r.error or f'HTTP {r.http_status}'}")
    return archive(r.content, url, state, today, r.content_type, root)
