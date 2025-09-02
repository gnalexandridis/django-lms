from django.contrib.admin.sites import site as admin_site
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AdminRegistrationTests(TestCase):
    def test_user_model_registered_in_admin(self):
        U = get_user_model()
        self.assertIn(U, admin_site._registry)

    def test_admin_changelist_loads(self):
        U = get_user_model()
        admin = U.objects.create_superuser(username="admin", password="x", email="a@a.com")
        self.client.force_login(admin)
        url = reverse("admin:index")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
