from django.contrib import admin
from .models import ArtistProfile

@admin.register(ArtistProfile)
class ArtistProfileAdmin(admin.ModelAdmin):
    list_display = ("stage_name", "slug", "theme_color", "email", "updated_at")
    prepopulated_fields = {"slug": ("stage_name",)}
