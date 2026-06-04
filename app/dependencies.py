from fastapi import Header, HTTPException, Depends
from app.schemas import User

async def get_current_user(
    x_user_id: str = Header(None, alias="X-User-Id"),
    x_user_role: str = Header("user", alias="X-User-Role")
) -> User:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Заголовок X-User-Id отсутствует")
    
    try:
        user_id = int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Некорректный X-User-Id")
        
    return User(id=user_id, role=x_user_role)

async def require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Требуется роль администратора")
    return user
