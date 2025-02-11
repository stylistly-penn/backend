from concurrent.futures import ThreadPoolExecutor
from rest_framework import serializers
from django.db import transaction, IntegrityError
from django.db.models import Prefetch
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework import viewsets
from api.permissions import IsAuthenticatedReadOrAdminWrite
import logging
import numpy as np
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    inline_serializer,
    OpenApiTypes,
)
from .models import Item
from api.brands.models import Brand
from api.color.models import Color
from api.relationships.models import ItemColor
from .serializers import ItemSerializer

logger = logging.getLogger("api.items")


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticatedReadOrAdminWrite]

    CUTOFF_DISTANCE = 50.0

    """
    Filtering route for color palettes: takes in POST request with query param color
    - color (string) -> RGB value for color to filter clothes on
    
    Filters items by their color being within a certain distance on the color wheel
    """

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="color",
                description="The color to filter by in format [R G B]",
                required=True,
                type=str,
            )
        ]
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="filter_by_color",
    )
    def filter_by_color(self, request):
        color_str = request.query_params.get("color")
        if not color_str:
            return Response({"error": "Color parameter is required"}, status=400)

        try:
            query_rgb = np.fromstring(color_str.strip("[]"), sep=" ").astype(int)
        except ValueError:
            return Response({"error": "Invalid color format"}, status=400)

        # Pre-fetch related colors to reduce DB queries
        items = Item.objects.prefetch_related(
            Prefetch("item_colors", queryset=ItemColor.objects.select_related("color"))
        ).all()

        def process_item(item):
            for color in item.item_colors.all():
                try:
                    item_rgb = np.fromstring(
                        color.color.code.strip("[]"), sep=" "
                    ).astype(int)
                    distance = np.linalg.norm(query_rgb - item_rgb)
                    if distance <= self.CUTOFF_DISTANCE:
                        return item
                except ValueError:
                    continue
            return None

        # Use ThreadPoolExecutor to parallelize processing
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(process_item, items))

        # Remove None values and serialize
        filtered_items = [item for item in results if item]
        return Response(ItemSerializer(filtered_items, many=True).data)

    """
    Ingestion route: takes in a POST request with a JSON body containing an item
    - description (string)
    - price (float)
    - brand (string)
    - item_url (string)
    - RGB (string)
    """

    @extend_schema(
        request=inline_serializer(
            name="ItemIngestionInput",
            fields={
                "description": serializers.CharField(help_text="Item description"),
                "price": serializers.FloatField(help_text="Price of the item"),
                "brand": serializers.CharField(help_text="Brand name of the item"),
                "product_url": serializers.URLField(help_text="URL for the product"),
                "RGB": serializers.CharField(
                    help_text="RGB color as a string, e.g. '[59 68 52]'"
                ),
            },
        ),
        responses={201: OpenApiTypes.NONE},
        description="""
            Ingestion route: takes in a POST request with a JSON body containing an item:
            - **description** (string)
            - **price** (float)
            - **brand** (string)
            - **product_url** (string)
            - **RGB** (string)
        """,
    )
    def create(self, request, *args, **kwargs):
        print(f"🔎 DEBUG: Request headers received: {request.headers}")
        brand_name = request.data.get("brand")
        brand, _ = Brand.objects.get_or_create(name=brand_name)

        color_rgb = request.data.get("RGB")
        color, _ = Color.objects.get_or_create(code=color_rgb)

        try:
            with transaction.atomic():
                # Ensure unique constraint prevents duplicates
                item, created = Item.objects.get_or_create(
                    description=request.data.get("description"),
                    price=float(request.data.get("price")),
                    brand=brand,
                    product_url=request.data.get("product_url"),
                )

                if not created:
                    print(f"Item already exists: {item}")

                # Check if ItemColor relationship exists
                ic, created = ItemColor.objects.get_or_create(
                    item=item,
                    color=color,
                    defaults={"image_url": request.data.get("item_url")},
                )

                if not created:
                    print(f"ItemColor already exists: {ic}")

            return Response(status=status.HTTP_201_CREATED)

        except IntegrityError:
            logger.error("IntegrityError: Duplicate detected!", exc_info=True)
            return Response(
                status=status.HTTP_409_CONFLICT
            )  # Return 409 Conflict for duplicate

        except Exception:
            logger.error("Error creating item", exc_info=True)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
