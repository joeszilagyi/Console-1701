# Caretaking Log

## 2026-05-03 21:24 PDT - scripts/dev_server.sh serviceability review

- Selected `scripts/dev_server.sh` as the oldest eligible tracked tool/script file after excluding ignored generated artifacts; initial mtime was epoch `1777861238` (`2026-05-03 19:20:38 PDT`).
- Reviewed the file under P1, P3-P7, P9-P15, P17-P22. P2, P8, and P16 did not apply to the selected script/tool file.
- Fixed bootstrap supportability by replacing activation-dependent `python` and `console-1701` calls with explicit `.venv/bin/python` and `.venv/bin/console-1701` calls.
- Added `--check` validation for the venv Python and runnable CLI entry point so broken venv wrappers fail before serving.
- Added concise stderr diagnostics around venv creation, dependency installation, config initialization, and server startup.
- Verified with `bash -n scripts/dev_server.sh`, `scripts/dev_server.sh --help`, `scripts/dev_server.sh --check`, a temp-copy missing-Python failure check, `.venv/bin/ruff check .`, and `.venv/bin/python -m pytest -q`.
