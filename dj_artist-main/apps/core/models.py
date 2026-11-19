from django.db import models
from django.utils.text import slugify

class ArtistProfile(models.Model):
    stage_name = models.CharField(max_length=120, default="DJ ARTIST")
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    theme_color = models.CharField(max_length=7, default="#5B00C8", help_text="Hex colour used for this DJ's site theme")
    hero_title = models.CharField(max_length=180, blank=True, default="Feel the heart beats")
    hero_kicker = models.CharField(max_length=100, blank=True, default="NEW SINGLE")
    signature_image = models.ImageField(upload_to="artist/signatures/", blank=True, null=True)
    tagline = models.CharField(max_length=200, blank=True, default="Music. Culture. Unforgettable Experiences.")
    short_bio = models.TextField(blank=True)
    full_bio = models.TextField(blank=True)
    hero_image = models.ImageField(upload_to="artist/", blank=True, null=True)
    logo = models.ImageField(upload_to="artist/", blank=True, null=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    instagram_url = models.URLField(blank=True)
     # NEW: where booking notifications for THIS DJ should go
    notification_email = models.EmailField(
        blank=True,
        help_text="Where booking notifications for this artist are sent. "
                  "Falls back to the site default if left blank.",
    )
    # optional: a cc/team address for this DJ
    booking_cc_email = models.EmailField(
        blank=True,
        help_text="Optional CC address (e.g. manager) for booking notifications.",
    )
    facebook_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Artist profile"

    def __str__(self):
        return self.stage_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.stage_name) or "dj"
        super().save(*args, **kwargs)

    @classmethod
    def current(cls):
        return cls.objects.order_by("id").first()
    @property
    def booking_inbox(self):
        """Effective booking notification address for this artist."""
        return self.notification_email or self.email or ""
    



def current_artist(request):
    """
    Makes `artist` and `artists` available in every template so the
    navbar social icons (Facebook / Instagram / YouTube) render on
    every page — not just the home page.

    Priority:
      1. ?dj=<slug> in the URL
      2. last DJ picked in session
      3. first artist in the DB (fallback so fresh visitors still see icons)
    """
    artist = None

    # 1) Explicit ?dj=<slug>
    dj_slug = request.GET.get("dj")
    if dj_slug:
        artist = ArtistProfile.objects.filter(slug=dj_slug).first()
        if artist:
            request.session["selected_dj_slug"] = artist.slug

    # 2) Session fallback
    if artist is None:
        slug = request.session.get("selected_dj_slug")
        if slug:
            artist = ArtistProfile.objects.filter(slug=slug).first()

    # 3) First artist in the DB
    if artist is None:
        artist = ArtistProfile.objects.order_by("id").first()

    return {
        "artist": artist,
        "artists": ArtistProfile.objects.order_by("stage_name"),
    }