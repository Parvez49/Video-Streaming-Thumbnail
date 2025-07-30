from rest_framework.routers import DefaultRouter

from .views import MediaViewSet

app_name = 'v1'

router = DefaultRouter()
router.register(r'media', MediaViewSet, basename='media')

urlpatterns = router.urls
