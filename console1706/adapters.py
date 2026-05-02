from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from pathlib import Path

IGNORE_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "vendor",
    "archive",
}

CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".rs",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".java",
    ".sql",
    ".sh",
}

TEST_MARKERS = ("/tests/", "test_", "_test.", ".test.", ".spec.")
STRUCTURAL_MARKERS = (
    "schema",
    "migrations",
    "exporters",
    "importers",
    "export_profiles",
    "tools/sqlite",
)


def safe_repo_name(path: str | Path) -> str:
    return Path(path).expanduser().resolve().name


def path_parts(path: str) -> list[str]:
    return [part for part in Path(path).parts if part not in ("", ".")]


def infer_adapter(repo_name: str, repo_path: str, changed_files: Iterable[str]) -> str:
    name = repo_name.lower()
    path = str(repo_path).lower()
    changed = "\n".join(changed_files).lower()
    if (
        name == "wiki"
        or path.endswith("/wiki")
        or "places/" in changed
        or "ufo-actions.log" in changed
    ):
        return "wiki"
    if name == "ufo-records" or "tools/sqlite" in changed or "schema_profiles.json" in changed:
        return "ufo-records"
    if name == "tcl" or "/tcl" in path:
        return "TCL"
    return "generic"


def infer_phase(adapter: str, changed_files: Iterable[str]) -> str:
    lowered = [path.lower() for path in changed_files]
    joined = "\n".join(lowered)
    if not lowered:
        return "idle"

    if adapter == "wiki":
        if "/prompts/" in joined or "/places/" in joined and "/runs/" in joined:
            return "gather"
        if "/state/" in joined or ".jsonl" in joined:
            return "verify"
        if "export" in joined:
            return "export"
        return "review"

    if adapter == "ufo-records":
        if "schema" in joined:
            return "schema"
        if "import" in joined:
            return "import"
        if "export" in joined or "bibliography" in joined:
            return "export"
        if any(_is_test_file(path) for path in lowered):
            return "test"
        if any(path.endswith((".md", ".rst", ".txt")) for path in lowered):
            return "docs"
        return "review"

    if adapter == "TCL":
        if "constraints" in joined:
            return "constraints"
        if any(_is_test_file(path) for path in lowered):
            return "tests"
        if any(path.endswith((".md", ".rst", ".txt")) for path in lowered):
            return "docs"
        return "concept"

    if any(_is_test_file(path) for path in lowered):
        return "test"
    if any(path.endswith((".md", ".rst", ".txt")) for path in lowered):
        return "docs"
    return "review"


def _known_area(path: str) -> str:
    lowered = path.lower()
    if "tools/sqlite/exporters" in lowered or "bibliography" in lowered:
        return "tools/sqlite/exporters"
    if "tools/sqlite/tests" in lowered:
        return "tools/sqlite/tests"
    if "tools/sqlite" in lowered:
        return "tools/sqlite"
    if "exporters" in lowered:
        return "exporters"
    if "importers" in lowered:
        return "importers"
    if "migrations" in lowered:
        return "migrations"
    if "schema" in lowered:
        return "schema"
    if "places/" in lowered and "/runs/" in lowered:
        return "Places/runs"
    if "places/" in lowered and "/state/" in lowered:
        return "Places/state"
    if "prompts/" in lowered:
        return "prompts"
    parts = path_parts(path)
    if len(parts) >= 2:
        return "/".join(parts[:2])
    if parts:
        return parts[0]
    return "root"


def _is_test_file(path: str) -> bool:
    normalized = "/" + path.lower().replace("\\", "/")
    return any(marker in normalized for marker in TEST_MARKERS)


def _is_code_file(path: str) -> bool:
    return Path(path).suffix.lower() in CODE_EXTENSIONS


def _is_structural_file(path: str) -> bool:
    lowered = path.lower().replace("\\", "/")
    return any(marker in lowered for marker in STRUCTURAL_MARKERS)


def cluster_changed_files(changed_files: list[str], adapter: str = "generic") -> dict[str, object]:
    top_level = Counter()
    second_level = Counter()
    extensions = Counter()
    known_areas = Counter()

    for file_path in changed_files:
        parts = path_parts(file_path)
        top_level[parts[0] if parts else "root"] += 1
        second_key = "/".join(parts[:2]) if len(parts) >= 2 else (parts[0] if parts else "root")
        second_level[second_key] += 1
        extensions[Path(file_path).suffix.lower() or "[none]"] += 1
        known_areas[_known_area(file_path)] += 1

    count = len(changed_files)
    primary_area, primary_count = ("none", 0)
    if known_areas:
        primary_area, primary_count = known_areas.most_common(1)[0]
    coherent = bool(count and (primary_count / count >= 0.6 or count <= 3))
    if count > 8 and len(known_areas) > 5:
        coherent = False

    return {
        "changed_count": count,
        "top_level": top_level.most_common(),
        "second_level": second_level.most_common(),
        "extensions": extensions.most_common(),
        "known_areas": known_areas.most_common(),
        "primary_area": primary_area,
        "primary_count": primary_count,
        "coherent": coherent,
        "structural": any(_is_structural_file(path) for path in changed_files),
        "tests_changed": any(_is_test_file(path) for path in changed_files),
        "code_changed": any(_is_code_file(path) for path in changed_files),
        "phase": infer_phase(adapter, changed_files),
        "adapter": adapter,
    }


def is_structural_file(path: str) -> bool:
    return _is_structural_file(path)


def is_test_file(path: str) -> bool:
    return _is_test_file(path)


def is_code_file(path: str) -> bool:
    return _is_code_file(path)
