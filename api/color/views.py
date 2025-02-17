from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Color
from .serializers import ColorSerializer
from api.season.serializers import SeasonSimpleSerializer
from api.permissions import IsAdminOrReadOnly
from api.relationships.models import SeasonColor


class ColorViewSet(viewsets.ModelViewSet):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [IsAdminOrReadOnly]

    @action(detail=False, methods=["get"], url_path="get_seasons/(?P<color_id>\d+)")
    def get_seasons(self, request, color_id):
        """
        GET /color/get_seasons/<color_id>

        Returns a list of seasons (id and name) associated with the given color.
        """
        # Query the SeasonColor table to find all season associations for the given color_id.
        season_colors = SeasonColor.objects.filter(color__id=color_id)
        # Extract unique Season instances from the query (in case a season appears more than once)
        seasons = list({sc.season.id: sc.season for sc in season_colors}.values())
        serializer = SeasonSimpleSerializer(seasons, many=True)
        return Response(serializer.data)
