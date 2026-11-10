# Anas Patel Final Project - Simple To-Do App

A small to-do app built with Python and FastAPI for IT-390.

## Features

- List tasks
- Filter tasks by All / Open / Done
- Add a task
- Mark a task complete
- JSON API at `/api/tasks`
- Health check at `/health`

Tasks are kept in memory, so they reset when the app restarts.

## Run locally

Requires Python 3.12+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000.

Run the tests:

```bash
pytest
```

## Environment variables

| Variable      | Default             | What it does                          |
|---------------|---------------------|---------------------------------------|
| `APP_TITLE`   | `Anas's To-Do List` | Page heading and browser tab title    |
| `ENVIRONMENT` | `local`             | Shown in the banner at the top        |

Example:

```bash
APP_TITLE="My Tasks" ENVIRONMENT=staging uvicorn app.main:app
```

## Endpoints

| Method | Path                         | Description                                   |
|--------|------------------------------|-----------------------------------------------|
| GET    | `/`                          | Home page (`?status=all\|open\|done`)         |
| POST   | `/tasks`                     | Add a task (HTML form)                        |
| POST   | `/tasks/{id}/complete`       | Mark a task complete (HTML form)              |
| GET    | `/api/tasks`                 | List tasks as JSON (`?status=all\|open\|done`) |
| POST   | `/api/tasks`                 | Add a task, body: `{"title": "..."}`          |
| POST   | `/api/tasks/{id}/complete`   | Mark a task complete                          |
| GET    | `/health`                    | Returns `{"status": "ok"}`                    |
