from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse

from lms_users.permissions import Roles


@login_required
def home(request):
    user = request.user
    role = getattr(user, "role", None)
    if role == Roles.STUDENT:
        return redirect(reverse("student_home"))
    elif role == Roles.TEACHER:
        return redirect(reverse("teacher_home"))
    return redirect(reverse("login"))
