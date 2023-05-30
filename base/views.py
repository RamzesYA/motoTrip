import re
from datetime import date

from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.http import HttpResponseNotFound
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView
from django.core.mail import send_mail

from base.forms import *
from base.models import *


def pageNotFound(request, exception):
    return HttpResponseNotFound('<h1>Страница не найдена</h1>')


def home(request):
    trips = Trip.objects.all()[:3]
    motos = Moto.objects.all()[:3]
    context = {
        'trips': trips,
        'motos': motos,
    }
    return render(request, 'base/home.html', context=context)


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

    def get_type(self):
        return TripType.choices()


class TripRent:
    def get_motoNames(self):
        return Moto.objects.values("name")


class DateMixin:
    def get_now_day(self):
        return date.today()


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
        type = self.request.GET.get("t_type")
        trip = Trip.objects.all()

        if lvl:
            trip = trip.filter(lvl=lvl)

        if duration:
            trip = trip.filter(duration=duration)

        if type:
            trip = trip.filter(type=type)

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


class TripView(DataMixin, TripRent, DateMixin, DetailView):
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

        res = Reservation()
        res.tourId = Tour.objects.get(tripId=Trip.objects.get(pk=self.kwargs['pk']), dateId=date)
        res.userId = self.request.user
        if rent == 'on':
            res.isRentMoto = True
            res.price = Trip.objects.get(pk=self.kwargs['pk']).priceWMoto
            res.motoId = Moto.objects.get(name__icontains=moto)
            message = f'''Спасибо что выбрали нашу компанию.\n 
                            Вы успешно оставили заявку на тур {str(res.tourId.tripId.name).title()}\n
                            Дата выезда: {res.tourId.dateId.dateStart}, мотоцикл: {str(res.motoId).title()}, стоимость: {res.price} рублей.'''
        else:
            res.isRentMoto = False
            res.price = Trip.objects.get(pk=self.kwargs['pk']).priceWOMoto
            message = f'''Спасибо что выбрали нашу компанию.\n 
                            Вы успешно оставили заявку на тур {str(res.tourId.tripId.name).title()}\n
                            Дата выезда: {res.tourId.dateId.dateStart}, стоимость: {res.price} рублей.'''
        res.save()
        subject = f'{str(res.userId).title()}, заявка на тур {str(res.tourId.tripId.name).title()} успешно принята!'
        to_email = res.userId.email
        send_mail(subject=subject, message=message, from_email='roma.efremov.2002@gmail.com', recipient_list=[to_email])
        return redirect('/')


class MotoView(DetailView):
    model = Moto
    template_name = 'base/motoInfo.html'
    pk_url_kwarg = 'pk'
    context_object_name = 'moto'


class ProfileView(DetailView, DateMixin, DataMixin):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    template_name = 'base/profile.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Тур")
        context['prof'] = Profile.objects.get(user=context['object'])
        context['reservations'] = Reservation.objects.filter(userId=context['object'])
        return dict(list(context.items()) + list(c_def.items()))

    def post(self, request, username):
        mail = self.request.POST.get("mail")
        fName = self.request.POST.get("fName")
        sName = self.request.POST.get("sName")
        number = self.request.POST.get("number")

        u = User.objects.get(username=username)
        p = Profile.objects.get(user=u)

        if mail and mail != 'Введите почту' and mail != u.email:
            u.email = mail

        pattern = r'^[а-яА-ЯёЁ]+$'
        if re.fullmatch(pattern, fName) and fName != 'Введите имя' and fName != u.first_name:
            u.first_name = fName

        if re.fullmatch(pattern, sName) and sName != 'Введите фамилию' and sName != u.last_name:
            u.last_name = sName

        u.save()
        pattern = r'^((\+7|7|8)+([0-9]){10})$'
        if re.fullmatch(pattern, number) and number != 'Введите номер телефона' and number != p.phone:
            p.phone = number
            p.save()

        return redirect('profile', username)


class NewsListView(ListView):
    model = News
    template_name = 'base/nCat.html'


class NewsDetailView(DetailView):
    model = News
    template_name = 'base/news.html'
    pk_url_kwarg = 'pk'
    context_object_name = 'news'

    def post(self, request, pk):
        content = self.request.POST.get("content")

        news = News.objects.get(pk=pk)

        news.comments.create(author=Profile.objects.get(pk=request.user.pk),
                             content=content)
        news.save()

        return redirect(request.META.get('HTTP_REFERER'))
