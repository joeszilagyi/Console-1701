from __future__ import annotations

from typing import Any


def codex_activity_hint(
    snapshot: dict[str, Any],
    log_events: list[dict[str, Any]] | None = None,
) -> str | None:
    """Return careful wording for likely Codex activity without depending on Codex internals."""
    events = log_events or []
    changed = snapshot.get("changed_files") or []
    clusters = snapshot.get("path_clusters") or {}
    commit_subject = (snapshot.get("commit_subject") or "").lower()
    logs_mention_codex = any("codex" in (event.get("message") or "").lower() for event in events)
    commit_mentions_codex = "codex" in commit_subject
    clustered_dirty = bool(snapshot.get("is_dirty") and clusters.get("coherent") and changed)

    if logs_mention_codex or commit_mentions_codex:
        return "Codex appears to have worked here. This is a detected pattern, not proof."
    if clustered_dirty and clusters.get("changed_count", 0) >= 2:
        return "This looks like a coherent agent pass. This is a detected pattern, not proof."
    return None
