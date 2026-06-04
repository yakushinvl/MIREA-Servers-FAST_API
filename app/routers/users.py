from fastapi import APIRouter, Depends
from app.schemas import User
from app.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=User)
async def get_me(user: User = Depends(get_current_user)):
    return user

@router.get("/{user_id}", response_model=User)
async def get_user_by_id(user_id: int):
    return User(id=user_id, role="user")
