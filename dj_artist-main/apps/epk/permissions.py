# apps/kit/permissions.py
from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def kit_required(view_func):
    """Only press-kit users (verified) can pass."""
    @wraps(view_func)
    @login_required(login_url="kit:login")
    def wrapper(request, *args, **kwargs):
        u = request.user
        if not u.is_kit_user:
            messages.error(request, "Press-kit access only.")
            return redirect("core:home")
        if not u.emailaddress_set.filter(verified=True).exists():
            messages.warning(request, "Please verify your email to continue.")
            return redirect("kit:verify_notice")
        return view_func(request, *args, **kwargs)
    return wrapper