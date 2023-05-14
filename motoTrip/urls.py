from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from base.views import *
from motoTrip import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('base.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = pageNotFound
