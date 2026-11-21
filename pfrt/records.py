"""Records: ids, percent change, validation, and reading/writing JSON (plan 2.2, 7.4).

A record is one state, one product, one effective date. Confirmed and rejected
records live in data/records/{state}/{id}.json. JSON is written with two-space
indentation and sorted keys so Git diffs are easy to read.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

PRODUCTS = ("CL", "CD", "IUI")
CHANGE_TYPES = ("change", "no_change", "initial")
EARLIEST_EFFECTIVE = dt.date(1990, 1, 1)
# A "rates in force" record (change_type initial) is dated when the rule text in force took
# effect, which can be long before the 15-year window (Kansas 1988, Delaware 1971).
EARLIEST_IN_FORCE = dt.date(1950, 1, 1)


# --- JSON files -----------------------------------------------------------------

def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: str | Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")


def records_dir(root: Path) -> Path:
    return Path(root) / "data" / "records"


def record_path(root: Path, state: str, record_id: str) -> Path:
    return records_dir(root) / state / f"{record_id}.json"


def load_all(root: Path) -> list[dict]:
    """Every record file (confirmed and rejected), sorted by path."""
    return [load_json(p) for p in sorted(records_dir(root).glob("*/*.json"))]


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- Ids and arithmetic -----------------------------------------------------------

def pct_change(old: float | None, new: float | None, same_basis: bool) -> float | None:
    """round((new - old) / old * 100, 1), or None when it cannot be computed fairly.

    None when old is missing or zero, new is missing, or the bases differ.
    Example: pct_change(0.50, 0.45, True) == -10.0
    """
    if old is None or new is None or old == 0 or not same_basis:
        return None
    return round((new - old) / old * 100, 1)


def make_id(state: str, product: str, effective_date: str, existing_ids: set[str] | list[str]) -> str:
    """{state}-{product}-{effective_date}-{n}; n starts at 1 and rises only on a clash."""
    n = 1
    while f"{state}-{product}-{effective_date}-{n}" in set(existing_ids):
        n += 1
    return f"{state}-{product}-{effective_date}-{n}"


def fill_pct_changes(rate_items: list[dict]) -> list[dict]:
    """Set pct_change on each rate item. An item may give old_basis when the old
    rate was quoted on a different basis; then pct_change is None."""
    for item in rate_items:
        same = item.get("old_basis") in (None, "", item.get("basis"))
        item["pct_change"] = pct_change(item.get("old_rate"), item.get("new_rate"), same)
    return rate_items


# --- Verified flag ------------------------------------------------------------------

def load_official_domains(path: str | Path) -> set[str]:
    with open(path, encoding="utf-8", newline="") as f:
        return {r["domain"].strip().lower() for r in csv.DictReader(f) if r["domain"].strip()}


def is_official(url: str, domains: set[str]) -> bool:
    """True if the URL's host is a listed domain or a subdomain of one."""
    host = urlsplit(url).hostname or ""
    return any(host == d or host.endswith("." + d) for d in domains)


def is_verified(record: dict, domains: set[str], root: Path) -> bool:
    """Plan 2.2: official source domain and a saved copy that exists."""
    copy = record.get("archived_copy") or ""
    return bool(copy) and (Path(root) / copy).exists() and is_official(record.get("source_url", ""), domains)


# --- Validation (plan 7.4) -----------------------------------------------------------

@dataclass(frozen=True)
class Issue:
    level: str      # "error" blocks; "warning" is listed
    field: str
    message: str

    def __str__(self) -> str:
        return f"{self.level.upper()}: {self.field}: {self.message}"


@dataclass
class Context:
    """What validation needs to know beyond the record itself."""
    states: set[str]
    official_domains: set[str]
    existing: list[dict]                 # other records, to find duplicates and the previous rate
    build_date: dt.date
    plausibility: list[tuple[str, list[str], float, float]]


def load_plausibility(path: str | Path) -> list[tuple[str, list[str], float, float]]:
    """config/plausibility.csv rows as (product, terms that must all appear in the basis, low, high).

    A blank product applies to every product; a blank basis_contains matches any basis.
    Rows naming a product are returned first, so they win over the general rows.
    Example row: IUI, (no terms), 0.50, 10.00 checks every IUI rate.
    """
    with open(path, encoding="utf-8", newline="") as f:
        rows = [((r.get("product") or "").strip().upper(),
                 [t.strip().lower() for t in r["basis_contains"].split(";") if t.strip()],
                 float(r["low"]), float(r["high"])) for r in csv.DictReader(f)]
    return sorted(rows, key=lambda row: row[0] == "")


def load_context(root: Path, exclude_id: str = "") -> Context:
    from pfrt import config
    root = Path(root)
    states = {s.state for s in config.load_states(root / "config/states.csv")}
    existing = [r for r in load_all(root) if r.get("record_id") != exclude_id]
    return Context(states, load_official_domains(root / "config/official_domains.csv"),
                   existing, dt.date.today(), load_plausibility(root / "config/plausibility.csv"))


def _plus_years(d: dt.date, years: int) -> dt.date:
    """Same day `years` later; 29 February becomes 28 February in a non-leap year."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)


def _date(value) -> dt.date | None:
    try:
        return dt.date.fromisoformat(value) if isinstance(value, str) and len(value) == 10 else None
    except ValueError:
        return None


def validate(record: dict, ctx: Context) -> list[Issue]:
    """Every check in plan 7.4 except the live HTTP 200 check (done by the link check, Stage 8)."""
    issues = _check_basics(record, ctx) + _check_dates(record, ctx) + _check_source(record, ctx)
    issues += _check_rates(record, ctx) + _check_history(record, ctx)
    summary = record.get("summary") or ""
    if not 20 <= len(summary) <= 600:
        issues.append(Issue("warning", "summary", f"length {len(summary)}; expected 20 to 600 characters"))
    return issues


def _check_basics(r: dict, ctx: Context) -> list[Issue]:
    out = []
    if r.get("state") not in ctx.states:
        out.append(Issue("error", "state", f"'{r.get('state')}' is not in states.csv"))
    if r.get("product") not in PRODUCTS:
        out.append(Issue("error", "product", f"'{r.get('product')}' must be one of {', '.join(PRODUCTS)}"))
    if r.get("change_type") not in CHANGE_TYPES:
        out.append(Issue("error", "change_type", f"'{r.get('change_type')}' must be one of {', '.join(CHANGE_TYPES)}"))
    return out


def _check_dates(r: dict, ctx: Context) -> list[Issue]:
    out = []
    eff = _date(r.get("effective_date"))
    if eff is None:
        out.append(Issue("error", "effective_date", f"'{r.get('effective_date')}' is not a real YYYY-MM-DD date"))
    else:
        earliest = EARLIEST_IN_FORCE if r.get("change_type") == "initial" else EARLIEST_EFFECTIVE
        if not earliest <= eff <= _plus_years(ctx.build_date, 3):
            out.append(Issue("error", "effective_date",
                             f"{eff} is outside {earliest.isoformat()} to build date plus 3 years"))
    comm = r.get("date_communicated")
    if comm:
        c = _date(comm)
        if c is None:
            out.append(Issue("error", "date_communicated", f"'{comm}' is not a real YYYY-MM-DD date"))
        elif eff and c > eff:
            out.append(Issue("warning", "date_communicated", f"{c} is later than the effective date {eff}"))
    return out


def _check_source(r: dict, ctx: Context) -> list[Issue]:
    url = r.get("source_url") or ""
    if not url:
        return [Issue("error", "source_url", "missing; write NONE if no public source is known")]
    if url == "NONE":
        return [] if r.get("verified") is False else [Issue("error", "verified", "must be false when source_url is NONE")]
    if not is_official(url, ctx.official_domains):
        return [Issue("warning", "source_url", "host is not in official_domains.csv; record stays unverified")]
    return []


def _check_rates(r: dict, ctx: Context) -> list[Issue]:
    out = []
    items = r.get("rate_items") or []
    if r.get("change_type") != "no_change" and not items:
        out.append(Issue("error", "rate_items", "at least one rate item is required unless change_type is no_change"))
    for i, item in enumerate(items, 1):
        out += _check_item(i, item, ctx, r.get("product") or "")
    return out


def _check_item(i: int, item: dict, ctx: Context, product: str = "") -> list[Issue]:
    out, where = [], f"rate_items[{i}]"
    for key in ("old_rate", "new_rate"):
        v = item.get(key)
        if v is not None and (not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0):
            out.append(Issue("error", f"{where}.{key}", f"'{v}' must be a number greater than 0"))
    if item.get("new_rate") is None:
        out.append(Issue("error", f"{where}.new_rate", "missing"))
    basis = (item.get("basis") or "").lower()
    if not basis:
        out.append(Issue("error", f"{where}.basis", "required when a rate is given"))
    new = item.get("new_rate")
    # The first range that fits this product and basis is the one used.
    for prod, terms, low, high in ctx.plausibility:
        if basis and prod in ("", product) and all(t in basis for t in terms):
            if isinstance(new, (int, float)) and not isinstance(new, bool) and not low <= new <= high:
                out.append(Issue("warning", f"{where}.new_rate",
                                 f"{new} is outside the plausible range {low} to {high} for {product or 'this product'}, '{basis}'"))
            break
    pct = item.get("pct_change")
    if pct is not None and abs(pct) > 50:
        out.append(Issue("warning", f"{where}.pct_change", f"{pct}% is a change of more than 50%"))
    return out


def _check_history(r: dict, ctx: Context) -> list[Issue]:
    """Duplicate check and the continuity check against the previous record."""
    out = []
    same = [x for x in ctx.existing if x.get("status") == "confirmed"
            and (x.get("state"), x.get("product")) == (r.get("state"), r.get("product"))]
    if any(x.get("effective_date") == r.get("effective_date") for x in same):
        out.append(Issue("error", "effective_date", "a confirmed record already exists for this state, product and effective date"))
    earlier = sorted((x for x in same if (x.get("effective_date") or "") < (r.get("effective_date") or "")),
                     key=lambda x: x["effective_date"])
    if earlier:
        prev = {(i.get("plan"), i.get("basis")): i.get("new_rate") for i in earlier[-1].get("rate_items", [])}
        for i, item in enumerate(r.get("rate_items") or [], 1):
            key = (item.get("plan"), item.get("basis"))
            if key in prev and item.get("old_rate") != prev[key]:
                out.append(Issue("warning", f"rate_items[{i}].old_rate",
                                 f"{item.get('old_rate')} differs from {prev[key]} in {earlier[-1].get('record_id')}"))
    return out
