from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
import logging
from django.core.mail import EmailMessage

from .models import BookingReply

import os

logger = logging.getLogger(__name__)


def _artist_recipient(artist):
    """
    Resolve the best inbox for a given artist, in priority order:
      1. artist.notification_email   (explicit override)
      2. artist.email                (the artist's contact email)
      3. settings.BOOKING_NOTIFICATION_EMAIL   (site-wide fallback)
      4. settings.DEFAULT_FROM_EMAIL            (last resort)
    """
    if artist:
        if getattr(artist, "notification_email", ""):
            return artist.notification_email
        if getattr(artist, "email", ""):
            return artist.email

    return (
        getattr(settings, "BOOKING_NOTIFICATION_EMAIL", None)
        or settings.DEFAULT_FROM_EMAIL
    )



def notify_new_booking(inquiry):
    artist = getattr(inquiry, "artist", None)

    recipient = _artist_recipient(artist)
    if not recipient:
        logger.error(
            "notify_new_booking: no recipient resolved for inquiry %s",
            inquiry.pk,
        )
        return

    artist_name = artist.stage_name if artist else "DJ ARTIST"

    email = EmailMessage(
        subject=f"New booking inquiry for {artist_name}: {inquiry.organization}",
        body=(
            f"New {inquiry.get_event_type_display()} inquiry "
            f"for {inquiry.event_date}.\n\n"
            f"Artist : {artist_name}\n"
            f"Contact: {inquiry.contact_name}, {inquiry.email}\n"
            f"Location: {inquiry.city_country}\n"
            f"Budget: {inquiry.budget or 'Not provided'}\n\n"
            f"Message:\n{inquiry.message}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
        cc=[artist.booking_cc_email] if artist and artist.booking_cc_email else [],
    )

    try:
        sent = email.send(fail_silently=False)   # returns number sent
        logger.info(
            "Booking notification for inquiry %s sent to %s (sent=%s)",
            inquiry.pk, recipient, sent,
        )
    except Exception:
        logger.exception(
            "Failed to send booking notification for inquiry %s to %s",
            inquiry.pk, recipient,
        )

# ---------------------------------------------------------------------
# NEW: Confirmation email sent to the person who submitted the inquiry
# ---------------------------------------------------------------------
def send_booking_confirmation(inquiry):
    """
    Send a confirmation email to the person who submitted the inquiry,
    letting them know their booking inquiry was received.

    Best-effort: failures never block the public user's flow.
    """
    # ✅ ADD THIS LINE
    artist_name = inquiry.artist.stage_name if inquiry.artist else "DJ ARTIST"

    try:
        send_mail(
            subject=f"We received your booking inquiry — {artist_name}",     # ✅ use artist_name
            message=(
                f"Hi {inquiry.contact_name},\n\n"
                f"Thank you for reaching out to {artist_name}. "              # ✅ use artist_name
                f"We have received your booking inquiry and the "
                f"management team will get back to you shortly.\n\n"
                f"Here is a summary of what you sent us:\n"
                f"-----------------------------------------\n"
                f"Organization : {inquiry.organization}\n"
                f"Event type   : {inquiry.event_type_display}\n"
                f"Event name   : {inquiry.event_name or '-'}\n"
                f"Event date   : {inquiry.event_date}\n"
                f"Venue        : {inquiry.venue or '-'}\n"
                f"Location     : {inquiry.city_country}\n"
                f"Audience     : "
                f"{inquiry.audience_size or 'Not provided'}\n"
                f"Budget       : {inquiry.budget or 'Not provided'}\n"
                f"Duration     : "
                f"{inquiry.performance_duration or 'Not provided'}\n"
                f"-----------------------------------------\n\n"
                f"Your message:\n{inquiry.message}\n\n"
                f"If you need to add anything, simply reply to this email.\n\n"
                f"— {artist_name} Management"                                    # ✅ use artist_name
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[inquiry.email],
            fail_silently=True,
        )
    except Exception:
        pass
    


# ---------------------------------------------------------------------
# Staff reply to a booking inquiry
# ---------------------------------------------------------------------
def send_booking_reply(booking, sender, subject, message):
    """
    Save a BookingReply and attempt to send the email.
    Returns the saved BookingReply with email_status set to
    'sent' or 'failed'.
    """
    reply = BookingReply.objects.create(
        booking=booking,
        sender=sender,
        recipient=booking.email,
        subject=subject,
        message=message,
        email_status="pending",
    )

    try:
        sent_count = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.email],
            fail_silently=False,
        )

        if sent_count != 1:
            raise RuntimeError(
                "The email backend did not confirm sending the email."
            )

        reply.email_status = "sent"
        reply.sent_at = timezone.now()
        reply.error_message = ""

    except Exception as error:
        reply.email_status = "failed"
        reply.error_message = str(error)

    reply.save(
        update_fields=["email_status", "sent_at", "error_message"]
    )

    return reply