from rest_framework import serializers
from .models import Item
from api.relationships.models import ItemColor
from api.color.models import Color


class ColorSerializer(serializers.ModelSerializer):
    """Serializes the color information along with its image URL."""

    code = serializers.CharField(
        source="color.code"
    )  # Gets the color code from the Color model
    image_url = serializers.URLField()

    class Meta:
        model = ItemColor
        fields = ["code", "image_url"]


class ItemSerializer(serializers.ModelSerializer):
    """Serializes the Item model, including associated colors and images."""

    colors = ColorSerializer(source="item_colors", many=True)

    class Meta:
        model = Item
        fields = ["id", "price", "size", "description", "brand", "colors"]
