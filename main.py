from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from models import User, UserAge, Feedback

app = FastAPI()

fake_user = User(name="Якушин Владимир", id=1)

feedbacks = []

class Calculation(BaseModel):
    num1: float
    num2: float

@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.post("/calculate")
async def calculate(data: Calculation):
    return {"result": data.num1 + data.num2}

@app.get("/users")
async def get_user():
    return fake_user

@app.post("/user")
async def check_adult(user: UserAge):
    return {
        "name": user.name,
        "age": user.age,
        "is_adult": user.age >= 18
    }

@app.post("/feedback")
async def create_feedback(feedback: Feedback):
    feedbacks.append(feedback.dict())
    return {"message": f"Спасибо, {feedback.name}! Ваш отзыв сохранён."}