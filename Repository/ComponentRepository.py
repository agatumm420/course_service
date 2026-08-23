from __future__ import annotations

from typing import Any

from psycopg import Connection


class ComponentRepository:
    def __init__(self, connection: Connection[dict[str, Any]]):
        self.connection = connection

    def list_for_lessons(self, lesson_ids: list[int]) -> list[dict[str, Any]]:
        if not lesson_ids:
            return []
        return self.connection.execute(
            """
            SELECT
                components.id,
                components.name,
                lesson_component.lesson_id,
                lesson_component.position
            FROM lesson_component
            JOIN components ON components.id = lesson_component.component_id
            WHERE lesson_component.lesson_id = ANY(%s)
            ORDER BY lesson_component.lesson_id,
                     lesson_component.position,
                     components.id
            """,
            (lesson_ids,),
        ).fetchall()

    def list(self) -> list[dict[str, Any]]:
        return self.connection.execute(
            "SELECT id, name FROM components ORDER BY name, id"
        ).fetchall()

    def get(self, component_id: int) -> dict[str, Any] | None:
        return self.connection.execute(
            "SELECT id, name FROM components WHERE id = %s", (component_id,)
        ).fetchone()

    def get_by_name(self, name: str) -> dict[str, Any] | None:
        return self.connection.execute(
            "SELECT id, name FROM components WHERE name = %s", (name,)
        ).fetchone()

    def create(self, name: str) -> int:
        return self.connection.execute(
            """
            INSERT INTO components (name)
            VALUES (%s)
            RETURNING id
            """,
            (name,),
        ).fetchone()["id"]
