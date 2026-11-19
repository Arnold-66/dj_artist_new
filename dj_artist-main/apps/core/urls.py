from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("artists/", views.artist_directory, name="artist_directory"),
]