from rest_framework import viewsets
from .models import Brand
from .serializers import BrandSerializer
from api.permissions import IsAdminOrReadOnly


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAdminOrReadOnly]
