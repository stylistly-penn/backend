# Generated by Django 5.1.2 on 2025-02-03 22:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brands', '0003_alter_brand_name'),
        ('items', '0002_alter_item_brand_item_unique_item_constraint'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='item',
            name='unique_item_constraint',
        ),
        migrations.AddConstraint(
            model_name='item',
            constraint=models.UniqueConstraint(fields=('description', 'price', 'size', 'product_url'), name='unique_item_constraint'),
        ),
    ]
