from console1701.adapters import cluster_changed_files, infer_adapter, infer_phase


def test_wiki_relative_prompts_and_places_runs_infer_gather_phase():
    assert infer_phase("wiki", ["prompts/start-here.md"]) == "gather"
    assert infer_phase("wiki", ["places/seattle/runs/001.jsonl"]) == "gather"


def test_backslash_paths_are_normalized_for_clusters():
    clusters = cluster_changed_files(
        ["tools\\sqlite\\tests\\test_export.py"],
        adapter="ufo-records",
    )

    assert clusters["primary_area"] == "tools/sqlite/tests"
    assert clusters["phase"] == "test"
    assert clusters["tests_changed"] is True
    assert clusters["structural"] is True


def test_tcl_adapter_uses_exact_repo_name_or_path_component():
    assert infer_adapter("main", "/tmp/TCL/main", []) == "TCL"
    assert infer_adapter("main", "/tmp/tcl-tools/main", []) == "generic"
