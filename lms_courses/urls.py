from django.urls import path

from .views.teacher import (
    MyCourseSemestersList,
    CourseSemesterCreate,
    CourseSemesterDetailView,
)

app_name = "lms_courses"

# Teacher-facing patterns (to be mounted at /teacher/courses/)
teacher_patterns = [
    path("", MyCourseSemestersList.as_view(), name="course_semester_list_teacher"),
    path("new/", CourseSemesterCreate.as_view(), name="course_semester_teacher_create"),
    path("<int:pk>/", CourseSemesterDetailView.as_view(), name="course_semester_teacher_detail"),
]
