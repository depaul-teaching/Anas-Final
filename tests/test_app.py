from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_page_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert "To-Do" in response.text


def test_add_and_complete_task_via_api():
    created = client.post("/api/tasks", json={"title": "Write tests"})
    assert created.status_code == 201
    task = created.json()
    assert task["title"] == "Write tests"
    assert task["done"] is False

    open_ids = [t["id"] for t in client.get("/api/tasks?status=open").json()]
    assert task["id"] in open_ids

    done = client.post(f"/api/tasks/{task['id']}/complete")
    assert done.status_code == 200
    assert done.json()["done"] is True

    done_ids = [t["id"] for t in client.get("/api/tasks?status=done").json()]
    assert task["id"] in done_ids


def test_blank_title_rejected():
    assert client.post("/api/tasks", json={"title": "   "}).status_code == 422


def test_complete_missing_task_returns_404():
    assert client.post("/api/tasks/99999/complete").status_code == 404


def test_form_add_redirects_home():
    response = client.post("/tasks", data={"title": "From the form"}, follow_redirects=False)
    assert response.status_code == 303
    assert "From the form" in client.get("/").text
