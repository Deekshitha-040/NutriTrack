from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from backend.database import Base

def now_utc():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    assessments = relationship("Assessment", back_populates="user", cascade="all, delete-orphan")

class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    participant_name: Mapped[str] = mapped_column(String(100))
    age_years: Mapped[float] = mapped_column(Float)
    gender: Mapped[str] = mapped_column(String(30))
    height_cm: Mapped[float] = mapped_column(Float)
    weight_kg: Mapped[float] = mapped_column(Float)
    dietary_habits: Mapped[str] = mapped_column(Text, default="")
    meals_per_day: Mapped[int] = mapped_column(Integer, default=3)
    food_patterns: Mapped[str] = mapped_column(Text, default="")
    physical_activity: Mapped[str] = mapped_column(String(40), default="moderate")
    dietary_preference: Mapped[str] = mapped_column(String(40), default="vegetarian")
    notes: Mapped[str] = mapped_column(Text, default="")
    bmi: Mapped[float] = mapped_column(Float)
    indicator_status: Mapped[str] = mapped_column(String(80))
    risk_level: Mapped[str] = mapped_column(String(40))
    observations: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    user = relationship("User", back_populates="assessments")
    prediction = relationship("Prediction", back_populates="assessment", uselist=False, cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="assessment", cascade="all, delete-orphan")

class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"), unique=True)
    method: Mapped[str] = mapped_column(String(100))
    result: Mapped[str] = mapped_column(String(100))
    explanation: Mapped[str] = mapped_column(Text)
    anomaly_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    assessment = relationship("Assessment", back_populates="prediction")

class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"), index=True)
    category: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)
    assessment = relationship("Assessment", back_populates="recommendations")
