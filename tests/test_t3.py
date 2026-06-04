import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_connection(client):
    with client.websocket_connect("/ws/rooms/test?username=alice") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "info"
        assert "alice" in data["text"]
        assert "вошел" in data["text"]

def test_message(client):
    with client.websocket_connect("/ws/rooms/room1?username=alice") as ws1:
        ws1.receive_json()
        
        with client.websocket_connect("/ws/rooms/room1?username=bob") as ws2:
            # Bob о себе
            ws2.receive_json()
            # Alice о Bob
            ws1.receive_json()
            
            ws1.send_json({"type": "message", "text": "Привет, Боб"})
            
            resp1 = ws1.receive_json()
            resp2 = ws2.receive_json()
            
            assert resp1["text"] == "Привет, Боб"
            assert resp1["username"] == "alice"
            assert resp2["text"] == "Привет, Боб"
            assert resp2["username"] == "alice"

def test_messageLong(client):
    with client.websocket_connect("/ws/rooms/test?username=alice") as websocket:
        websocket.receive_json()
        long_text = "a" * 301
        websocket.send_json({"type": "message", "text": long_text})
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert data["detail"] == "Сообщение слишком длинное"

def test_isolation(client):
    with client.websocket_connect("/ws/rooms/room1?username=alice") as ws1:
        ws1.receive_json()
        with client.websocket_connect("/ws/rooms/room2?username=bob") as ws2:
            ws2.receive_json()
            ws1.send_json({"type": "message", "text": "Secret"})
            ws1.receive_json()
            pass

def test_getUsers(client):
    with client.websocket_connect("/ws/rooms/python?username=alice") as ws:
        response = client.get("/rooms/python/users")
        assert "alice" in response.json()["users"]
    
    response = client.get("/rooms/python/users")
    assert "alice" not in response.json()["users"]
