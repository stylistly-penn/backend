from .models import Season
from rest_framework import serializers


class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = ["name"]
