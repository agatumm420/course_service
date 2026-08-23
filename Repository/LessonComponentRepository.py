from __future__ import annotations

from typing import Any

from psycopg import Connection


class LessonComponentRepository:
    def __init__(self, connection: Connection[dict[str, Any]]):
        self.connection = connection

    def delete_for_lesson(self, lesson_id: int) -> None:
        self.connection.execute(
            "DELETE FROM lesson_component WHERE lesson_id = %s", (lesson_id,)
        )

    def assign(self, lesson_id: int, component_id: int, position: int) -> None:
        self.connection.execute(
            """
            INSERT INTO lesson_component (lesson_id, component_id, position)
            VALUES (%s, %s, %s)
            """,
            (lesson_id, component_id, position),
        )
