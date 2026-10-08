"""Pure browser-side sensor rules, exercised without host metrics or page loads."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RULES = Path(__file__).resolve().parents[1] / "console1701/static/live_rules.js"


def evaluate(rule: str, values: dict) -> dict:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is unavailable for browser-side rule tests")
    script = (
        "const r=require(process.argv[1]); const v=JSON.parse(process.argv[2]); "
        "console.log(JSON.stringify(r[process.argv[3]](v)));"
    )
    result = subprocess.run(
        [node, "-e", script, str(RULES), json.dumps(values), rule],
        capture_output=True,
        check=True,
        text=True,
        timeout=5,
    )
    return json.loads(result.stdout)


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (
            {
                "cpu": 74.9,
                "loadPerCore": 0.9,
                "memoryAvailable": 15,
                "memoryPsi": 9.9,
                "cpuPsi": 19.9,
            },
            "ok",
        ),
        ({"cpu": 75}, "warning"),
        ({"cpu": 90}, "critical"),
        ({"loadPerCore": 1}, "warning"),
        ({"loadPerCore": 1.5}, "critical"),
        ({"memoryAvailable": 14.9}, "warning"),
        ({"memoryAvailable": 4.9}, "critical"),
        ({"memoryPsi": 10}, "warning"),
        ({"memoryPsi": 30}, "critical"),
        ({"cpuPsi": 20}, "warning"),
        ({"cpu": None, "memoryAvailable": None, "memoryPsi": "invalid"}, "ok"),
    ],
)
def test_cpu_ram_boundaries(values: dict, expected: str) -> None:
    result = evaluate("cpuRam", values)
    assert result["state"] == expected
    assert result["thresholds"]["cpu"]["critical"] == 90


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ({"rootUsed": 84.9, "homeUsed": 89.9, "ioPsi": 9.9}, "ok"),
        ({"rootUsed": 85}, "warning"),
        ({"rootUsed": 95}, "critical"),
        ({"homeUsed": 90}, "warning"),
        ({"homeUsed": 95}, "critical"),
        ({"ioPsi": 10}, "warning"),
        ({"ioPsi": 30}, "critical"),
        ({"rootUsed": None, "homeUsed": "invalid"}, "ok"),
    ],
)
def test_filesystem_boundaries(values: dict, expected: str) -> None:
    assert evaluate("filesystem", values)["state"] == expected


def test_rules_load_before_main_script() -> None:
    template = (RULES.parents[1] / "templates/index.html").read_text()
    assert template.index("/static/live_rules.js") < template.index("/static/app.js")
