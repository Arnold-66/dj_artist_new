from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('core', '0002_dj_branding_fields'), ('epk', '0004_presskit_is_active')]
    operations = [migrations.AddField(model_name='presskit', name='artist', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='press_kits', to='core.artistprofile'))]
