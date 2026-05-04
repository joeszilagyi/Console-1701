from __future__ import annotations

from typing import Any

CODEX_HINT = "codex"


def _event_mentions_codex(event: dict[str, Any]) -> bool:
    fields = [
        event.get("source"),
        event.get("type"),
        event.get("category"),
        event.get("message"),
    ]
    return any(CODEX_HINT in str(value).lower() for value in fields if value is not None)


def codex_activity_hint(
    snapshot: dict[str, Any],
    log_events: list[dict[str, Any]] | None = None,
) -> str | None:
    """Return cautious local-only wording for likely Codex activity.

    This is a heuristic over local Git/log evidence, not proof and not a call
    into Codex internals or any external service.
    """
    events = log_events or []
    changed = snapshot.get("changed_files") or []
    clusters = snapshot.get("path_clusters") or {}
    commit_subject = (snapshot.get("commit_subject") or "").lower()
    logs_mention_codex = any(_event_mentions_codex(event) for event in events)
    commit_mentions_codex = CODEX_HINT in commit_subject
    clustered_dirty = bool(snapshot.get("is_dirty") and clusters.get("coherent") and changed)

    if logs_mention_codex or commit_mentions_codex:
        return "Codex appears to have worked here. This is a detected pattern, not proof."
    if clustered_dirty and clusters.get("changed_count", 0) >= 2:
        return "This looks like a coherent agent pass. This is a detected pattern, not proof."
    return None
