from fastapi import FastAPI, HTTPException, Response, Request, Cookie, Depends
from fastapi.responses import JSONResponse
from models import UserCreate, CommonHeaders
import uuid
import time
from datetime import datetime
from itsdangerous import URLSafeSerializer
from pydantic import BaseModel

app = FastAPI()
SECRET_KEY = "keyyy"
serializer = URLSafeSerializer(SECRET_KEY)

# Задание 3.1
@app.post("/create_user")
async def create_user(user: UserCreate):
    return user

# Задание 3.2
sample_products = [
    {"product_id": 123, "name": "Smartphone", "category": "Electronics", "price": 599.99},
    {"product_id": 456, "name": "Phone Case", "category": "Accessories", "price": 19.99},
    {"product_id": 789, "name": "Iphone", "category": "Electronics", "price": 1299.99},
    {"product_id": 101, "name": "Headphones", "category": "Accessories", "price": 99.99},
    {"product_id": 202, "name": "Smartwatch", "category": "Electronics", "price": 299.99},
]

@app.get("/product/{product_id}")
async def get_product(product_id: int):
    for p in sample_products:
        if p["product_id"] == product_id:
            return p
    raise HTTPException(status_code=404, detail="Product not found")

@app.get("/products/search")
async def search_products(keyword: str, category: str | None = None, limit: int = 10):
    result = []
    keyword_lower = keyword.lower()
    for p in sample_products:
        if keyword_lower in p["name"].lower():
            if category is None or p["category"] == category:
                result.append(p)
    return result[:limit]

# Задание 5.1 – простая cookie‑аутентификация
valid_tokens = set()

class LoginData(BaseModel):
    username: str
    password: str

@app.post("/login")
async def login(data: LoginData, response: Response):
    if data.username == "user123" and data.password == "password123":
        token = str(uuid.uuid4())
        valid_tokens.add(token)
        response.set_cookie(key="session_token", value=token, httponly=True, max_age=3600)
        return {"message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/user")
async def get_user(session_token: str | None = Cookie(None)):
    if session_token is None or session_token not in valid_tokens:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"username": "user123", "email": "user@example.com"}

@app.post("/login-signed")
async def login_signed(data: LoginData, response: Response):
    if data.username == "user123" and data.password == "password123":
        user_id = str(uuid.uuid4())
        token = serializer.dumps(user_id)
        response.set_cookie(key="session_token_signed", value=token, httponly=True, max_age=3600)
        return {"message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/profile")
async def get_profile(session_token_signed: str | None = Cookie(None, alias="session_token_signed")):
    if session_token_signed is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        user_id = serializer.loads(session_token_signed)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")
    return {"user_id": user_id, "name": "Test User"}

@app.post("/login-session")
async def login_session(data: LoginData, response: Response):
    if data.username == "user123" and data.password == "password123":
        user_id = str(uuid.uuid4())
        timestamp = int(time.time())
        data_str = f"{user_id}.{timestamp}"
        token = serializer.dumps(data_str)
        response.set_cookie(key="session_token_timed", value=token, httponly=True, max_age=300)
        return {"message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/session-profile")
async def session_profile(request: Request, response: Response):
    token = request.cookies.get("session_token_timed")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        data_str = serializer.loads(token)
        user_id, ts_str = data_str.split('.')
        timestamp = int(ts_str)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session")

    now = int(time.time())
    elapsed = now - timestamp
    if elapsed > 300:
        raise HTTPException(status_code=401, detail="Session expired")
    elif elapsed >= 180:
        new_timestamp = now
        new_data_str = f"{user_id}.{new_timestamp}"
        new_token = serializer.dumps(new_data_str)
        response.set_cookie(key="session_token_timed", value=new_token, httponly=True, max_age=300)
        return {"user_id": user_id, "message": "Session extended"}
    else:
        return {"user_id": user_id, "message": "Session valid"}

# Задание 5.4 – работа с заголовками
@app.get("/headers")
async def get_headers(headers: CommonHeaders = Depends()):
    return {
        "User-Agent": headers.user_agent,
        "Accept-Language": headers.accept_language
    }

@app.get("/info")
async def get_info(headers: CommonHeaders = Depends()):
    current_time = datetime.utcnow().isoformat() + "Z"
    response = JSONResponse(content={
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": {
            "User-Agent": headers.user_agent,
            "Accept-Language": headers.accept_language
        }
    })
    response.headers["X-Server-Time"] = current_time
    return response