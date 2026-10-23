"""
app/web.py  —  Flask web interface for the Student Academic Task Manager.

Run from the student-task-manager/ directory:
    python -m app.web

Then open http://127.0.0.1:5000 in your browser.
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from app import database as db
from app.models import Task

app = Flask(__name__)
app.secret_key = "student-task-manager-secret"


# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """FR-3: view all tasks."""
    try:
        tasks = list(db.load_all().values())
    except RuntimeError as exc:
        flash(str(exc), "error")
        tasks = []
    return render_template("index.html", tasks=tasks)


@app.route("/create", methods=["GET", "POST"])
def create():
    """FR-1 / FR-2: create a new task."""
    if request.method == "POST":
        try:
            task = Task(
                title=       request.form["title"].strip(),
                description= request.form.get("description", "").strip(),
                due_date=    request.form["due_date"].strip(),
                priority=    request.form["priority"].strip(),
            )
            db.save_task(task)
            flash(f"Task created successfully! ID: {task.id}", "success")
            return redirect(url_for("index"))
        except (ValueError, RuntimeError) as exc:
            flash(str(exc), "error")
    return render_template("form.html", action="Create", task=None)


@app.route("/update/<task_id>", methods=["GET", "POST"])
def update(task_id):
    """FR-4 / FR-7: update a task by ID; ID is preserved."""
    tasks = db.load_all()

    # FR-6: distinguish unknown IDs
    if task_id not in tasks:
        flash(f"No task found with ID '{task_id}'.", "error")
        return redirect(url_for("index"))

    task = tasks[task_id]

    if request.method == "POST":
        try:
            updated = Task(
                id=          task_id,
                title=       request.form["title"].strip(),
                description= request.form.get("description", "").strip(),
                due_date=    request.form["due_date"].strip(),
                priority=    request.form["priority"].strip(),
                completed=   "completed" in request.form,
            )
            db.save_task(updated)
            flash(f"Task '{task_id}' updated successfully.", "success")
            return redirect(url_for("index"))
        except (ValueError, RuntimeError) as exc:
            flash(str(exc), "error")

    return render_template("form.html", action="Update", task=task)


@app.route("/delete/<task_id>", methods=["POST"])
def delete(task_id):
    """FR-5 / FR-6 / FR-7: delete a task by ID."""
    try:
        removed = db.delete_task(task_id)
        if removed:
            flash(f"Task '{task_id}' deleted.", "success")
        else:
            # FR-6: never report a failed operation as successful
            flash(f"No task found with ID '{task_id}'.", "error")
    except RuntimeError as exc:
        flash(str(exc), "error")
    return redirect(url_for("index"))


@app.route("/toggle/<task_id>", methods=["POST"])
def toggle(task_id):
    """Quick-toggle completion status from the task list."""
    tasks = db.load_all()
    if task_id not in tasks:
        flash(f"No task found with ID '{task_id}'.", "error")
        return redirect(url_for("index"))
    task = tasks[task_id]
    task.completed = not task.completed
    db.save_task(task)
    return redirect(url_for("index"))


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
