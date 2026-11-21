"""Print the text around search phrases in saved HTML pages or PDFs (research aid).

PDF text is extracted with pypdf (first 30 pages); HTML text uses the project's normalizer.
Scanned PDFs have no text and show 0 characters.

Run from the repository folder (Windows):
    .venv\\Scripts\\python.exe -I tools\\grep_pages.py . "phrase1|phrase2" FILE [FILE ...]
The phrases form one case-insensitive regular expression; up to 4 hits per file are shown.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from pfrt import documents  # noqa: E402

pattern = re.compile(sys.argv[2], re.I)
for name in sys.argv[3:]:
    p = Path(name)
    raw = p.read_bytes()
    text = documents.pdf_text(raw) if raw[:4] == b"%PDF" else documents.normalize.html_to_text(raw)
    hits = list(pattern.finditer(text))
    print(f"===== {p.name}: {len(text)} chars, {len(hits)} hits")
    for m in hits[:4]:
        print("  ..." + " ".join(text[max(0, m.start() - 200): m.end() + 400].split()) + "...")
