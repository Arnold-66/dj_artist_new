from django import forms
from apps.core.models import ArtistProfile

class ArtistProfileForm(forms.ModelForm):
    class Meta:
        model = ArtistProfile
        fields = ["stage_name", "slug", "tagline", "hero_kicker", "hero_title", "theme_color", "short_bio", "full_bio", "hero_image", "signature_image", "logo", "email", "phone", "instagram_url", "facebook_url", "tiktok_url", "youtube_url"]
        widgets = {"short_bio": forms.Textarea(attrs={"rows": 4}), "full_bio": forms.Textarea(attrs={"rows": 7}), "theme_color": forms.TextInput(attrs={"type": "color"})}
