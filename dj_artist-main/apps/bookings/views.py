from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from apps.core.views import selected_artist   # <-- NEW import
from apps.core.models import ArtistProfile
from .forms import (
    BookingInquiryForm,
    BookingReplyForm,
    BookingStatusForm,
)
from .models import BookingInquiry
from .services import (
    notify_new_booking,
    send_booking_confirmation,
    send_booking_reply,
)


# =====================================================================
# PUBLIC VIEW
# =====================================================================
def booking_create(request):
    # Try selected_artist() first (honours ?dj= and session),
    # then fall back to the first artist in the DB.
    artist = selected_artist(request) or ArtistProfile.objects.order_by("id").first()

    if request.method == "POST":
        form = BookingInquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.artist = artist
            inquiry.save()

            notify_new_booking(inquiry)
            send_booking_confirmation(inquiry)

            messages.success(
                request,
                "Thank you. Your booking inquiry has been received "
                "and a confirmation email has been sent to you.",
            )
            return redirect("bookings:create")
    else:
        form = BookingInquiryForm()

    return render(request, "bookings/form.html", {
        "form": form,
        "artist": artist,
    })


# =====================================================================
# STAFF VIEWS
# =====================================================================
@staff_member_required
def bookings_list(request):
    bookings = BookingInquiry.objects.select_related("artist").all()

    selected_status = request.GET.get("status", "")
    if selected_status in dict(BookingInquiry.STATUSES):
        bookings = bookings.filter(status=selected_status)

    selected_artist = request.GET.get("artist", "")
    if selected_artist:
        bookings = bookings.filter(artist__slug=selected_artist)

    return render(request, "bookings/bookings_list.html", {
        "bookings": bookings,
        "selected_status": selected_status,
        "selected_artist": selected_artist,
        "statuses": BookingInquiry.STATUSES,
        "artists": ArtistProfile.objects.order_by("stage_name"),
        "total_count": BookingInquiry.objects.count(),
        "new_count": BookingInquiry.objects.filter(status="new").count(),
        "confirmed_count": BookingInquiry.objects.filter(status="confirmed").count(),
    })

@staff_member_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(BookingInquiry, pk=booking_id)

    status_form = BookingStatusForm(instance=booking)
    reply_form = BookingReplyForm(
        initial={
            "subject": f"Re: Booking inquiry - {booking.organization}",
        }
    )

    if request.method == "POST":
        action = request.POST.get("action")

        # ---- Update status ----
        if action == "update_status":
            status_form = BookingStatusForm(request.POST, instance=booking)
            if status_form.is_valid():
                status_form.save()
                messages.success(request, "Booking status updated.")
                return redirect(
                    "bookings:booking_detail", booking_id=booking.pk
                )

        # ---- Send email reply ----
        elif action == "send_reply":
            reply_form = BookingReplyForm(request.POST)
            if reply_form.is_valid():
                reply = send_booking_reply(
                    booking=booking,
                    sender=request.user,
                    subject=reply_form.cleaned_data["subject"],
                    message=reply_form.cleaned_data["message"],
                )
                if reply.email_status == "sent":
                    messages.success(request, "Your reply was sent.")
                else:
                    messages.error(request, "Reply could not be sent.")
                return redirect(
                    "bookings:booking_detail", booking_id=booking.pk
                )

    return render(
        request,
        "bookings/booking_detail.html",
        {
            "booking": booking,
            "status_form": status_form,
            "reply_form": reply_form,
            "replies": booking.replies.select_related("sender").all(),
        },
    )