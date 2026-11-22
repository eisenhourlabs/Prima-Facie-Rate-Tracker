"""Read and check the configuration files in config/.

Three files are loaded here:
- config/states.csv: one row per state in scope.
- config/sources.csv: one row per web page or document the job watches.
- config/manual_checks.csv: checks made by hand in given months (optional).

Any problem raises ConfigError with the file name, the row (line) number and
the column, so it can be fixed in the CSV by hand.
"""

from __future__ import annotations

import csv
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

# Allowed values, taken from plan section 2.3.
ROLES = {"leading", "lagging"}

# Placeholders a source url may contain, for documents published under a new address
# each period (decision 2026-11-21, Alabama Administrative Monthly). The check replaces
# them with the run date's value before fetching; see resolve_url.
URL_PLACEHOLDERS = {"{prev_month}"}   # the month before the run, as YYYY-MM
WATCH_MODES = {"new_links", "any_change", "new_text"}
YES_NO = {"yes", "no"}

STATE_COLUMNS = [
    "state", "name", "cl", "cd", "iui", "group",
    "cycle_years", "next_notice_expected_by", "notes",
]
SOURCE_COLUMNS = [
    "source_id", "state", "products", "role", "watch_mode", "url", "format",
    "selector", "must_contain", "citation", "enabled", "verification",
    "verified_on", "notes",
]


class ConfigError(Exception):
    """A problem in one of the config CSV files."""


@dataclass(frozen=True)
class State:
    state: str
    name: str
    cl: str
    cd: str
    iui: str
    group: str
    cycle_years: str
    next_notice_expected_by: str
    notes: str


@dataclass(frozen=True)
class Source:
    source_id: str
    state: str
    products: str
    role: str
    watch_mode: str
    url: str
    format: str
    selector: str
    must_contain: str
    citation: str
    enabled: str
    verification: str
    verified_on: str
    notes: str

    @property
    def is_enabled(self) -> bool:
        return self.enabled == "yes"


def resolve_url(url: str, today: dt.date) -> str:
    """Fill in the url placeholders for a run on `today`.

    "{prev_month}" becomes the month before today as YYYY-MM: a run on
    2026-12-03 reads ".../aam/2026-11". A url without placeholders is unchanged.
    """
    if "{prev_month}" in url:
        first = today.replace(day=1)
        prev = first - dt.timedelta(days=1)
        url = url.replace("{prev_month}", f"{prev.year:04d}-{prev.month:02d}")
    return url


def _read_rows(path: Path, required: list[str]) -> list[tuple[int, dict[str, str]]]:
    """Return (line number, row) pairs after checking every required column exists.

    Line numbers count the header as line 1, so the first data row is line 2.
    This matches what VS Code shows when the CSV is opened.
    """
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        missing = [c for c in required if c not in header]
        if missing:
            raise ConfigError(f"{path}: row 1 (header): missing column(s) {', '.join(missing)}")
        rows = []
        for row in reader:
            # More cells than header columns usually means a comma inside an unquoted
            # value (for example a note); the row would be read wrongly, so stop.
            if row.get(None):
                raise ConfigError(f"{path}: row {reader.line_num}: more cells than columns; "
                                  "put double quotes around any value that contains a comma")
            # Strip stray spaces; treat absent trailing cells as empty.
            clean = {k: (v or "").strip() for k, v in row.items() if k is not None}
            rows.append((reader.line_num, clean))
        return rows


def _fail(path: Path, line: int, column: str, message: str) -> ConfigError:
    return ConfigError(f"{path}: row {line}, column '{column}': {message}")


def load_states(path: str | Path) -> list[State]:
    """Load config/states.csv. Raises ConfigError on a missing column or a repeated state."""
    path = Path(path)
    states: list[State] = []
    seen: set[str] = set()
    for line, row in _read_rows(path, STATE_COLUMNS):
        code = row["state"]
        if not code:
            raise _fail(path, line, "state", "state code is blank")
        if code in seen:
            raise _fail(path, line, "state", f"state '{code}' appears more than once")
        seen.add(code)
        states.append(State(**{c: row[c] for c in STATE_COLUMNS}))
    return states


def load_sources(path: str | Path, known_states: set[str]) -> list[Source]:
    """Load config/sources.csv and check each row against the rules in plan Stage 0.

    known_states is the set of state codes from states.csv; every source must
    belong to one of them.
    """
    path = Path(path)
    sources: list[Source] = []
    seen: dict[str, int] = {}  # source_id -> line where first seen
    for line, row in _read_rows(path, SOURCE_COLUMNS):
        _check_source_row(path, line, row, seen, known_states)
        seen[row["source_id"]] = line
        sources.append(Source(**{c: row[c] for c in SOURCE_COLUMNS}))
    return sources


def _check_source_row(path: Path, line: int, row: dict[str, str],
                      seen: dict[str, int], known_states: set[str]) -> None:
    """Raise ConfigError for the first problem found in one sources.csv row."""
    sid = row["source_id"]
    if not sid:
        raise _fail(path, line, "source_id", "source_id is blank")
    if sid in seen:
        raise _fail(path, line, "source_id",
                    f"duplicate source_id '{sid}' (first used on row {seen[sid]})")
    if row["state"] not in known_states:
        raise _fail(path, line, "state", f"state '{row['state']}' is not in states.csv")
    if row["role"] not in ROLES:
        raise _fail(path, line, "role", f"'{row['role']}' is not one of {sorted(ROLES)}")
    if row["watch_mode"] not in WATCH_MODES:
        raise _fail(path, line, "watch_mode",
                    f"'{row['watch_mode']}' is not one of {sorted(WATCH_MODES)}")
    if row["enabled"] not in YES_NO:
        raise _fail(path, line, "enabled", f"'{row['enabled']}' must be 'yes' or 'no'")
    if row["enabled"] == "yes" and not row["url"]:
        raise _fail(path, line, "url", "source is enabled but its url is blank")
    unknown = set(re.findall(r"\{[^}]*\}", row["url"])) - URL_PLACEHOLDERS
    if unknown:
        raise _fail(path, line, "url", f"unknown placeholder {sorted(unknown)}; allowed: {sorted(URL_PLACEHOLDERS)}")


MANUAL_CHECK_COLUMNS = ["state", "months", "what"]


@dataclass(frozen=True)
class ManualCheck:
    """A check made by hand in given months (plan Q11 option A, owner decision 2026-11-21).

    Statute-fixed states change rates by legislation, which no watched page may show
    before the codified text is updated; the run summary lists these checks when due.
    """
    state: str
    months: tuple[int, ...]
    what: str


def load_manual_checks(path: str | Path, known_states: set[str]) -> list[ManualCheck]:
    """Load config/manual_checks.csv (optional: a missing file means no manual checks).

    months is a list of month numbers separated by semicolons, for example "5;9".
    """
    path = Path(path)
    if not path.exists():
        return []
    checks: list[ManualCheck] = []
    for line, row in _read_rows(path, MANUAL_CHECK_COLUMNS):
        if row["state"] not in known_states:
            raise _fail(path, line, "state", f"state '{row['state']}' is not in states.csv")
        try:
            months = tuple(int(m) for m in row["months"].split(";") if m.strip())
        except ValueError:
            raise _fail(path, line, "months", f"'{row['months']}' must be month numbers separated by ';'") from None
        if not months or any(not 1 <= m <= 12 for m in months):
            raise _fail(path, line, "months", f"'{row['months']}' must be month numbers from 1 to 12")
        if not row["what"]:
            raise _fail(path, line, "what", "say what to check")
        checks.append(ManualCheck(row["state"], months, row["what"]))
    return checks


def check(states_path: str | Path, sources_path: str | Path, manual_path: str | Path | None = None) -> str:
    """Load the config files and return the one-line summary for `pfrt config check`."""
    states = load_states(states_path)
    sources = load_sources(sources_path, {s.state for s in states})
    enabled = sum(1 for s in sources if s.is_enabled)
    out = f"{len(states)} states, {len(sources)} sources ({enabled} enabled)"
    if manual_path is not None:
        out += f", {len(load_manual_checks(manual_path, {s.state for s in states}))} manual checks"
    return out
