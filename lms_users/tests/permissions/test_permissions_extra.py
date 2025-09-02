from django.test import TestCase

from lms_users.permissions import has_role, is_student, is_teacher, normalize_roles


class Dummy:
    def __init__(self, role=None, is_superuser=False, is_staff=False):
        self.role = role
        self.is_superuser = is_superuser
        self.is_staff = is_staff


class TestPermissionsHelpers(TestCase):
    def test_normalize_and_checks(self):
        self.assertEqual(normalize_roles(None), tuple())
        self.assertTrue(has_role(Dummy(is_superuser=True), None))
        self.assertTrue(has_role(Dummy(is_staff=True), ("ANY",)))
        self.assertTrue(is_student(Dummy(role="STUDENT")))
        self.assertTrue(is_teacher(Dummy(role="TEACHER")))
