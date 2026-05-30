import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer
from passlib.context import CryptContext
from database import get_db_connection
from models import UserInDB, TokenData
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 for JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login_jwt")
basic_security = HTTPBasic()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def auth_user(credentials: HTTPBasicCredentials = Depends(basic_security)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (credentials.username,))
    user_row = cursor.fetchone()
    conn.close()

    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="неправильный пароль или ник",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    user = UserInDB(username=user_row["username"], hashed_password=user_row["password"], role=user_row["role"])
    
    if not (secrets.compare_digest(credentials.username, user.username) and verify_password(credentials.password, user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильный пароль или ник",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="ошибка валидации данных",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (token_data.username,))
    user_row = cursor.fetchone()
    conn.close()
    
    if user_row is None:
        raise credentials_exception
    return UserInDB(username=user_row["username"], hashed_password=user_row["password"], role=user_row["role"])

# Task 7.1: RBAC dependency
def check_role(required_roles: list[str]):
    def role_checker(user: UserInDB = Depends(get_current_user)):
        if user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нет доступа"
            )
        return user
    return role_checker

# Task 6.3: Basic Auth for Docs
def authenticate_docs(credentials: HTTPBasicCredentials = Depends(basic_security)):
    correct_username = os.getenv("DOCS_USER", "admin")
    correct_password = os.getenv("DOCS_PASSWORD", "admin")
    if not (secrets.compare_digest(credentials.username, correct_username) and 
            secrets.compare_digest(credentials.password, correct_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильные данные доступа",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
