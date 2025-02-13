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
from .serializers import ItemSerializer, ItemFilterSerializer

logger = logging.getLogger("api.items")


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticatedReadOrAdminWrite]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="color_id",
                description="The ID of the color to filter by",
                required=True,
                type=int,
            )
        ]
    )
    @action(detail=False, methods=["get"], url_path="filter_by_color/(?P<color_id>\d+)")
    def filter_by_color_id(self, request, color_id):
        """
        Filters items by a given color id.

        Returns items that have an associated ItemColor with the given color id.
        The items are sorted by the euclidean_distance of that relationship.
        The nested 'colors' field will contain only the best matching ItemColor.
        """
        try:
            color_id = int(color_id)
        except ValueError:
            return Response(
                {"error": "Invalid color id"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Filter items that have at least one associated ItemColor with this color id,
        # order them by the euclidean_distance from that relation, and eliminate duplicates.
        items = (
            self.get_queryset()
            .filter(item_colors__color__id=color_id)
            .distinct()
            .order_by("item_colors__euclidean_distance")
        )

        # Use the ItemFilterSerializer which expects "filter_color_id" in its context.
        serializer = ItemFilterSerializer(
            items, many=True, context={"filter_color_id": color_id}
        )
        return Response(serializer.data)

    @extend_schema(
        request=inline_serializer(
            name="ItemIngestionInput",
            fields={
                "description": serializers.CharField(help_text="Item description"),
                "price": serializers.FloatField(help_text="Price of the item"),
                "brand": serializers.CharField(help_text="Brand name of the item"),
                "product_url": serializers.URLField(help_text="URL for the product"),
                "item_url": serializers.URLField(help_text="URL for the item image"),
                "color_id": serializers.IntegerField(
                    help_text="ID of the closest color"
                ),
                "euclidean_distance": serializers.FloatField(
                    help_text="Computed Euclidean distance"
                ),
                "real_rgb": serializers.CharField(
                    help_text="Real RGB value, e.g. '[59 68 52]'"
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
            - **item_url** (string)
            - **color_id** (integer)
            - **euclidean_distance** (float)
            - **real_rgb** (string, e.g. "[59 68 52]")
        """,
    )
    def create(self, request, *args, **kwargs):
        print(f"🔎 DEBUG: Request headers received: {request.headers}")
        brand_name = request.data.get("brand")
        brand, _ = Brand.objects.get_or_create(name=brand_name)

        color_id = request.data.get("color_id")
        euclidean_distance = request.data.get("euclidean_distance")
        real_rgb = request.data.get("real_rgb")
        color = Color.objects.get(pk=color_id)

        try:
            with transaction.atomic():
                # Ensure we only have one unique item record
                item, _ = Item.objects.get_or_create(
                    description=request.data.get("description"),
                    price=float(request.data.get("price")),
                    brand=brand,
                    product_url=request.data.get("product_url"),
                )

                # Always create a new ItemColor record for each ingestion call
                ic = ItemColor.objects.create(
                    item=item,
                    color=color,
                    image_url=request.data.get("item_url"),
                    euclidean_distance=euclidean_distance,
                    real_rgb=real_rgb,
                )

            return Response(status=status.HTTP_201_CREATED)

        except IntegrityError:
            logger.error("IntegrityError: Duplicate detected!", exc_info=True)
            return Response(status=status.HTTP_409_CONFLICT)

        except Exception:
            logger.error("Error creating item", exc_info=True)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
