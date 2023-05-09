from django.urls import path, re_path, include
from .views import *


urlpatterns = [
    path('', home, name='home'),
    path('register/', RegisterUser.as_view(), name='register'),
    path('login/', LoginUser.as_view(), name='login'),
    path('logout/', logout_user, name='logout'),
    path('trips/', TripCatalog.as_view(), name='tCatalog'),
    path('trips/<int:pk>', TripView.as_view(), name='trip'),
    path('booking/', BookView.as_view(), name='book'),
    path('moto/', MotoCatalog.as_view(), name='mCatalog'),
    path('moto/<int:pk>', MotoView.as_view(), name='moto'),
]
