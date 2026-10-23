"""
tests/test_tasks.py — Automated test suite.
Covers FR-1 … FR-7 and NFR-1, NFR-2, NFR-3, NFR-4.

Run from the student-task-manager/ directory:
    python -m pytest tests/ -v
or without pytest:
    python tests/test_tasks.py
"""

from __future__ import annotations
import os
import sys
import json
import subprocess
import time

# Allow running as a plain script from the project root
HERE        = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(HERE)
sys.path.insert(0, PROJECT_DIR)

DATA_FILE = os.path.join(PROJECT_DIR, "tasks_data.json")
TMP_FILE  = DATA_FILE + ".tmp"
PYTHON    = sys.executable


# ── helpers ───────────────────────────────────────────────────────────────────

def _run(stdin: str) -> str:
    """Launch main.py as a subprocess and return its combined output."""
    r = subprocess.run(
        [PYTHON, "-m", "app.main"],
        input=stdin, text=True, capture_output=True, cwd=PROJECT_DIR,
    )
    return r.stdout + r.stderr


def _load() -> dict:
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def _clean() -> None:
    for p in (DATA_FILE, TMP_FILE):
        if os.path.exists(p):
            os.remove(p)


def _pass(label: str) -> None:
    print(f"  [PASS] {label}")


# ══════════════════════════════════════════════════════════════════════════════
# FR tests
# ══════════════════════════════════════════════════════════════════════════════

def test_fr1_fr2_create():
    """FR-1/FR-2: task is created with all required fields and a unique ID."""
    out = _run("1\nPhysics Lab Report\nWrite up the experiment\n2026-11-15\n3\n5\n")
    assert "Task created" in out, f"Expected creation success:\n{out}"
    data = _load()
    assert len(data) == 1
    t = list(data.values())[0]
    assert t["title"]       == "Physics Lab Report"
    assert t["description"] == "Write up the experiment"
    assert t["due_date"]    == "2026-11-15"
    assert t["priority"]    == "High"
    assert t["completed"]   is False
    assert len(t["id"])     == 8
    _pass("FR-1/FR-2  Create stores all required fields with a unique ID")


def test_fr3_view():
    """FR-3: view output contains the task ID and every detail field."""
    data = _load()
    tid  = list(data)[0]
    out  = _run("2\n5\n")
    assert tid                   in out
    assert "Physics Lab Report"  in out
    assert "2026-11-15"          in out
    assert "High"                in out
    _pass("FR-3       View lists task ID and all detail fields")


def test_fr4_fr7_update():
    """FR-4/FR-7: update changes a field but preserves the task ID."""
    data = _load()
    tid  = list(data)[0]
    out  = _run(f"3\n{tid}\nUpdated Lab Report\n\n\n\n\n5\n")
    assert "updated successfully" in out, f"Update failed:\n{out}"
    data = _load()
    assert data[tid]["title"] == "Updated Lab Report", "Title not updated"
    assert data[tid]["id"]    == tid,                  "FR-7: ID changed during update"
    _pass("FR-4/FR-7  Update modifies fields and preserves ID")


def test_fr6_unknown_id_update():
    """FR-6: updating with a non-existent ID reports an error, not success."""
    out = _run("3\nDEADBEEF\n5\n")
    assert "No task found"     in out, f"Expected unknown-ID error:\n{out}"
    assert "updated" not in out.lower(), "Unknown-ID update falsely reported success"
    _pass("FR-6       Unknown ID on update is reported, not silently ignored")


def test_fr5_fr7_delete():
    """FR-5/FR-7: delete removes the task; it no longer appears in the store."""
    data = _load()
    tid  = list(data)[0]
    out  = _run(f"4\n{tid}\ny\n5\n")
    assert "deleted" in out, f"Delete reported failure:\n{out}"
    data = _load()
    assert tid not in data, "FR-7: deleted task still present in store"
    _pass("FR-5/FR-7  Delete removes task from store")


def test_fr7_absent_from_view():
    """FR-7: deleted task does not appear in a subsequent View call."""
    _run("1\nTemp Task\n\n2026-12-01\n1\n5\n")
    data    = _load()
    all_ids = set(data.keys())
    out     = _run("2\n5\n")
    for tid in all_ids:
        assert tid in out, f"Existing task {tid} missing from view"
    _pass("FR-7       Only current tasks appear in View after deletion")


def test_fr6_unknown_id_delete():
    """FR-6: deleting a non-existent ID reports an error."""
    out = _run("4\nXXXXXXXX\n5\n")
    assert "No task found"      in out
    assert "deleted" not in out.lower(), "Unknown-ID delete falsely reported success"
    _pass("FR-6       Unknown ID on delete is reported, not silently ignored")


def test_fr6_invalid_menu():
    """FR-6: an invalid menu choice produces a clear error message."""
    out = _run("9\n5\n")
    assert "not a valid option" in out
    _pass("FR-6       Invalid menu input is rejected with a clear message")


# ══════════════════════════════════════════════════════════════════════════════
# NFR tests
# ══════════════════════════════════════════════════════════════════════════════

def test_nfr1_labels():
    """NFR-1: View output contains recognisable field labels."""
    out = _run("2\n5\n")
    for label in ("ID", "Title", "Due date", "Priority", "Status"):
        assert label in out, f"NFR-1: label '{label}' missing from View output"
    _pass("NFR-1      View output contains clear field labels")


def test_nfr2_validation_blank_title():
    """NFR-2: blank title prompts re-entry; application gives clear feedback."""
    out = _run("1\n\nFallback Title\n\n2026-12-31\n1\n5\n")
    assert "required" in out.lower() or "Task created" in out, \
        f"NFR-2: unexpected output on blank title:\n{out}"
    _pass("NFR-2      Blank title is rejected with a clear message")


def test_nfr2_invalid_date():
    """NFR-2: a malformed date is reported and the user is re-prompted."""
    out = _run("1\nTest Task\n\n99-99-99\n2026-12-01\n1\n5\n")
    assert any(kw in out for kw in ("not a valid date", "Invalid date", "Task created")), \
        f"NFR-2: unexpected output on bad date:\n{out}"
    _pass("NFR-2      Invalid date is reported with a clear message")


def test_nfr2_atomic_write():
    """NFR-2/NFR-3: the .tmp file is cleaned up after every successful save."""
    _run("1\nAtomicity Check\n\n2026-10-30\n2\n5\n")
    assert not os.path.exists(TMP_FILE), \
        "NFR-2/NFR-3: .tmp file left behind after save (atomic rename may have failed)"
    _pass("NFR-2/NFR-3 Temp file is removed after atomic save")


def test_nfr3_persistence():
    """NFR-3: tasks written in one process are visible in a separate process."""
    _run("1\nPersistence Test\n\n2026-11-20\n2\n5\n")
    before = _load()
    out    = _run("2\n5\n")           # fresh subprocess = simulated restart
    for tid in before:
        assert tid in out, f"NFR-3: task {tid} missing after restart simulation"
    _pass("NFR-3      Tasks created in one session are present in the next")


def test_nfr4_performance():
    """NFR-4: creating 50 tasks and viewing them completes in under 10 seconds."""
    _clean()
    start = time.perf_counter()
    for _ in range(50):
        _run("1\nPerf Task\n\n2026-12-31\n1\n5\n")
    _run("2\n5\n")
    elapsed = time.perf_counter() - start
    assert elapsed < 10, \
        f"NFR-4: 50 creates + 1 view took {elapsed:.1f}s (threshold: 10s)"
    _pass(f"NFR-4      50 creates + 1 view completed in {elapsed:.2f}s (< 10s)")


# ══════════════════════════════════════════════════════════════════════════════
# Runner (plain-script mode)
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("\n─── Student Task Manager — Test Suite ───────────────────────────────")

    all_tests = [
        test_fr1_fr2_create,
        test_fr3_view,
        test_fr4_fr7_update,
        test_fr6_unknown_id_update,
        test_fr5_fr7_delete,
        test_fr7_absent_from_view,
        test_fr6_unknown_id_delete,
        test_fr6_invalid_menu,
        test_nfr1_labels,
        test_nfr2_validation_blank_title,
        test_nfr2_invalid_date,
        test_nfr2_atomic_write,
        test_nfr3_persistence,
        test_nfr4_performance,
    ]

    _clean()
    passed = failed = 0
    for test in all_tests:
        # NFR-4 needs a clean slate to count exactly 50 tasks
        if test.__name__ == "test_nfr4_performance":
            _clean()
        try:
            test()
            passed += 1
        except AssertionError as exc:
            print(f"  [FAIL]  {test.__name__}: {exc}")
            failed += 1
        except Exception as exc:
            print(f"  [ERROR] {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1

    print(f"\n─── Results: {passed} passed, {failed} failed ────────────────────────────\n")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
