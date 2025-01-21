from rest_framework import serializers
from api.season.models import Season
from api.color.models import Color
from api.relationships.models import SeasonColor


class ColorSerializer(serializers.ModelSerializer):
    """Serializes colors associated with a season."""

    code = serializers.CharField()

    class Meta:
        model = Color
        fields = ["code"]


class SeasonSerializer(serializers.ModelSerializer):
    """Serializes a season along with its colors."""

    colors = serializers.SerializerMethodField()

    class Meta:
        model = Season
        fields = ["name", "colors"]

    def get_colors(self, obj):
        colors = Color.objects.filter(color_seasons__season=obj)
        return ColorSerializer(colors, many=True).data
