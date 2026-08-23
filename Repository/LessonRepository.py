from __future__ import annotations

from typing import Any

from psycopg import Connection


LESSON_QUERY = """
    SELECT
        lessons.*,
        courses.title AS course_title
    FROM lessons
    LEFT JOIN courses ON courses.id = lessons.course_id
"""


class LessonRepository:
    def __init__(self, connection: Connection[dict[str, Any]]):
        self.connection = connection

    @staticmethod
    def _to_dict(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "title": row["title"],
            "course_id": row["course_id"],
            "course_title": row.get("course_title"),
            "position": row["position"],
            "components": [],
            "next_lesson_id": row["next_lesson_id"],
            "created_at": row["created_at"],
        }

    def list(self, course_id: int | None = None) -> list[dict[str, Any]]:
        if course_id is None:
            rows = self.connection.execute(
                LESSON_QUERY
                + " ORDER BY course_title, lessons.position, lessons.id"
            ).fetchall()
        else:
            rows = self.connection.execute(
                LESSON_QUERY
                + " WHERE lessons.course_id = %s"
                + " ORDER BY lessons.position, lessons.id",
                (course_id,),
            ).fetchall()
        return [self._to_dict(row) for row in rows]

    def get(self, lesson_id: int) -> dict[str, Any] | None:
        row = self.connection.execute(
            LESSON_QUERY + " WHERE lessons.id = %s", (lesson_id,)
        ).fetchone()
        return self._to_dict(row) if row else None

    def get_record(self, lesson_id: int) -> dict[str, Any] | None:
        return self.connection.execute(
            "SELECT * FROM lessons WHERE id = %s", (lesson_id,)
        ).fetchone()

    def next_position(self, course_id: int | None) -> int:
        if course_id is None:
            row = self.connection.execute(
                "SELECT COALESCE(MAX(position), 0) + 1 AS position "
                "FROM lessons WHERE course_id IS NULL"
            ).fetchone()
        else:
            row = self.connection.execute(
                "SELECT COALESCE(MAX(position), 0) + 1 AS position "
                "FROM lessons WHERE course_id = %s",
                (course_id,),
            ).fetchone()
        return int(row["position"])

    def create(
        self,
        title: str,
        course_id: int | None,
        position: int,
    ) -> int:
        return self.connection.execute(
            """
            INSERT INTO lessons (title, course_id, position)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (title, course_id, position),
        ).fetchone()["id"]

    def update(
        self,
        lesson_id: int,
        title: str,
        course_id: int | None,
        position: int,
    ) -> None:
        self.connection.execute(
            """
            UPDATE lessons
            SET title = %s, course_id = %s, position = %s
            WHERE id = %s
            """,
            (title, course_id, position, lesson_id),
        )

    def delete(self, lesson_id: int) -> None:
        self.connection.execute("DELETE FROM lessons WHERE id = %s", (lesson_id,))

    def ids_for_course(self, course_id: int) -> list[int]:
        rows = self.connection.execute(
            "SELECT id FROM lessons WHERE course_id = %s", (course_id,)
        ).fetchall()
        return [row["id"] for row in rows]

    def reorder(self, course_id: int, lesson_ids: list[int]) -> None:
        for position, lesson_id in enumerate(lesson_ids, start=1):
            self.connection.execute(
                "UPDATE lessons SET position = %s WHERE id = %s",
                (position, lesson_id),
            )
        self.sync_links(course_id)

    def sync_links(self, course_id: int) -> None:
        lessons = self.connection.execute(
            "SELECT id FROM lessons WHERE course_id = %s ORDER BY position, id",
            (course_id,),
        ).fetchall()
        for index, lesson in enumerate(lessons):
            next_id = lessons[index + 1]["id"] if index + 1 < len(lessons) else None
            self.connection.execute(
                "UPDATE lessons SET position = %s, next_lesson_id = %s WHERE id = %s",
                (index + 1, next_id, lesson["id"]),
            )
