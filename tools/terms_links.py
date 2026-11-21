"""Fetch pages politely and list links that look like terms, policy, legal or disclaimer pages.

Run from the repository folder (Windows):
    .venv\Scripts\python.exe -I tools\terms_links.py . URL [URL ...]

Use it before fetching from a new host: read the terms it finds (docs/onboarding.md step 3).
"""
import sys

sys.path.insert(0, sys.argv[1])
from pfrt import fetch, normalize  # noqa: E402

KEYS = ('term', 'policy', 'policies', 'legal', 'disclaim', 'conditions', 'acceptable', 'copyright')
session, throttle = fetch.new_session(), fetch.Throttle()
robots = fetch.RobotsCache(session, throttle)
for url in sys.argv[2:]:
    verdict, reason = robots.check(url)
    if verdict != 'allowed':
        print(f'SKIP {url}: {verdict} {reason}')
        continue
    r = fetch.download(url, session, throttle)
    print(f'{r.http_status} {url} {len(r.content or b"")} bytes {r.error or ""}')
    if r.http_status == 200 and 'html' in (r.content_type or ''):
        for link, text in normalize.extract_links(r.content, r.final_url or url).items():
            if any(k in (link + ' ' + text).lower() for k in KEYS):
                print(f'   {link} | {text[:80]}')
