"""Turn a fetched web page into stable text and a link list (plan section 3.1).

The goal is that the same page fetched twice gives the same text and hash, so
only real content changes are noticed. Page chrome (menus, footers, scripts)
and volatile fragments ("Last updated ...") are removed.
"""

from __future__ import annotations

import hashlib
import re
import warnings
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

# RSS feeds (Delaware's Register) are read with the HTML parser on purpose: their
# titles and descriptions come out as plain text, which is all new_text needs.
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Elements that are never content. The plan also lists "form", but ASP.NET and
# SharePoint sites (for example oci.wi.gov) wrap the whole page in one <form>,
# so removing forms would remove everything. Forms are kept.
STRIP_TAGS = ["script", "style", "noscript", "nav", "header", "footer", "iframe"]

# Volatile fragments removed from page text. Each pattern has a test in
# tests/test_normalize.py. Add new ones here, with a test, when a source shows noise.
VOLATILE_PATTERNS = [
    re.compile(r"last (?:updated|modified|reviewed)\s*:?\s*[^.|]{0,40}?\d{4}", re.I),
    re.compile(r"page (?:generated|rendered) [^.|]{0,60}", re.I),
    re.compile(r"(?:©|&copy;|\(c\)|copyright)\s*(?:\d{4}\s*[-–]\s*)?\d{4}[^.|]{0,80}"
               r"(?:\.\s*all rights reserved\.?)?", re.I),
    re.compile(r"(?:visitor|hit|page view)s?\s*(?:count(?:er)?)?\s*:?\s*[\d,]+", re.I),
]

# Query parameters that only track visitors and never change the document.
TRACKING_PARAMS = {"sessionid", "sid", "_ga"}


class SelectorNotFound(Exception):
    """The source's CSS selector matched nothing; the page layout probably changed."""


def _soup(html: str | bytes, selector: str = "") -> BeautifulSoup:
    """Parse the page and, if a selector is given, keep only the matching element."""
    soup = BeautifulSoup(html, "html.parser")
    if selector:
        part = soup.select_one(selector)
        if part is None:
            raise SelectorNotFound(selector)
        soup = BeautifulSoup(str(part), "html.parser")
    return soup


def html_to_text(html: str | bytes, selector: str = "") -> str:
    """Visible text of the page (or the selected part), whitespace collapsed, volatile bits removed."""
    soup = _soup(html, selector)
    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    for pattern in VOLATILE_PATTERNS:
        text = pattern.sub(" ", text)
    return " ".join(text.split())


def clean_url(url: str) -> str:
    """Drop the #fragment and tracking parameters; lowercase the scheme and host."""
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in TRACKING_PARAMS]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path,
                       urlencode(query), ""))


# A javascript: link whose first action opens a document: javascript:window.open("url", ...)
WINDOW_OPEN = re.compile(r"""javascript:\s*window\.open\(\s*["']([^"']+)["']""", re.I)


def extract_links(html: str | bytes, base_url: str, selector: str = "") -> dict[str, str]:
    """Map of absolute, cleaned URL -> anchor text for every link in the page (or selected part).

    If the same URL appears twice, the longest anchor text is kept, so a bare
    icon link does not hide a descriptive one.
    """
    links: dict[str, str] = {}
    for a in _soup(html, selector).find_all("a", href=True):
        href = a["href"].strip()
        # Some sites (Alabama's Department of Insurance) open each document with
        # href="javascript:window.open('../pdf/x.pdf', ...)". Use the address inside.
        opened = WINDOW_OPEN.match(href)
        if opened:
            href = opened.group(1).strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        url = clean_url(urljoin(base_url, href))
        text = " ".join(a.get_text(" ").split())
        if len(text) >= len(links.get(url, "")):
            links[url] = text
    return links


def sha256_hex(data: str | bytes) -> str:
    """SHA-256 as lowercase hex. Text is hashed as UTF-8 bytes."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()
