"""Tests for pfrt.config. They use small CSV files written to a temporary folder."""

from pathlib import Path

import pytest

from pfrt import config
from pfrt.__main__ import main

REPO = Path(__file__).resolve().parent.parent
HEADER = ",".join(config.SOURCE_COLUMNS)


def source_line(source_id="ZZ-test", state="ZZ", role="leading",
                watch_mode="new_links", url="https://example.gov/x", enabled="no"):
    """Build one sources.csv data line with the given values and blanks elsewhere."""
    values = {c: "" for c in config.SOURCE_COLUMNS}
    values.update(source_id=source_id, state=state, role=role,
                  watch_mode=watch_mode, url=url, enabled=enabled)
    return ",".join(values[c] for c in config.SOURCE_COLUMNS)


def write(tmp_path: Path, *lines: str, header: str = HEADER) -> Path:
    path = tmp_path / "sources.csv"
    path.write_text("\n".join([header, *lines]) + "\n", encoding="utf-8")
    return path


# --- The real config files -------------------------------------------------

def test_real_config_has_44_states_and_only_fetched_sources_enabled():
    states = config.load_states(REPO / "config/states.csv")
    sources = config.load_sources(REPO / "config/sources.csv", {s.state for s in states})
    assert len(states) == 44
    # Plan Stage 6 acceptance 4: no source is enabled unless it was fetched and verified.
    bad = [s.source_id for s in sources if s.is_enabled and s.verification != "fetched"]
    assert bad == []


def test_cli_config_check_prints_summary(capsys, monkeypatch):
    monkeypatch.chdir(REPO)
    assert main(["config", "check"]) == 0
    assert capsys.readouterr().out.startswith("44 states, ")


# --- Each error named in plan Stage 0 ---------------------------------------

def test_valid_file_loads(tmp_path):
    path = write(tmp_path, source_line(), source_line(source_id="ZZ-two", enabled="yes"))
    assert len(config.load_sources(path, {"ZZ"})) == 2


def test_missing_column(tmp_path):
    path = write(tmp_path, header=HEADER.replace(",must_contain", ""))
    with pytest.raises(config.ConfigError, match="missing column.*must_contain"):
        config.load_sources(path, {"ZZ"})


def test_duplicate_source_id_names_the_row(tmp_path):
    path = write(tmp_path, source_line(), source_line())
    with pytest.raises(config.ConfigError, match=r"row 3, column 'source_id'.*row 2"):
        config.load_sources(path, {"ZZ"})


@pytest.mark.parametrize("kwargs, column", [
    ({"state": "QQ"}, "state"),
    ({"role": "primary"}, "role"),
    ({"watch_mode": "hash"}, "watch_mode"),
    ({"enabled": "Y"}, "enabled"),
    ({"enabled": "yes", "url": ""}, "url"),
])
def test_bad_values_name_row_and_column(tmp_path, kwargs, column):
    path = write(tmp_path, source_line(**kwargs))
    with pytest.raises(config.ConfigError, match=rf"row 2, column '{column}'"):
        config.load_sources(path, {"ZZ"})


def test_disabled_source_may_have_blank_url(tmp_path):
    path = write(tmp_path, source_line(url="", enabled="no"))
    assert config.load_sources(path, {"ZZ"})[0].url == ""


def test_duplicate_state_in_states_csv(tmp_path):
    path = tmp_path / "states.csv"
    blank = "," * (len(config.STATE_COLUMNS) - 2)
    path.write_text(",".join(config.STATE_COLUMNS) + f"\nZZ,Zed{blank}\nZZ,Zed{blank}\n",
                    encoding="utf-8")
    with pytest.raises(config.ConfigError, match=r"row 3, column 'state'"):
        config.load_states(path)


def test_row_with_unquoted_comma_is_refused(tmp_path):
    """A note with an unquoted comma gives the row extra cells; config check must stop."""
    import shutil
    from pfrt import config
    from tests.conftest import REPO
    shutil.copy(REPO / "config" / "states.csv", tmp_path / "states.csv")
    with open(tmp_path / "states.csv", "a", encoding="utf-8") as f:
        f.write("ZZ,Test State,yes,yes,no,notice,3,,A note, with a comma,how it is checked,\n")
    import pytest
    with pytest.raises(config.ConfigError, match="more cells than columns"):
        config.load_states(tmp_path / "states.csv")


# --- Manual checks (Q11 option A) ---------------------------------------------

def test_real_manual_checks_load_and_cover_the_statute_fixed_states():
    states = {s.state for s in config.load_states(REPO / "config/states.csv")}
    checks = config.load_manual_checks(REPO / "config/manual_checks.csv", states)
    assert {"LA", "MS", "MO", "NC"} <= {c.state for c in checks}


def test_manual_checks_file_is_optional(tmp_path):
    assert config.load_manual_checks(tmp_path / "missing.csv", {"LA"}) == []


@pytest.mark.parametrize("row, column", [
    ("ZZ,5;9,check", "state"),
    ("LA,13,check", "months"),
    ("LA,may,check", "months"),
    ("LA,5;9,", "what"),
])
def test_bad_manual_check_names_row_and_column(tmp_path, row, column):
    path = tmp_path / "manual_checks.csv"
    path.write_text("state,months,what\n" + row + "\n", encoding="utf-8")
    with pytest.raises(config.ConfigError, match=f"row 2, column '{column}'"):
        config.load_manual_checks(path, {"LA"})


# --- URL placeholders (decision 2026-11-21) ----------------------------------

@pytest.mark.parametrize("today, expected", [
    ("2026-12-03", "https://example.gov/aam/2026-11"),
    ("2026-12-18", "https://example.gov/aam/2026-11"),
    ("2027-01-03", "https://example.gov/aam/2026-12"),   # January reads December of the year before
    ("2026-03-01", "https://example.gov/aam/2026-02"),
])
def test_prev_month_placeholder(today, expected):
    import datetime as dt
    assert config.resolve_url("https://example.gov/aam/{prev_month}", dt.date.fromisoformat(today)) == expected


def test_url_without_placeholder_is_unchanged():
    import datetime as dt
    url = "https://example.gov/x?a=1"
    assert config.resolve_url(url, dt.date(2026, 12, 3)) == url


def test_prev_month_placeholder_is_accepted(tmp_path):
    path = write(tmp_path, source_line(url="https://example.gov/aam/{prev_month}"))
    assert config.load_sources(path, {"ZZ"})[0].url.endswith("{prev_month}")


def test_unknown_placeholder_is_refused(tmp_path):
    path = write(tmp_path, source_line(url="https://example.gov/aam/{month}"))
    with pytest.raises(config.ConfigError, match="placeholder"):
        config.load_sources(path, {"ZZ"})
