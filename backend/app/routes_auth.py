from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import User, ExamSchedule
from .schemas import RegisterRequest, LoginRequest, ExamUpdate
from .security import hash_password, verify_password, create_token, get_current_user
from .services import exam_info

router = APIRouter(tags=["auth & profile"])


def _user_dict(u: User) -> dict:
    return {"user_id": u.user_id, "name": u.name, "email": u.email, "age": u.age, "gender": u.gender,
            "course": u.course, "year": u.year, "living_conditions": u.living_conditions,
            "mental_health_history": bool(u.mental_health_history)}


@router.post("/auth/register", status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    user = User(name=body.name, email=body.email, password_hash=hash_password(body.password), age=body.age,
                gender=body.gender, course=body.course, year=body.year, living_conditions=body.living_conditions,
                mental_health_history=int(body.mental_health_history))
    db.add(user)
    db.flush()
    db.add(ExamSchedule(user_id=user.user_id, exam_date=body.exam_date, exam_label=body.exam_label,
                        updated_at=datetime.utcnow()))
    db.commit()
    db.refresh(user)
    return {"token": create_token(user.user_id), "user": _user_dict(user),
            "exam": exam_info(user, date.today())}


@router.post("/auth/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    return {"token": create_token(user.user_id), "user": _user_dict(user)}


@router.get("/profile")
def profile(user: User = Depends(get_current_user)):
    return {"user": _user_dict(user), "exam": exam_info(user, date.today())}


@router.put("/profile/exam")
def update_exam(body: ExamUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.add(ExamSchedule(user_id=user.user_id, exam_date=body.exam_date, exam_label=body.exam_label,
                        updated_at=datetime.utcnow()))
    db.commit()
    db.refresh(user)
    return {"exam": exam_info(user, date.today())}


@router.get("/exam/countdown")
def countdown(user: User = Depends(get_current_user)):
    """Days Remaining = Exam Date - Today (computed on every request; the student is never re-asked)."""
    return exam_info(user, date.today())
