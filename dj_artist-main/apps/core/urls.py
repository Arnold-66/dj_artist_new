from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    # Landing page = artist directory
    path("", views.artist_directory, name="artist_directory"),

    # Home page for a specific artist (used when clicking a directory row)
    path("artists/<slug:slug>/", views.home, name="home"),
]