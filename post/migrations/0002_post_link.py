# Generated by Django 3.1.2 on 2020-10-01 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('post', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='link',
            field=models.URLField(null=True),
        ),
    ]
