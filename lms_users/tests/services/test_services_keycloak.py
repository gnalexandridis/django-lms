from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from lms_users.models import Roles
from lms_users.services.keycloak import (
    KeycloakClient,
    provision_local_student_from_kc,
    search_students,
)


class TestSearchStudentsAndProvision(TestCase):
    def setUp(self):
        U = get_user_model()
        U.objects.create_user(username="alice", role=Roles.STUDENT)
        U.objects.create_user(username="albert", role=Roles.STUDENT)
        U.objects.create_user(username="teacher1", role=Roles.TEACHER)

    @override_settings(E2E_TEST_LOGIN=True)
    def test_search_students_local_only_in_e2e_mode(self):
        res = search_students("al")
        usernames = [r["username"] for r in res]
        self.assertIn("alice", usernames)
        self.assertIn("albert", usernames)
        self.assertNotIn("teacher1", usernames)

    @override_settings(E2E_TEST_LOGIN=False)
    def test_search_students_deduplicates_local_over_keycloak(self):
        # Mock KC to return a duplicate and a new user
        kc_users = [
            {"username": "alice", "firstName": "Ali", "lastName": "Ce"},
            {"username": "bob", "firstName": "Bob", "lastName": "Ross"},
        ]
        with patch.object(KeycloakClient, "search_users_in_group", return_value=kc_users):
            res = search_students("a")
        usernames = [r["username"] for r in res]
        # Local alice should appear once and before KC bob
        self.assertEqual(usernames.count("alice"), 1)
        self.assertIn("bob", usernames)

    def test_provision_returns_existing_user(self):
        U = get_user_model()
        existing = U.objects.create_user(username="kcuser", role=Roles.STUDENT)
        out = provision_local_student_from_kc("kcuser")
        # Compare on stable field to avoid type checker noise
        self.assertEqual(out.username, existing.username)  # type: ignore[union-attr]

    def test_provision_returns_none_when_not_found(self):
        with patch.object(KeycloakClient, "get_user_by_username", return_value=None):
            out = provision_local_student_from_kc("nouser")
        self.assertIsNone(out)

    def test_provision_creates_with_names_and_role(self):
        with patch.object(
            KeycloakClient,
            "get_user_by_username",
            return_value={
                "username": "kcnew",
                "email": "k@c.example",
                "firstName": "Key",
                "lastName": "Cloak",
            },
        ):
            user = provision_local_student_from_kc("kcnew")
        assert user is not None
        self.assertEqual(user.username, "kcnew")
        self.assertEqual(user.email, "k@c.example")
        # Names set when model supports them (AbstractUser based)
        self.assertEqual(getattr(user, "first_name", ""), "Key")
        self.assertEqual(getattr(user, "last_name", ""), "Cloak")
        self.assertEqual(getattr(user, "role", None), Roles.STUDENT)
