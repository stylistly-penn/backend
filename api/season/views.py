from .models import Season
from .serializers import SeasonSerializer
from rest_framework import viewsets


class SeasonViewSet(viewsets.ModelViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
