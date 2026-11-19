from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('core', '0002_dj_branding_fields'), ('music', '0003_mix_apple_music_url_mix_audiomack_url_and_more')]
    operations = [migrations.AddField(model_name='mix', name='artist', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mixes', to='core.artistprofile'))]
