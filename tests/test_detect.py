"""Keyword and detection-rule tests (plan 9.1: Keywords, Detect; Stage 1 acceptance 2-4)."""

from bs4 import BeautifulSoup

from pfrt import check, detect, fetch
from tests.conftest import FIXTURES


# --- Keywords ---------------------------------------------------------------

def test_plan_example_bulletin_277_prematches(keywords):
    m = detect.keyword_match("Bulletin 277 - Credit Life and Accident and Health Rates", keywords)
    assert m.prematches and "credit life" in m.product


def test_plan_example_bulletin_278_does_not_prematch(keywords):
    assert not detect.keyword_match("Bulletin 278 - Reporting of Ownership Information",
                                    keywords).prematches


def test_case_does_not_matter(keywords):
    assert detect.keyword_match("PRIMA FACIE Credit LIFE", keywords).matches


def test_credit_union_alone_does_not_prematch(keywords):
    assert not detect.keyword_match("Credit union mergers", keywords).prematches


def test_full_match_needs_product_and_strong_or_rate(keywords):
    assert not detect.keyword_match("prima facie rates", keywords).matches     # no product
    assert not detect.keyword_match("credit life", keywords).matches           # no strong/rate
    assert detect.keyword_match("credit life premiums", keywords).matches      # substring "premium"


def test_text_test_results(keywords):
    assert detect.text_test("Prima facie credit life rates", 5_000, keywords)[0] == "match"
    assert detect.text_test("", 50_000, keywords)[0] == "unreadable"        # scanned image
    assert detect.text_test("Page 1", 50_000, keywords)[0] == "unreadable"  # under 200 chars, over 20 KB
    assert detect.text_test("Ownership reporting. " * 20, 5_000, keywords)[0] == "no_match"


# --- Rules on simple inputs ---------------------------------------------------

def snap(links=None, sha="old"):
    return {"content_sha256": sha, "links": links or {}}


def test_first_run_is_baseline_with_no_findings(keywords):
    assert detect.compare("new_links", None, "h", {"https://x.gov/a.pdf": "Credit life"}, keywords) == []


def test_r2_on_any_change_hash_difference(keywords):
    assert [f.rule for f in detect.compare("any_change", snap(), "new", {}, keywords)] == ["R2_content_changed"]
    assert detect.compare("any_change", snap(sha="same"), "same", {}, keywords) == []


def test_r3_change_with_no_matching_link(keywords):
    old = snap({"https://x.gov/1.pdf": "Bulletin 1"})
    new = {"https://x.gov/1.pdf": "Bulletin 1", "https://x.gov/2.pdf": "Bulletin 2 - Ownership"}
    [f] = detect.compare("new_links", old, "new", new, keywords)
    assert f.rule == "R3_changed_no_match" and f.new_anchors == ("Bulletin 2 - Ownership",)


def test_r4_bare_pdf_link(keywords):
    [f] = detect.compare("new_links", snap(), "new", {"https://x.gov/b9.pdf": ""}, keywords)
    assert f.rule == "R4_new_bare_pdf_link"


def test_26_new_links_is_suspect_redesign(keywords):
    new = {f"https://x.gov/{i}.pdf": f"Credit life {i}" for i in range(26)}
    [f] = detect.compare("new_links", snap(), "new", new, keywords)
    assert f.rule == "suspect_redesign"


def test_25_new_links_is_not_a_redesign(keywords):
    new = {f"https://x.gov/{i}.pdf": f"Credit life {i}" for i in range(25)}
    assert len(detect.compare("new_links", snap(), "new", new, keywords)) == 25


# --- Stage 1 acceptance tests on real saved pages ------------------------------

def snapshot_of(source, content: bytes) -> dict:
    sha, links = check.fingerprint(source, fetched_bytes(source, content))
    return {"content_sha256": sha, "links": links, "byte_count": len(content)}


def fetched_bytes(source, content: bytes) -> fetch.FetchResult:
    return fetch.FetchResult(status="ok", http_status=200, final_url=source.url,
                             content=content, byte_count=len(content))


def test_acceptance_2_indiana_removed_bulletin_gives_one_r1(sources, keywords):
    src = sources["IN-bulletins"]
    full = (FIXTURES / "IN-bulletins.html").read_bytes()
    soup = BeautifulSoup(full, "html.parser")
    soup.find("a", string=lambda t: t and "Bulletin 277" in t).find_parent("li").decompose()
    old = snapshot_of(src, str(soup).encode("utf-8"))

    sha, links = check.fingerprint(src, fetched_bytes(src, full))
    findings = detect.compare(src.watch_mode, old, sha, links, keywords)

    assert len(findings) == 1
    f = findings[0]
    assert f.rule == "R1_new_matching_link"
    assert "Bulletin-277.pdf" in f.url
    assert f.anchor_text == "Bulletin 277 - Credit Life and Accident and Health Rates"


def test_acceptance_3_same_page_twice_gives_no_findings(sources, keywords):
    for sid, name in [("IN-bulletins", "IN-bulletins.html"),
                      ("WI-bulletins-index", "WI-bulletins-index.html")]:
        src = sources[sid]
        content = (FIXTURES / name).read_bytes()
        sha, links = check.fingerprint(src, fetched_bytes(src, content))
        assert detect.compare(src.watch_mode, snapshot_of(src, content), sha, links, keywords) == []


def test_acceptance_4_pdf_one_byte_changed_gives_one_r2(sources, keywords):
    # The plan names the Idaho PDF; doi.idaho.gov could not be reached on
    # 2026-11-20, so the Wisconsin 2023 bulletin PDF (also any_change) stands in.
    src = sources["WI-bulletin-2023"]
    original = (FIXTURES / "WI-bulletin-2023.pdf").read_bytes()
    changed = bytearray(original)
    changed[len(changed) // 2] ^= 0x01
    sha, links = check.fingerprint(src, fetched_bytes(src, bytes(changed)))
    findings = detect.compare(src.watch_mode, snapshot_of(src, original), sha, links, keywords)
    assert [f.rule for f in findings] == ["R2_content_changed"]


def test_wisconsin_index_selector_finds_the_2026_bulletin(sources):
    src = sources["WI-bulletins-index"]
    content = (FIXTURES / "WI-bulletins-index.html").read_bytes()
    _, links = check.fingerprint(src, fetched_bytes(src, content))
    assert any("Bulletin20261016PrimaFacieRates" in u for u in links)
    assert len(links) < 100  # the selector keeps the bulletin list, not the site menu
