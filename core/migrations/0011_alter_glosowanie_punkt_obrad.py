import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_merge_20260308_1638"),
    ]

    operations = [
        migrations.AlterField(
            model_name="glosowanie",
            name="punkt_obrad",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="glosowania",
                to="core.punktobrad",
            ),
        ),
    ]
