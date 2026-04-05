from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_alter_glosowanie_punkt_obrad"),
    ]

    operations = [
        migrations.AddField(
            model_name="sesja",
            name="opis",
            field=models.TextField(blank=True),
        ),
    ]
