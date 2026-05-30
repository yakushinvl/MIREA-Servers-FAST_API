import os
from datetime import timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from auth import (
    get_password_hash, auth_user, create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user, check_role,
    verify_password
)
from database import init_db, get_db_connection
from models import User, UserInDB, Todo, TodoCreate, TodoUpdate, Token

load_dotenv()

limiter = Limiter(key_func=get_remote_address)
MODE = os.getenv("MODE", "DEV").upper()

docs_url = None
redoc_url = None
openapi_url = None

app = FastAPI(docs_url=docs_url, redoc_url=redoc_url, openapi_url=openapi_url)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
async def root():
    return {"status": "ok"}

if MODE == "DEV":
    @app.get("/docs", include_in_schema=False)
    async def get_documentation():
        return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")

    @app.get("/openapi.json", include_in_schema=False)
    async def openapi():
        return get_openapi(title=app.title, version=app.version, routes=app.routes)
elif MODE == "PROD":
    pass


@app.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("1/minute")
async def register(user: User):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (user.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь уже есть")
    
    hashed_pwd = get_password_hash(user.password)
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user.username, hashed_pwd))
    conn.commit()
    conn.close()
    return {"message": "Новый юзер создан"}

@app.get("/login")
async def login_basic(user: UserInDB = Depends(auth_user)):
    return {"message": f"Привет, {user.username}!"}

@app.post("/login_jwt", response_model=Token)
@limiter.limit("5/minute")
async def login_jwt(user: User):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (user.username,))
    user_row = cursor.fetchone()
    conn.close()
    
    if not user_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Юзер не найден")
    
    if not verify_password(user.password, user_row["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ошибка авторизации")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_row["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/protected_resource")
async def protected_resource(user: UserInDB = Depends(get_current_user)):
    return {"message": "Доступ выдан", "user": user.username}

@app.post("/admin_resource")
async def admin_resource():
    return {"message": "Админ", "action": "Ресурс создан"}

@app.get("/user_resource")
async def user_resource(user: UserInDB = Depends(check_role(["admin", "user"]))):
    return {"message": f"{user.username}, текст"}


@app.post("/todos", status_code=status.HTTP_201_CREATED, response_model=Todo)
async def create_todo(todo: TodoCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO todos (title, description) VALUES (?, ?)",
        (todo.title, todo.description)
    )
    todo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {**todo.dict(), "id": todo_id, "completed": False}

@app.get("/todos/{todo_id}", response_model=Todo)
async def read_todo(todo_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Todo не найдено")
    return dict(row)

@app.put("/todos/{todo_id}", response_model=Todo)
async def update_todo(todo_id: int, todo: TodoUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE todos SET title = ?, description = ?, completed = ? WHERE id = ?",
        (todo.title, todo.description, todo.completed, todo_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Todo не найдено")
    conn.commit()
    conn.close()
    return {**todo.dict(), "id": todo_id}

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Todo не найдено")
    conn.commit()
    conn.close()
    return {"message": "Todo удалён"}

@app.post("/promote/{username}")
async def promote_user(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = 'admin' WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return {"message": f"{username} повышен до admin"}
