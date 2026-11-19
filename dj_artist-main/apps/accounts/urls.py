from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # ---------- Auth ----------
    path("login/", views.StaffLoginView.as_view(), name="login"),
    path("logout/", views.staff_logout, name="logout"),

    path("signup/", views.signup, name="signup"),

    # ---------- Password reset ----------
    path("password-reset/", views.StaffPasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", views.StaffPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", views.StaffPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password-reset/complete/", views.StaffPasswordResetCompleteView.as_view(), name="password_reset_complete"),

   
    # ---------- Users (admin only) ----------
    path("users/", views.user_list, name="user_list"),
    path("users/create/", views.user_create, name="user_create"),
    path("users/<int:user_id>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:user_id>/delete/", views.user_delete, name="user_delete"),
    path("users/<int:user_id>/toggle/", views.user_toggle_active, name="user_toggle"),


]