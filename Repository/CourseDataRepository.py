from __future__ import annotations

from typing import Any

from psycopg import Connection


class CourseDataRepository:
    def __init__(self, connection: Connection[dict[str, Any]]):
        self.connection = connection

    def create(self, user_id: int, course_id: int) -> dict[str, Any]:
        return self.connection.execute(
            """
            INSERT INTO course_data (user_id, course_id)
            VALUES (%s, %s)
            RETURNING id, user_id, course_id
            """,
            (user_id, course_id),
        ).fetchone()

    def get_by_user_and_course(
        self, user_id: int, course_id: int
    ) -> dict[str, Any] | None:
        return self.connection.execute(
            """
            SELECT id, user_id, course_id
            FROM course_data
            WHERE user_id = %s AND course_id = %s
            ORDER BY id
            LIMIT 1
            """,
            (user_id, course_id),
        ).fetchone()
