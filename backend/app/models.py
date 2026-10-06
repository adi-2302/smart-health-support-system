"""SQLAlchemy models. Mirrors backend/schema.sql (5 entities), with one addition:
Predictions.risk_score (0-10, probability-weighted) so trends can be tracked on a
continuous scale rather than only on the 3 class labels."""
from datetime import datetime, date
from sqlalchemy import Integer, String, Float, Date, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    age: Mapped[int | None] = mapped_column(Integer)
    gender: Mapped[str | None] = mapped_column(String)
    course: Mapped[str | None] = mapped_column(String)
    year: Mapped[str | None] = mapped_column(String)
    living_conditions: Mapped[str | None] = mapped_column(String)
    mental_health_history: Mapped[int] = mapped_column(Integer, default=0)  # 0/1, model input
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    exams = relationship("ExamSchedule", back_populates="user", order_by="ExamSchedule.updated_at.desc()")
    responses = relationship("DailyResponse", back_populates="user")


class ExamSchedule(Base):
    __tablename__ = "exam_schedule"
    exam_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    exam_label: Mapped[str | None] = mapped_column(String)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="exams")


class DailyResponse(Base):
    __tablename__ = "daily_responses"
    __table_args__ = (UniqueConstraint("user_id", "response_date", name="uq_user_day"),)
    response_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    response_date: Mapped[date] = mapped_column(Date, nullable=False)
    # Raw questionnaire answers (0-4 scale; blood_pressure 1-3)
    anxiety_level: Mapped[int] = mapped_column(Integer)
    self_esteem: Mapped[int] = mapped_column(Integer)
    depression: Mapped[int] = mapped_column(Integer)
    headache: Mapped[int] = mapped_column(Integer)
    blood_pressure: Mapped[int] = mapped_column(Integer)
    sleep_quality: Mapped[int] = mapped_column(Integer)
    breathing_problem: Mapped[int] = mapped_column(Integer)
    noise_level: Mapped[int] = mapped_column(Integer)
    living_conditions: Mapped[int] = mapped_column(Integer)
    safety: Mapped[int] = mapped_column(Integer)
    basic_needs: Mapped[int] = mapped_column(Integer)
    academic_performance: Mapped[int] = mapped_column(Integer)
    study_load: Mapped[int] = mapped_column(Integer)
    teacher_student_relationship: Mapped[int] = mapped_column(Integer)
    future_career_concerns: Mapped[int] = mapped_column(Integer)
    social_support: Mapped[int] = mapped_column(Integer)
    peer_pressure: Mapped[int] = mapped_column(Integer)
    extracurricular_activities: Mapped[int] = mapped_column(Integer)
    bullying: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="responses")
    prediction = relationship("Prediction", back_populates="response", uselist=False)


class Prediction(Base):
    __tablename__ = "predictions"
    prediction_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    response_id: Mapped[int] = mapped_column(ForeignKey("daily_responses.response_id"), nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    predicted_stress_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Low 1=Medium 2=High
    prediction_confidence: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[float] = mapped_column(Float)  # 0-10
    shap_top_factors: Mapped[str | None] = mapped_column(Text)  # JSON
    predicted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    response = relationship("DailyResponse", back_populates="prediction")


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"
    __table_args__ = (UniqueConstraint("user_id", "week_start_date", name="uq_user_week"),)
    report_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    week_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    average_stress_level: Mapped[float | None] = mapped_column(Float)
    highest_stress_day: Mapped[date | None] = mapped_column(Date)
    lowest_stress_day: Mapped[date | None] = mapped_column(Date)
    previous_week_comparison: Mapped[str | None] = mapped_column(String)
    early_warning_triggered: Mapped[int] = mapped_column(Integer, default=0)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
