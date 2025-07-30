from django.db import models
from django.utils.translation import gettext_lazy as _


class Media(models.Model):
    class Type(models.TextChoices):
        PHOTO = 'photo', _('Photo')
        VIDEO = 'video', _('Video')

    type = models.CharField(verbose_name=_('type'), max_length=10, choices=Type.choices)
    file = models.FileField(verbose_name=_('file'), upload_to='media_center/')
    thumbnail = models.ImageField(
        verbose_name=_('thumbnail'),
        upload_to='media_center/',
        blank=True,
        null=True,
        help_text=_('Optional. A thumbnail image for the media.')
    )
    hls_playlist = models.URLField(
        verbose_name=_('HLS Playlist'),
        max_length=2048,
        blank=True,
        null=True,
        help_text=_('Path to the HLS playlist (.m3u8) file.')
    )
    phash = models.CharField(verbose_name=_('Perceptual Hash'), max_length=64, null=True, blank=True)

    class Meta:
        verbose_name = _('media')
        verbose_name_plural = _('media')
        indexes = [
            models.Index(fields=['phash']),
            models.Index(fields=['type'])
        ]
