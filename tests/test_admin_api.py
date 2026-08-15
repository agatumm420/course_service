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
        self.created_course_ids = []

    def tearDown(self):
        for lesson_id in self.created_lesson_ids:
            self.client.delete(f"/api/admin/lessons/{lesson_id}")
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
        response = self.client.post(
            "/api/admin/lessons",
            json={"title": title, "course_id": course_id, "data": {"minutes": 5}},
        )
        self.assertEqual(response.status_code, 201)
        self.created_lesson_ids.append(response.json()["id"])
        return response.json()

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
            json={"title": "Lost lesson", "course_id": 2_147_483_647, "data": {}},
        )
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
