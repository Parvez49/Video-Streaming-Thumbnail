from django.urls import include, path

app_name = 'media_center'

urlpatterns = [
    path('v1/', include('media_center.api.v1.urls')),
]
