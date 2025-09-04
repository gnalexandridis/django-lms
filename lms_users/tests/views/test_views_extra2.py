from django.test import TestCase, override_settings

from lms_users.models import Roles, User


class TestProviderLogout(TestCase):
    @override_settings(OIDC_OP_LOGOUT_ENDPOINT="https://idp/logout", OIDC_RP_CLIENT_ID="abc")
    def test_provider_logout_builds_url(self):
        User.objects.create_user("u", password="x", role=Roles.STUDENT)
        self.client.login(username="u", password="x")
        from lms_users.views import provider_logout

        resp = provider_logout(self.client.request().wsgi_request)  # type: ignore[arg-type]
        self.assertTrue(isinstance(resp, str))
        self.assertIn("https://idp/logout?", resp)
        self.assertIn("client_id=abc", resp)
