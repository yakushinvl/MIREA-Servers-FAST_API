from pydantic import BaseModel, Field, field_validator

class User(BaseModel):
    name: str
    id: int

class UserAge(BaseModel):
    name: str
    age: int

class Feedback(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    message: str = Field(..., min_length=10, max_length=500)

    @field_validator('message')
    @classmethod
    def check_forbidden_words(cls, v):
        forbidden_words = ["кринж", "рофл", "вайб"]
        for word in forbidden_words:
            if word in v.lower():
                raise ValueError("Использование недопустимых слов")
        return v
