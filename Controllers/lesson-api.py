from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from ..Models.Lesson import Lesson
from ..database import SessionLocal
from app import app, get_db
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, UUID4
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from Repository.UserRepository import UserRepository
from Repository.CourseRepository import CourseRepository
from Repository.CourseDataRepository import CourseDataRepository
from Repository.LessonRepository import LessonRepository
from Repository.LessonDataRepository import LessonDataRepository
class ResourceSchema(BaseModel):
    id: int
    url: HttpUrl
    class Config:
        orm_mode = True

class LessonSchema(BaseModel):
    id: int
    title: str
    index: int
    endpoint: UUID4
    resources: List[ResourceSchema]
    class Config:
        orm_mode = True


@app.get("/lessons/{lesson_id}/next/", response_model=LessonSchema)
def read_next_lesson(
    lesson_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    lesson_repo       = LessonRepository(db)
    lesson_data_repo  = LessonDataRepository(db)
    course_data_repo  = CourseDataRepository(db)

    current = lesson_repo.get(lesson_id)
    if not current:
        raise HTTPException(404, "Lesson not found")

    nxt = lesson_repo.get_next_by_id(lesson_id)
    if not nxt:
        raise HTTPException(404, "Next lesson not found")

    existing_ld = lesson_data_repo.get_by_lesson_id(lesson_id)
    if not existing_ld:
        raise HTTPException(404, "No lesson progress found for this lesson")

    lesson_data_repo.create(
        lesson_id=nxt.id,
        course_data_id=existing_ld.course_data_id,
        data={} 
    )
    course_data_repo.set_current_lesson(existing_ld.course_data_id, nxt.id)
    db.commit()

    resources = []
    for res in nxt.resources:
        fn  = res.path.rsplit("/", 1)[-1]
        url = request.url_for("uploads") + f"/{fn}"
        resources.append(ResourceSchema(id=res.id, url=url))

    return LessonSchema(
        id=nxt.id,
        title=nxt.title,
        index=nxt.index,
        endpoint=nxt.endpoint,
        resources=resources
    )

@app.get(
    "/users/{user_id}/courses/{course_id}/current-lesson",
    response_model=LessonSchema,
    summary="Get the current lesson for a user’s course"
)
def get_current_lesson(
    user_id: int,
    course_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    cd_repo     = CourseDataRepository(db)


    cd = cd_repo.get_by_user_and_course(user_id, course_id)
    if not cd or not cd.current_lesson:
        raise HTTPException(
            status_code=404,
            detail="No current lesson found for this user/course"
        )

    lesson = cd.current_lesson

    resources = []
    for res in lesson.resources:
        fn  = res.path.rsplit("/", 1)[-1]
        url = request.url_for("uploads") + f"/{fn}"
        resources.append(ResourceSchema(id=res.id, url=url))

    return LessonSchema(
        id=lesson.id,
        title=lesson.title,
        index=lesson.index,
        endpoint=lesson.endpoint,
        resources=resources
    )
