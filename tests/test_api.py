"""HTTP endpoint tests (require fastapi + httpx; skipped otherwise)."""
from datetime import date, timedelta


def create(client, **body):
    body.setdefault("title", "Task")
    response = client.post("/tasks", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_task(client):
    data = create(client, title="Write docs", priority="high")
    assert data["id"] == 1
    assert data["title"] == "Write docs"
    assert data["status"] == "pending"
    assert data["priority"] == "high"
    assert "created_at" in data


def test_create_invalid_returns_422(client):
    assert client.post("/tasks", json={"title": "  "}).status_code == 422
    assert client.post("/tasks", json={"title": "x", "status": "done"}).status_code == 422
    assert client.post("/tasks", json={}).status_code == 422


def test_create_past_due_date_returns_422(client):
    past = (date.today() - timedelta(days=3)).isoformat()
    assert client.post("/tasks", json={"title": "x", "due_date": past}).status_code == 422


def test_list_tasks(client):
    create(client, title="a")
    create(client, title="b")
    response = client.get("/tasks")
    assert response.status_code == 200
    assert [t["title"] for t in response.json()] == ["a", "b"]


def test_filter_by_status_endpoint(client):
    create(client, title="todo", status="pending")
    create(client, title="done", status="completed")
    response = client.get("/tasks", params={"status": "pending"})
    assert response.status_code == 200
    assert [t["title"] for t in response.json()] == ["todo"]


def test_filter_by_priority_endpoint(client):
    create(client, title="lo", priority="low")
    create(client, title="hi", priority="high")
    response = client.get("/tasks", params={"priority": "high"})
    assert [t["title"] for t in response.json()] == ["hi"]


def test_filter_combined_endpoint(client):
    create(client, title="match", status="in_progress", priority="high")
    create(client, title="other", status="in_progress", priority="low")
    response = client.get("/tasks", params={"status": "in_progress", "priority": "high"})
    assert [t["title"] for t in response.json()] == ["match"]


def test_invalid_filter_value_returns_422(client):
    assert client.get("/tasks", params={"status": "bogus"}).status_code == 422


def test_get_task(client):
    task = create(client, title="find me")
    response = client.get(f"/tasks/{task['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "find me"


def test_get_missing_returns_404(client):
    assert client.get("/tasks/999").status_code == 404


def test_update_task(client):
    task = create(client, title="old", description="keep")
    response = client.patch(f"/tasks/{task['id']}", json={"status": "completed"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["title"] == "old"
    assert body["description"] == "keep"


def test_update_empty_body_returns_422(client):
    task = create(client)
    assert client.patch(f"/tasks/{task['id']}", json={}).status_code == 422


def test_update_missing_returns_404(client):
    assert client.patch("/tasks/999", json={"title": "x"}).status_code == 404


def test_delete_task(client):
    task = create(client)
    assert client.delete(f"/tasks/{task['id']}").status_code == 204
    assert client.get(f"/tasks/{task['id']}").status_code == 404


def test_delete_missing_returns_404(client):
    assert client.delete("/tasks/999").status_code == 404
