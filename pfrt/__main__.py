"""Command-line entry point. Run as:  python -m pfrt <command>

Commands available so far:
  python -m pfrt config check     load config/*.csv and print a summary or the error
"""

from __future__ import annotations

import argparse
import sys

from pfrt import config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pfrt", description="Prima Facie Rate Tracker")
    sub = parser.add_subparsers(dest="command", required=True)

    cfg = sub.add_parser("config", help="work with the config files")
    cfg_sub = cfg.add_subparsers(dest="action", required=True)
    chk = cfg_sub.add_parser("check", help="validate states.csv and sources.csv")
    chk.add_argument("--states", default="config/states.csv", help="path to states.csv")
    chk.add_argument("--sources", default="config/sources.csv", help="path to sources.csv")

    args = parser.parse_args(argv)

    if args.command == "config" and args.action == "check":
        try:
            print(config.check(args.states, args.sources))
        except config.ConfigError as err:
            print(f"Config error: {err}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
