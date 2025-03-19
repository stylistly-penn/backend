from django.db import models
from django.conf import settings

# Create your models here.


class List(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lists"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.name} - {self.owner.email}"  # Using email instead of username since that's what our User model uses


class ListItem(models.Model):
    list = models.ForeignKey(List, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(
        "items.Item", on_delete=models.CASCADE, related_name="list_items"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-added_at"]
        unique_together = ["list", "item"]  # Prevent duplicate items in the same list

    def __str__(self):
        return f"{self.item.name} in {self.list.name}"
