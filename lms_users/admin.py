from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin interface for User model."""

    # Define the fields to be displayed in the admin list view.
    list_display = ("username", "email", "role", "is_staff", "is_superuser")
    # Define the fields to be used for searching in the admin interface.
    search_fields = ("username", "email")
    # Define the fields to be used for filtering in the admin interface.
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
