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

    @field_validator("message")
    def check_bad_words(cls, v: str) -> str:
        bad_words = ["крингк", "рофл", "вайб"]
        v_lower = v.lower()
        for word in bad_words:
            if word in v_lower:
                raise ValueError("Использование недопустимых слов")
        return v