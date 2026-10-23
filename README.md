# Student Academic Task Manager

A command-line application that lets students create, view, update, and delete
academic tasks. All data is stored locally in a JSON file.

---

## Project structure

```
student-task-manager/
├── app/
│   ├── __init__.py     # package marker
│   ├── main.py         # CLI menu and user interaction (FR-1 … FR-7)
│   ├── models.py       # Task dataclass with built-in field validation
│   └── database.py     # JSON persistence with atomic writes
├── tests/
│   ├── __init__.py
│   └── test_tasks.py   # automated test suite (FR-1 … FR-7, NFR-1 … NFR-4)
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Requirements

- Python 3.10 or later (uses the `X | Y` union syntax in type hints)
- No third-party packages are required to run the application

To install the optional test runner:

```bash
pip install -r requirements.txt
```

---

## Running the application

From inside the `student-task-manager/` directory:

```bash
python -m app.main
```

or

```bash
python app/main.py
```

Task data is saved automatically to `tasks_data.json` in the project root.

---

## Running the tests

```bash
# with pytest (recommended)
pytest tests/ -v

# without pytest
python tests/test_tasks.py
```

---

## Functional requirements

| ID   | Requirement |
|------|-------------|
| FR-1 | Students can create an academic task |
| FR-2 | Each task has a unique ID, title, description, due date, priority, and completion status |
| FR-3 | Students can view their task list and see each task's ID and details |
| FR-4 | Students can update an existing task by its ID |
| FR-5 | Students can delete an existing task by its ID |
| FR-6 | The application distinguishes unknown task IDs, reports invalid input, and never reports a failed operation as successful |
| FR-7 | An ID identifies at most one task; updating retains the ID; deleting removes it from subsequent views |

## Non-functional requirements

| ID    | Requirement |
|-------|-------------|
| NFR-1 | Actions and fields have clear labels; feedback is understandable |
| NFR-2 | Invalid input and failed saves are always reported; no silent data corruption |
| NFR-3 | Successfully saved tasks survive a process restart |
| NFR-4 | View and update are responsive for a typical student-sized task list |
| NFR-5 | Task data is stored only on the local filesystem; no network calls are made |

---

## Data storage

Tasks are written to `tasks_data.json`.  
Saves are **atomic**: the application writes to `tasks_data.json.tmp` first, then
renames it over the live file, so a crash mid-write cannot corrupt existing data.

---

## Modules at a glance

### `app/models.py`
Defines the `Task` dataclass.  
`Task.__post_init__` validates every field and raises `ValueError` with a
human-readable message when validation fails.

### `app/database.py`
- `load_all()` — reads and validates the JSON file; returns `{id: Task}`
- `save_all()` — atomic write via `.tmp` + `os.replace()`
- `save_task()` — upsert a single task
- `delete_task()` — remove a task by ID; returns `True` if it existed

### `app/main.py`
Interactive CLI menu.  
Each menu action calls the database layer and surfaces any error to the user
without crashing.
