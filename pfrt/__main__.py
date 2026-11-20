"""Command-line entry point. Run as:  python -m pfrt <command>

Commands available so far:
  python -m pfrt config check
      Load config/*.csv and print a summary or the error.
  python -m pfrt check --dry-run [--offline] [--states IN,WI] [--include-disabled]
      Fetch each enabled source, compare with its last snapshot and print what
      changed. Stage 1: --dry-run is required; nothing is written or sent.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from pfrt import check, config, detect


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pfrt", description="Prima Facie Rate Tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    cfg = sub.add_parser("config", help="work with the config files")
    cfg_sub = cfg.add_subparsers(dest="action", required=True)
    chk = cfg_sub.add_parser("check", help="validate states.csv and sources.csv")
    chk.add_argument("--states", default="config/states.csv", help="path to states.csv")
    chk.add_argument("--sources", default="config/sources.csv", help="path to sources.csv")

    run = sub.add_parser("check", help="check sources for changes")
    run.add_argument("--dry-run", action="store_true", help="write nothing, send nothing")
    run.add_argument("--offline", action="store_true", help="read tests/fixtures/ instead of the web")
    run.add_argument("--states", default="", help="comma-separated state codes, e.g. IN,WI")
    run.add_argument("--include-disabled", action="store_true",
                     help="also check disabled sources that have a URL (for trying a new source)")
    return parser


def cmd_config_check(args) -> int:
    try:
        print(config.check(args.states, args.sources))
    except config.ConfigError as err:
        print(f"Config error: {err}", file=sys.stderr)
        return 1
    return 0


def select_sources(sources, states_arg: str, include_disabled: bool):
    wanted = {s.strip().upper() for s in states_arg.split(",") if s.strip()}
    out = []
    for s in sources:
        if wanted and s.state not in wanted:
            continue
        if s.is_enabled or (include_disabled and s.url):
            out.append(s)
    return out, wanted


def cmd_check(args) -> int:
    if not args.dry_run:
        print("Stage 1 supports only --dry-run. Writing snapshots and candidates arrives in Stage 2.",
              file=sys.stderr)
        return 2
    root = Path(".")
    try:
        states = config.load_states(root / "config/states.csv")
        sources = config.load_sources(root / "config/sources.csv", {s.state for s in states})
    except config.ConfigError as err:
        print(f"Config error: {err}", file=sys.stderr)
        return 1
    keywords = detect.load_keywords(root / "config/keywords.csv")
    chosen, wanted = select_sources(sources, args.states, args.include_disabled)
    print(f"Dry run: {len(chosen)} source(s){' (offline)' if args.offline else ''}. Nothing is written.")
    start = time.monotonic()
    results = check.run(chosen, keywords, root, offline=args.offline)
    print_summary(results, sources, wanted or {s.state for s in states}, time.monotonic() - start)
    return 0


def print_summary(results, all_sources, states_in_scope, seconds: float) -> None:
    gaps = check.not_fully_checked(results)
    monitored = {s.state for s in all_sources if s.is_enabled and s.role == "leading"}
    not_monitored = sorted(states_in_scope - monitored)
    findings = sum(len(r.findings) for r in results)
    print(f"\nDone in {seconds:.0f}s. {len(results)} source(s) checked, {findings} finding(s).")
    print("States not fully checked: " + (", ".join(
        f"{st} ({', '.join(f'{r.source.source_id} {r.status}' for r in rs)})"
        for st, rs in sorted(gaps.items())) or "none"))
    print("Not monitored (no enabled leading source): " + (", ".join(not_monitored) or "none"))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "config":
        return cmd_config_check(args)
    if args.command == "check":
        return cmd_check(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
