from __future__ import annotations


from django.shortcuts import render

from lms_users.decorators import role_required
from lms_users.permissions import Roles


@role_required(Roles.STUDENT)
def student_home(request):
    return render(request, "lms_courses/student/home.html")
