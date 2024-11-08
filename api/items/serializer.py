from rest_framework import serializers
from .model import Item


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ["id", "price", "size", "description", "brand"]
