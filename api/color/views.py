from rest_framework import viewsets
from .models import Color
from .serializers import ColorSerializer


class ColorViewSet(viewsets.ModelViewSet):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
