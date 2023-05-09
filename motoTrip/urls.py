from django.contrib import admin
from django.urls import path, include
from base.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('base.urls')),
]

handler404 = pageNotFound
