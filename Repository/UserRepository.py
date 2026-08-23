from __future__ import annotations

from typing import Any

from psycopg import Connection


class UserRepository:
    def __init__(self, connection: Connection[dict[str, Any]]):
        self.connection = connection

    def get(self, user_id: int) -> dict[str, Any] | None:
        return self.connection.execute(
            "SELECT * FROM app_users WHERE id = %s", (user_id,)
        ).fetchone()
