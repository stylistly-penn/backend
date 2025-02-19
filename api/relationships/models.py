from django.db import models
from rest_framework.permissions import AllowAny
from api.color.models import Color
from api.season.models import Season


class ItemColor(models.Model):
    item = models.ForeignKey(
        "items.Item", on_delete=models.CASCADE, related_name="item_colors"
    )
    color = models.ForeignKey(
        Color, on_delete=models.CASCADE, related_name="color_items"
    )
    image_url = models.URLField(max_length=200)
    euclidean_distance = models.FloatField(default=0.0)
    real_rgb = models.CharField(
        max_length=20, default="", help_text="The original RGB from the CSV"
    )

    permissions_classes = [AllowAny]

    class Meta:
        unique_together = ("item", "real_rgb", "color")


class SeasonColor(models.Model):
    season = models.ForeignKey(
        Season, on_delete=models.CASCADE, related_name="season_colors"
    )
    color = models.ForeignKey(
        Color, on_delete=models.CASCADE, related_name="color_seasons"
    )

    permissions_classes = [AllowAny]

    class Meta:
        unique_together = ("season", "color")
