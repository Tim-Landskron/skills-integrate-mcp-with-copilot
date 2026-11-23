import unittest

from src.auth import hash_password, verify_password


class PasswordHashTests(unittest.TestCase):
    def test_hash_verifies_only_the_original_password(self):
        credential = hash_password("correct horse battery staple")

        self.assertTrue(verify_password("correct horse battery staple", credential))
        self.assertFalse(verify_password("wrong password", credential))
        self.assertNotIn("password", credential)

    def test_invalid_hash_parameters_are_rejected(self):
        credential = hash_password("correct horse battery staple")
        credential["iterations"] = 1

        with self.assertRaises(ValueError):
            verify_password("correct horse battery staple", credential)


if __name__ == "__main__":
    unittest.main()
