from django.urls import path

from .views.student import StudentCourseDetailView, StudentCourseListView
from .views.teacher import (
    CourseSemesterCreate,
    CourseSemesterDeleteView,
    CourseSemesterDetailView,
    EnrollmentCreateView,
    EnrollmentDeleteView,
    FinalAssignmentCreateView,
    FinalAssignmentDeleteView,
    FinalAssignmentManageView,
    FinalAssignmentUpdateView,
    LabSessionCreateView,
    LabSessionDeleteView,
    LabSessionManageView,
    MyCourseSemestersList,
    export_course_semester,
)

app_name = "lms_courses"

# Teacher-facing patterns (to be mounted at /teacher/courses/)
teacher_patterns = [
    path("", MyCourseSemestersList.as_view(), name="course_semester_list_teacher"),
    path("new/", CourseSemesterCreate.as_view(), name="course_semester_teacher_create"),
    path("<int:pk>/", CourseSemesterDetailView.as_view(), name="course_semester_teacher_detail"),
    path("<int:pk>/delete/", CourseSemesterDeleteView.as_view(), name="course_semester_delete"),
    path("<int:pk>/sessions/new/", LabSessionCreateView.as_view(), name="lab_session_create"),
    path(
        "<int:pk>/sessions/<int:session_id>/manage/",
        LabSessionManageView.as_view(),
        name="lab_session_manage",
    ),
    path(
        "<int:pk>/sessions/<int:session_id>/delete/",
        LabSessionDeleteView.as_view(),
        name="lab_session_delete",
    ),
    path("<int:pk>/enroll/", EnrollmentCreateView.as_view(), name="enroll_student"),
    path(
        "<int:pk>/enrollments/<int:student_id>/delete/",
        EnrollmentDeleteView.as_view(),
        name="unenroll_student",
    ),
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
        "<int:pk>/final-assignment/delete/",
        FinalAssignmentDeleteView.as_view(),
        name="final_assignment_delete",
    ),
    path(
        "<int:pk>/final-assignment/manage/",
        FinalAssignmentManageView.as_view(),
        name="final_assignment_manage",
    ),
    path("<int:pk>/export/", export_course_semester, name="course_semester_export"),
]

# Student-facing patterns (to be mounted at /student/courses/)
student_patterns = [
    path("", StudentCourseListView.as_view(), name="student_course_list"),
    path("<int:pk>/", StudentCourseDetailView.as_view(), name="student_course_detail"),
]
