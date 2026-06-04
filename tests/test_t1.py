import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.storage import storage

@pytest.fixture
def client():
    storage.tasks = []
    storage.task_counter = 1
    return TestClient(app)

def test_createSuccess(client):
    response = client.post(
        "/tasks",
        json={"title": "Test Task", "status": "todo", "priority": 3},
        headers={"X-User-Id": "10"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["owner_id"] == 10

def test_createErrorTitle(client):
    response = client.post(
        "/tasks",
        json={"title": "Te", "priority": 3},
        headers={"X-User-Id": "10"}
    )
    assert response.status_code == 422

def test_createUnauthorized(client):
    response = client.post(
        "/tasks",
        json={"title": "Test Task", "priority": 3}
    )
    assert response.status_code == 401

def test_filters(client):
    client.post("/tasks", json={"title": "Task 1", "status": "todo", "priority": 1}, headers={"X-User-Id": "10"})
    client.post("/tasks", json={"title": "Task 2", "status": "done", "priority": 5}, headers={"X-User-Id": "10"})
    
    # по статусу
    response = client.get("/tasks?status=done", headers={"X-User-Id": "10"})
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "done"
    
    # по приоритету
    response = client.get("/tasks?min_priority=3", headers={"X-User-Id": "10"})
    assert len(response.json()) == 1
    assert response.json()[0]["priority"] == 5

def test_checkOwnership(client):
    client.post("/tasks", json={"title": "User 10 Task", "priority": 1}, headers={"X-User-Id": "10"})
    
    response = client.get("/tasks", headers={"X-User-Id": "20"})
    assert len(response.json()) == 0

def test_updateStatus(client):
    resp = client.post("/tasks", json={"title": "Task", "priority": 1}, headers={"X-User-Id": "10"})
    task_id = resp.json()["id"]
    
    response = client.patch(f"/tasks/{task_id}/status", json={"status": "done"}, headers={"X-User-Id": "10"})
    assert response.status_code == 200
    assert response.json()["status"] == "done"

def test_delete(client):
    resp = client.post("/tasks", json={"title": "To delete", "priority": 1}, headers={"X-User-Id": "10"})
    task_id = resp.json()["id"]
    
    response = client.delete(f"/tasks/{task_id}", headers={"X-User-Id": "10"})
    assert response.status_code == 204
    
    response = client.get(f"/tasks/{task_id}", headers={"X-User-Id": "10"})
    assert response.status_code == 404
