from rest_framework import serializers

from media_center.models import Media
from media_center.tasks import generate_hls_for_media
from media_center.utils import generate_thumbnail
from django.conf import settings


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = [
            'id',
            'type',
            'file',
            'thumbnail',
            'hls_playlist',
            'phash',
        ]
        read_only_fields = ['thumbnail', 'hls_playlist', 'phash']

    def validate(self, attrs):
        attrs = super().validate(attrs)

        media_type = attrs.get('type') or self.instance.type
        attrs['thumbnail'], attrs['phash'] = generate_thumbnail(attrs['file'], media_type)

        return attrs

    def create(self, validated_data):
        media = super().create(validated_data)
        if media.type == 'video' and media.file:
            media_url = media.file.url
            if media_url.startswith("/"):
                full_url = f"{settings.MEDIA_HOST_URL}{media_url}"
            else:
                full_url = media_url
            print('full_url: ', full_url)
            generate_hls_for_media.delay(full_url, media.id)
        return media
