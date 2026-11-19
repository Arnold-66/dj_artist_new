import io
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MixForm
from .models import Mix
from apps.download.utils import log_download


# ---------------------------------------------------------------------
# LIST — public, but scoped for logged-in users
# ---------------------------------------------------------------------
def mix_list(request):
    videos = Mix.objects.filter(is_published=True, media_type="video")
    audios = Mix.objects.filter(is_published=True, media_type="audio")

    # If a DJ is selected in session, scope to that artist
    selected_dj = request.session.get("selected_dj")
    if selected_dj and Mix.objects.filter(artist__isnull=False).exists():
        videos = videos.filter(artist_id=selected_dj)
        audios = audios.filter(artist_id=selected_dj)

    # If the logged-in user is a DJ/operator, scope to their accessible artists
    user = request.user
    if user.is_authenticated and not user.is_staff and not user.is_superuser:
        artists = user.accessible_artists() if hasattr(user, "accessible_artists") else []
        if artists:
            videos = videos.filter(artist__in=artists)
            audios = audios.filter(artist__in=artists)

    platform_order = ["Spotify", "SoundCloud", "Audiomack"]
    audio_groups = []
    for platform in platform_order:
        tracks = audios.filter(platform__iexact=platform)
        if tracks.exists():
            audio_groups.append({"name": platform, "tracks": tracks})

    other_tracks = (
        audios.exclude(platform__iexact="Spotify")
        .exclude(platform__iexact="SoundCloud")
        .exclude(platform__iexact="Audiomack")
    )
    if other_tracks.exists():
        audio_groups.append({"name": "Other Platforms", "tracks": other_tracks})

    # Determine permissions for template
    can_manage = user.is_authenticated and (
        user.is_superuser or getattr(user, "is_admin_role", False) or user.is_staff
    )
    can_download = user.is_authenticated and getattr(user, "can_download", False)

    return render(
        request,
        "music/list.html",
        {
            "videos": videos,
            "audio_groups": audio_groups,
            "total_audio_count": audios.count(),
            "can_manage": can_manage,
            "can_download": can_download,
        },
    )


# ---------------------------------------------------------------------
# ADD / EDIT / DELETE — staff (admin/operator/DJ) only
# ---------------------------------------------------------------------
@staff_member_required
def mix_add(request):
    if request.method == "POST":
        form = MixForm(request.POST, request.FILES)
        # Scope artist dropdown to the user's accessible artists
        if hasattr(request.user, "accessible_artists"):
            form.fields["artist"].queryset = request.user.accessible_artists()
        if form.is_valid():
            mix = form.save()
            messages.success(request, f'"{mix.title}" was added successfully.')
            return redirect("music:list")
    else:
        form = MixForm()
        if hasattr(request.user, "accessible_artists"):
            form.fields["artist"].queryset = request.user.accessible_artists()

    return render(request, "music/add.html", {"form": form})


@staff_member_required
def mix_edit(request, pk):
    mix = get_object_or_404(Mix, pk=pk)
    # Only allow if user can manage this artist
    if hasattr(request.user, "can_manage_artist") and not request.user.can_manage_artist(mix.artist):
        messages.error(request, "You cannot edit that track.")
        return redirect("music:list")

    if request.method == "POST":
        form = MixForm(request.POST, request.FILES, instance=mix)
        if hasattr(request.user, "accessible_artists"):
            form.fields["artist"].queryset = request.user.accessible_artists()
        if form.is_valid():
            mix = form.save()
            messages.success(request, f'"{mix.title}" was updated successfully.')
            return redirect("music:list")
    else:
        form = MixForm(instance=mix)
        if hasattr(request.user, "accessible_artists"):
            form.fields["artist"].queryset = request.user.accessible_artists()

    return render(request, "music/edit.html", {"form": form, "mix": mix})


@staff_member_required
def mix_delete(request, pk):
    mix = get_object_or_404(Mix, pk=pk)
    if hasattr(request.user, "can_manage_artist") and not request.user.can_manage_artist(mix.artist):
        messages.error(request, "You cannot delete that track.")
        return redirect("music:list")

    if request.method == "POST":
        title = mix.title
        mix.delete()
        messages.success(request, f'"{title}" was deleted successfully.')
        return redirect("music:list")

    return render(request, "music/delete_confirm.html", {"mix": mix})


# ---------------------------------------------------------------------
# DOWNLOAD — login required; kit users audio only
# ---------------------------------------------------------------------
@login_required
def mix_download(request, pk):
    user = request.user

    # Gate 1: must be verified (or staff/operator)
    if not getattr(user, "can_download", False):
        messages.error(
            request,
            "Please verify your email address before downloading. "
            "Check your inbox for the verification link.",
        )
        return redirect("account_email_verification_sent")  # allauth

    mix = get_object_or_404(Mix, pk=pk, is_published=True)

    # Gate 2: kit users can only download audio
    if getattr(user, "is_kit_user", False) and mix.media_type == "video":
        messages.error(request, "Kit users may only download audio tracks.")
        return redirect("music:list")

    file_field = None
    mime_type = None
    is_audio = False

    if mix.media_type == "video" and mix.video_file:
        file_field = mix.video_file
        mime_type = "video/mp4"
    elif mix.media_type == "audio" and mix.audio_file:
        file_field = mix.audio_file
        mime_type = "audio/mpeg"
        is_audio = True

    if not file_field:
        messages.error(request, "No downloadable file is attached to this mix.")
        return redirect("music:list")

    filename = Path(file_field.name).name

    # Log the download
    try:
        log_download(
            user,
            title=mix.title,
            kind="audio" if is_audio else "video",
            reference_id=mix.pk,
            file_url=file_field.url,
            request=request,
        )
    except Exception:
        pass  # don't block download if logging fails

    # Embed cover art in ID3 tags for audio
    if is_audio and mix.cover_image:
        try:
            buffer = _embed_cover_in_audio(file_field, mix)
            if buffer:
                return FileResponse(
                    buffer,
                    as_attachment=True,
                    filename=filename,
                    content_type=mime_type,
                )
        except Exception:
            pass

    return FileResponse(
        file_field.open("rb"),
        as_attachment=True,
        filename=filename,
        content_type=mime_type or "application/octet-stream",
    )


def _embed_cover_in_audio(file_field, mix):
    """Embed cover image as ID3 APIC frame (album art). Returns BytesIO or None."""
    try:
        from mutagen.id3 import ID3, APIC, ID3NoHeaderError, TIT2
    except ImportError:
        return None

    stream = io.BytesIO(file_field.read())
    stream.seek(0)

    cover_bytes = mix.cover_image.read()
    mix.cover_image.seek(0)

    cover_ext = Path(mix.cover_image.name).suffix.lower().lstrip(".")
    cover_mime = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
    }.get(cover_ext, "image/jpeg")

    suffix = Path(file_field.name).suffix.lower()
    if suffix in {".mp3", ".m4a", ".mp4"}:
        try:
            try:
                tags = ID3(stream)
            except ID3NoHeaderError:
                tags = ID3()

            tags.add(
                APIC(
                    encoding=3,
                    mime=cover_mime,
                    type=3,
                    desc="Cover",
                    data=cover_bytes,
                )
            )
            tags.add(TIT2(encoding=3, text=mix.title))
            tags.save(stream)
            stream.seek(0)
            return stream
        except Exception:
            return None

    return None