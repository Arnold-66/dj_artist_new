from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('core', '0002_dj_branding_fields'), ('events', '0001_initial')]
    operations = [migrations.AddField(model_name='event', name='artist', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='events', to='core.artistprofile'))]
