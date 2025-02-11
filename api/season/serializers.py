from rest_framework import serializers
from api.season.models import Season
from api.color.models import Color
from drf_spectacular.utils import extend_schema_field


class SeasonColorSerializer(serializers.ModelSerializer):
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

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_colors(self, obj):
        colors = Color.objects.filter(color_seasons__season=obj)
        return SeasonColorSerializer(colors, many=True).data
