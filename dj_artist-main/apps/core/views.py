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

def home(request, slug):
    """Home page for a specific artist, selected by slug in the URL."""
    artist = get_object_or_404(ArtistProfile, slug=slug)

    # Remember selection for this session (optional but harmless)
    request.session["selected_dj"] = artist.pk

    events = Event.objects.filter(is_published=True, artist=artist).order_by("start_at")[:3]
    mixes  = Mix.objects.filter(is_published=True, artist=artist)[:3]
    videos = Mix.objects.filter(is_published=True, media_type="video", artist=artist)
    audios = Mix.objects.filter(is_published=True, media_type="audio", artist=artist)

    artists = ArtistProfile.objects.order_by("id")
    kit = PressKit.objects.filter(artist=artist, is_published=True).first()

    return render(request, "core/home.html", {
        "artist": artist,
        "artists": artists,
        "events": events,
        "mixes": mixes,
        "videos": videos,
        "audios": audios,
        "artist_kit": kit,
    })


def artist_directory(request):
    """
    Public directory of all artists — this is the landing page.
    Each row links to the artist's home page by slug.
    """
    artists = ArtistProfile.objects.order_by("stage_name")

    q = request.GET.get("q", "").strip()
    if q:
        artists = artists.filter(
            Q(stage_name__icontains=q)
            | Q(tagline__icontains=q)
            | Q(short_bio__icontains=q)
        )

    return render(request, "core/artist_directory.html", {
        "artists": artists,
        "search_query": q,
    })