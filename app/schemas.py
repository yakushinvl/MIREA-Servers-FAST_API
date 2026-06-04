from pydantic import BaseModel, Field
from typing import List, Optional

# задачи
class TaskBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=80)
    description: Optional[str] = None
    status: str = "todo"  # todo, in_progress, done
    priority: int = Field(..., ge=1, le=5)

class TaskCreate(TaskBase):
    pass

class TaskUpdateStatus(BaseModel):
    status: str

class Task(TaskBase):
    id: int
    owner_id: int

# юзеры
class User(BaseModel):
    id: int
    role: str

# WebSocket
class WSMessage(BaseModel):
    type: str
    text: Optional[str] = None

class WSResponse(BaseModel):
    type: str
    room_id: Optional[str] = None
    username: Optional[str] = None
    text: Optional[str] = None
    detail: Optional[str] = None

class RoomUsers(BaseModel):
    room_id: str
    users: List[str]

# админка
class AdminStats(BaseModel):
    total_tasks: int
    by_status: dict
