from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.http import HttpResponseNotFound, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView

from base.forms import *
from base.models import *


def pageNotFound(request, exception):
    return HttpResponseNotFound('<h1>Страница не найдена</h1>')


def home(request):
    return render(request, 'base/base.html')


menu = [{'title': "О сайте", 'url_name': 'about'},
        {'title': "Добавить статью", 'url_name': 'add_page'},
        {'title': "Обратная связь", 'url_name': 'contact'},
        {'title': "Войти", 'url_name': 'login'}]


class MotoFilter:
    def get_copacity(self):
        return Moto.objects.values("engineCapacity").order_by('engineCapacity')

    def get_name(self):
        full_names = Moto.objects.values("name")
        return set([element['name'].split()[0].capitalize() for element in full_names])


class TripFilter:
    def get_lvl(self):
        return LvlType.choices()

    def get_duration(self):
        durations = Trip.objects.values("duration")
        return set([duration['duration'] for duration in durations])


class TripRent:
    def get_motoNames(self):
        return Moto.objects.values("name")


class DataMixin:
    def get_user_context(self, **kwargs):
        context = kwargs
        context['menu'] = menu
        return context


def logout_user(request):
    logout(request)
    return redirect('login')


class RegisterUser(DataMixin, CreateView):
    form_class = RegisterUserForm
    template_name = 'base/register.html'
    success_url = reverse_lazy('login')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title='Регистрация')
        return dict(list(context.items()) + list(c_def.items()))


class LoginUser(DataMixin, LoginView):
    form_class = LoginUserForm
    template_name = 'base/login.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Авторизация")
        return dict(list(context.items()) + list(c_def.items()))


class TripCatalog(DataMixin, TripFilter, ListView):
    model = Trip
    template_name = 'base/tripCat.html'

    def get_queryset(self):
        lvl = self.request.GET.get("t_lvl")
        duration = self.request.GET.get("t_duration")
        trip = Trip.objects.all()

        if lvl:
            trip = trip.filter(lvl=lvl)

        if duration:
            trip = trip.filter(duration=duration)

        return trip

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Туры")
        return dict(list(context.items()) + list(c_def.items()))


class MotoCatalog(MotoFilter, ListView):
    model = Moto
    template_name = 'base/motoCat.html'

    def get_queryset(self):
        name = self.request.GET.get("mName")
        capacity = self.request.GET.get("capacity")
        min_weight = self.request.GET.get("min_weight")
        max_weight = self.request.GET.get("max_weight")
        moto = Moto.objects.all()

        if name:
            moto = moto.filter(name__icontains=name)

        if capacity:
            moto = moto.filter(engineCapacity=capacity)

        if min_weight and max_weight:
            moto = moto.filter(weight__range=(min_weight, max_weight))

        return moto


class TripView(DataMixin, TripRent, DetailView):
    model = Trip
    template_name = 'base/tripInfo.html'
    pk_url_kwarg = 'pk'
    context_object_name = 'trip'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Тур")
        context['tour'] = Tour.objects.filter(tripId=Trip.objects.get(pk=self.kwargs['pk']))
        return dict(list(context.items()) + list(c_def.items()))

    def post(self, request, pk):
        date = self.request.POST.get("dateId")
        rent = self.request.POST.get("isrent")
        moto = self.request.POST.get("mName")
        print(moto)

        res = Reservation()
        res.tourId = Tour.objects.get(tripId=Trip.objects.get(pk=self.kwargs['pk']), dateId=date)
        res.userId = self.request.user
        if rent == 'on':
            res.isRentMoto = True
            res.price = Trip.objects.get(pk=self.kwargs['pk']).priceWMoto
            res.motoId = Moto.objects.get(name__icontains=moto)
        else:
            res.isRentMoto = False
            res.price = Trip.objects.get(pk=self.kwargs['pk']).priceWOMoto
        res.save()
        return redirect('/')


class BookView(CreateView):
    form_class = AddBookForm
    template_name = 'base/book.html'


class MotoView(DetailView):
    model = Moto
    template_name = 'base/motoInfo.html'
    pk_url_kwarg = 'pk'
    context_object_name = 'moto'
