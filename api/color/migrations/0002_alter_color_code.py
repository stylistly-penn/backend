# Generated by Django 5.1.2 on 2024-11-22 18:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('color', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='color',
            name='code',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]