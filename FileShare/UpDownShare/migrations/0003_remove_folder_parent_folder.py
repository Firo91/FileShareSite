# Generated by Django 4.2 on 2023-07-06 07:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('UpDownShare', '0002_alter_file_file'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='folder',
            name='parent_folder',
        ),
    ]
