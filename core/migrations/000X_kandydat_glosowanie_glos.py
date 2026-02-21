from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0009_wniosek_typ'),
    ]

    operations = [
        migrations.CreateModel(
            name='Kandydat',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('imie', models.CharField(max_length=100)),
                ('nazwisko', models.CharField(max_length=100)),
                ('opis', models.TextField(blank=True)),
                ('punkt_obrad', models.ForeignKey('core.PunktObrad', on_delete=models.CASCADE, related_name='kandydaci')),
            ],
        ),
        migrations.AddField(
            model_name='glosowanie',
            name='typ',
            field=models.CharField(max_length=20, choices=[('zwykle', 'Zwykłe (za/przeciw/wstrzymuje)'), ('kandydaci', 'Imienne na kandydata')], default='zwykle'),
        ),
        migrations.AddField(
            model_name='glos',
            name='kandydat',
            field=models.ForeignKey('core.Kandydat', on_delete=models.CASCADE, blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='glos',
            name='glos',
            field=models.CharField(max_length=10, choices=[('za', 'Za'), ('przeciw', 'Przeciw'), ('wstrzymuje', 'Wstrzymuję się')], blank=True, null=True),
        ),
    ]