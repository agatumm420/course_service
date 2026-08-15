from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from psycopg import Connection
from psycopg.types.json import Json

from database import get_db, row_to_course, row_to_lesson


SERVICE_DIR = Path(__file__).resolve().parent


app = FastAPI(
    title="Courses Service",
    description="Course and lesson management API with a lightweight admin panel.",
    version="1.0.0",
)


class CourseInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)


class LessonInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=160)
    course_id: int | None = None
    position: int | None = Field(default=None, ge=1)
    data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("data")
    @classmethod
    def data_must_be_serializable(cls, value: dict[str, Any]) -> dict[str, Any]:
        try:
            json.dumps(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Lesson data must be valid JSON") from exc
        return value


class ReorderInput(BaseModel):
    lesson_ids: list[int]


def require_course(connection: Connection, course_id: int) -> dict[str, Any]:
    course = connection.execute(
        "SELECT * FROM courses WHERE id = %s", (course_id,)
    ).fetchone()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def require_lesson(connection: Connection, lesson_id: int) -> dict[str, Any]:
    lesson = connection.execute(
        "SELECT * FROM lessons WHERE id = %s", (lesson_id,)
    ).fetchone()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


def next_position(connection: Connection, course_id: int | None) -> int:
    if course_id is None:
        row = connection.execute(
            "SELECT COALESCE(MAX(position), 0) + 1 AS position "
            "FROM lessons WHERE course_id IS NULL"
        ).fetchone()
    else:
        row = connection.execute(
            "SELECT COALESCE(MAX(position), 0) + 1 AS position "
            "FROM lessons WHERE course_id = %s",
            (course_id,),
        ).fetchone()
    return int(row["position"])


def sync_lesson_links(connection: Connection, course_id: int) -> None:
    lessons = connection.execute(
        "SELECT id FROM lessons WHERE course_id = %s ORDER BY position, id",
        (course_id,),
    ).fetchall()
    for index, lesson in enumerate(lessons):
        next_id = lessons[index + 1]["id"] if index + 1 < len(lessons) else None
        connection.execute(
            "UPDATE lessons SET position = %s, next_lesson_id = %s WHERE id = %s",
            (index + 1, next_id, lesson["id"]),
        )


def lesson_query() -> str:
    return """
        SELECT lessons.*, courses.title AS course_title
        FROM lessons
        LEFT JOIN courses ON courses.id = lessons.course_id
    """


@app.get("/", include_in_schema=False)
def admin_panel() -> FileResponse:
    return FileResponse(SERVICE_DIR / "static" / "admin.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/admin/courses")
def list_courses(connection: Connection = Depends(get_db)) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT courses.*, COUNT(lessons.id) AS lesson_count
        FROM courses
        LEFT JOIN lessons ON lessons.course_id = courses.id
        GROUP BY courses.id
        ORDER BY courses.created_at DESC, courses.id DESC
        """
    ).fetchall()
    return [row_to_course(row, row["lesson_count"]) for row in rows]


@app.post("/api/admin/courses", status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseInput,
    connection: Connection = Depends(get_db),
) -> dict[str, Any]:
    course_id = connection.execute(
        "INSERT INTO courses (title, description) VALUES (%s, %s) RETURNING id",
        (payload.title, payload.description),
    ).fetchone()["id"]
    connection.commit()
    course = require_course(connection, course_id)
    return row_to_course(course, 0)


@app.put("/api/admin/courses/{course_id}")
def update_course(
    course_id: int,
    payload: CourseInput,
    connection: Connection = Depends(get_db),
) -> dict[str, Any]:
    require_course(connection, course_id)
    connection.execute(
        "UPDATE courses SET title = %s, description = %s WHERE id = %s",
        (payload.title, payload.description, course_id),
    )
    connection.commit()
    course = require_course(connection, course_id)
    count = connection.execute(
        "SELECT COUNT(*) AS total FROM lessons WHERE course_id = %s", (course_id,)
    ).fetchone()["total"]
    return row_to_course(course, count)


@app.delete("/api/admin/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    connection: Connection = Depends(get_db),
) -> Response:
    require_course(connection, course_id)
    connection.execute("DELETE FROM courses WHERE id = %s", (course_id,))
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/admin/lessons")
def list_lessons(
    course_id: int | None = Query(default=None),
    connection: Connection = Depends(get_db),
) -> list[dict[str, Any]]:
    if course_id is None:
        rows = connection.execute(
            lesson_query() + " ORDER BY course_title, lessons.position, lessons.id"
        ).fetchall()
    else:
        require_course(connection, course_id)
        rows = connection.execute(
            lesson_query()
            + " WHERE lessons.course_id = %s ORDER BY lessons.position, lessons.id",
            (course_id,),
        ).fetchall()
    return [row_to_lesson(row) for row in rows]


@app.post("/api/admin/lessons", status_code=status.HTTP_201_CREATED)
def create_lesson(
    payload: LessonInput,
    connection: Connection = Depends(get_db),
) -> dict[str, Any]:
    if payload.course_id is not None:
        require_course(connection, payload.course_id)
    position = payload.position or next_position(connection, payload.course_id)
    lesson_id = connection.execute(
        """
        INSERT INTO lessons (title, course_id, position, endpoint, data)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            payload.title,
            payload.course_id,
            position,
            str(uuid.uuid4()),
            Json(payload.data),
        ),
    ).fetchone()["id"]
    if payload.course_id is not None:
        sync_lesson_links(connection, payload.course_id)
    connection.commit()
    row = connection.execute(
        lesson_query() + " WHERE lessons.id = %s", (lesson_id,)
    ).fetchone()
    return row_to_lesson(row)


@app.put("/api/admin/lessons/{lesson_id}")
def update_lesson(
    lesson_id: int,
    payload: LessonInput,
    connection: Connection = Depends(get_db),
) -> dict[str, Any]:
    existing = require_lesson(connection, lesson_id)
    if payload.course_id is not None:
        require_course(connection, payload.course_id)
    if payload.position is not None:
        position = payload.position
    elif payload.course_id == existing["course_id"]:
        position = existing["position"]
    else:
        position = next_position(connection, payload.course_id)
    connection.execute(
        """
        UPDATE lessons
        SET title = %s, course_id = %s, position = %s, data = %s
        WHERE id = %s
        """,
        (
            payload.title,
            payload.course_id,
            position,
            Json(payload.data),
            lesson_id,
        ),
    )
    old_course_id = existing["course_id"]
    if old_course_id is not None:
        sync_lesson_links(connection, old_course_id)
    if payload.course_id is not None and payload.course_id != old_course_id:
        sync_lesson_links(connection, payload.course_id)
    connection.commit()
    row = connection.execute(
        lesson_query() + " WHERE lessons.id = %s", (lesson_id,)
    ).fetchone()
    return row_to_lesson(row)


@app.delete("/api/admin/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    lesson_id: int,
    connection: Connection = Depends(get_db),
) -> Response:
    lesson = require_lesson(connection, lesson_id)
    course_id = lesson["course_id"]
    connection.execute("DELETE FROM lessons WHERE id = %s", (lesson_id,))
    if course_id is not None:
        sync_lesson_links(connection, course_id)
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/admin/courses/{course_id}/lessons/reorder")
def reorder_lessons(
    course_id: int,
    payload: ReorderInput,
    connection: Connection = Depends(get_db),
) -> list[dict[str, Any]]:
    require_course(connection, course_id)
    current_ids = [
        row["id"]
        for row in connection.execute(
            "SELECT id FROM lessons WHERE course_id = %s", (course_id,)
        ).fetchall()
    ]
    if len(payload.lesson_ids) != len(set(payload.lesson_ids)):
        raise HTTPException(status_code=400, detail="Lesson IDs must be unique")
    if set(payload.lesson_ids) != set(current_ids):
        raise HTTPException(
            status_code=400,
            detail="Provide every lesson in this course exactly once",
        )
    for position, lesson_id in enumerate(payload.lesson_ids, start=1):
        connection.execute(
            "UPDATE lessons SET position = %s WHERE id = %s",
            (position, lesson_id),
        )
    sync_lesson_links(connection, course_id)
    connection.commit()
    rows = connection.execute(
        lesson_query()
        + " WHERE lessons.course_id = %s ORDER BY lessons.position, lessons.id",
        (course_id,),
    ).fetchall()
    return [row_to_lesson(row) for row in rows]
