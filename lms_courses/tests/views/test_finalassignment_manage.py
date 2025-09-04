from django.test import TestCase
from django.urls import reverse

from lms_courses.models import Course, CourseSemester, FinalAssignment
from lms_users.models import Roles, User


class TestFinalAssignmentManageView(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="t1", password="x", role=Roles.TEACHER)
        self.client.login(username="t1", password="x")
        course = Course.objects.create(code="CS402", title="Programming II")
        self.cs = CourseSemester.objects.create(
            course=course, year=2025, semester="WINTER", owner=self.teacher
        )
        self.fa = FinalAssignment.objects.create(
            course_semester=self.cs, title="Project X", max_grade=20, due_date="2025-02-15"
        )

    def test_post_and_prefill(self):
        s1 = User.objects.create_user(username="s1", password="x", role=Roles.STUDENT)
        self.cs.students.add(s1)
        url = reverse("lms_courses_teacher:final_assignment_manage", args=[self.cs.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        data = {f"submitted_{s1.pk}": "on", f"fa_grade_{s1.pk}": "17"}
        resp2 = self.client.post(url, data)
        self.assertEqual(resp2.status_code, 302)

        # Validate counters on detail page (use data-testids for stability)
        detail = reverse("lms_courses_teacher:course_semester_teacher_detail", args=[self.cs.pk])
        resp3 = self.client.get(detail)
        self.assertContains(resp3, 'data-testid="fa-submitted-count"')
        self.assertContains(resp3, ">1<")
        self.assertContains(resp3, 'data-testid="fa-graded-count"')
        self.assertContains(resp3, ">1<")

        # GET manage again to ensure prefilled values
        resp4 = self.client.get(url)
        self.assertEqual(resp4.status_code, 200)
        self.assertContains(resp4, f'name="submitted_{s1.pk}" checked')
        self.assertContains(resp4, f'name="fa_grade_{s1.pk}" value="17"')
