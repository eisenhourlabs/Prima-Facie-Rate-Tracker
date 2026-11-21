"""Normalize and link tests (plan 9.1: Normalize, Links)."""

import pytest

from pfrt import normalize


def test_nav_script_footer_removed():
    html = ("<html><body><nav>Home | About</nav><script>var x=1</script>"
            "<p>Bulletin 277</p><footer>Contact us</footer></body></html>")
    assert normalize.html_to_text(html) == "Bulletin 277"


@pytest.mark.parametrize("fragment", [
    "Last updated: November 3, 2026",
    "Last modified 11/03/2026",
    "Page generated at 13:17:42 by server 4",
    "© 2026 State of Example. All rights reserved",
    "Copyright 2001-2026 State of Example",
    "Visitor counter: 12,345",
])
def test_volatile_fragment_removed(fragment):
    a = normalize.html_to_text(f"<p>Bulletin list</p><p>{fragment}</p>")
    b = normalize.html_to_text("<p>Bulletin list</p>")
    assert a == b


def test_page_wrapped_in_one_form_keeps_its_text():
    # ASP.NET / SharePoint pages such as oci.wi.gov put everything inside <form>.
    html = "<html><body><form id='aspnetForm'><p>Bulletins Issued</p></form></body></html>"
    assert normalize.html_to_text(html) == "Bulletins Issued"


def test_whitespace_differences_give_same_hash():
    a = normalize.html_to_text("<p>Credit   life\n rates</p>")
    b = normalize.html_to_text("<p>Credit life rates</p>")
    assert normalize.sha256_hex(a) == normalize.sha256_hex(b)


def test_selector_keeps_only_that_part():
    html = "<div id='menu'>Menu text</div><div id='list'><p>Bulletin 277</p></div>"
    assert normalize.html_to_text(html, "#list") == "Bulletin 277"


def test_selector_that_matches_nothing_raises():
    with pytest.raises(normalize.SelectorNotFound):
        normalize.html_to_text("<p>x</p>", "#gone")


def test_plan_example_link():
    html = '<a href="/idoi/files/Bulletin-277.pdf">Bulletin 277 - Credit Life and Accident and Health Rates</a>'
    links = normalize.extract_links(html, "https://www.in.gov/idoi/2591.htm")
    assert links == {"https://www.in.gov/idoi/files/Bulletin-277.pdf":
                     "Bulletin 277 - Credit Life and Accident and Health Rates"}


def test_link_fragment_and_tracking_dropped_host_lowercased():
    html = '<a href="HTTPS://WWW.Example.GOV/a.pdf?utm_source=x&id=7&sid=9&_ga=1#page=2">A</a>'
    links = normalize.extract_links(html, "https://www.example.gov/")
    assert list(links) == ["https://www.example.gov/a.pdf?id=7"]


def test_anchor_text_collapsed_and_mailto_skipped():
    html = '<a href="b.pdf">  Bulletin\n   278 </a><a href="mailto:x@example.gov">mail</a>'
    assert normalize.extract_links(html, "https://example.gov/dir/") == {
        "https://example.gov/dir/b.pdf": "Bulletin 278"}


def test_javascript_window_open_link_uses_its_address():
    # As on www.aldoi.gov/Legal/Regulations.aspx; other javascript: links are still skipped.
    html = ("<a href='javascript:window.open(\"../PDF/Legal/117-1999.pdf\",\"_blank\"); "
            "_blank.focus()'>PDF</a><a href='javascript:void(0)'>Menu</a>")
    assert normalize.extract_links(html, "https://www.aldoi.gov/Legal/Regulations.aspx") == {
        "https://www.aldoi.gov/PDF/Legal/117-1999.pdf": "PDF"}


def test_duplicate_link_keeps_longer_text():
    html = '<a href="b.pdf"><img src="i.png"></a><a href="b.pdf">Bulletin 278</a>'
    assert normalize.extract_links(html, "https://example.gov/") == {
        "https://example.gov/b.pdf": "Bulletin 278"}
