from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Min, Q
from .models import List, ListItem
from .serializers import ListSerializer, ListItemSerializer, ListWithItemsSerializer
from api.permissions import IsOwnerOrReadOnly

# Create your views here.


class ListViewSet(viewsets.ModelViewSet):
    serializer_class = ListSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        return List.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def add_item(self, request, pk=None):
        list_obj = self.get_object()
        item_id = request.data.get("item_id")

        if not item_id:
            return Response(
                {"error": "item_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            list_item = ListItem.objects.create(list=list_obj, item_id=item_id)
            serializer = ListItemSerializer(list_item, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def items(self, request, pk=None):
        list_obj = self.get_object()

        # Get ordering parameters
        order_by = request.query_params.get("order_by", "added_at")
        reverse = request.query_params.get("reverse", "true").lower() == "true"

        # Get the user's season for filtering
        user = request.user
        season_id = user.season_id if hasattr(user, "season_id") else None

        # Start with the list's items
        list_items = ListItem.objects.filter(list=list_obj)

        # Apply ordering
        if order_by == "price":
            list_items = list_items.order_by("item__price")
        elif order_by == "euclidean_distance":
            if season_id:
                # Use the minimum euclidean distance among colors in the season
                list_items = list_items.annotate(
                    min_season_distance=Min(
                        "item__item_colors__euclidean_distance",
                        filter=Q(
                            item__item_colors__color__color_seasons__season_id=season_id
                        ),
                    )
                ).order_by("min_season_distance")
            else:
                # Use the minimum euclidean distance across all colors
                list_items = list_items.annotate(
                    min_distance=Min("item__item_colors__euclidean_distance")
                ).order_by("min_distance")
        else:  # Default to added_at ordering
            list_items = list_items.order_by("added_at")

        # Apply reverse if requested
        if reverse:
            list_items = list_items.reverse()

        # Serialize the ordered list items
        serializer = ListItemSerializer(
            list_items, many=True, context={"request": request}
        )
        return Response(serializer.data)
