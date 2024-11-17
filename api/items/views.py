from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Item
from api.brands.models import Brand
from api.color.models import Color
from api.relationships.models import ItemColor
from .serializers import ItemSerializer


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
        brand = Brand.objects.get(name=brand_name)

        if brand is None:
            try:
                brand = Brand.objects.create(name=brand_name)
                print(brand)
            except:
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        color_rgb = request.data.get("RGB")
        color = Color.objects.get(code=color_rgb)

        if color is None:
            try:
                color = Color.objects.create(code=color_rgb)
            except:
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
