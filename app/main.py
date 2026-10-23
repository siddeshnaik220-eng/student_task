"""
main.py — CLI entry point for the Student Academic Task Manager.

Run with:
    python -m app.main          (from the student-task-manager/ directory)
    python app/main.py

Covers FR-1 … FR-7 and NFR-1 … NFR-5.
"""

from __future__ import annotations
from app.models import Task, PRIORITIES
from app import database as db


# ══════════════════════════════════════════════════════════════════════════════
# UI helpers                                                              NFR-1
# ══════════════════════════════════════════════════════════════════════════════

def _err(msg: str)  -> None: print(f"\n  [!] {msg}")
def _ok(msg: str)   -> None: print(f"\n  ✔  {msg}")
def _section(title: str) -> None:
    print(f"\n── {title} {'─' * max(0, 42 - len(title))}")


def _confirm(message: str) -> bool:
    """Yes/No prompt; default answer is No (the safe choice)."""
    return input(f"\n  {message} [y/N]: ").strip().lower() == "y"


# ── field-level prompts ───────────────────────────────────────────────────────

def _ask_title(current: str = "") -> str:
    hint = f"current: {current}" if current else "required"
    while True:
        raw = input(f"  Title [{hint}]: ").strip()
        value = raw or current
        if not value:
            _err("Title is required and cannot be blank.")
            continue
        if len(value) > 120:
            _err(f"Title is too long ({len(value)}/120 chars).")
            continue
        return value


def _ask_description(current: str = "") -> str:
    hint = f"current: {current[:40]}…" if current else "optional — press Enter to skip"
    raw = input(f"  Description [{hint}]: ").strip()
    value = raw or current
    if len(value) > 500:
        _err(f"Description too long ({len(value)}/500). Truncated to 500 chars.")
        value = value[:500]
    return value


def _ask_date(current: str = "") -> str:
    hint = f"current: {current}" if current else "YYYY-MM-DD"
    from datetime import datetime
    while True:
        raw = input(f"  Due date [{hint}]: ").strip()
        value = raw or current
        if not value:
            _err("Due date is required.")
            continue
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            _err(f"'{value}' is not a valid date. Use YYYY-MM-DD (e.g. 2026-12-31).")


def _ask_priority(current: str = "") -> str:
    hint = current if current else "not set"
    while True:
        print(f"  Priority  1=Low  2=Medium  3=High  [current: {hint}]")
        raw = input("  Choose [1/2/3, or Enter to keep]: ").strip()
        mapping = {"1": "Low", "2": "Medium", "3": "High"}
        if raw in mapping:
            return mapping[raw]
        if not raw and current:
            return current
        _err("Enter 1 (Low), 2 (Medium), or 3 (High).")


def _ask_completion(current: bool) -> bool:
    label = "Yes" if current else "No"
    raw = input(f"  Completed? [current: {label}]  y=Yes / n=No / Enter=keep: ").strip().lower()
    if raw == "y": return True
    if raw == "n": return False
    return current


# ══════════════════════════════════════════════════════════════════════════════
# Core operations                                                   FR-1 … FR-7
# ══════════════════════════════════════════════════════════════════════════════

def create_task() -> None:
    """
    FR-1 / FR-2  Collect task details and persist a new task.
    NFR-1        Every field is clearly labelled with usage hints.
    NFR-2        Task() validation runs before any write attempt.
    """
    _section("Create New Task")
    print("  Fields marked * are required.\n")

    title       = _ask_title()
    description = _ask_description()
    due_date    = _ask_date()
    priority    = _ask_priority()

    try:
        task = Task(
            title=title, description=description,
            due_date=due_date, priority=priority,
        )
        db.save_task(task)
    except (ValueError, RuntimeError) as exc:
        # NFR-2: validation / save failures are always reported, never silenced
        _err(str(exc))
        return

    _ok(f"Task created successfully.  ID: {task.id}")


def view_tasks() -> None:
    """
    FR-3         Display all tasks with their IDs and every detail field.
    NFR-1        Consistent labelled output; shows task count.
    NFR-4        O(n) iteration — fast for any normal student list size.
    """
    try:
        tasks = db.load_all()
    except RuntimeError as exc:
        _err(str(exc))
        return

    _section("Task List")
    if not tasks:
        print("  (no tasks yet — choose option 1 to create one)")
        return

    count = len(tasks)
    print(f"  {count} task{'s' if count != 1 else ''} found.")
    for task in tasks.values():
        print(task.display())


def update_task() -> None:
    """
    FR-4 / FR-7  Update any field of an existing task, preserving its ID.
    FR-6         Reports clearly when the supplied ID is unknown.
    NFR-1        Shows current values; pressing Enter keeps each one.
    NFR-2        Builds a new Task (triggering full validation) before saving.
    """
    try:
        tasks = db.load_all()
    except RuntimeError as exc:
        _err(str(exc))
        return

    if not tasks:
        _err("No tasks exist yet. Create one first (option 1).")
        return

    _section("Update Task")
    task_id = input("  Task ID to update: ").strip().upper()

    if not task_id:
        _err("Task ID cannot be blank.")
        return

    # FR-6 / NFR-2: explicitly distinguish unknown IDs
    if task_id not in tasks:
        _err(f"No task found with ID '{task_id}'. Use 'View tasks' to see valid IDs.")
        return

    task = tasks[task_id]
    print(f"\n  Editing task  ID: {task_id}  |  Press Enter on any field to keep the current value.")
    print(task.display())

    new_title       = _ask_title(task.title)
    new_description = _ask_description(task.description)
    new_due_date    = _ask_date(task.due_date)
    new_priority    = _ask_priority(task.priority)
    new_completed   = _ask_completion(task.completed)

    try:
        updated = Task(
            id=          task_id,          # FR-7: ID is never changed
            title=       new_title,
            description= new_description,
            due_date=    new_due_date,
            priority=    new_priority,
            completed=   new_completed,
        )
        db.save_task(updated)
    except (ValueError, RuntimeError) as exc:
        _err(f"Update cancelled — {exc}")
        return

    _ok(f"Task '{task_id}' updated successfully.")


def delete_task() -> None:
    """
    FR-5 / FR-6 / FR-7  Delete a task by ID; shows title for confirmation.
    FR-6   Reports clearly when the supplied ID is unknown.
    FR-7   Confirms removal before reporting success (NFR-2: no false positives).
    """
    try:
        tasks = db.load_all()
    except RuntimeError as exc:
        _err(str(exc))
        return

    if not tasks:
        _err("No tasks exist yet. Create one first (option 1).")
        return

    _section("Delete Task")
    task_id = input("  Task ID to delete: ").strip().upper()

    if not task_id:
        _err("Task ID cannot be blank.")
        return

    # FR-6: distinguish unknown IDs
    if task_id not in tasks:
        _err(f"No task found with ID '{task_id}'. Use 'View tasks' to see valid IDs.")
        return

    task = tasks[task_id]
    print(f"\n  Task to delete: '{task.title}'  (ID: {task_id})")

    if not _confirm("This action cannot be undone.  Delete this task?"):
        print("  Deletion cancelled. No changes were made.")
        return

    try:
        removed = db.delete_task(task_id)
    except RuntimeError as exc:
        _err(str(exc))
        return

    if removed:
        # FR-7: only report success after confirming the record is gone
        _ok(f"Task '{task_id}' deleted. It will no longer appear in the task list.")
    else:
        # Defensive: shouldn't happen since we checked above, but FR-6 requires
        # we never report a failed operation as successful.
        _err(f"Task '{task_id}' could not be deleted (it may have already been removed).")


# ══════════════════════════════════════════════════════════════════════════════
# Main menu
# ══════════════════════════════════════════════════════════════════════════════

_MENU = """
╔══════════════════════════════════════════╗
║     Student Academic Task Manager        ║
╠══════════════════════════════════════════╣
║  1. Create a new task                    ║
║  2. View all tasks                       ║
║  3. Update an existing task              ║
║  4. Delete a task                        ║
║  5. Exit                                 ║
╚══════════════════════════════════════════╝"""

_ACTIONS = {
    "1": create_task,
    "2": view_tasks,
    "3": update_task,
    "4": delete_task,
}


def main() -> None:
    """
    Entry point.
    FR-6   Invalid menu choices are reported, not silently ignored.
    NFR-1  Menu options are clearly labelled with action descriptions.
    NFR-2  RuntimeErrors from any operation surface as [!] messages.
    """
    while True:
        print(_MENU)
        choice = input("\n  Select an option [1–5]: ").strip()

        if choice == "5":
            print("\n  Goodbye! Your tasks are saved.\n")
            break

        action = _ACTIONS.get(choice)
        if action is None:
            _err(f"'{choice}' is not a valid option. Please enter a number from 1 to 5.")
            continue

        action()


if __name__ == "__main__":
    main()
