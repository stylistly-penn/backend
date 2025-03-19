from rest_framework import serializers
from .models import List, ListItem
from api.items.serializers import ItemSerializer, ItemSeasonFilterSerializer


class ListSerializer(serializers.ModelSerializer):
    class Meta:
        model = List
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class ListItemSerializer(serializers.ModelSerializer):
    item = serializers.SerializerMethodField()

    class Meta:
        model = ListItem
        fields = ["id", "item", "added_at"]
        read_only_fields = ["added_at"]

    def get_item(self, obj):
        # Get the user's season from the request context
        user = self.context.get("request").user
        season_id = user.season_id if hasattr(user, "season_id") else None

        if season_id:
            # Use ItemSeasonFilterSerializer if user has a season
            serializer = ItemSeasonFilterSerializer(
                obj.item, context={"season_id": season_id}
            )
        else:
            # Use regular ItemSerializer if no season
            serializer = ItemSerializer(obj.item)

        return serializer.data


class ListWithItemsSerializer(serializers.ModelSerializer):
    items = ListItemSerializer(many=True, read_only=True)

    class Meta:
        model = List
        fields = ["id", "name", "items", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
