from django.db import models
from rest_framework.permissions import AllowAny


class Color(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=50, unique=True)

    permissions_classes = [AllowAny]
