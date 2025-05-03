from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl, UUID4

from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate as sqlalchemy_paginate

from  app import get_db, app
from ..Models.User import User
from ..Models.Course import Course
from ..Models.Lesson import Lesson
from ..Models.CourseData import CourseData
from ..Models.LessonData import LessonData

from Repository.UserRepository import UserRepository
from Repository.CourseRepository import CourseRepository
from Repository.CourseDataRepository import CourseDataRepository
from Repository.LessonRepository import LessonRepository
from Repository.LessonDataRepository import LessonDataRepository

class CourseSchema(BaseModel):
    id: int
    title: str
    resource_url: Optional[HttpUrl] = None

    class Config:
        orm_mode = True


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


class CourseDataSchema(BaseModel):
    id: int
    user_id: int
    course_id: int
    current_lesson: Optional[LessonSchema] = None

    class Config:
        orm_mode = True


@app.get("/courses/", response_model=Page[CourseSchema])
def list_courses(
    request: Request,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(None),
):
    course_repo = CourseRepository(db)

    query = course_repo.query(user_id=user_id)
    page = sqlalchemy_paginate(query)

    new_items: List[CourseSchema] = []
    for course in page.items:
        if course.resource:
            filename = course.resource.path.rsplit("/", 1)[-1]
            url = request.url_for("uploads") + f"/{filename}"
        else:
            url = None

        new_items.append(CourseSchema(
            id=course.id,
            title=course.title,
            resource_url=url
        ))

    page.items = new_items
    return page

@app.post(
    "/users/{user_id}/courses/{course_id}/enroll",
    response_model=CourseDataSchema,
    summary="Enroll a user in a course and initialize their first lesson"
)
def enroll_user_in_course(
    user_id: int,
    course_id: int,
    request: Request,
    db: Session = Depends(get_db),
):

    user_repo        = UserRepository(db)
    course_repo      = CourseRepository(db)
    cd_repo          = CourseDataRepository(db)
    lesson_repo      = LessonRepository(db)
    lesson_data_repo = LessonDataRepository(db)

    user = user_repo.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    course = course_repo.get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    course_data = cd_repo.create(user_id=user_id, course_id=course_id)

    first_lesson = lesson_repo.get_first_by_course(course_id)
    lesson_schema: Optional[LessonSchema] = None

    if first_lesson:
        lesson_data_repo.create(
            lesson_id=first_lesson.id,
            course_data_id=course_data.id,
            data={}
        )

        res_list: List[ResourceSchema] = []
        for res in first_lesson.resources:
            fn = res.path.rsplit("/", 1)[-1]
            url = request.url_for("uploads") + f"/{fn}"
            res_list.append(ResourceSchema(id=res.id, url=url))

        lesson_schema = LessonSchema(
            id=first_lesson.id,
            title=first_lesson.title,
            index=first_lesson.index,
            endpoint=first_lesson.endpoint,
            resources=res_list
        )

    db.commit()
    db.refresh(course_data)

    return CourseDataSchema(
        id=course_data.id,
        user_id=user_id,
        course_id=course_id,
        current_lesson=lesson_schema
    )
