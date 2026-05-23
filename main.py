from fastapi import FastAPI
from fastapi.responses import FileResponse
from models import User, UserAge, Feedback

app = FastAPI()

feedbacks = []

@app.get("/welcome")
async def welcome():
    return {"message": "Добро пожаловать в моё приложение FastAPI!"}

@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.post("/calculate")
async def calculate(num1: int, num2: int):
    return {"result": num1 + num2}

@app.get("/users")
async def get_user():
    user = User(name="Якушин Владимир", id=1)
    return user

@app.post("/user")
async def check_adult(user: UserAge):
    is_adult = user.age >= 18
    return {**user.model_dump(), "is_adult": is_adult}

@app.post("/feedback")
async def add_feedback(feedback: Feedback):
    feedbacks.append(feedback)
    return {"message": f"Спасибо, {feedback.name}! Ваш отзыв сохранён."}
