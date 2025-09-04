from typing import cast

from django import forms
from django.conf import settings

from lms_users.models import Roles, User

from .models import (
    Course,
    CourseSemester,
    LabParticipation,
    LabReport,
    LabReportGrade,
    LabSession,
)


class CourseSemesterForm(forms.ModelForm):
    # form-level validators για όρια έτους
    year = forms.IntegerField(
        min_value=2000,
        max_value=2100,
        error_messages={
            "required": "This field is required",
            "min_value": "Ensure this value is greater than or equal to 2000",
            "max_value": "Ensure this value is less than or equal to 2100",
        },
    )

    class Meta:
        model = CourseSemester
        fields = ["course", "year", "semester", "enrollment_limit"]

    def __init__(self, *args, **kwargs):
        # παίρνουμε το request για να ξέρουμε τον owner
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        # κατάλογος μαθημάτων (admin-provided)
        course_field = cast(forms.ModelChoiceField, self.fields["course"])
        course_field.queryset = Course.objects.all().order_by("code")
        # Show only course title in the select so E2E can select by visible text "Programming I"
        course_field.label_from_instance = lambda obj: getattr(obj, "title", str(obj))
        # Force English validation strings expected by tests
        self.fields["semester"].error_messages.update(
            {
                "required": "This field is required",
                "invalid_choice": "Select a valid choice",
            }
        )
        # Tailwind-friendly widget classes
        for name in ["course", "year", "semester", "enrollment_limit"]:
            field = self.fields.get(name)
            if field is not None:
                css = (
                    "block w-full rounded border border-gray-300 px-3 py-2 "
                    "focus:outline-none focus:ring-2 focus:ring-indigo-500"
                )
                try:
                    field.widget.attrs.setdefault("class", css)
                except Exception:
                    pass

    def clean(self):
        cleaned = super().clean()
        course = cleaned.get("course")
        year = cleaned.get("year")
        semester = cleaned.get("semester")
        owner = getattr(self.request, "user", None)

        if owner and course and year and semester:
            exists = CourseSemester.objects.filter(
                course=course, year=year, semester=semester, owner=owner
            ).exists()
            if exists:
                raise forms.ValidationError(
                    "A course semester with this course, year and semester already exists for you."
                )
        return cleaned

    def save(self, commit=True):
        obj: CourseSemester = super().save(commit=False)
        user = getattr(self.request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            obj.owner = user
        if commit:
            obj.save()
        return obj


class LabSessionForm(forms.ModelForm):
    # Ensure week starts at 1 so we fail fast at form validation time
    week = forms.IntegerField(min_value=1)
    date = forms.DateField(
        input_formats=[
            "%Y-%m-%d",  # ISO (preferred)
            "%d/%m/%Y",  # common EU
            "%m/%d/%Y",  # common US
        ],
        # Use text input so Selenium send_keys posts exactly what we type
        widget=forms.DateInput(attrs={"type": "text", "placeholder": "YYYY-MM-DD"}),
        error_messages={"required": "This field is required"},
    )

    class Meta:
        model = LabSession
        fields = ["name", "week", "date"]

    def __init__(self, *args, **kwargs):
        # περιμένουμε course_semester από το view
        self.course_semester: CourseSemester = kwargs.pop("course_semester")
        super().__init__(*args, **kwargs)
        # Tailwind-friendly widget classes
        css = (
            "block w-full rounded border border-gray-300 px-3 py-2 "
            "focus:outline-none focus:ring-2 focus:ring-indigo-500"
        )
        for name in ["name", "week", "date"]:
            field = self.fields.get(name)
            if field is not None:
                try:
                    field.widget.attrs.setdefault("class", css)
                except Exception:
                    pass

    def clean(self):
        cleaned = super().clean()
        name = cleaned.get("name")
        week = cleaned.get("week")
        # Validate uniqueness against the provided course_semester so we don't 500 on IntegrityError
        if self.course_semester and name and week is not None:
            exists = LabSession.objects.filter(
                course_semester=self.course_semester, name=name, week=week
            ).exists()
            if exists:
                raise forms.ValidationError(
                    "A lab session with this name and week already exists for this course semester."
                )
        return cleaned

    def save(self, commit=True):
        obj: LabSession = super().save(commit=False)
        obj.course_semester = self.course_semester
        if commit:
            obj.save()
        return obj


class EnrollmentForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        error_messages={"required": "This field is required"},
    )

    def __init__(self, *args, **kwargs):
        self.course_semester: CourseSemester = kwargs.pop("course_semester")
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # If OIDC is disabled (local/dev), auto-provision a shadow student user
            if getattr(settings, "E2E_TEST_LOGIN", False):
                user = User.objects.create_user(username=username)
                # Set role to STUDENT and unusable password for safety
                user.role = getattr(Roles, "STUDENT", "STUDENT")
                try:
                    user.set_unusable_password()
                except Exception:
                    pass
                user.save()
            else:
                # OIDC enabled: try Keycloak lookup and local provision
                pass
        return user

    def save(self):
        user: User = self.cleaned_data["username"]
        self.course_semester.students.add(user)
        return user


class LabParticipationGradeForm(forms.Form):
    """Dynamic form created per session to edit attendance and grades per student.

    We generate fields like present_<id> (bool) and grade_<id> (int).
    """

    def __init__(self, *args, **kwargs):
        self.session: LabSession = kwargs.pop("session")
        self.report: LabReport | None = kwargs.pop("report", None)
        self.students_qs = kwargs.pop("students_qs")
        super().__init__(*args, **kwargs)

        for student in self.students_qs:
            self.fields[f"present_{student.id}"] = forms.BooleanField(required=False)
            max_grade = self.report.max_grade if self.report else 10
            self.fields[f"grade_{student.id}"] = forms.IntegerField(
                required=False, min_value=0, max_value=max_grade
            )

    def save(self):
        report = self.report
        if report is None:
            # Create a default report if missing
            report = LabReport.objects.create(
                session=self.session,
                title=f"Report: {self.session.name}",
                max_grade=10,
                due_date=self.session.date,
            )

        for student in self.students_qs:
            present_val = bool(self.cleaned_data.get(f"present_{student.id}") or False)
            part, _ = LabParticipation.objects.get_or_create(
                session=self.session, student=student, defaults={"present": present_val}
            )
            if part.present != present_val:
                part.present = present_val
                part.save()

            grade_val = self.cleaned_data.get(f"grade_{student.id}")
            gr, _ = LabReportGrade.objects.get_or_create(
                lab_report=report, student=student, defaults={"grade": grade_val}
            )
            if gr.grade != grade_val:
                gr.grade = grade_val
                gr.save()
