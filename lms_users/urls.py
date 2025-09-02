from django.urls import path

from . import views

app_name = "lms_users"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("test-login/", views.test_login_view, name="test_login"),
    path("logout/", views.logout_view, name="logout"),
]
