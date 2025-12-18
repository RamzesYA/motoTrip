from django.urls import path, re_path, include
from .views import *


urlpatterns = [
    path('', home, name='home'),
    path('register/', RegisterUser.as_view(), name='register'),
    path('login/', LoginUser.as_view(), name='login'),
    path('logout/', logout_user, name='logout'),
    path('trips/', TripCatalog.as_view(), name='tCatalog'),
    path('trips/<int:pk>', TripView.as_view(), name='trip'),
    path('profile/<slug:username>/', ProfileView.as_view(), name='profile'),
    path('moto/', MotoCatalog.as_view(), name='mCatalog'),
    path('moto/<int:pk>', MotoView.as_view(), name='moto'),
    path('news/', NewsListView.as_view(), name='nCat'),
    path('news/<int:pk>', NewsDetailView.as_view(), name='news'),
    path('calendar/', CalendarListView.as_view(), name='calendar'),
    path('statistics/', Statistics.as_view(), name='staistics'),
]
