# Generated by Django 4.2 on 2023-07-04 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('UpDownShare', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='file',
            field=models.FileField(upload_to='main/'),
        ),
    ]
