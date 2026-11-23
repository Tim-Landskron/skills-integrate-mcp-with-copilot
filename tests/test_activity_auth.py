import unittest

from fastapi import HTTPException
from starlette.requests import Request

from src.app import (
    activities,
    require_teacher,
    signup_for_activity,
    unregister_from_activity,
)


def make_request(session=None):
    return Request({"type": "http", "headers": [], "session": session or {}})


class ActivityAuthorizationTests(unittest.TestCase):
    def test_anonymous_users_cannot_signup_or_unregister(self):
        anonymous_request = make_request()

        with self.assertRaises(HTTPException) as signup_error:
            signup_for_activity(
                "Chess Club", "test-student@mergington.edu", anonymous_request
            )
        self.assertEqual(signup_error.exception.status_code, 401)

        with self.assertRaises(HTTPException) as unregister_error:
            unregister_from_activity(
                "Chess Club", "michael@mergington.edu", anonymous_request
            )
        self.assertEqual(unregister_error.exception.status_code, 401)

    def test_teacher_can_manage_signups(self):
        teacher_request = make_request({"role": "teacher"})
        email = "test-student@mergington.edu"

        try:
            result = signup_for_activity("Chess Club", email, teacher_request)
            self.assertIn(email, activities["Chess Club"]["participants"])
            self.assertIn("Signed up", result["message"])

            result = unregister_from_activity("Chess Club", email, teacher_request)
            self.assertNotIn(email, activities["Chess Club"]["participants"])
            self.assertIn("Unregistered", result["message"])
        finally:
            if email in activities["Chess Club"]["participants"]:
                activities["Chess Club"]["participants"].remove(email)

    def test_teacher_check_requires_teacher_role(self):
        with self.assertRaises(HTTPException) as error:
            require_teacher(make_request({"username": "student"}))
        self.assertEqual(error.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
