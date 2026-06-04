from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Dict, List
from app.schemas import RoomUsers

router = APIRouter(tags=["websocket"])

class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, room_id: str, username: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {}
        self.rooms[room_id][username] = websocket
        
        await self.broadcast(room_id, {
            "type": "info",
            "text": f"Пользователь {username} вошел в комнату"
        })

    async def disconnect(self, room_id: str, username: str):
        if room_id in self.rooms and username in self.rooms[room_id]:
            del self.rooms[room_id][username]
            if not self.rooms[room_id]:
                del self.rooms[room_id]
            else:
                await self.broadcast(room_id, {
                    "type": "info",
                    "text": f"Пользователь {username} покинул комнату"
                })

    async def broadcast(self, room_id: str, payload: dict):
        if room_id in self.rooms:
            for username, websocket in self.rooms[room_id].items():
                try:
                    await websocket.send_json(payload)
                except:
                    pass

    def get_users(self, room_id: str) -> List[str]:
        if room_id in self.rooms:
            return list(self.rooms[room_id].keys())
        return []

manager = RoomManager()

@router.websocket("/ws/rooms/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    username: str = Query(None)
):
    if not username or not username.strip():
        await websocket.close(code=1008)
        return

    await manager.connect(room_id, username, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "message":
                text = data.get("text", "")
                if len(text) > 300:
                    await websocket.send_json({
                        "type": "error",
                        "detail": "Сообщение слишком длинное"
                    })
                else:
                    await manager.broadcast(room_id, {
                        "type": "message",
                        "room_id": room_id,
                        "username": username,
                        "text": text
                    })
    except WebSocketDisconnect:
        await manager.disconnect(room_id, username)

@router.get("/rooms/{room_id}/users", response_model=RoomUsers)
async def get_room_users(room_id: str):
    return RoomUsers(room_id=room_id, users=manager.get_users(room_id))
