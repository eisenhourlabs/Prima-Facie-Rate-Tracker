"""Download pages or documents with the project's fetcher, for research and seeding.

Uses pfrt.fetch, so robots.txt (and config/robots_overrides.csv), the 5-second gap per host,
the honest user agent and the CA bundle all apply. Saves each response under OUT_DIR, named
after the last part of the URL path, and prints the HTTP status, type, size and sha8. For
HTML pages it also lists links that mention prima facie, credit or rates.

Run from the repository folder (Windows):
    .venv\\Scripts\\python.exe -I tools\\polite_get.py . OUT_DIR URL [URL ...]

Save downloads outside the repository (for example in a scratch folder), then copy the
public documents a batch needs into seed/documents/ (git-ignored).
Note: two URLs whose paths end in the same name overwrite each other in OUT_DIR, unless
--numbered is given first: then each file name starts with the URL's position and host
(for example 03_doi.idaho.gov_robots.txt). The probe workflow uses --numbered.
    .venv\\Scripts\\python.exe -I tools\\polite_get.py . OUT_DIR --numbered URL [URL ...]
"""
import hashlib
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

repo, out = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(repo))
from pfrt import fetch, normalize  # noqa: E402

out.mkdir(parents=True, exist_ok=True)
session, throttle = fetch.new_session(), fetch.Throttle()
robots = fetch.RobotsCache(session, throttle)
urls = sys.argv[3:]
numbered = bool(urls) and urls[0] == "--numbered"
if numbered:
    urls = urls[1:]
for position, url in enumerate(urls, start=1):
    verdict, reason = robots.check(url)
    if verdict != "allowed":
        print(f"SKIP {url}: {verdict} {reason}")
        continue
    r = fetch.download(url, session, throttle)
    name = unquote(Path(urlsplit(url).path).name) or "index.html"
    if numbered:
        name = f"{position:02d}_{urlsplit(url).hostname}_{name}"
    if r.http_status == 200:
        (out / name).write_bytes(r.content)
    sha = hashlib.sha256(r.content or b"").hexdigest()[:8]
    print(f"{r.http_status} {url} -> {name} {r.content_type} {len(r.content or b'')} bytes sha8={sha} {r.error or ''}")
    if r.http_status == 200 and "html" in (r.content_type or ""):
        for link, text in normalize.extract_links(r.content, url).items():
            low = (link + " " + text).lower()
            if "prima" in low or "credit" in low or "rates" in low:
                print(f"   LINK {link} | {text}")
