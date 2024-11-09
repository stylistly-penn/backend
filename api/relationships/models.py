from django.db import models
from rest_framework.permissions import AllowAny
from api.items.models import Item
from api.color.models import Color
from api.season.models import Season


class ItemColor(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="item_colors")
    color = models.ForeignKey(
        Color, on_delete=models.CASCADE, related_name="color_items"
    )
    image_url = models.URLField(max_length=200)

    permissions_classes = [AllowAny]

    class Meta:
        unique_together = ("item", "color")


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
