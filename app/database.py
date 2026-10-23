"""
database.py — JSON persistence layer.

NFR-2  Saves are atomic: write to a .tmp file then rename so a crash
       mid-write cannot corrupt the live data file.
NFR-3  Tasks written to disk survive process restarts.
NFR-5  Data stays on the local filesystem; no network calls are made.
"""

from __future__ import annotations
import json
import os
from app.models import Task

# ── file paths ────────────────────────────────────────────────────────────────
_BASE_DIR  = os.path.join(os.path.dirname(__file__), "..")   # project root
DATA_FILE  = os.path.normpath(os.path.join(_BASE_DIR, "tasks_data.json"))
_TMP_FILE  = DATA_FILE + ".tmp"


# ── public API ────────────────────────────────────────────────────────────────

def load_all() -> dict[str, Task]:
    """
    Load all tasks from disk and return them as {id: Task}.

    Returns an empty dict when the data file does not exist yet.
    Raises RuntimeError if the file exists but cannot be read or parsed,
    so the caller can surface the error without silently losing data (NFR-2).
    """
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as fh:
            raw: dict = json.load(fh)

        if not isinstance(raw, dict):
            raise ValueError("Top-level value is not a JSON object.")

        tasks: dict[str, Task] = {}
        for key, record in raw.items():
            if not isinstance(record, dict):
                raise ValueError(f"Record '{key}' is not a JSON object.")
            task = Task.from_dict(record)
            if task.id != key:
                raise ValueError(
                    f"Key '{key}' does not match task ID '{task.id}'."
                )
            tasks[key] = task

        return tasks

    except (json.JSONDecodeError, ValueError, OSError) as exc:
        raise RuntimeError(
            f"Could not read task data from '{DATA_FILE}': {exc}\n"
            "  The file may be corrupt. Rename or delete it to start fresh."
        ) from exc


def save_all(tasks: dict[str, Task]) -> None:
    """
    Atomically persist all tasks to disk (NFR-2 / NFR-3).

    Writes to a .tmp file first, then renames it over the real file.
    A crash mid-write therefore cannot leave the data file half-written.
    Raises RuntimeError on any I/O failure.
    """
    payload = {tid: task.to_dict() for tid, task in tasks.items()}
    try:
        with open(_TMP_FILE, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        os.replace(_TMP_FILE, DATA_FILE)    # atomic on all supported platforms
    except OSError as exc:
        raise RuntimeError(
            f"Could not save task data: {exc}\n"
            "  Your changes have NOT been saved."
        ) from exc


def get_task(task_id: str) -> Task | None:
    """Return the Task with the given ID, or None if not found."""
    return load_all().get(task_id.upper())


def save_task(task: Task) -> None:
    """Insert or overwrite a single task, leaving all others unchanged."""
    tasks = load_all()
    tasks[task.id] = task
    save_all(tasks)


def delete_task(task_id: str) -> bool:
    """
    Remove the task with the given ID.
    Returns True if it existed and was removed, False if it was not found.
    """
    tasks = load_all()
    if task_id not in tasks:
        return False
    del tasks[task_id]
    save_all(tasks)
    return True
