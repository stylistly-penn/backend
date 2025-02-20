from concurrent.futures import ThreadPoolExecutor
from rest_framework import serializers
from django.db import transaction, IntegrityError
from django.db.models import Prefetch, Min
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
from .serializers import (
    ItemSerializer,
    ItemFilterSerializer,
    ItemSeasonFilterSerializer,
)
from rest_framework.pagination import PageNumberPagination
from django.db import models

logger = logging.getLogger("api.items")


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all().order_by("id")
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticatedReadOrAdminWrite]
    pagination_class = PageNumberPagination

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

        page = self.paginate_queryset(items)
        serializer = ItemFilterSerializer(
            page, many=True, context={"filter_color_id": color_id}
        )
        return self.get_paginated_response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="brand_id",
                description="The ID of the brand to filter by",
                required=True,
                type=int,
            )
        ]
    )
    @action(detail=False, methods=["get"], url_path="filter_by_brand/(?P<brand_id>\d+)")
    def filter_by_brand_id(self, request, brand_id):
        """
        Filters items by a given brand id.

        Returns items that have the specified brand.
        The items are sorted by their id.
        """
        try:
            brand_id = int(brand_id)
        except ValueError:
            return Response(
                {"error": "Invalid brand id"}, status=status.HTTP_400_BAD_REQUEST
            )

        items = self.get_queryset().filter(brand__id=brand_id).distinct()

        page = self.paginate_queryset(items)
        serializer = ItemFilterSerializer(
            page, many=True, context={"filter_brand_id": brand_id}
        )
        return self.get_paginated_response(serializer.data)

    @extend_schema(
        request=inline_serializer(
            name="ItemIngestionInput",
            fields={
                "description": serializers.CharField(help_text="Item description"),
                "price": serializers.FloatField(help_text="Price of the item"),
                "brand": serializers.CharField(help_text="Brand name of the item"),
                "product_url": serializers.URLField(help_text="URL for the product"),
                "product_id": serializers.CharField(help_text="Product ID"),
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
            - **product_id** (string)
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
                    product_id=request.data.get("product_id"),
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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="color_id",
                description="Filter by color id",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="brand_id",
                description="Filter by brand id",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="size",
                description="Filter by item size",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="season_id",
                description="Filter by season id",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="order_by",
                description="Order by field (euclidean_distance or price)",
                required=False,
                type=str,
            ),
        ],
        responses=ItemFilterSerializer,
        description="""
        Filters items based on query parameters:
          - color_id: filter items that have an associated ItemColor with this color id.
          - brand_id: filter items that match this brand.
          - size: filter items with the given size.
          - season_id: filter items by season id.
          - order_by: order the result by 'euclidean_distance' (if filtering by color) or by 'price'.
          
        Note: If both color_id and season_id are provided, color_id takes precedence.
        """,
    )
    @action(detail=False, methods=["get"], url_path="filter_items")
    def filter_items(self, request):
        color_id = request.query_params.get("color_id")
        brand_id = request.query_params.get("brand_id")
        size = request.query_params.get("size")
        season_id = request.query_params.get("season_id")
        order_by = request.query_params.get("order_by")

        qs = self.get_queryset()

        # Filter by brand
        if brand_id:
            try:
                brand_id = int(brand_id)
                qs = qs.filter(brand__id=brand_id)
            except ValueError:
                return Response(
                    {"error": "Invalid brand id"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Filter by size
        if size:
            qs = qs.filter(size=size)

        # Filter and order by color, season, or neither
        if color_id:
            try:
                color_id = int(color_id)
                qs = qs.filter(item_colors__color_id=color_id)
                if order_by == "euclidean_distance":
                    # Use the euclidean distance for the specific color
                    qs = qs.annotate(
                        color_distance=models.Min(
                            "item_colors__euclidean_distance",
                            filter=models.Q(item_colors__color_id=color_id),
                        )
                    ).order_by("color_distance")
            except ValueError:
                return Response(
                    {"error": "Invalid color id"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif season_id:
            try:
                season_id = int(season_id)
                qs = qs.filter(item_colors__color__color_seasons__season_id=season_id)
                if order_by == "euclidean_distance":
                    # Use the minimum euclidean distance among colors in the season
                    qs = qs.annotate(
                        min_season_distance=models.Min(
                            "item_colors__euclidean_distance",
                            filter=models.Q(
                                item_colors__color__color_seasons__season_id=season_id
                            ),
                        )
                    ).order_by("min_season_distance")
            except ValueError:
                return Response(
                    {"error": "Invalid season id"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            # No color or season filter
            if order_by == "euclidean_distance":
                # Use the minimum euclidean distance across all colors
                qs = qs.annotate(
                    min_distance=models.Min("item_colors__euclidean_distance")
                ).order_by("min_distance")

        qs = qs.distinct()

        # Apply price ordering if requested and not already ordered by distance
        if order_by == "price":
            qs = qs.order_by("price")
        elif not order_by or (order_by != "euclidean_distance"):
            qs = qs.order_by("id")

        serializer_context = {}
        if color_id:
            serializer_context["filter_color_id"] = color_id
        if brand_id:
            serializer_context["filter_brand_id"] = brand_id
        if season_id and not color_id:
            serializer_context["season_id"] = season_id

        page = self.paginate_queryset(qs)
        # Use ItemSerializer when no color/season filter to show all colors
        if not color_id and not season_id:
            serializer = ItemSerializer(page, many=True)
        elif color_id:
            serializer = ItemFilterSerializer(
                page, many=True, context=serializer_context
            )
        else:
            serializer = ItemSeasonFilterSerializer(
                page, many=True, context=serializer_context
            )

        return self.get_paginated_response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="season_id",
                description="The ID of the season to filter by",
                required=True,
                type=int,
            )
        ]
    )
    @action(
        detail=False, methods=["get"], url_path="filter_by_season/(?P<season_id>\d+)"
    )
    def filter_by_season(self, request, season_id):
        """
        Filters items by a given season.

        Returns items that have at least one associated color in the specified season.
        Only returns the colors that belong to that season for each item.
        """
        try:
            season_id = int(season_id)
        except ValueError:
            return Response(
                {"error": "Invalid season id"}, status=status.HTTP_400_BAD_REQUEST
            )

        items = (
            self.get_queryset()
            .filter(item_colors__color__color_seasons__season_id=season_id)
            .distinct()
            .order_by("id")
        )

        page = self.paginate_queryset(items)
        serializer = ItemSeasonFilterSerializer(
            page, many=True, context={"season_id": season_id}
        )
        return self.get_paginated_response(serializer.data)
