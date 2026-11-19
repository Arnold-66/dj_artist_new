from django.db import migrations, models
from django.utils.text import slugify

def populate_slugs(apps, schema_editor):
    ArtistProfile = apps.get_model('core', 'ArtistProfile')
    for profile in ArtistProfile.objects.all().order_by('id'):
        base = slugify(profile.stage_name) or f'dj-{profile.pk}'
        slug = base
        n = 2
        while ArtistProfile.objects.filter(slug=slug).exclude(pk=profile.pk).exists():
            slug = f'{base}-{n}'
            n += 1
        profile.slug = slug
        profile.save(update_fields=['slug'])

class Migration(migrations.Migration):
    dependencies = [('core', '0001_initial')]
    operations = [
        migrations.AddField(model_name='artistprofile', name='slug', field=models.SlugField(blank=True, max_length=140, default='')),
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
        migrations.AlterField(model_name='artistprofile', name='slug', field=models.SlugField(blank=True, max_length=140, unique=True)),
        migrations.AddField(model_name='artistprofile', name='theme_color', field=models.CharField(default='#5B00C8', help_text="Hex colour used for this DJ's site theme", max_length=7)),
        migrations.AddField(model_name='artistprofile', name='hero_title', field=models.CharField(blank=True, default='Feel the heart beats', max_length=180)),
        migrations.AddField(model_name='artistprofile', name='hero_kicker', field=models.CharField(blank=True, default='NEW SINGLE', max_length=100)),
        migrations.AddField(model_name='artistprofile', name='signature_image', field=models.ImageField(blank=True, null=True, upload_to='artist/signatures/')),
    ]
