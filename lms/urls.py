from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path

from lms_courses import urls as course_urls

from .views import home, student_home, teacher_export_dashboard, teacher_home

urlpatterns = [
    path("oidc/", include("mozilla_django_oidc.urls")),
    path("admin/", admin.site.urls),
    path("users/", include(("lms_users.urls", "lms_users"), namespace="lms_users")),
    path(
        "teacher/courses/",
        include(
            (course_urls.teacher_patterns, "lms_courses_teacher"), namespace="lms_courses_teacher"
        ),
    ),
    path(
        "student/courses/",
        include(
            (course_urls.student_patterns, "lms_courses_student"), namespace="lms_courses_student"
        ),
    ),
    path("teacher/", teacher_home, name="teacher_home"),
    path("student/", student_home, name="student_home"),
    path("export", teacher_export_dashboard, name="teacher_export_dashboard"),
    path("", home, name="home"),
]


def handler403(request, exception=None):  # type: ignore[func-returns-value]
    return render(request, "errors/403.html", status=403)
