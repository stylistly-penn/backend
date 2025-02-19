from django.db import models
from rest_framework.permissions import AllowAny
from api.brands.models import Brand


class Item(models.Model):
    price = models.FloatField()
    size = models.CharField(max_length=50)
    description = models.TextField()
    product_url = models.TextField()
    product_id = models.TextField(default="")
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="items")

    permissions_classes = [AllowAny]

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product_id"],
                name="unique_item_constraint",
            )
        ]
