from __future__ import annotations

from typing import Any

from psycopg import Connection
from psycopg.types.json import Json


class LessonDataRepository:
    def __init__(self, connection: Connection[dict[str, Any]]):
        self.connection = connection

    def replace(self, lesson_id: int, data: dict[str, Any]) -> None:
        self.connection.execute(
            "DELETE FROM lesson_data WHERE lesson_id = %s", (lesson_id,)
        )
        self.connection.execute(
            "INSERT INTO lesson_data (lesson_id, data) VALUES (%s, %s)",
            (lesson_id, Json(data)),
        )
