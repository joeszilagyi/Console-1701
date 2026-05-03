from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version

from console1706.config import DEFAULT_CONFIG_PATH, init_config, load_config
from console1706.db import connect_db, init_db
from console1706.handoff import DEFAULT_TASK, create_handoff_packet
from console1706.scanner import run_scan

CLI_DESCRIPTION = """Local-only Debian machine console.

Commands read local config and write only console-1706 state/config paths unless
the named command explicitly says otherwise. The web server always binds to
127.0.0.1, even if a wider host is requested.
"""

CLI_EPILOG = """Examples:
  console-1706 init-config
  console-1706 scan
  console-1706 serve
  console-1706 handoff --repo-id 1 --task "Review this local repo state."
"""


def _add_config_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        default=None,
        help=f"Config path. Default: {DEFAULT_CONFIG_PATH}",
    )


def _package_version() -> str:
    try:
        return version("console-1706")
    except PackageNotFoundError:
        return "unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="console-1706",
        description=CLI_DESCRIPTION,
        epilog=CLI_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {_package_version()}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init-config",
        help="Create the local config.yml if missing",
        description="Create the console-1706 YAML config without scanning or serving.",
    )
    _add_config_arg(init_parser)
    init_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing config")

    scan_parser = subparsers.add_parser(
        "scan",
        help="Probe the local host, configured repos, and logs once",
        description=(
            "Run one safe local scan. The scan reads local host/repo/log facts and writes the "
            "configured console-1706 SQLite state."
        ),
    )
    _add_config_arg(scan_parser)

    serve_parser = subparsers.add_parser(
        "serve",
        help="Run the local-only web UI on 127.0.0.1",
        description="Serve the console locally. Binding outside 127.0.0.1 is refused.",
    )
    _add_config_arg(serve_parser)
    serve_parser.add_argument("--host", default=None, help="Bind host. Forced to 127.0.0.1.")
    serve_parser.add_argument("--port", type=int, default=None, help="Bind port. Default: 1706.")

    handoff_parser = subparsers.add_parser(
        "handoff",
        help="Create a local Markdown handoff packet",
        description="Write a bounded Markdown handoff packet under console-1706 state.",
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

    if args.command == "serve":
        import uvicorn

        from console1706.app import create_app

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
