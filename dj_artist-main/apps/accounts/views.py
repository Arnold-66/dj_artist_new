from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST



from .forms import (
    StaffLoginForm,
    StaffUserForm,
    StaffUserCreateForm,

)

from django.contrib.auth.views import (
    LoginView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.urls import reverse_lazy
from apps.accounts.forms import PressKitSignupForm

from apps.dashboard.models import AuditLog
from .permissions import admin_required, staff_required

User = get_user_model()


# =========================================================
# USERS (admin only)
# =========================================================
@admin_required
def user_list(request):
    users = User.objects.order_by("role", "username")
    return render(request, "dashboard/user_list.html", {"users": users})


@admin_required
def user_create(request):
    if request.method == "POST":
        form = StaffUserCreateForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            AuditLog.objects.create(
                actor=request.user, action="create", app_label="accounts",
                model_name="User", object_id=str(new_user.pk),
                object_repr=str(new_user), changes={"created_role": new_user.role},
            )
            messages.success(request, f"User '{new_user.username}' created.")
            return redirect("dashboard:user_list")
    else:
        form = StaffUserCreateForm()
    return render(request, "dashboard/user_form.html", {"form": form, "title": "Create User"})


@admin_required
def user_edit(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)
    if not request.user.can_manage_role(user_obj):
        messages.error(request, "You cannot edit that user.")
        return redirect("dashboard:user_list")

    if request.method == "POST":
        form = StaffUserForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                actor=request.user, action="update", app_label="accounts",
                model_name="User", object_id=str(user_obj.pk),
                object_repr=str(user_obj), changes={"updated": user_obj.role},
            )
            messages.success(request, "User updated.")
            return redirect("dashboard:user_list")
    else:
        form = StaffUserForm(instance=user_obj)

    return render(request, "dashboard/user_form.html", {"form": form, "title": f"Edit {user_obj.username}"})


@admin_required
def user_delete(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)
    if user_obj == request.user:
        messages.error(request, "You cannot delete yourself.")
        return redirect("dashboard:user_list")
    if not request.user.can_manage_role(user_obj):
        messages.error(request, "You cannot delete that user.")
        return redirect("dashboard:user_list")

    if request.method == "POST":
        name = user_obj.username
        user_obj.delete()
        AuditLog.objects.create(
            actor=request.user, action="delete", app_label="accounts",
            model_name="User", object_id=str(user_id),
            object_repr=name, changes={"deleted": name},
        )
        messages.success(request, f"User '{name}' deleted.")
        return redirect("dashboard:user_list")
    return render(request, "dashboard/user_confirm_delete.html", {"user_obj": user_obj})

@admin_required
@require_POST
def user_toggle_active(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)
    if user_obj == request.user:
        messages.error(request, "You cannot deactivate yourself.")
        return redirect("dashboard:user_list")
    user_obj.is_active = not user_obj.is_active
    user_obj.save(update_fields=["is_active"])
    messages.success(request, f"{user_obj.username} is now {'active' if user_obj.is_active else 'inactive'}.")
    return redirect("dashboard:user_list")


# =========================================================
# AUTH
# =========================================================
# apps/account/views.py
class StaffLoginView(LoginView):
    template_name = "account/login.html"
    authentication_form = StaffLoginForm
    redirect_authenticated_user = False

    def get_success_url(self):
        user = self.request.user
        # Kit users → press kit portal
        if user.is_kit_user:
            return reverse("epk:official")
        # Management → dashboard
        if (user.is_staff or user.is_admin_role
                or user.is_operator_role or user.is_dj_role):
            return reverse("dashboard:overview")
        # Fallback
        return reverse("core:home")

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_active:
            form.add_error(None, "This account is inactive.")
            return self.form_invalid(form)
        # Management must have a role
        if not (user.is_kit_user or user.is_staff
                or user.is_admin_role or user.is_operator_role
                or user.is_dj_role):
            form.add_error(None, "This account does not have management access.")
            return self.form_invalid(form)
        # Regular LoginView flow: logs user in and redirects via get_success_url()
        return super().form_valid(form)


@require_POST
def staff_logout(request):
    logout(request)
    return redirect("accounts:login")

# =========================================================
# PUBLIC SIGNUP (kit users)
# =========================================================
def signup(request):
    if request.user.is_authenticated:
        return redirect("epk:official")

    if request.method == "POST":
        form = PressKitSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                "Account created. You can now sign in to access press kits.",
            )
            # Auto-login optional; here we redirect to login.
            return redirect("account:login")
    else:
        form = PressKitSignupForm()

    return render(request, "account/signup.html", {"form": form})

# =========================================================
# PASSWORD RESET
# =========================================================
class StaffPasswordResetView(PasswordResetView):
    template_name = "account/password_reset_form.html"
    email_template_name = "account/password_reset_email.html"
    subject_template_name = "account/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class StaffPasswordResetDoneView(PasswordResetDoneView):
    template_name = "account/password_reset_done.html"


class StaffPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "account/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class StaffPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "account/password_reset_complete.html"

