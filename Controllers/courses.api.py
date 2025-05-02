from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from ..Models.Lesson import Lesson
from ..database import SessionLocal
from ..main import app
from ..Models.User import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@app.get("/users/{user_id}/courses/")
def list_user_courses(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is not None:
        return [{"course_id": course.id, "course_title": course.title} for course in user.courses]
    else:
        return {"error": "User not found"}