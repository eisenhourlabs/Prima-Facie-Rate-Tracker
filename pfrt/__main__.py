"""Command-line entry point. Run as:  python -m pfrt <command>

  config check                       validate config/*.csv
  check [--dry-run] [--offline] [--states IN,WI] [--include-disabled]
                                     check sources; without --dry-run, save snapshots,
                                     documents, candidates and a run log
  review list [--origin manual]      open candidates
  review show ID                     every field of a candidate or record
  review add --state WI --url URL [--source-id ID] [--title T]
                                     make a candidate from a document by hand
  review confirm ID [--values FILE] [--next-expected YYYY-MM-DD]
                                     confirm (asks for each field if no --values)
  review reject ID --reason "..."
  review amend ID --values FILE --reason "..."
  review retract ID --reason "..."
  validate                           check every confirmed record (plan 7.4)
  notify test                        send a test email if email is configured

Every check run saves a readable summary next to its run log. Email and the
GitHub issue are off until configured; see pfrt/notify.py.

--values FILE is JSON: {"records": [{...record fields...}, ...]} for confirm,
or {...fields to change...} for amend. See CLAUDE.md for the review protocol.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

from pfrt import check, config, detect, notify, records, review


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pfrt", description="Prima Facie Rate Tracker")
    parser.add_argument("--root", default=".", help="repository folder (default: current folder)")
    sub = parser.add_subparsers(dest="command", required=True)

    cfg = sub.add_parser("config", help="work with the config files").add_subparsers(dest="action", required=True)
    chk = cfg.add_parser("check", help="validate states.csv and sources.csv")
    chk.add_argument("--states", default="config/states.csv")
    chk.add_argument("--sources", default="config/sources.csv")

    run = sub.add_parser("check", help="check sources for changes")
    run.add_argument("--dry-run", action="store_true", help="write nothing, send nothing")
    run.add_argument("--offline", action="store_true", help="read saved pages instead of the web")
    run.add_argument("--fixtures", default="", help="folder of saved pages for --offline")
    run.add_argument("--states", default="", help="comma-separated state codes, e.g. IN,WI")
    run.add_argument("--include-disabled", action="store_true",
                     help="also check disabled sources that have a URL (only with --dry-run)")

    rv = sub.add_parser("review", help="review candidates and records").add_subparsers(dest="action", required=True)
    rv.add_parser("list").add_argument("--origin", default="", help="monitor, seed or manual")
    rv.add_parser("show").add_argument("id")
    add = rv.add_parser("add")
    add.add_argument("--state", required=True)
    add.add_argument("--url", required=True)
    add.add_argument("--source-id", default="")
    add.add_argument("--title", default="")
    conf = rv.add_parser("confirm")
    conf.add_argument("id")
    conf.add_argument("--values", default="", help="JSON file with the record values")
    conf.add_argument("--next-expected", default="", help="state's next expected notice date")
    rej = rv.add_parser("reject")
    rej.add_argument("id")
    rej.add_argument("--reason", required=True)
    am = rv.add_parser("amend")
    am.add_argument("id")
    am.add_argument("--values", required=True)
    am.add_argument("--reason", required=True)
    ret = rv.add_parser("retract")
    ret.add_argument("id")
    ret.add_argument("--reason", required=True)

    sub.add_parser("validate", help="validate every confirmed record")
    nt = sub.add_parser("notify", help="notifications").add_subparsers(dest="action", required=True)
    nt.add_parser("test", help="send a test message if email is configured")
    return parser


def cmd_config_check(args, root: Path) -> int:
    try:
        print(config.check(root / args.states, root / args.sources))
    except config.ConfigError as err:
        print(f"Config error: {err}", file=sys.stderr)
        return 1
    return 0


def select_sources(sources, states_arg: str, include_disabled: bool):
    wanted = {s.strip().upper() for s in states_arg.split(",") if s.strip()}
    chosen = [s for s in sources if (not wanted or s.state in wanted)
              and (s.is_enabled or (include_disabled and s.url))]
    return chosen, wanted


def cmd_check(args, root: Path) -> int:
    if args.include_disabled and not args.dry_run:
        print("--include-disabled is only allowed with --dry-run.", file=sys.stderr)
        return 2
    try:
        states = config.load_states(root / "config/states.csv")
        sources = config.load_sources(root / "config/sources.csv", {s.state for s in states})
    except config.ConfigError as err:
        print(f"Config error: {err}", file=sys.stderr)
        return 1
    chosen, wanted = select_sources(sources, args.states, args.include_disabled)
    ctx = check.RunContext(root=root, keywords=detect.load_keywords(root / "config/keywords.csv"),
                           now=dt.datetime.now(dt.timezone.utc).replace(microsecond=0),
                           dry_run=args.dry_run, offline=args.offline,
                           fixture_dir=Path(args.fixtures) if args.fixtures else None)
    mode = "Dry run" if args.dry_run else "Run"
    print(f"{mode} {ctx.run_id}: {len(chosen)} source(s){' (offline)' if args.offline else ''}."
          f"{' Nothing is written.' if args.dry_run else ''}")
    start, started = time.monotonic(), ctx.stamp
    results = check.run(chosen, ctx)
    scope = wanted or {s.state for s in states}
    print_summary(results, sources, scope, time.monotonic() - start)
    log = check.build_run_log(results, sources, scope, ctx, started)
    email = compose_summary(log, results, states, root)
    path = check.write_run_log(log, f"{email.subject}\n\n{email.body}", ctx)
    write_step_summary(email)
    if path:
        print(f"Run log: {path.relative_to(root).as_posix()}")
    if args.dry_run:
        print(f"\n--- Summary that would be saved and sent ---\n{email.subject}\n\n{email.body}")
        return 0
    has_news = bool(log["totals"]["candidates"] or log["states_not_fully_checked"])
    try:
        for line in notify.deliver(email, dict(os.environ), has_news):
            print(f"Notify: {line}")
    except notify.NotifyError as err:
        print(f"Notify failed: {err}", file=sys.stderr)
        return 3
    return 0


def repo_url() -> str:
    """https://github.com/owner/repo when running in GitHub Actions, else ''."""
    server, repo = os.environ.get("GITHUB_SERVER_URL"), os.environ.get("GITHUB_REPOSITORY")
    return f"{server}/{repo}" if server and repo else ""


def compose_summary(log: dict, results, states, root: Path) -> notify.Email:
    from pfrt import candidates as cand_mod
    open_cands = cand_mod.load_all(root)
    new_ids = {cid for r in results for cid in r.candidates_created}
    new = [c for c in open_cands if c["candidate_id"] in new_ids]
    in_scope = [s for s in states if s.state in set(log["states_in_scope"])]
    expected = notify.expected_not_seen(in_scope, records.load_all(root), open_cands, dt.date.today())
    return notify.compose(log, new, expected, len(open_cands), repo_url())


def write_step_summary(email: notify.Email) -> None:
    """In GitHub Actions, show the summary on the run's page."""
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        with open(target, "a", encoding="utf-8") as f:
            f.write(f"## {email.subject}\n\n```\n{email.body}```\n")


def cmd_notify_test() -> int:
    """Send a short test message through whatever channels are configured."""
    email = notify.Email("[PFRT] Test message", "This is a test from the Prima Facie Rate Tracker workflow.\n")
    if not notify.email_configured(dict(os.environ)):
        print("Notify: email not configured (set SMTP_USER, SMTP_APP_PASSWORD and ALERT_TO secrets).")
        return 0
    try:
        notify.send(email, dict(os.environ))
    except notify.NotifyError as err:
        print(f"Notify failed: {err}", file=sys.stderr)
        return 3
    print("Notify: test email sent")
    return 0


def print_summary(results, all_sources, states_in_scope, seconds: float) -> None:
    gaps = check.not_fully_checked(results)
    created = sum(len(r.candidates_created) for r in results)
    findings = sum(len(r.findings) for r in results)
    print(f"\nDone in {seconds:.0f}s. {len(results)} source(s) checked, {findings} finding(s), "
          f"{created} candidate(s) created.")
    print("States not fully checked: " + (", ".join(
        f"{st} ({', '.join(f'{r.source.source_id} {r.status}' for r in rs)})"
        for st, rs in sorted(gaps.items())) or "none"))
    print("Not monitored (no enabled leading source): "
          + (", ".join(check.not_monitored(all_sources, states_in_scope)) or "none"))


def _now() -> str:
    return records.now_utc()


def _load_values(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def cmd_review(args, root: Path) -> int:
    a = args.action
    if a == "list":
        print(review.format_list(review.list_open(root, args.origin)))
    elif a == "show":
        print(review.show(root, args.id))
    elif a == "add":
        cmd_review_add(args, root)
    elif a == "confirm":
        cmd_review_confirm(args, root)
    elif a == "reject":
        print(f"Rejected. Saved as {review.reject(root, args.id, args.reason, _now()).relative_to(root).as_posix()}")
    elif a == "amend":
        rec, issues = review.amend(root, args.id, _load_values(args.values), args.reason, _now())
        print(f"Amended {rec['record_id']}.")
        print_issues(issues)
    elif a == "retract":
        print(f"Retracted {review.retract(root, args.id, args.reason, _now())['record_id']}; status is now rejected.")
    return 0


def cmd_review_add(args, root: Path) -> None:
    source = None
    if args.source_id:
        states = config.load_states(root / "config/states.csv")
        by_id = {s.source_id: s for s in config.load_sources(root / "config/sources.csv", {s.state for s in states})}
        if args.source_id not in by_id:
            raise review.ReviewError(f"no source with id {args.source_id}")
        source = by_id[args.source_id]
    cand = review.add(root, args.state.upper(), args.url, _now(), source, args.title)
    print(f"Created {cand['candidate_id']}; saved copy {cand['archived_copy']}")


def cmd_review_confirm(args, root: Path) -> None:
    if args.values:
        data = _load_values(args.values)
        entries = data["records"]
        next_expected = args.next_expected or data.get("next_notice_expected_by", "")
    else:
        _, _, cand = review.find(root, args.id)
        entries = review.prompt_entries(cand)
        next_expected = args.next_expected or input("Next expected notice date for this state (blank to skip): ").strip()
    written, issues = review.confirm(root, args.id, entries, _now(), next_expected)
    for rec in written:
        print(f"Confirmed {rec['record_id']} (verified: {rec['verified']})")
    print_issues(issues)


def print_issues(issues) -> None:
    for issue in issues:
        print(f"  {issue}")


def cmd_validate(root: Path) -> int:
    confirmed = [r for r in records.load_all(root) if r.get("status") == "confirmed"]
    errors = 0
    for rec in confirmed:
        ctx = records.load_context(root, exclude_id=rec["record_id"])
        issues = records.validate(rec, ctx)
        errors += sum(i.level == "error" for i in issues)
        for issue in issues:
            print(f"{rec['record_id']}: {issue}")
    print(f"{len(confirmed)} confirmed record(s) checked, {errors} error(s).")
    return 1 if errors else 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    try:
        if args.command == "config":
            return cmd_config_check(args, root)
        if args.command == "check":
            return cmd_check(args, root)
        if args.command == "review":
            return cmd_review(args, root)
        if args.command == "validate":
            return cmd_validate(root)
        if args.command == "notify":
            return cmd_notify_test()
    except review.ReviewError as err:
        print(f"Not done: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
