from __future__ import annotations

import argparse
import sys

from console1706.config import DEFAULT_CONFIG_PATH, init_config, load_config
from console1706.db import connect_db, init_db
from console1706.handoff import DEFAULT_TASK, create_handoff_packet
from console1706.scanner import run_scan


def _add_config_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        default=None,
        help=f"Config path. Default: {DEFAULT_CONFIG_PATH}",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="console-1706")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-config", help="Create config.yml if missing")
    _add_config_arg(init_parser)
    init_parser.add_argument("--overwrite", action="store_true", help="Overwrite existing config")

    scan_parser = subparsers.add_parser("scan", help="Scan configured and discovered local repos")
    _add_config_arg(scan_parser)

    serve_parser = subparsers.add_parser("serve", help="Run the local web UI")
    _add_config_arg(serve_parser)
    serve_parser.add_argument("--host", default=None, help="Bind host. Forced to 127.0.0.1.")
    serve_parser.add_argument("--port", type=int, default=None, help="Bind port. Default: 1706.")

    handoff_parser = subparsers.add_parser("handoff", help="Create a Markdown handoff packet")
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
