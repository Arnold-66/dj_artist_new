from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django import forms

from .models import User


# =========================================================
# FORMS
# =========================================================
class CustomUserCreationForm(UserCreationForm):
    """Extends Django's creation form with our email field (required, unique)."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "role")


class CustomUserChangeForm(UserChangeForm):
    """Extends Django's change form with all our extra fields."""

    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"


# =========================================================
# ADMIN
# =========================================================
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    # ---------- List view ----------
    list_display = (
        "username",
        "email",
        "role",
        "is_active",
        "is_staff",
        "is_subscribed",
        "subscribed_at",
    )
    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
        "is_subscribed",
    )
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)

    # ---------- Detail view ----------
    # BaseUserAdmin.fieldsets is a tuple of (section_title, {"fields": [...]})
    # We append our custom fields as extra sections.
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Role & Access",
            {
                "fields": (
                    "role",
                    "dj_profile",
                    "managed_artists",
                )
            },
        ),
        (
            "Subscription",
            {
                "fields": (
                    "is_subscribed",
                    "subscribed_at",
                    "unsubscribed_at",
                )
            },
        ),
    )

    # ---------- Add view ----------
    # BaseUserAdmin.add_fieldsets is also a tuple — we extend it.
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Role & Access",
            {
                "fields": (
                    "email",
                    "role",
                )
            },
        ),
    )

    # Optional: make managed_artists nicer in the admin
    filter_horizontal = BaseUserAdmin.filter_horizontal + ("managed_artists",)

    def get_form(self, request, obj=None, **kwargs):
        """
        Django's UserCreationForm expects `password1`/`password2`, but
        BaseUserAdmin handles that automatically via add_fieldsets.
        We just ensure the email field is required on add.
        """
        form = super().get_form(request, obj, **kwargs)
        if obj is None:  # add view
            form.base_fields["email"].required = True
        return form