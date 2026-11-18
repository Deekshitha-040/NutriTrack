from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Literal

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class AssessmentIn(BaseModel):
    participant_name: str = Field(min_length=2, max_length=100)
    age_years: float = Field(gt=0, le=120)
    gender: Literal["female", "male", "other", "not_specified"] = "not_specified"
    height_cm: float = Field(ge=30, le=250)
    weight_kg: float = Field(gt=1, le=400)
    dietary_habits: str = Field(default="", max_length=1500)
    meals_per_day: int = Field(default=3, ge=0, le=10)
    food_patterns: str = Field(default="", max_length=1500)
    physical_activity: Literal["low", "moderate", "high"] = "moderate"
    dietary_preference: Literal["vegetarian", "non_vegetarian", "vegan", "eggetarian"] = "vegetarian"
    notes: str = Field(default="", max_length=1000)

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    model_config = ConfigDict(from_attributes=True)
