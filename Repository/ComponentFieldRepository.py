from __future__ import annotations

from typing import Any

from psycopg import Connection
from psycopg.types.json import Json


class ComponentFieldRepository:
    def __init__(self, connection: Connection[dict[str, Any]]):
        self.connection = connection

    def list_for_components(self, component_ids: list[int]) -> list[dict[str, Any]]:
        if not component_ids:
            return []
        return self.connection.execute(
            """
            SELECT id, component_id, name, value, data
            FROM component_fields
            WHERE component_id = ANY(%s)
            ORDER BY component_id, id
            """,
            (component_ids,),
        ).fetchall()

    def create(
        self,
        component_id: int,
        name: str,
        value: str | None,
        data: Any | None,
    ) -> int:
        json_data = Json(data) if data is not None else None
        return self.connection.execute(
            """
            INSERT INTO component_fields (component_id, name, value, data)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (component_id, name, value, json_data),
        ).fetchone()["id"]
