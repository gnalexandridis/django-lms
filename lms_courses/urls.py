from django.urls import path

from .views.teacher import (
    CourseSemesterCreate,
    CourseSemesterDetailView,
    EnrollmentCreateView,
    FinalAssignmentCreateView,
    FinalAssignmentManageView,
    FinalAssignmentUpdateView,
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
    path(
        "<int:pk>/final-assignment/new/",
        FinalAssignmentCreateView.as_view(),
        name="final_assignment_create",
    ),
    path(
        "<int:pk>/final-assignment/edit/",
        FinalAssignmentUpdateView.as_view(),
        name="final_assignment_edit",
    ),
    path(
        "<int:pk>/final-assignment/manage/",
        FinalAssignmentManageView.as_view(),
        name="final_assignment_manage",
    ),
]
