from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.bookings.models import BookingInquiry
from apps.bookings.services import send_booking_reply
from apps.core.models import ArtistProfile
from apps.epk.models import PressKit
from apps.events.models import Event
from apps.music.models import Mix

from .forms import (
    StaffLoginForm,
    DJProfileForm,
    DJProfileSelfForm,
    StaffUserForm,
    StaffUserCreateForm,
    MixForm,
    EventForm,
    BookingStatusForm,
    BookingReplyForm,
)
from .models import AuditLog
from .permissions import admin_required, staff_required

User = get_user_model()


# =========================================================
# AUTH
# =========================================================
class StaffLoginView(LoginView):
    template_name = "dashboard/login.html"
    authentication_form = StaffLoginForm
    redirect_authenticated_user = False

    def form_valid(self, form):
        user = form.get_user()
        if user.is_kit_user or not user.is_active:
            form.add_error(None, "This account does not have management access.")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("dashboard:overview")


@require_POST
def staff_logout(request):
    logout(request)
    return redirect("dashboard:login")


# =========================================================
# OVERVIEW
# =========================================================
@staff_required
def overview(request):
    from django.db.models import Q

    user = request.user

    # Superuser or admin-role → see EVERYTHING on the site.
    # Operator / DJ staff      → see only their accessible artists.
    is_admin = user.is_superuser or getattr(user, "is_admin_role", False)

    artists = user.accessible_artists()
    accessible_ids = list(artists.values_list("pk", flat=True))

    # ---- Events ----
    if is_admin:
        # Admin sees ALL events — including ones with no artist assigned.
        events_qs = Event.objects.all()
    else:
        # Staff sees their artists' events, PLUS any unassigned events
        # (so items created before the artist FK was filled in still show).
        events_qs = Event.objects.filter(
            Q(artist__in=accessible_ids) | Q(artist__isnull=True)
        )

    # ---- Music ----
    if is_admin:
        mixes_qs = Mix.objects.all()
    else:
        mixes_qs = Mix.objects.filter(
            Q(artist__in=accessible_ids) | Q(artist__isnull=True)
        )

    # ---- Bookings (no artist FK yet → everyone sees all for now) ----
    bookings_qs = BookingInquiry.objects.all()

    # ---- Upcoming events ----
    upcoming_qs = (
        events_qs.filter(is_published=True, start_at__gte=timezone.now())
        .order_by("start_at")[:6]
    )

    context = {
        "booking_count": bookings_qs.count(),
        "new_bookings": bookings_qs.filter(status="new").count(),
        "confirmed_bookings": bookings_qs.filter(status="confirmed").count(),
        "subscriber_count": User.objects.filter(
            is_subscribed=True, role=User.ROLE_KIT_USER
        ).count(),

        "event_count": events_qs.count(),
        "mix_count": mixes_qs.count(),
        "audio_count": mixes_qs.filter(media_type="audio").count(),
        "video_count": mixes_qs.filter(media_type="video").count(),

        "recent_bookings": bookings_qs.order_by("-created_at")[:6],
        "upcoming_events": upcoming_qs,
        "accessible_artists": artists,
        "staff_role": (
            "Super Administrator" if user.is_superuser
            else user.get_role_display()
        ),
        "is_admin_view": is_admin,
    }
    return render(request, "dashboard/overview.html", context)



# =========================================================
# ARTIST PROFILES
# =========================================================

@staff_required
def dj_list(request):
    user = request.user

    artists = user.accessible_artists().order_by("stage_name")

    return render(request, "dashboard/dj_list.html", {
        "djs": artists,
        "is_admin_view": user.is_admin_role,
    })


@admin_required
def dj_create(request):
    if request.method == "POST":
        form = DJProfileForm(request.POST, request.FILES)

        if form.is_valid():
            dj = form.save()

            AuditLog.objects.create(
                actor=request.user,
                action="create",
                app_label="core",
                model_name="ArtistProfile",
                object_id=str(dj.pk),
                object_repr=str(dj),
                changes={"created": dj.stage_name},
            )

            messages.success(
                request,
                f"Artist profile '{dj.stage_name}' created successfully."
            )

            return redirect("dashboard:dj_list")

    else:
        form = DJProfileForm()

    return render(request, "dashboard/dj_form.html", {
        "form": form,
        "title": "Create Artist Profile",
        "submit_label": "CREATE ARTIST",
        "is_admin_view": True,
    })


@staff_required
def dj_edit(request, pk):
    dj = get_object_or_404(
        request.user.accessible_artists(),
        pk=pk,
    )

    is_admin = request.user.is_admin_role

    # Admin can manage assignments.
    # DJ/operator can only edit profile information.
    FormClass = DJProfileForm if is_admin else DJProfileSelfForm

    if request.method == "POST":
        form = FormClass(
            request.POST,
            request.FILES,
            instance=dj,
        )

        if form.is_valid():
            form.save()

            AuditLog.objects.create(
                actor=request.user,
                action="update",
                app_label="core",
                model_name="ArtistProfile",
                object_id=str(dj.pk),
                object_repr=str(dj),
                changes={"updated": dj.stage_name},
            )

            messages.success(
                request,
                f"{dj.stage_name}'s profile has been updated."
            )

            return redirect("dashboard:dj_list")

    else:
        form = FormClass(instance=dj)

    return render(request, "dashboard/dj_form.html", {
        "form": form,
        "dj": dj,
        "title": f"Edit {dj.stage_name}",
        "submit_label": "SAVE CHANGES",
        "is_admin_view": is_admin,
    })


@admin_required
def dj_delete(request, pk):
    dj = get_object_or_404(ArtistProfile, pk=pk)

    if request.method == "POST":
        name = dj.stage_name

        AuditLog.objects.create(
            actor=request.user,
            action="delete",
            app_label="core",
            model_name="ArtistProfile",
            object_id=str(pk),
            object_repr=name,
            changes={"deleted": name},
        )

        dj.delete()

        messages.success(
            request,
            f"Artist profile '{name}' deleted."
        )

        return redirect("dashboard:dj_list")

    return render(request, "dashboard/dj_confirm_delete.html", {
        "dj": dj,
    })

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
# BOOKINGS (scoped)
# =========================================================
@staff_required
def bookings_list(request):
    bookings = BookingInquiry.objects.order_by("-created_at")
    selected_status = request.GET.get("status", "")
    if selected_status:
        bookings = bookings.filter(status=selected_status)

    return render(request, "dashboard/bookings_list.html", {
        "bookings": bookings,
        "selected_status": selected_status,
        "statuses": BookingInquiry.STATUSES,
    })

@staff_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(BookingInquiry, pk=booking_id)
    # No artist FK yet — no scoping check.

    status_form = BookingStatusForm(instance=booking)
    reply_form = BookingReplyForm(initial={"subject": f"Re: Booking inquiry - {booking.organization}"})

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update_status":
            status_form = BookingStatusForm(request.POST, instance=booking)
            if status_form.is_valid():
                status_form.save()
                messages.success(request, "Booking status updated.")
                return redirect("dashboard:booking_detail", booking_id=booking.pk)
        elif action == "send_reply":
            reply_form = BookingReplyForm(request.POST)
            if reply_form.is_valid():
                reply = send_booking_reply(
                    booking=booking, sender=request.user,
                    subject=reply_form.cleaned_data["subject"],
                    message=reply_form.cleaned_data["message"],
                )
                messages.success(request, "Reply sent." if reply.email_status == "sent" else "Reply could not be sent.")
                return redirect("dashboard:booking_detail", booking_id=booking.pk)

    return render(request, "dashboard/booking_detail.html", {
        "booking": booking,
        "status_form": status_form,
        "reply_form": reply_form,
        "replies": booking.replies.select_related("sender").all(),
    })




# =========================================================
# MUSIC (scoped)
# =========================================================
@staff_required
def music_list(request):
    artists = request.user.accessible_artists()
    mixes = (
        Mix.objects.filter(artist__in=artists).order_by("-created_at")
        if artists.exists() else Mix.objects.none()
    )
    return render(request, "dashboard/music_list.html", {"mixes": mixes})


@staff_required
def music_create(request):
    artists = request.user.accessible_artists()
    if request.method == "POST":
        form = MixForm(request.POST, request.FILES)
        if "artist" in form.fields:
            form.fields["artist"].queryset = artists
        if form.is_valid():
            mix = form.save()
            AuditLog.objects.create(
                actor=request.user, action="create", app_label="music",
                model_name="Mix", object_id=str(mix.pk),
                object_repr=str(mix), changes={"created": mix.title},
            )
            messages.success(request, f"Music '{mix.title}' created.")
            return redirect("dashboard:music_list")
    else:
        form = MixForm()
        if "artist" in form.fields:
            form.fields["artist"].queryset = artists

    return render(request, "dashboard/music_form.html", {
        "form": form, "title": "Add Music", "submit_label": "CREATE",
    })


@staff_required
def music_edit(request, pk):
    mix = get_object_or_404(Mix, pk=pk)
    if not request.user.can_manage_artist(mix.artist):
        messages.error(request, "You cannot edit that track.")
        return redirect("dashboard:music_list")

    if request.method == "POST":
        form = MixForm(request.POST, request.FILES, instance=mix)
        if "artist" in form.fields:
            form.fields["artist"].queryset = request.user.accessible_artists()
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                actor=request.user, action="update", app_label="music",
                model_name="Mix", object_id=str(mix.pk),
                object_repr=str(mix), changes={"updated": mix.title},
            )
            messages.success(request, "Music updated.")
            return redirect("dashboard:music_list")
    else:
        form = MixForm(instance=mix)
        if "artist" in form.fields:
            form.fields["artist"].queryset = request.user.accessible_artists()

    return render(request, "dashboard/music_form.html", {
        "form": form, "title": f"Edit {mix.title}", "submit_label": "SAVE",
    })


@staff_required
def music_delete(request, pk):
    mix = get_object_or_404(Mix, pk=pk)
    if not request.user.can_manage_artist(mix.artist):
        messages.error(request, "You cannot delete that track.")
        return redirect("dashboard:music_list")

    if request.method == "POST":
        title = mix.title
        mix.delete()
        AuditLog.objects.create(
            actor=request.user, action="delete", app_label="music",
            model_name="Mix", object_id=str(pk),
            object_repr=title, changes={"deleted": title},
        )
        messages.success(request, f"Music '{title}' deleted.")
        return redirect("dashboard:music_list")

    return render(request, "dashboard/music_confirm_delete.html", {"mix": mix})


# =========================================================
# EVENTS (scoped)
# =========================================================
@staff_required
def event_list(request):
    artists = request.user.accessible_artists()
    events = (
        Event.objects.filter(artist__in=artists).order_by("-start_at")
        if artists.exists() else Event.objects.none()
    )
    return render(request, "dashboard/event_list.html", {"events": events})


@staff_required
def event_create(request):
    artists = request.user.accessible_artists()
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if "artist" in form.fields:
            form.fields["artist"].queryset = artists
        if form.is_valid():
            event = form.save()
            AuditLog.objects.create(
                actor=request.user, action="create", app_label="events",
                model_name="Event", object_id=str(event.pk),
                object_repr=str(event), changes={"created": event.title},
            )
            messages.success(request, f"Event '{event.title}' created.")
            return redirect("dashboard:event_list")
    else:
        form = EventForm()
        if "artist" in form.fields:
            form.fields["artist"].queryset = artists

    return render(request, "dashboard/event_form.html", {
        "form": form, "title": "Add Event", "submit_label": "CREATE EVENT",
    })


@staff_required
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not request.user.can_manage_artist(event.artist):
        messages.error(request, "You cannot edit that event.")
        return redirect("dashboard:event_list")

    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        if "artist" in form.fields:
            form.fields["artist"].queryset = request.user.accessible_artists()
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                actor=request.user, action="update", app_label="events",
                model_name="Event", object_id=str(event.pk),
                object_repr=str(event), changes={"updated": event.title},
            )
            messages.success(request, "Event updated.")
            return redirect("dashboard:event_list")
    else:
        form = EventForm(instance=event)
        if "artist" in form.fields:
            form.fields["artist"].queryset = request.user.accessible_artists()

    return render(request, "dashboard/event_form.html", {
        "form": form, "title": f"Edit {event.title}", "submit_label": "SAVE EVENT",
    })


@staff_required
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not request.user.can_manage_artist(event.artist):
        messages.error(request, "You cannot delete that event.")
        return redirect("dashboard:event_list")

    if request.method == "POST":
        title = event.title
        event.delete()
        AuditLog.objects.create(
            actor=request.user, action="delete", app_label="events",
            model_name="Event", object_id=str(pk),
            object_repr=title, changes={"deleted": title},
        )
        messages.success(request, f"Event '{title}' deleted.")
        return redirect("dashboard:event_list")

    return render(request, "dashboard/event_confirm_delete.html", {"event": event})


# =========================================================
# PRESS KITS (scoped list)
# =========================================================
@staff_required
def epk_list(request):
    artists = request.user.accessible_artists()
    kits = (
        PressKit.objects.filter(artist__in=artists).order_by("-updated_at")
        if artists.exists() else PressKit.objects.none()
    )
    return render(request, "dashboard/epk_list.html", {"kits": kits})