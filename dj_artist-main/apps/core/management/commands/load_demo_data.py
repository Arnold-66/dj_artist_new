from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.core.models import ArtistProfile
from apps.events.models import Event
from apps.music.models import Mix
from apps.epk.models import PressKit

class Command(BaseCommand):
    help = "Load two editable DJ demo profiles, their EPKs, events and music."

    def handle(self, *args, **options):
        demos = [
            {"stage_name": "City Girl Ug", "slug": "city-girl-ug", "theme_color": "#5B00C8", "hero_title": "Feel the heart beats", "hero_kicker": "NEW SINGLE", "tagline": "Deep rhythms. Electric nights. Unforgettable energy.", "short_bio": "DEMO BIO: Replace this with City Girl Ug's approved biography.", "full_bio": "DEMO CONTENT. Add the artist's verified biography, genres, career highlights and notable performances."},
            {"stage_name": "Dj Scratch Laizor", "slug": "dj-scratch-laizor", "theme_color": "#9B2CBA", "hero_title": "Move with the music", "hero_kicker": "LIVE THE SOUND", "tagline": "A different sound for every unforgettable moment.", "short_bio": "DEMO BIO: Replace this with Dj Scratch Laizor's approved biography.", "full_bio": "DEMO CONTENT. Add the artist's verified biography, genres, career highlights and notable performances."},
        ]
        artists = []
        for data in demos:
            slug = data.pop("slug")
            artist, _ = ArtistProfile.objects.update_or_create(slug=slug, defaults=data)
            artists.append(artist)

        for artist in artists:
            PressKit.objects.get_or_create(
                slug=f"{artist.slug}-epk",
                defaults={"artist": artist, "title": f"{artist.stage_name} — Official EPK", "short_bio": artist.short_bio, "full_bio": artist.full_bio, "is_published": True, "is_active": True},
            )

        now = timezone.now()
        for artist, suffix, place in [(artists[0], "kampala", "Kampala, Uganda"), (artists[1], "kigali", "Kigali, Rwanda")]:
            Event.objects.get_or_create(
                slug=f"demo-{suffix}-live",
                defaults={"artist": artist, "title": f"DEMO · {artist.stage_name} Live", "event_type": "Demo event — replace me", "venue": "Demo venue", "city_country": place, "start_at": now + timedelta(days=14), "end_at": now + timedelta(days=14, hours=3), "description": "DEMO CONTENT ONLY. Replace or delete before publishing.", "is_published": True},
            )
            Mix.objects.get_or_create(
                title=f"DEMO · {artist.stage_name} Session",
                defaults={"artist": artist, "media_type": "audio", "platform": "YouTube", "embed_url": "https://www.youtube.com/embed/ScMzIvxBSi4", "description": "DEMO EMBED — replace with the artist's real release.", "is_published": True},
            )
            Mix.objects.get_or_create(
                title=f"DEMO · {artist.stage_name} Live Video",
                defaults={"artist": artist, "media_type": "video", "platform": "YouTube", "embed_url": "https://www.youtube.com/embed/ScMzIvxBSi4", "description": "DEMO VIDEO — replace with the artist's real performance.", "is_published": True},
            )
        self.stdout.write(self.style.SUCCESS("Two DJ demo profiles, EPKs, events and music created. Replace all DEMO content before launch."))
