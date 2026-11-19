from .models import ArtistProfile

def dj_site_context(request):
    artists = ArtistProfile.objects.order_by('id')
    selected = artists.filter(pk=request.session.get('selected_dj')).first() or artists.first()
    return {'artists': artists, 'artist': selected}
