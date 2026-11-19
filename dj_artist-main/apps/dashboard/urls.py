from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
   
    
    # ---------- Overview ----------
    path("", views.overview, name="overview"),

    # ---------- DJ profiles ----------
    path("djs/", views.dj_list, name="dj_list"),
    path("djs/add/", views.dj_create, name="dj_create"),
    path("djs/<int:pk>/edit/", views.dj_edit, name="dj_edit"),
    path("djs/<int:pk>/delete/", views.dj_delete, name="dj_delete"),

    # ---------- Music ----------
    path("music/", views.music_list, name="music_list"),
    path("music/add/", views.music_create, name="music_create"),
    path("music/<int:pk>/edit/", views.music_edit, name="music_edit"),
    path("music/<int:pk>/delete/", views.music_delete, name="music_delete"),

    # ---------- Events ----------
    path("events/", views.event_list, name="event_list"),
    path("events/add/", views.event_create, name="event_create"),
    path("events/<int:pk>/edit/", views.event_edit, name="event_edit"),
    path("events/<int:pk>/delete/", views.event_delete, name="event_delete"),

    # ---------- Press Kits (scoped list) ----------
    path("epk/", views.epk_list, name="epk_list"),

    # ---------- Bookings (scoped) ----------
    path("bookings/", views.bookings_list, name="bookings_list"),
    path("bookings/<int:booking_id>/", views.booking_detail, name="booking_detail"),

   
]