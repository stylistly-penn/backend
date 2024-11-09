from django.db import models
from rest_framework.permissions import AllowAny
from django.contrib.postgres.fields import ArrayField


class Brand(models.Model):
    name = models.CharField(max_length=50)
    styles = ArrayField(models.CharField(max_length=50))

    permissions_classes = [AllowAny]
