from django.db import models
from rest_framework.permissions import AllowAny


class Season(models.Model):
    name = models.CharField(max_length=255)

    permission_classes = [AllowAny]
