# apps/dashboard/permissions.py
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def staff_required(view_func):
    @wraps(view_func)
    @login_required(login_url="accounts:login")
    def wrapper(request, *args, **kwargs):
        u = request.user
        # Kit users NEVER get into the management dashboard, even if is_staff
        if u.is_kit_user:
            messages.error(request, "Press-kit accounts cannot access the dashboard.")
            return redirect("accounts:download_history")
        if not (u.is_staff or u.is_admin_role or u.is_operator_role or u.is_dj_role):
            messages.error(request, "You do not have access to the dashboard.")
            return redirect("core:home")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    @login_required(login_url="accounts:login")
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin_role:
            messages.error(request, "Administrator access only.")
            return redirect("dashboard:overview")
        return view_func(request, *args, **kwargs)
    return wrapper