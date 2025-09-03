from typing import cast

from django import forms

from .models import (
    Course,
    CourseSemester,
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
