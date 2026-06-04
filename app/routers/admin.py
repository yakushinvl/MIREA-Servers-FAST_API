from fastapi import APIRouter, Depends, HTTPException, Response
from app.schemas import AdminStats, User
from app.storage import get_storage, Storage
from app.dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/stats", response_model=AdminStats)
async def get_stats(
    storage: Storage = Depends(get_storage)
):
    tasks = storage.get_tasks()
    stats = {
        "todo": 0,
        "in_progress": 0,
        "done": 0
    }
    for t in tasks:
        if t.status in stats:
            stats[t.status] += 1
            
    return AdminStats(
        total_tasks=len(tasks),
        by_status=stats
    )

@router.delete("/tasks/{task_id}", status_code=204)
async def admin_delete_task(
    task_id: int,
    storage: Storage = Depends(get_storage)
):
    task = storage.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    storage.delete_task(task_id)
    return Response(status_code=204)
