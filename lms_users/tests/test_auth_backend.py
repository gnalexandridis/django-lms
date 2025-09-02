from django.test import TestCase

from lms_users.auth_backends import KeycloakOIDCBackend
from lms_users.models import Roles, User


class TestKeycloakOIDCBackend(TestCase):
    def setUp(self):
        self.backend = KeycloakOIDCBackend()

    def test_filter_users_by_claims_no_username(self):
        qs = self.backend.filter_users_by_claims({})
        self.assertEqual(qs.count(), 0)

    def test_filter_users_by_claims_with_username(self):
        u = User.objects.create_user("kcuser", password="x")
        qs = self.backend.filter_users_by_claims({"preferred_username": "kcuser"})
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first(), u)

    def test_create_user_and_role_mapping(self):
        claims = {"preferred_username": "teach", "email": "t@example.com", "groups": ["teacher"]}
        u = self.backend.create_user(claims)
        self.assertEqual(u.username, "teach")
        self.assertEqual(u.email, "t@example.com")
        self.assertEqual(u.role, Roles.TEACHER)

    def test_update_user_changes_email_and_role(self):
        u = User.objects.create_user("stud", password="x", role=Roles.STUDENT, email="s@old")
        claims = {"email": "s@new", "groups": ["teacher"]}
        u2 = self.backend.update_user(u, claims)
        self.assertEqual(u2.email, "s@new")
        self.assertEqual(u2.role, Roles.TEACHER)
