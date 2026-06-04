from fastapi import APIRouter, Depends, HTTPException, Response
from typing import List, Optional
from app.schemas import Task, TaskCreate, TaskUpdateStatus, User
from app.storage import get_storage, Storage
from app.dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("", response_model=Task, status_code=201)
async def create_task(
    task_in: TaskCreate, 
    user: User = Depends(get_current_user),
    storage: Storage = Depends(get_storage)
):
    return storage.add_task(task_in.model_dump(), user.id)

@router.get("", response_model=List[Task])
async def get_tasks(
    status: Optional[str] = None,
    min_priority: Optional[int] = None,
    user: User = Depends(get_current_user),
    storage: Storage = Depends(get_storage)
):
    tasks = storage.get_tasks(user.id)
    if status:
        tasks = [t for t in tasks if t.status == status]
    if min_priority:
        tasks = [t for t in tasks if t.priority >= min_priority]
    return tasks

@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: int,
    user: User = Depends(get_current_user),
    storage: Storage = Depends(get_storage)
):
    task = storage.get_task(task_id)
    if not task or task.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task

@router.patch("/{task_id}/status", response_model=Task)
async def update_task_status(
    task_id: int,
    status_update: TaskUpdateStatus,
    user: User = Depends(get_current_user),
    storage: Storage = Depends(get_storage)
):
    task = storage.get_task(task_id)
    if not task or task.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    task.status = status_update.status
    return task

@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    user: User = Depends(get_current_user),
    storage: Storage = Depends(get_storage)
):
    task = storage.get_task(task_id)
    if not task or task.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    storage.delete_task(task_id)
    return Response(status_code=204)
