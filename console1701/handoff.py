from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from console1701.config import DEFAULT_HANDOFF_DIR
from console1701.db import json_dumps, utc_now
from console1701.evidence import get_attention_items, get_repo_detail

DEFAULT_TASK = "Review this local evidence and tell me what needs human attention next."
HANDOFF_FILENAME_ATTEMPTS = 10


def _slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    return value.strip("-") or "repo"


def _bullet_list(values: list[str]) -> str:
    if not values:
        return "- None found."
    return "\n".join(f"- {value}" for value in values)


def _handoff_filename(created_at: str, repo_name: str, packet_title: str) -> str:
    title_slug = _slug(packet_title)[:40]
    return f"{created_at[:10]}_{_slug(repo_name)}_{title_slug}_{uuid4().hex[:8]}.md"


def _write_unique_handoff_file(
    handoff_dir: Path,
    *,
    created_at: str,
    repo_name: str,
    packet_title: str,
    markdown: str,
) -> Path:
    for _ in range(HANDOFF_FILENAME_ATTEMPTS):
        path = handoff_dir / _handoff_filename(created_at, repo_name, packet_title)
        try:
            with path.open("x", encoding="utf-8") as handle:
                handle.write(markdown)
        except FileExistsError:
            continue
        return path
    raise FileExistsError(f"Could not reserve a unique handoff packet path in {handoff_dir}")


def build_handoff_markdown(
    detail: dict[str, Any],
    *,
    task: str = DEFAULT_TASK,
    generated_at: str | None = None,
) -> str:
    generated = generated_at or utc_now()
    repo = detail["repo"]
    snapshot = detail.get("snapshot") or {}
    interpretation = detail.get("interpretation") or {}
    test = detail.get("test") or {}
    attention = detail.get("attention") or []
    evidence = interpretation.get("evidence") or {}
    changed_files = evidence.get("changed_files") or snapshot.get("changed_files") or []
    recent_commits = snapshot.get("recent_commits") or []

    attention_text = "\n".join(
        f"- {item['title']}: {item['next_sane_action']}" for item in attention
    ) or "- None open."
    recent_text = "\n".join(
        f"- {commit.get('sha')} {commit.get('time')} {commit.get('subject')}"
        for commit in recent_commits
    ) or "- None found."

    return f"""# console-1701 handoff: {repo['name']}

Generated: {generated}
Repo: {repo['name']}
Path: {repo['path']}

## CONTROLLED_CONTEXT_BEGIN

### Current interpretation

{interpretation.get('meaning') or 'No interpretation exists yet. Run console-1701 scan first.'}

Headline: {interpretation.get('headline') or 'No headline available.'}
State: {interpretation.get('state') or 'Unknown'}
Next sane action: {interpretation.get('next_sane_action') or 'Run a scan or inspect evidence.'}

### Local evidence

Branch: {snapshot.get('branch') or 'unknown'}
Dirty: {'yes' if snapshot.get('is_dirty') else 'no'}
Latest commit: {snapshot.get('commit_sha') or 'unknown'} {snapshot.get('commit_subject') or ''}
Ahead/behind: ahead={snapshot.get('ahead_count')} behind={snapshot.get('behind_count')}

Changed files:

{_bullet_list(changed_files)}

Recent commits:

{recent_text}

Last known test:

Command: {test.get('command') or 'none'}
Result: {test.get('status') or 'unknown'}
Summary: {test.get('summary') or 'No test evidence found.'}

Attention items:

{attention_text}

### Constraints

- Do not delete data.
- Do not rewrite unrelated files.
- Do not run destructive Git commands.
- Do not assume network access.
- Do not invent missing evidence.
- If something is unclear, say what evidence is missing.

## CONTROLLED_CONTEXT_END

## LLM_TASK_BEGIN

{task}

## LLM_TASK_END

## OUTPUT_CONTRACT_BEGIN

Return:

1. Plain-English diagnosis.
2. Evidence you used.
3. Specific files to inspect.
4. Suggested next command or next human action.
5. What you are uncertain about.

Do not return generic advice.

## OUTPUT_CONTRACT_END
"""


def create_handoff_packet(
    conn: sqlite3.Connection,
    config: dict[str, Any],
    *,
    repo_id: int,
    task: str = DEFAULT_TASK,
    title: str | None = None,
) -> dict[str, Any]:
    detail = get_repo_detail(conn, repo_id)
    if not detail:
        raise ValueError(f"Repo id not found: {repo_id}")

    handoff_dir = Path(config.get("_handoff_dir", DEFAULT_HANDOFF_DIR))
    handoff_dir.mkdir(parents=True, exist_ok=True)
    now = utc_now()
    repo_name = detail["repo"]["name"]
    packet_title = title or f"{repo_name} handoff"
    markdown = build_handoff_markdown(detail, task=task, generated_at=now)
    path = _write_unique_handoff_file(
        handoff_dir,
        created_at=now,
        repo_name=repo_name,
        packet_title=packet_title,
        markdown=markdown,
    )

    evidence = {
        "repo": detail["repo"],
        "snapshot": detail.get("snapshot"),
        "interpretation": detail.get("interpretation"),
        "attention": get_attention_items(conn, repo_id=repo_id),
    }
    cursor = conn.execute(
        """
        INSERT INTO handoff_packets (repo_id, created_at, title, path, task, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (repo_id, now, packet_title, str(path), task, json_dumps(evidence)),
    )
    conn.commit()
    return {
        "id": int(cursor.lastrowid),
        "repo_id": repo_id,
        "created_at": now,
        "title": packet_title,
        "path": str(path),
        "task": task,
    }
