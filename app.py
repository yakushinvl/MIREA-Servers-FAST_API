import uuid
import time
import re
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Response, Header, Cookie
from pydantic import BaseModel, EmailStr, Field, field_validator
from itsdangerous import Signer, BadSignature, SignatureExpired

app = FastAPI()

SECRET_KEY = "super-secret-key"
signer = Signer(SECRET_KEY)

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    age: Optional[int] = Field(None, gt=0)
    is_subscribed: Optional[bool] = False

@app.post("/create_user")
def create_user(user: UserCreate):
    return user

sample_products = [
    {"product_id": 123, "name": "Smartphone", "category": "Electronics", "price": 599.99},
    {"product_id": 456, "name": "Phone Case", "category": "Accessories", "price": 19.99},
    {"product_id": 789, "name": "Iphone", "category": "Electronics", "price": 1299.99},
    {"product_id": 101, "name": "Headphones", "category": "Accessories", "price": 99.99},
    {"product_id": 202, "name": "Smartwatch", "category": "Electronics", "price": 299.99},
]

@app.get("/product/{product_id}")
def get_product(product_id: int):
    for product in sample_products:
        if product["product_id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")

@app.get("/products/search")
def search_products(keyword: str, category: Optional[str] = None, limit: int = 10):
    results = []
    for product in sample_products:
        if keyword.lower() in product["name"].lower():
            if category is None or product["category"] == category:
                results.append(product)
    return results[:limit]

class LoginData(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(data: LoginData, response: Response):
    user_id = str(uuid.uuid4())
    current_time = int(time.time())
    payload = f"{user_id}.{current_time}"
    token = signer.sign(payload).decode()
    response.set_cookie(key="session_token", value=token, httponly=True, max_age=300)
    return {"message": "Logged in successfully"}

@app.get("/user")
@app.get("/profile")
def get_profile(response: Response, session_token: Optional[str] = Cookie(None)):
    if not session_token:
        raise HTTPException(status_code=401, detail="неавторизован")
    
    try:
        payload = signer.unsign(session_token).decode()
        parts = payload.split('.')
        if len(parts) != 2:
            raise HTTPException(status_code=401, detail="неправильная сессия")
        
        user_id, timestamp_str = parts
        last_activity = int(timestamp_str)
        current_time = int(time.time())
        elapsed = current_time - last_activity

        if elapsed > 300:
            raise HTTPException(status_code=401, detail="сессия устарела")
        
        if 180 <= elapsed < 300:
            new_payload = f"{user_id}.{current_time}"
            new_token = signer.sign(new_payload).decode()
            response.set_cookie(key="session_token", value=new_token, httponly=True, max_age=300)

        return {"user_id": user_id, "last_activity": last_activity}
    except (BadSignature, SignatureExpired, ValueError):
        raise HTTPException(status_code=401, detail="неправильная сессия")

class CommonHeaders(BaseModel):
    user_agent: str = Field(..., alias="user-agent")
    accept_language: str = Field(..., alias="accept-language")

    @field_validator("accept_language")
    @classmethod
    def validate_accept_language(cls, v: str) -> str:
        pattern = r"^[a-zA-Z-]+(,[a-zA-Z-]+(;q=[0-9.]+)?)*$"
        if not re.match(pattern, v):
            raise ValueError("неправильный формат accept-language")
        return v

@app.get("/headers")
def get_headers(headers: CommonHeaders = Header()):
    return {
        "User-Agent": headers.user_agent,
        "Accept-Language": headers.accept_language
    }

@app.get("/info")
def get_info(response: Response, headers: CommonHeaders = Header()):
    response.headers["X-Server-Time"] = datetime.now().isoformat()
    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны",
        "headers": {
            "User-Agent": headers.user_agent,
            "Accept-Language": headers.accept_language
        }
    }
