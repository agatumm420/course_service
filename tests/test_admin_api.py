import os
import unittest
import uuid

from fastapi.testclient import TestClient


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@unittest.skipUnless(
    TEST_DATABASE_URL,
    "Set TEST_DATABASE_URL to a migrated disposable PostgreSQL database",
)
class AdminApiIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DATABASE_URL"] = TEST_DATABASE_URL
        from app import app

        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)
        os.environ.pop("DATABASE_URL", None)

    def setUp(self):
        self.created_lesson_ids = []
        self.created_component_ids = set()
        self.created_course_ids = []

    def tearDown(self):
        for lesson_id in self.created_lesson_ids:
            self.client.delete(f"/api/admin/lessons/{lesson_id}")
        if self.created_component_ids:
            from database import connect

            with connect() as connection:
                connection.execute(
                    "DELETE FROM components WHERE id = ANY(%s)",
                    (list(self.created_component_ids),),
                )
        for course_id in self.created_course_ids:
            self.client.delete(f"/api/admin/courses/{course_id}")

    def create_course(self):
        response = self.client.post(
            "/api/admin/courses",
            json={
                "title": f"Test course {uuid.uuid4()}",
                "description": "Disposable integration-test data",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.created_course_ids.append(response.json()["id"])
        return response.json()

    def create_lesson(self, course_id, title):
        suffix = uuid.uuid4()
        component_names = [f"hero-{suffix}", f"footer-{suffix}"]
        response = self.client.post(
            "/api/admin/lessons",
            json={
                "title": title,
                "course_id": course_id,
                "components": [
                    {
                        "name": component_names[0],
                        "fields": [
                            {"name": "title", "value": title},
                            {"name": "settings", "data": {"minutes": 5}},
                        ]
                    },
                    {
                        "name": component_names[1],
                        "fields": [{"name": "footer", "value": "Continue"}],
                    },
                ],
            },
        )
        self.assertEqual(response.status_code, 201)
        lesson = response.json()
        self.created_lesson_ids.append(lesson["id"])
        self.created_component_ids.update(
            component["id"] for component in lesson["components"]
        )
        self.assertEqual(
            [component["position"] for component in lesson["components"]], [1, 2]
        )
        self.assertEqual(
            [component["name"] for component in lesson["components"]],
            component_names,
        )
        self.assertEqual(lesson["components"][0]["fields"][0]["name"], "title")
        self.assertEqual(
            lesson["components"][0]["fields"][1]["data"], {"minutes": 5}
        )
        return lesson

    def test_course_lesson_workflow_and_links(self):
        course = self.create_course()
        first = self.create_lesson(course["id"], "Welcome")
        second = self.create_lesson(course["id"], "Practice")

        lessons = self.client.get(
            "/api/admin/lessons", params={"course_id": course["id"]}
        ).json()
        self.assertEqual([lesson["title"] for lesson in lessons], ["Welcome", "Practice"])
        self.assertEqual(lessons[0]["next_lesson_id"], second["id"])
        self.assertIsNone(lessons[1]["next_lesson_id"])

        reordered = self.client.post(
            f"/api/admin/courses/{course['id']}/lessons/reorder",
            json={"lesson_ids": [second["id"], first["id"]]},
        )
        self.assertEqual(reordered.status_code, 200)
        self.assertEqual(
            [lesson["title"] for lesson in reordered.json()],
            ["Practice", "Welcome"],
        )
        self.assertEqual(reordered.json()[0]["next_lesson_id"], first["id"])

    def test_invalid_course_assignment_is_rejected(self):
        response = self.client.post(
            "/api/admin/lessons",
            json={
                "title": "Lost lesson",
                "course_id": 2_147_483_647,
                "components": [],
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_components_and_fields_can_be_replaced(self):
        course = self.create_course()
        lesson = self.create_lesson(course["id"], "First lesson")
        component_name = f"quote-{uuid.uuid4()}"

        response = self.client.put(
            f"/api/admin/lessons/{lesson['id']}",
            json={
                "title": "Updated lesson",
                "course_id": course["id"],
                "components": [
                    {
                        "name": component_name,
                        "fields": [
                            {"name": "quote_text", "value": "Recovery takes time"},
                            {
                                "name": "appearance",
                                "data": {"emphasis": "strong"},
                            },
                        ]
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        updated = response.json()
        self.created_component_ids.update(
            component["id"] for component in updated["components"]
        )
        self.assertEqual(len(updated["components"]), 1)
        self.assertEqual(updated["components"][0]["name"], component_name)
        self.assertEqual(updated["components"][0]["position"], 1)
        self.assertEqual(
            [field["name"] for field in updated["components"][0]["fields"]],
            ["quote_text", "appearance"],
        )
        self.assertEqual(
            updated["components"][0]["fields"][1]["data"],
            {"emphasis": "strong"},
        )

    def test_saved_component_can_be_assigned_to_another_lesson(self):
        course = self.create_course()
        first = self.create_lesson(course["id"], "First lesson")
        saved_component = first["components"][0]

        library = self.client.get("/api/admin/components")
        self.assertEqual(library.status_code, 200)
        self.assertIn(
            saved_component["name"],
            [component["name"] for component in library.json()],
        )

        response = self.client.post(
            "/api/admin/lessons",
            json={
                "title": "Second lesson",
                "course_id": course["id"],
                "components": [{"component_id": saved_component["id"]}],
            },
        )

        self.assertEqual(response.status_code, 201)
        second = response.json()
        self.created_lesson_ids.append(second["id"])
        self.assertEqual(second["components"][0]["id"], saved_component["id"])
        self.assertEqual(
            second["components"][0]["name"], saved_component["name"]
        )

    def test_component_names_must_be_unique(self):
        course = self.create_course()
        lesson = self.create_lesson(course["id"], "First lesson")

        response = self.client.post(
            "/api/admin/lessons",
            json={
                "title": "Duplicate component",
                "course_id": course["id"],
                "components": [
                    {
                        "name": lesson["components"][0]["name"],
                        "fields": [],
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 409)


if __name__ == "__main__":
    unittest.main()
