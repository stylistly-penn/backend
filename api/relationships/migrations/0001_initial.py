# Generated by Django 5.1.2 on 2024-11-09 18:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('color', '__first__'),
        ('items', '0001_initial'),
        ('season', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemColor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_url', models.URLField()),
                ('color', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='color_items', to='color.color')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='item_colors', to='items.item')),
            ],
            options={
                'unique_together': {('item', 'color')},
            },
        ),
        migrations.CreateModel(
            name='SeasonColor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('color', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='color_seasons', to='color.color')),
                ('season', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='season_colors', to='season.season')),
            ],
            options={
                'unique_together': {('season', 'color')},
            },
        ),
    ]
