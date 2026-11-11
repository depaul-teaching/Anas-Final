# Anas Patel Final Project - Simple To-Do App

A small to-do app built with Python and FastAPI for IT-390.

## Features

- List tasks
- Filter tasks by All / Open / Done
- Add a task
- Mark a task complete, or click its green "Done" label to move it back to To-Do
- Delete a task
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

## Run with Docker

Build the image:

```bash
docker build -t task-tracker:dev .
```

Run it:

```bash
docker run --rm -p 8000:8000 -e ENVIRONMENT=docker -e APP_TITLE="Anas Task Tracker" task-tracker:dev
```

Open http://localhost:8000. Check health with `curl -i http://localhost:8000/health`.

## Environment variables

| Variable      | Default             | What it does                          |
|---------------|---------------------|---------------------------------------|
| `APP_TITLE`   | `Anas's To-Do List` | Browser tab title    |
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
| POST   | `/tasks/{id}/reopen`         | Move a task back to To-Do (HTML form)         |
| POST   | `/tasks/{id}/delete`         | Delete a task (HTML form)                     |
| GET    | `/api/tasks`                 | List tasks as JSON (`?status=all\|open\|done`) |
| POST   | `/api/tasks`                 | Add a task, body: `{"title": "..."}`          |
| POST   | `/api/tasks/{id}/complete`   | Mark a task complete                          |
| POST   | `/api/tasks/{id}/reopen`     | Move a task back to To-Do                     |
| DELETE | `/api/tasks/{id}`            | Delete a task                                 |
| GET    | `/health`                    | Returns `{"status": "ok"}`                    |
