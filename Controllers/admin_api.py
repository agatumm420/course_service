from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from psycopg import Connection
from psycopg.errors import UniqueViolation

from database import get_db
from Repository.ComponentFieldRepository import ComponentFieldRepository
from Repository.ComponentRepository import ComponentRepository
from Repository.CourseRepository import CourseRepository
from Repository.LessonComponentRepository import LessonComponentRepository
from Repository.LessonRepository import LessonRepository


SERVICE_DIR = Path(__file__).resolve().parents[1]
router = APIRouter()


class CourseInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)


class ComponentFieldInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    value: str | None = None
    data: Any | None = None

    @field_validator("data")
    @classmethod
    def data_must_be_serializable(cls, value: Any | None) -> Any | None:
        try:
            json.dumps(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Component field data must be valid JSON") from exc
        return value


class ComponentInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    component_id: int | None = Field(default=None, gt=0)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    fields: list[ComponentFieldInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def is_existing_or_new(self) -> "ComponentInput":
        if self.component_id is None and self.name is None:
            raise ValueError("A new component needs a name")
        if self.component_id is not None and (
            self.name is not None or self.fields
        ):
            raise ValueError(
                "Existing components must be provided using component_id only"
            )
        return self


class LessonInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=100)
    course_id: int | None = None
    position: int | None = Field(default=None, ge=1)
    components: list[ComponentInput] = Field(default_factory=list)

    @model_validator(mode="after")
    def components_are_unique(self) -> "LessonInput":
        component_ids = [
            component.component_id
            for component in self.components
            if component.component_id is not None
        ]
        if len(component_ids) != len(set(component_ids)):
            raise ValueError("A component can only be assigned once per lesson")
        return self


class ReorderInput(BaseModel):
    lesson_ids: list[int]


def require_course(repository: CourseRepository, course_id: int) -> dict[str, Any]:
    course = repository.get(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def require_lesson(repository: LessonRepository, lesson_id: int) -> dict[str, Any]:
    lesson = repository.get_record(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


def attach_components(
    lessons: list[dict[str, Any]],
    component_repository: ComponentRepository,
    field_repository: ComponentFieldRepository,
) -> list[dict[str, Any]]:
    components = component_repository.list_for_lessons(
        [lesson["id"] for lesson in lessons]
    )
    attach_fields(components, field_repository)

    components_by_lesson: dict[int, list[dict[str, Any]]] = {}
    for component in components:
        components_by_lesson.setdefault(component["lesson_id"], []).append(component)

    for lesson in lessons:
        lesson["components"] = components_by_lesson.get(lesson["id"], [])
    return lessons


def attach_fields(
    components: list[dict[str, Any]],
    field_repository: ComponentFieldRepository,
) -> list[dict[str, Any]]:
    fields = field_repository.list_for_components(
        [component["id"] for component in components]
    )

    fields_by_component: dict[int, list[dict[str, Any]]] = {}
    for field in fields:
        fields_by_component.setdefault(field["component_id"], []).append(field)

    for component in components:
        component["fields"] = fields_by_component.get(component["id"], [])
    return components


def get_lesson_with_components(
    lesson_id: int,
    lesson_repository: LessonRepository,
    component_repository: ComponentRepository,
    field_repository: ComponentFieldRepository,
) -> dict[str, Any]:
    lesson = lesson_repository.get(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return attach_components(
        [lesson], component_repository, field_repository
    )[0]


def replace_components(
    lesson_id: int,
    components: list[ComponentInput],
    component_repository: ComponentRepository,
    field_repository: ComponentFieldRepository,
    assignment_repository: LessonComponentRepository,
) -> None:
    assignment_repository.delete_for_lesson(lesson_id)
    for position, component in enumerate(components, start=1):
        if component.component_id is not None:
            if component_repository.get(component.component_id) is None:
                raise HTTPException(status_code=404, detail="Component not found")
            component_id = component.component_id
        else:
            if component_repository.get_by_name(component.name) is not None:
                raise HTTPException(
                    status_code=409,
                    detail="Component name already exists; select the saved component",
                )
            try:
                component_id = component_repository.create(component.name)
            except UniqueViolation as exc:
                component_repository.connection.rollback()
                raise HTTPException(
                    status_code=409, detail="Component name already exists"
                ) from exc
            for field in component.fields:
                field_repository.create(
                    component_id,
                    field.name,
                    field.value,
                    field.data,
                )
        assignment_repository.assign(lesson_id, component_id, position)


@router.get("/", include_in_schema=False)
def admin_panel() -> FileResponse:
    return FileResponse(SERVICE_DIR / "static" / "admin.html")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/admin/courses")
def list_courses(
    connection: Connection = Depends(get_db),
) -> list[dict[str, Any]]:
    return CourseRepository(connection).list_with_lesson_counts()


@router.post("/api/admin/courses", status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseInput,
    connection: Connection = Depends(get_db),
) -> dict[str, Any]:
    repository = CourseRepository(connection)
    course_id = repository.create(payload.title, payload.description)
    connection.commit()
    return repository.get_with_lesson_count(course_id)


@router.put("/api/admin/courses/{course_id}")
def update_course(
    course_id: int,
    payload: CourseInput,
    connection: Connection = Depends(get_db),
) -> dict[str, Any]:
    repository = CourseRepository(connection)
    require_course(repository, course_id)
    repository.update(course_id, payload.title, payload.description)
    connection.commit()
    return repository.get_with_lesson_count(course_id)


@router.delete(
    "/api/admin/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_course(
    course_id: int,
    connection: Connection = Depends(get_db),
) -> Response:
    repository = CourseRepository(connection)
    require_course(repository, course_id)
    repository.delete(course_id)
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/api/admin/components")
def list_components(
    connection: Connection = Depends(get_db),
) -> list[dict[str, Any]]:
    components = ComponentRepository(connection).list()
    return attach_fields(components, ComponentFieldRepository(connection))


@router.get("/api/admin/lessons")
def list_lessons(
    course_id: int | None = Query(default=None),
    connection: Connection = Depends(get_db),
) -> list[dict[str, Any]]:
    if course_id is not None:
        require_course(CourseRepository(connection), course_id)

    lessons = LessonRepository(connection).list(course_id)
    return attach_components(
        lessons,
        ComponentRepository(connection),
        ComponentFieldRepository(connection),
    )


@router.post("/api/admin/lessons", status_code=status.HTTP_201_CREATED)
def create_lesson(
    payload: LessonInput,
    connection: Connection = Depends(get_db),
) -> dict[str, Any]:
    course_repository = CourseRepository(connection)
    lesson_repository = LessonRepository(connection)
    component_repository = ComponentRepository(connection)
    field_repository = ComponentFieldRepository(connection)
    assignment_repository = LessonComponentRepository(connection)

    if payload.course_id is not None:
        require_course(course_repository, payload.course_id)

    position = payload.position or lesson_repository.next_position(payload.course_id)
    lesson_id = lesson_repository.create(payload.title, payload.course_id, position)
    replace_components(
        lesson_id,
        payload.components,
        component_repository,
        field_repository,
        assignment_repository,
    )
    if payload.course_id is not None:
        lesson_repository.sync_links(payload.course_id)

    connection.commit()
    return get_lesson_with_components(
        lesson_id,
        lesson_repository,
        component_repository,
        field_repository,
    )


@router.put("/api/admin/lessons/{lesson_id}")
def update_lesson(
    lesson_id: int,
    payload: LessonInput,
    connection: Connection = Depends(get_db),
) -> dict[str, Any]:
    course_repository = CourseRepository(connection)
    lesson_repository = LessonRepository(connection)
    component_repository = ComponentRepository(connection)
    field_repository = ComponentFieldRepository(connection)
    assignment_repository = LessonComponentRepository(connection)

    existing = require_lesson(lesson_repository, lesson_id)
    if payload.course_id is not None:
        require_course(course_repository, payload.course_id)

    if payload.position is not None:
        position = payload.position
    elif payload.course_id == existing["course_id"]:
        position = existing["position"]
    else:
        position = lesson_repository.next_position(payload.course_id)

    lesson_repository.update(
        lesson_id,
        payload.title,
        payload.course_id,
        position,
    )
    replace_components(
        lesson_id,
        payload.components,
        component_repository,
        field_repository,
        assignment_repository,
    )

    old_course_id = existing["course_id"]
    if old_course_id is not None:
        lesson_repository.sync_links(old_course_id)
    if payload.course_id is not None and payload.course_id != old_course_id:
        lesson_repository.sync_links(payload.course_id)

    connection.commit()
    return get_lesson_with_components(
        lesson_id,
        lesson_repository,
        component_repository,
        field_repository,
    )


@router.delete(
    "/api/admin/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_lesson(
    lesson_id: int,
    connection: Connection = Depends(get_db),
) -> Response:
    repository = LessonRepository(connection)
    lesson = require_lesson(repository, lesson_id)
    repository.delete(lesson_id)
    if lesson["course_id"] is not None:
        repository.sync_links(lesson["course_id"])
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/api/admin/courses/{course_id}/lessons/reorder")
def reorder_lessons(
    course_id: int,
    payload: ReorderInput,
    connection: Connection = Depends(get_db),
) -> list[dict[str, Any]]:
    require_course(CourseRepository(connection), course_id)
    lesson_repository = LessonRepository(connection)
    current_ids = lesson_repository.ids_for_course(course_id)

    if len(payload.lesson_ids) != len(set(payload.lesson_ids)):
        raise HTTPException(status_code=400, detail="Lesson IDs must be unique")
    if set(payload.lesson_ids) != set(current_ids):
        raise HTTPException(
            status_code=400,
            detail="Provide every lesson in this course exactly once",
        )

    lesson_repository.reorder(course_id, payload.lesson_ids)
    connection.commit()
    lessons = lesson_repository.list(course_id)
    return attach_components(
        lessons,
        ComponentRepository(connection),
        ComponentFieldRepository(connection),
    )
