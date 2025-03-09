from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from ..Models.Lesson import Lesson
from ..database import SessionLocal
from ..main import app



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/lessons/{lesson_id}/next/")
def read_next_lesson(lesson_id: int, db: Session = Depends(get_db)):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if lesson is None:
        return {"error": "Lesson not found"}
    next_lesson = lesson.get_next_lesson(db)
    return next_lesson


