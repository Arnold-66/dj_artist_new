from django.shortcuts import render, redirect, get_object_or_404
from apps.core.models import ArtistProfile
from apps.events.models import Event
from apps.music.models import Mix
from apps.epk.models import PressKit
from .models import ArtistProfile
from django.db.models import Q


def selected_artist(request):
    artists = ArtistProfile.objects.order_by("id")
    slug = request.GET.get("dj")
    if slug:
        artist = get_object_or_404(artists, slug=slug)
        request.session["selected_dj"] = artist.pk
    else:
        artist = artists.filter(pk=request.session.get("selected_dj")).first() or artists.first()
    if artist:
        request.session["selected_dj"] = artist.pk
    return artist

def home(request):
    artist = selected_artist(request)
    events = Event.objects.filter(is_published=True).filter(artist=artist).order_by("start_at")[:3] if artist and Event.objects.filter(artist__isnull=False).exists() else Event.objects.filter(is_published=True).order_by("start_at")[:3]
    mixes = Mix.objects.filter(is_published=True, artist=artist)[:3] if artist and Mix.objects.filter(artist__isnull=False).exists() else Mix.objects.filter(is_published=True)[:3]
    videos = Mix.objects.filter(is_published=True, media_type="video", artist=artist) if artist and Mix.objects.filter(artist__isnull=False).exists() else Mix.objects.filter(is_published=True, media_type="video")
    audios = Mix.objects.filter(is_published=True, media_type="audio", artist=artist) if artist and Mix.objects.filter(artist__isnull=False).exists() else Mix.objects.filter(is_published=True, media_type="audio")
    artists = ArtistProfile.objects.order_by("id")
    kit = PressKit.objects.filter(artist=artist, is_published=True).first() if artist else None
    return render(request, "core/home.html", {"artist": artist, "artists": artists, "events": events, "mixes": mixes, "videos": videos, "audios": audios, "artist_kit": kit})


def artist_directory(request):
    """
    Public directory of all artists.
    Each row links to the home page with ?dj=<slug>.
    """
    artists = ArtistProfile.objects.order_by("stage_name")

    q = request.GET.get("q", "").strip()
    if q:
        artists = artists.filter(
            Q(stage_name__icontains=q)
            | Q(tagline__icontains=q)
            | Q(short_bio__icontains=q)
        )

    return render(
        request,
        "core/artist_directory.html",
        {"artists": artists, "search_query": q},
    )