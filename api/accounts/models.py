from django.contrib.auth.models import AbstractUser
from django.db import models
from api.season.models import Season


class User(AbstractUser):
    season = models.ForeignKey(
        Season, on_delete=models.SET_NULL, null=True, blank=True, related_name="users"
    )

    # Fix reverse accessor conflicts
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_set",  # Prevents conflict with default User model
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions_set",  # Prevents conflict with default User model
        blank=True,
    )
