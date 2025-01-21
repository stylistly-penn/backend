from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
import logging
import numpy as np
from .models import Item
from api.brands.models import Brand
from api.color.models import Color
from api.relationships.models import ItemColor
from .serializers import ItemSerializer

logger = logging.getLogger("api.items")


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]

    CUTOFF_DISTANCE = 50.0

    """
    Filtering route for color palettes: takes in POST request with query param color
    - color (string) -> RGB value for color to filter clothes on
    
    Filters items by their color being within a certain distance on the color wheel
    """

    @action(detail=False, methods=["get"], url_path="filter_by_color")
    def filter_by_color(self, request):
        color_str = request.query_params.get(
            "color"
        )  # Expecting string like "[161 109 68]"
        if not color_str:
            return Response({"error": "Color parameter is required"}, status=400)

        try:
            query_rgb = np.fromstring(color_str.strip("[]"), sep=" ").astype(int)
        except ValueError:
            return Response({"error": "Invalid color format"}, status=400)

        filtered_items = []
        for item in Item.objects.all():
            for color in item.item_colors.all():
                item_color_str = color.color.code
                item_rgb = np.fromstring(item_color_str.strip("[]"), sep=" ").astype(
                    int
                )

                # Compute Euclidean distance
                distance = np.linalg.norm(query_rgb - item_rgb)

                if distance <= self.CUTOFF_DISTANCE:
                    filtered_items.append(item)

        return Response(ItemSerializer(filtered_items, many=True).data)

    """
    Ingestion route: takes in a POST request with a JSON body containing an item
    - description (string)
    - price (float)
    - brand (string)
    - item_url (string)
    - RGB (string)
    """

    def create(self, request, *args, **kwargs):
        print(f"🔎 DEBUG: Request headers received: {request.headers}")
        brand_name = request.data.get("brand")
        brand, created = Brand.objects.get_or_create(name=brand_name)

        if created:
            print(f"Created brand: {brand_name}")

        color_rgb = request.data.get("RGB")
        color, created = Color.objects.get_or_create(code=color_rgb)

        if created:
            print(f"Created color: {color_rgb}")

        try:
            item = Item.objects.create(
                description=request.data.get("description"),
                price=float(request.data.get("price")),
                brand=brand,
            )
            ic = ItemColor.objects.create(
                item=item,
                color=color,
                image_url=request.data.get("item_url"),
            )
            return Response(status=status.HTTP_201_CREATED)
        except:
            logger.error("Error creating item", exc_info=True)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
