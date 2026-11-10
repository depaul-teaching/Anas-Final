"""Simple to-do app built with FastAPI.

Features:
  - List tasks, filtered by All / Open / Done
  - Add a task
  - Mark a task complete, or click "Done" to move it back to To-Do
  - Delete a task
  - JSON API at /api/tasks
  - Health check at /health

Tasks are stored in memory, so they reset when the app restarts.
"""

import os
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app.store import TaskStore

# Values that change between environments come from environment variables.
APP_TITLE = os.getenv("APP_TITLE", "Anas's To-Do List")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

BASE_DIR = Path(__file__).resolve().parent
VALID_FILTERS = ("all", "open", "done")

app = FastAPI(title=APP_TITLE)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

store = TaskStore()
store.seed(["Pick a project topic", "Write the to-do app", "Containerize the app"])
store.complete(1)


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)


def _normalize_filter(status: str) -> str:
    status = status.lower()
    return status if status in VALID_FILTERS else "all"


def _redirect_home(status: str) -> RedirectResponse:
    # 303 tells the browser to follow up with a GET, so refreshing won't resubmit the form.
    return RedirectResponse(f"/?status={_normalize_filter(status)}", status_code=303)


# ---------- HTML pages ----------


@app.get("/")
def index(request: Request, status: str = "all"):
    status = _normalize_filter(status)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "app_title": APP_TITLE,
            "environment": ENVIRONMENT,
            "tasks": store.list(status),
            "status": status,
            "counts": store.counts(),
        },
    )


@app.post("/tasks")
def add_task(title: str = Form(...), status: str = Form("all")):
    title = title.strip()
    if title:
        store.add(title[:200])
    return _redirect_home(status)


@app.post("/tasks/{task_id}/complete")
def complete_task(task_id: int, status: str = Form("all")):
    if store.complete(task_id) is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return _redirect_home(status)


@app.post("/tasks/{task_id}/reopen")
def reopen_task(task_id: int, status: str = Form("all")):
    if store.reopen(task_id) is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return _redirect_home(status)


# HTML forms can only send GET or POST, so the page deletes with POST.
@app.post("/tasks/{task_id}/delete")
def delete_task(task_id: int, status: str = Form("all")):
    if not store.delete(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return _redirect_home(status)


# ---------- JSON API ----------


@app.get("/api/tasks")
def api_list_tasks(status: str = "all"):
    return [task.to_dict() for task in store.list(_normalize_filter(status))]


@app.post("/api/tasks", status_code=201)
def api_add_task(task: TaskIn):
    title = task.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Title cannot be blank")
    return store.add(title).to_dict()


@app.post("/api/tasks/{task_id}/complete")
def api_complete_task(task_id: int):
    task = store.complete(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@app.post("/api/tasks/{task_id}/reopen")
def api_reopen_task(task_id: int):
    task = store.reopen(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@app.delete("/api/tasks/{task_id}", status_code=204)
def api_delete_task(task_id: int):
    if not store.delete(task_id):
        raise HTTPException(status_code=404, detail="Task not found")


# ---------- Health ----------


@app.get("/health")
def health():
    return {"status": "ok"}
