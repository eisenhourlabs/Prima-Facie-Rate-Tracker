"""Build the one-page site from confirmed records (plan sections 2.5 and 8).

Output: site/index.html (one file, inline CSS, no JavaScript) plus site/archive/
with the saved copies the page links to. Only records with status "confirmed"
are shown.
"""

from __future__ import annotations

import datetime as dt
import re
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

from pfrt import records

RECENT_DAYS = 365
HISTORY_YEARS = 15
STALE_DAYS = 20          # checks run twice a month; older than this means they have stopped
PRODUCT_NAMES = {"CL": "Credit life", "CD": "Credit disability", "IUI": "Involuntary unemployment"}
REPO_URL = "https://github.com/eisenhourlabs/Prima-Facie-Rate-Tracker"
TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


# --- Selecting records ---------------------------------------------------------------

def _confirmed(recs: list[dict]) -> list[dict]:
    return [r for r in recs if r.get("status") == "confirmed"]


def _years_before(d: dt.date, years: int) -> dt.date:
    try:
        return d.replace(year=d.year - years)
    except ValueError:              # 29 February in a non-leap year
        return d.replace(year=d.year - years, day=28)


def select_recent(recs: list[dict], today: dt.date) -> list[dict]:
    """Communicated in the last 365 days, not 'no change', soonest effective date first."""
    since = (today - dt.timedelta(days=RECENT_DAYS)).isoformat()
    out = [r for r in _confirmed(recs)
           if (r.get("date_communicated") or "") >= since and r.get("change_type") != "no_change"]
    return sorted(out, key=lambda r: (r["effective_date"], r["state"], r["product"]))


def select_history(recs: list[dict], today: dt.date) -> dict[str, list[dict]]:
    """Effective in the last 15 years, by state, newest first within each state."""
    since = _years_before(today, HISTORY_YEARS).isoformat()
    out: dict[str, list[dict]] = {}
    for r in _confirmed(recs):
        if r["effective_date"] >= since:
            out.setdefault(r["state"], []).append(r)
    for state_recs in out.values():
        state_recs.sort(key=lambda r: (r["effective_date"], r["product"]), reverse=True)
    return out


# --- Formatting helpers used by the template -----------------------------------------------

def long_date(iso: str) -> str:
    """2027-01-01 -> 1 January 2027 (month as a word, plan 8.4).

    A blank date (allowed for old seed records) is shown as "Not stated".
    """
    if not iso:
        return "Not stated"
    d = dt.date.fromisoformat(iso[:10])
    return f"{d.day} {d:%B %Y}"


def rate(v) -> str:
    """At least two decimals, more only when the source gives more: 0.6 -> 0.60, 0.662 -> 0.662."""
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return "-"       # missing (None, or absent from the record)
    text = f"{v:.4f}".rstrip("0")
    whole, _, frac = text.partition(".")
    return f"{whole}.{frac.ljust(2, '0')}"


def pct(v) -> str:
    return f"{v:+.1f}%" if isinstance(v, (int, float)) and not isinstance(v, bool) else "-"


def change_text(rec: dict) -> str:
    """Headline change for the Recent table: one rate old to new, a range, or 'See source'."""
    items = rec.get("rate_items") or []
    if len(items) == 1:
        i = items[0]
        old = f"{rate(i.get('old_rate'))} to " if i.get("old_rate") is not None else ""
        tail = f" ({pct(i['pct_change'])})" if i.get("pct_change") is not None else ""
        return f"{old}{rate(i.get('new_rate'))} {i.get('basis', '')}{tail}"
    pcts = [i["pct_change"] for i in items if i.get("pct_change") is not None]
    if pcts:
        lo, hi = min(pcts), max(pcts)
        span = pct(lo) if lo == hi else f"{pct(lo)} to {pct(hi)}"
        return f"{len(items)} rates, changes of {span}"
    return f"{len(items)} rates; see source" if items else "See source"


def doc_label(path_or_url: str) -> str:
    return "PDF" if path_or_url.lower().split("?")[0].endswith(".pdf") else "web page"


ARCHIVE_PATH = re.compile(r"archive/[A-Z]{2}/[\w.-]+?\.(?:pdf|html|doc|rtf)")
URL = re.compile(r"https?://[^\s,;)]+[^\s,;).]")


def note_html(text: str) -> Markup:
    """Escape a note, then make its URLs and saved-copy paths into links."""
    out = str(escape(text or ""))
    out = URL.sub(lambda m: f'<a href="{m.group(0)}">official {doc_label(m.group(0))}</a>', out)
    out = ARCHIVE_PATH.sub(lambda m: f'<a href="{m.group(0)}">saved copy ({doc_label(m.group(0))})</a>', out)
    return Markup(out)


# --- Last run ---------------------------------------------------------------------------

def last_run(root: Path) -> dict | None:
    """The newest real (not dry-run) run log, or None if the job has never run."""
    for p in sorted((Path(root) / "data" / "runs").glob("run-*.json"), reverse=True):
        log = records.load_json(p)
        if not log.get("dry_run") and not log.get("offline"):
            return log
    return None


def run_status(log: dict | None, today: dt.date) -> dict:
    """What the 'Last checked' line says, including whether the data looks stale at build time."""
    if not log:
        return {"date": None, "stale": True, "checked": 0, "monitored": 0, "unchecked": [], "not_monitored": []}
    finished = dt.date.fromisoformat(log["finished_at"][:10])
    monitored = log.get("monitored_state_count", 0)
    unchecked = log.get("states_not_fully_checked", [])
    return {"date": long_date(log["finished_at"]), "stale": (today - finished).days > STALE_DAYS,
            "checked": monitored - len(unchecked), "monitored": monitored,
            "unchecked": unchecked, "not_monitored": log.get("not_monitored", [])}


# --- Rendering ---------------------------------------------------------------------------

def render(recent: list[dict], history: dict[str, list[dict]], states, last: dict | None,
           out_dir: Path, root: Path, today: dt.date) -> Path:
    """Write out_dir/index.html and copy every saved copy the page links to."""
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html", "j2"]),
                      trim_blocks=True, lstrip_blocks=True)
    env.filters.update(long_date=long_date, rate=rate, pct=pct, change=change_text, doc_label=doc_label,
                       note_html=note_html)
    by_name = sorted(states, key=lambda s: s.name)
    html = env.get_template("index.html.j2").render(
        recent=recent, history=history, states=by_name, status=run_status(last, today),
        products=PRODUCT_NAMES, today=today.isoformat(), repo_url=REPO_URL,
        stale_days=STALE_DAYS, build_date=long_date(today.isoformat()))
    out_dir = Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8", newline="\n")
    _copy_archives(recent, history, out_dir, root)
    return out_dir / "index.html"


def _copy_archives(recent, history, out_dir: Path, root: Path) -> None:
    shown = recent + [r for recs in history.values() for r in recs]
    for path in {r.get("archived_copy") for r in shown} | _table_copies(shown):
        if path and (Path(root) / path).exists():
            target = out_dir / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(root) / path, target)


def _table_copies(shown: list[dict]) -> set[str]:
    """Saved copies named in a rate_table_note (for example a separate rate table)."""
    return {m for r in shown for m in ARCHIVE_PATH.findall(r.get("rate_table_note") or "")}


def build(root: Path, out_dir: Path | None = None, today: dt.date | None = None) -> Path:
    """python -m pfrt build"""
    from pfrt import config
    root = Path(root)
    today = today or dt.date.today()
    recs = records.load_all(root)
    states = config.load_states(root / "config/states.csv")
    return render(select_recent(recs, today), select_history(recs, today), states,
                  last_run(root), out_dir or root / "site", root, today)
