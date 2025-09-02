from django.core.exceptions import ValidationError
from django.test import TestCase

from lms_users.typing_utils import UserModel as U


class UserModelTests(TestCase):
    def test_user_has_role_field(self):
        u = U.objects.create_user(username="u1", password="x")
        self.assertTrue(hasattr(u, "role"))

    def test_default_role_is_student(self):
        u = U.objects.create_user(username="u2", password="x")
        # default "STUDENT"
        self.assertEqual(u.role, "STUDENT")

    def test_role_choices_enforced(self):
        u = U.objects.create_user(username="u3", password="x")
        u.role = "NOT_A_ROLE"
        with self.assertRaises(ValidationError):
            u.full_clean()  # should fail due to choices

    def test_superuser_flags(self):
        admin = U.objects.create_superuser(
            username="admin", password="x", email="admin@example.com"
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_str_returns_username(self):
        u = U.objects.create_user(username="u4", password="x")
        self.assertEqual(str(u), "u4")
