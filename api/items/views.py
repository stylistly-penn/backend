from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
import logging
from .models import Item
from api.brands.models import Brand
from api.color.models import Color
from api.relationships.models import ItemColor
from .serializers import ItemSerializer

logger = logging.getLogger("api.items")


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [AllowAny]

    """
    Ingestion route: takes in a POST request with a JSON body containing an item
    - description (string)
    - price (float)
    - brand (string)
    - item_url (string)
    - RGB (string)
    """

    def create(self, request, *args, **kwargs):
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
