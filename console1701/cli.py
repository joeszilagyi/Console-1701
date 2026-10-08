from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version

from console1701.config import DEFAULT_CONFIG_PATH, init_config, load_config
from console1701.db import connect_db, init_db, utc_now
from console1701.handoff import DEFAULT_TASK, create_handoff_packet
from console1701.history import (
    history_cutoff,
    history_expired_counts,
    prune_history_batch,
    record_history_prune,
)
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_sources_status
from console1701.scanner import run_scan

CLI_DESCRIPTION = """Local-only Debian machine console.

Commands read local config and write only console-1701 state/config paths unless
the named command explicitly says otherwise. The web server always binds to
127.0.0.1, even if a wider host is requested.
"""

CLI_EPILOG = """Examples:
  console-1701 init-config
  console-1701 scan
  console-1701 serve
  console-1701 handoff --repo-id 1 --task "Review this local repo state."
"""


def _add_config_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        default=None,
        help=f"Config path. Default: {DEFAULT_CONFIG_PATH}",
    )


def _package_version() -> str:
    try:
        return version("console-1701")
    except PackageNotFoundError:
        return "unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="console-1701",
        description=CLI_DESCRIPTION,
        epilog=CLI_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {_package_version()}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init-config",
        help="Create the local config.yml if missing",
        description="Create the console-1701 YAML config without scanning or serving.",
    )
    _add_config_arg(init_parser)
    init_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing config")

    scan_parser = subparsers.add_parser(
        "scan",
        help="Probe the local host, configured repos, and logs once",
        description=(
            "Run one safe local scan. The scan reads local host/repo/log facts and writes the "
            "configured console-1701 SQLite state."
        ),
    )
    _add_config_arg(scan_parser)

    prune_parser = subparsers.add_parser(
        "prune-history",
        help="Preview or prune expired host, repo, test, and log scan history",
        description=(
            "Show rows older than sqlite.history_retention_days. --apply deletes one bounded "
            "batch; --all continues until no expired rows remain. News and attention history "
            "use separate retention rules."
        ),
    )
    _add_config_arg(prune_parser)
    prune_parser.add_argument("--apply", action="store_true", help="Delete expired rows")
    prune_parser.add_argument("--all", action="store_true", help="Process every expired batch")
    prune_parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Rows per table per batch; default is sqlite.history_prune_batch_size (max 10000)",
    )
    prune_parser.add_argument(
        "--vacuum", action="store_true", help="Compact SQLite after --apply (needs free disk space)"
    )

    news_scan_parser = subparsers.add_parser(
        "news-scan",
        help="Ingest configured recent-signal sources once",
        description=(
            "Run one explicit recent-signal ingest pass. Local fixtures are supported; an "
            "allowlisted official HTTPS source may be fetched only with every required config "
            "opt-in. Page loads and host scans never fetch news."
        ),
    )
    _add_config_arg(news_scan_parser)

    news_sources_parser = subparsers.add_parser(
        "news-sources",
        help="List configured recent-signal sources and current policy/health state",
        description=(
            "Read configured recent-signal sources plus their SQLite-backed health/fetch status, "
            "registry metadata, and audit-friendly access details. This command does not fetch "
            "sources."
        ),
    )
    _add_config_arg(news_sources_parser)

    serve_parser = subparsers.add_parser(
        "serve",
        help="Run the local-only web UI on 127.0.0.1",
        description="Serve the console locally. Binding outside 127.0.0.1 is refused.",
    )
    _add_config_arg(serve_parser)
    serve_parser.add_argument("--host", default=None, help="Bind host. Forced to 127.0.0.1.")
    serve_parser.add_argument("--port", type=int, default=None, help="Bind port. Default: 1701.")

    handoff_parser = subparsers.add_parser(
        "handoff",
        help="Create a local Markdown handoff packet",
        description="Write a bounded Markdown handoff packet under console-1701 state.",
    )
    _add_config_arg(handoff_parser)
    handoff_parser.add_argument("--repo-id", type=int, required=True)
    handoff_parser.add_argument("--task", default=DEFAULT_TASK)
    handoff_parser.add_argument("--title", default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-config":
        path = init_config(args.config, overwrite=args.overwrite)
        print(f"Config ready: {path}")
        return 0

    if args.command == "scan":
        result = run_scan(args.config)
        print(
            "Scan {status}: repos_seen={repos_seen} repos_scanned={repos_scanned}".format(
                **result
            )
        )
        if result.get("errors"):
            for error in result["errors"]:
                print(f"- {error}", file=sys.stderr)
        return 0 if result["status"] in {"complete", "capped"} else 1

    if args.command == "prune-history":
        if (args.all or args.vacuum) and not args.apply:
            parser.error("--all and --vacuum require --apply")
        config = load_config(args.config)
        sqlite_cfg = config["sqlite"]
        batch_size = (
            args.batch_size
            if args.batch_size is not None
            else int(sqlite_cfg["history_prune_batch_size"])
        )
        if not 1 <= batch_size <= 10000:
            parser.error("--batch-size must be between 1 and 10000")
        cutoff = history_cutoff(utc_now(), int(sqlite_cfg["history_retention_days"]))
        conn = connect_db(
            config["_db_path"],
            busy_timeout_ms=int(sqlite_cfg.get("busy_timeout_ms", 5000)),
            journal_mode=str(sqlite_cfg.get("journal_mode", "WAL")),
        )
        try:
            init_db(conn)
            before = history_expired_counts(conn, cutoff)
            print(f"History cutoff: {cutoff}")
            print("Expired rows: " + ", ".join(f"{key}={value}" for key, value in before.items()))
            if not args.apply:
                return 0
            deleted = dict.fromkeys(before, 0)
            while True:
                batch = prune_history_batch(
                    conn,
                    cutoff,
                    batch_size=batch_size,
                )
                for key, count in batch.items():
                    deleted[key] += count
                conn.commit()
                if not args.all or not any(batch.values()):
                    break
            record_history_prune(conn, cutoff=cutoff, deleted=deleted)
            conn.commit()
            print("Deleted rows: " + ", ".join(f"{key}={value}" for key, value in deleted.items()))
            if args.vacuum:
                conn.execute("VACUUM")
                print("SQLite vacuum complete.")
            return 0
        finally:
            conn.close()

    if args.command == "news-scan":
        result = run_news_scan(args.config)
        print(
            "News scan {status}: configured_sources={configured_sources} "
            "scanned_sources={scanned_sources} healthy_sources={healthy_sources} "
            "item_count={item_count}".format(**result)
        )
        if result.get("errors"):
            for error in result["errors"]:
                print(f"- {error}", file=sys.stderr)
        return 0 if result["status"] in {"complete", "disabled", "partial"} else 1

    if args.command == "news-sources":
        config = load_config(args.config)
        sqlite_cfg = config.get("sqlite", {})
        with connect_db(
            config["_db_path"],
            busy_timeout_ms=int(sqlite_cfg.get("busy_timeout_ms", 5000)),
            journal_mode=str(sqlite_cfg.get("journal_mode", "WAL")),
        ) as conn:
            init_db(conn)
            statuses = get_news_sources_status(conn, config)
        if not statuses:
            print("No news sources are configured.")
            return 0
        for source in statuses:
            print(
                "{scope} {source_key} enabled={enabled} kind={kind} family={family} "
                "class={source_class} verification={verification} access={access} "
                "policy={policy} health={health} items={item_count}".format(
                    scope=source["scope"],
                    source_key=source["source_key"],
                    enabled="yes" if source["enabled"] else "no",
                    kind=source["kind"],
                    family=source.get("source_family") or "unknown",
                    source_class=source.get("source_class") or "unknown",
                    verification=source.get("verification_status") or "unknown",
                    access=source.get("expected_access_kind") or "unknown",
                    policy=(source.get("policy") or {}).get("policy_state") or "unknown",
                    health=source.get("health_state") or "not_run",
                    item_count=source.get("item_count") or 0,
                )
            )
            print(
                "  note={note}".format(
                    note=source.get("health_message") or "No recent source note recorded."
                )
            )
            print(
                "  last_success={last_success} last_failure={last_failure} "
                "next_eligible={next_eligible} last_fetch={last_fetch}".format(
                    last_success=source.get("last_success_at") or "never",
                    last_failure=source.get("last_failure_at") or "never",
                    next_eligible=source.get("next_eligible_at") or "n/a",
                    last_fetch=(
                        (source.get("latest_fetch_run") or {}).get("finished_at")
                        or (source.get("latest_fetch_run") or {}).get("started_at")
                        or "never"
                    ),
                )
            )
        return 0

    if args.command == "serve":
        import uvicorn

        from console1701.app import create_app

        config = load_config(args.config)
        host = args.host or config["server"]["host"]
        if host != "127.0.0.1":
            print("Refusing to bind outside localhost; using 127.0.0.1.", file=sys.stderr)
            host = "127.0.0.1"
        port = args.port or int(config["server"]["port"])
        app = create_app(args.config)
        uvicorn.run(app, host=host, port=port)
        return 0

    if args.command == "handoff":
        config = load_config(args.config)
        sqlite_cfg = config.get("sqlite", {})
        with connect_db(
            config["_db_path"],
            busy_timeout_ms=int(sqlite_cfg.get("busy_timeout_ms", 5000)),
            journal_mode=str(sqlite_cfg.get("journal_mode", "WAL")),
        ) as conn:
            init_db(conn)
            packet = create_handoff_packet(
                conn,
                config,
                repo_id=args.repo_id,
                task=args.task,
                title=args.title,
            )
        print(packet["path"])
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
