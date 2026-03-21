from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_alter_uzytkownik_rola"),
    ]

    operations = [
        migrations.AddField(
            model_name="uzytkownik",
            name="opis",
            field=models.TextField(blank=True, default=""),
        ),
    ]
