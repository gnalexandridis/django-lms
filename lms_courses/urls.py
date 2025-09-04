from django.urls import path

from .views.teacher import (
    CourseSemesterCreate,
    CourseSemesterDetailView,
    EnrollmentCreateView,
    LabSessionCreateView,
    LabSessionManageView,
    MyCourseSemestersList,
)

app_name = "lms_courses"

# Teacher-facing patterns (to be mounted at /teacher/courses/)
teacher_patterns = [
    path("", MyCourseSemestersList.as_view(), name="course_semester_list_teacher"),
    path("new/", CourseSemesterCreate.as_view(), name="course_semester_teacher_create"),
    path("<int:pk>/", CourseSemesterDetailView.as_view(), name="course_semester_teacher_detail"),
    path("<int:pk>/sessions/new/", LabSessionCreateView.as_view(), name="lab_session_create"),
    path(
        "<int:pk>/sessions/<int:session_id>/manage/",
        LabSessionManageView.as_view(),
        name="lab_session_manage",
    ),
    path("<int:pk>/enroll/", EnrollmentCreateView.as_view(), name="enroll_student"),
]
