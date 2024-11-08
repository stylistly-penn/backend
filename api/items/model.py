from django.db import models
from rest_framework.permissions import AllowAny


class Item(models.Model):
    price = models.FloatField()
    size = models.CharField(max_length=50)
    description = models.TextField()
    brand = models.CharField(max_length=100)

    permissions_classes = [AllowAny]
