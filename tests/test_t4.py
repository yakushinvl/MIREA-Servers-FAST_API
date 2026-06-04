import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.storage import storage

@pytest.fixture
def client():
    storage.tasks = []
    storage.task_counter = 1
    return TestClient(app)

def test_usersMe(client):
    response = client.get("/users/me", headers={"X-User-Id": "10", "X-User-Role": "admin"})
    assert response.status_code == 200
    assert response.json()["id"] == 10
    assert response.json()["role"] == "admin"

def test_adminStatsError(client):
    response = client.get("/admin/stats", headers={"X-User-Id": "10", "X-User-Role": "user"})
    assert response.status_code == 403

def test_adminStatsSuccess(client):
    r1 = client.post("/tasks", json={"title": "Task 1", "priority": 1}, headers={"X-User-Id": "10"})
    assert r1.status_code == 201
    r2 = client.post("/tasks", json={"title": "Task 2", "priority": 2}, headers={"X-User-Id": "20"})
    assert r2.status_code == 201
    
    response = client.get("/admin/stats", headers={"X-User-Id": "1", "X-User-Role": "admin"})
    assert response.status_code == 200
    assert response.json()["total_tasks"] == 2

def test_adminDeleteTask(client):
    resp = client.post("/tasks", json={"title": "Owner10 Task", "priority": 1}, headers={"X-User-Id": "10"})
    task_id = resp.json()["id"]
    
    response = client.delete(f"/admin/tasks/{task_id}", headers={"X-User-Id": "1", "X-User-Role": "admin"})
    assert response.status_code == 204
    
    assert len(storage.tasks) == 0

def test_userDeleteTask(client):
    resp = client.post("/tasks", json={"title": "Owner10 Task", "priority": 1}, headers={"X-User-Id": "10"})
    task_id = resp.json()["id"]
    
    response = client.delete(f"/tasks/{task_id}", headers={"X-User-Id": "20"})
    assert response.status_code == 404
