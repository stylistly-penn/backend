from rest_framework import serializers
from .models import Item
from api.relationships.models import ItemColor
from api.color.models import Color
from api.brands.serializers import BrandSerializer


class ItemColorSerializer(serializers.ModelSerializer):
    """Serializes the color information along with its image URL."""

    code = serializers.CharField(source="color.code")
    color_id = serializers.PrimaryKeyRelatedField(
        source="color.id", queryset=Color.objects.all()
    )
    image_url = serializers.URLField()

    class Meta:
        model = ItemColor
        fields = ["code", "real_rgb", "image_url", "color_id", "euclidean_distance"]


class ItemFilterSerializer(serializers.ModelSerializer):
    """Serializes an item with its attributes and a filtered colors field.

    Expects a 'filter_color_id' in the serializer context, and returns only
    the best matching color (sorted by euclidean_distance) for that filter.
    """

    brand = BrandSerializer(read_only=True)
    colors = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = ["id", "description", "price", "brand", "product_url", "colors"]

    def get_colors(self, obj):
        filter_color_id = self.context.get("filter_color_id")
        qs = obj.item_colors.all()  # Using the related name "item_colors"
        if filter_color_id:
            qs = qs.filter(color__id=filter_color_id)
        if qs.exists():
            best_color = qs.order_by("euclidean_distance").first()
            return [ItemColorSerializer(best_color, context=self.context).data]
        return []


class ItemSerializer(serializers.ModelSerializer):
    """Serializes the item information along with all of its colors."""

    brand = BrandSerializer(read_only=True)
    colors = ItemColorSerializer(many=True, read_only=True, source="item_colors")

    class Meta:
        model = Item
        fields = ["id", "description", "price", "brand", "product_url", "colors"]
