# Generated by Django 3.1.2 on 2020-10-01 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_auto_20201001_0940'),
    ]

    operations = [
        migrations.AlterField(
            model_name='networkuser',
            name='lat',
            field=models.FloatField(default=float("nan")),
        ),
        migrations.AlterField(
            model_name='networkuser',
            name='lng',
            field=models.FloatField(default=float("nan")),
        ),
    ]
