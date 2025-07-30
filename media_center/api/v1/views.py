from rest_framework import viewsets

from media_center.models import Media
from .serializers import MediaSerializer


class MediaViewSet(viewsets.ModelViewSet):
    serializer_class = MediaSerializer

    def get_queryset(self):
        return Media.objects.all().order_by('-id')
