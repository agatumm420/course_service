from __future__ import annotations

from typing import Any

from psycopg import Connection


class CourseRepository:
    def __init__(self, connection: Connection[dict[str, Any]]):
        self.connection = connection

    @staticmethod
    def _to_dict(
        row: dict[str, Any], lesson_count: int | None = None
    ) -> dict[str, Any]:
        result = {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "created_at": row["created_at"],
        }
        if lesson_count is not None:
            result["lesson_count"] = lesson_count
        return result

    def list_with_lesson_counts(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT courses.*, COUNT(lessons.id) AS lesson_count
            FROM courses
            LEFT JOIN lessons ON lessons.course_id = courses.id
            GROUP BY courses.id
            ORDER BY courses.created_at DESC, courses.id DESC
            """
        ).fetchall()
        return [self._to_dict(row, row["lesson_count"]) for row in rows]

    def get(self, course_id: int) -> dict[str, Any] | None:
        return self.connection.execute(
            "SELECT * FROM courses WHERE id = %s", (course_id,)
        ).fetchone()

    def get_with_lesson_count(self, course_id: int) -> dict[str, Any] | None:
        row = self.get(course_id)
        if row is None:
            return None
        count = self.connection.execute(
            "SELECT COUNT(*) AS total FROM lessons WHERE course_id = %s",
            (course_id,),
        ).fetchone()["total"]
        return self._to_dict(row, count)

    def create(self, title: str, description: str) -> int:
        return self.connection.execute(
            "INSERT INTO courses (title, description) VALUES (%s, %s) RETURNING id",
            (title, description),
        ).fetchone()["id"]

    def update(self, course_id: int, title: str, description: str) -> None:
        self.connection.execute(
            "UPDATE courses SET title = %s, description = %s WHERE id = %s",
            (title, description, course_id),
        )

    def delete(self, course_id: int) -> None:
        self.connection.execute("DELETE FROM courses WHERE id = %s", (course_id,))
