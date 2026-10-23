"""
models.py — Task data model.

FR-2: Each task has a unique ID, title, description,
      due date, priority, and completion status.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime
import uuid

PRIORITIES: tuple[str, ...] = ("Low", "Medium", "High")


def _new_id() -> str:
    """Return an 8-character uppercase hex ID derived from a UUID4."""
    return str(uuid.uuid4())[:8].upper()


@dataclass
class Task:
    """Represents a single academic task."""

    title:       str
    description: str
    due_date:    str                          # stored as "YYYY-MM-DD" string
    priority:    str                          # one of PRIORITIES
    completed:   bool  = False
    id:          str   = field(default_factory=_new_id)

    # ── validation ───────────────────────────────────────────────────────────

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        """Raise ValueError with a clear message on any invalid field (NFR-2)."""
        if not self.title or not self.title.strip():
            raise ValueError("Title must not be empty.")
        if len(self.title) > 120:
            raise ValueError(
                f"Title is too long ({len(self.title)}/120 chars)."
            )
        if len(self.description) > 500:
            raise ValueError(
                f"Description is too long ({len(self.description)}/500 chars)."
            )
        try:
            datetime.strptime(self.due_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"Due date '{self.due_date}' is not valid. Use YYYY-MM-DD."
            )
        if self.priority not in PRIORITIES:
            raise ValueError(
                f"Priority must be one of {PRIORITIES}, got '{self.priority}'."
            )

    # ── serialisation helpers ─────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Convert to a plain dict suitable for JSON serialisation."""
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Task":
        """
        Reconstruct a Task from a stored dict.
        Raises ValueError if any required key is missing or invalid.
        """
        required = {"id", "title", "description", "due_date", "priority", "completed"}
        missing = required - data.keys()
        if missing:
            raise ValueError(f"Task record is missing fields: {missing}")
        return Task(
            id=          data["id"],
            title=       data["title"],
            description= data["description"],
            due_date=    data["due_date"],
            priority=    data["priority"],
            completed=   bool(data["completed"]),
        )

    def display(self) -> str:
        """Return a human-readable multi-line representation (NFR-1)."""
        status = "✔ Completed" if self.completed else "○ Pending"
        return (
            f"\n  ID          : {self.id}\n"
            f"  Title       : {self.title}\n"
            f"  Description : {self.description or '(none)'}\n"
            f"  Due date    : {self.due_date}\n"
            f"  Priority    : {self.priority}\n"
            f"  Status      : {status}\n"
            f"  {'─' * 44}"
        )
