import os
import re
import random
from datetime import date, timedelta

from sklearn.cluster import KMeans
from django.contrib.staticfiles import finders

from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.http import HttpResponseNotFound, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView
from django.core.mail import send_mail
from django.db.models.functions import TruncMonth
from django.db.models import Sum
from django.db.models import Count
from django.views.generic import View

from base.forms import *
from base.models import *
from motoTrip import settings


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


class TripCatalog(ListView, DataMixin, TripFilter):
    model = Trip
    template_name = 'base/tripCat.html'

    # Получаем выборку для конкретного пользователя
    def getSelfDataSet(self, UserId):
        dataSet = []
        trips = []

        res = Reservation.objects.filter(userId=UserId)
        tur = [i.tourId for i in res]

        for i in tur:
            if i.tripId not in trips:
                trips.append(i.tripId)

        for trip in trips:
            dataSet.append([trip.pk, trip.duration, trip.length, getLvl(trip), getType(trip), trip.priceWMoto])

        # print(dataSet)
        return dataSet

    # Получаем рекомендации для конкретного тура
    def getTripRec(self, model, UserId):

        dataSet = self.getSelfDataSet(UserId)
        excludeIds = []

        for i in dataSet:
            excludeIds.append(i[0])

        excludeIds = set(excludeIds)

        all_predictions = model.predict(dataSet)
        allRec = getAllRec(model)
        allDataSet = getAllDataSet()
        tripIds = []

        for i in range(len(allRec)):
            if str(all_predictions[0]) == str(allRec[i]) and allDataSet[i][0] not in excludeIds:
                tripIds.append(allDataSet[i][0])

        return random.sample(tripIds, 3)

    def is_test(self, UserId):
        if Reservation.objects.filter(userId=UserId).count() == 0:
            return True
        else:
            return False

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

    def post(self, request, *args, **kwargs):
        q1 = self.request.POST.get("q1")
        q2 = self.request.POST.get("q2")
        q3 = self.request.POST.get("q3")

        dataSet = [[0, 2 if q1 == '2' else 8 if q1 == '8' else 15, 500 if q1 == '0' else 1200 if q1 == '1' else 2000,
                    0 if q1 == '0' else 1 if q1 == '1' else 2, 0 if q2 == '0' else 1,
                    100000 if q1 == '0' else 150000 if q1 == '1' else 200000]]

        all_predictions = getModel().predict(dataSet)
        allRec = getAllRec(getModel())
        allDataSet = getAllDataSet()
        tripIds = []

        for i in range(len(allRec)):
            if str(all_predictions[0]) == str(allRec[i]):
                tripIds.append(allDataSet[i][0])

        self.object_list = self.get_queryset()
        context = self.get_context_data()
        context['recTripsT'] = Trip.objects.filter(pk__in=random.sample(tripIds, 3))

        return render(request, self.template_name, context=context)


    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Туры")
        if self.request.user.is_authenticated:
            context['isTest'] = self.is_test(self.request.user.id)
            if not self.is_test(self.request.user.id):
                context['recTrips'] = Trip.objects.filter(pk__in=self.getTripRec(getModel(), self.request.user.id))

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

    # Получаем выборку по туру
    def getTripDataSet(self):
        trip = Trip.objects.get(pk=self.kwargs['pk'])
        dataSet = [[trip.pk, trip.duration, trip.length, getLvl(trip), getType(trip), trip.priceWMoto]]
        return dataSet

    # Получаем рекомендации для конкретного тура
    def getTripRec(self, model):
        dataSet = self.getTripDataSet()
        all_predictions = model.predict(dataSet)
        allRec = getAllRec(model)
        allDataSet = getAllDataSet()
        tripIds = []

        for i in range(len(allRec)):
            if str(all_predictions[0]) == str(allRec[i]) and allDataSet[i][0] != self.kwargs['pk']:
                tripIds.append(allDataSet[i][0])

        return random.sample(tripIds, 3)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Тур")
        context['tour'] = Tour.objects.filter(tripId=Trip.objects.get(pk=self.kwargs['pk']))
        context['recTrips'] = Trip.objects.filter(pk__in=self.getTripRec(getModel()))

        if ToursStats.objects.filter(tripId=Trip.objects.get(pk=self.kwargs['pk']), date=date.today()).exists():
            stat = ToursStats.objects.get(tripId=self.kwargs['pk'], date=date.today())
            stat.count += 1
            stat.save()
        else:
            stat = ToursStats()
            stat.tripId = Trip.objects.get(pk=self.kwargs['pk'])
            stat.date = date.today()
            stat.count = 1
            stat.save()

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


class MotoView(DataMixin, TripRent, DateMixin, DetailView):
    model = Moto
    template_name = 'base/motoInfo.html'
    pk_url_kwarg = 'pk'
    context_object_name = 'moto'

    def get_context_data(self, *, object_list=None, **kwargs):
        n_date = date.today()
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Мото")
        context['n_date1'] = n_date + timedelta(1)
        context['n_date90'] = date.today() + timedelta(90)
        return dict(list(context.items()) + list(c_def.items()))

    def post(self, request, pk):
        days = self.request.POST.get("days")
        day = self.request.POST.get("day")

        res = MotoReservation()
        res.motoId = Moto.objects.get(pk=self.kwargs['pk'])
        res.userId = self.request.user
        res.days = days
        res.day = day

        message = f'''Спасибо что выбрали нашу компанию.\n 
                        Вы успешно оставили заявку на бронирование мотоцикла {str(Moto.objects.get(pk=self.kwargs['pk']).name).title()}\n
                        Кол-во дней: {days}, стоимость: {int(days)*int(Moto.objects.get(pk=self.kwargs['pk']).rentPrice)} рублей.'''
        res.save()
        subject = f"{str(res.userId).title()}, заявка на бронирование мотоцикла {str(Moto.objects.get(pk=self.kwargs['pk']).name).title()} успешно принята!"
        to_email = res.userId.email
        send_mail(subject=subject, message=message, from_email='roma.efremov.2002@gmail.com', recipient_list=[to_email])
        return redirect('/')


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


class CalendarListView(ListView, DateMixin, DataMixin):
    model = Tour
    template_name = 'base/calendar.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Календарь")
        tmp = Dates.objects.annotate(month_year=TruncMonth('dateStart')).values('month_year').distinct().filter(dateStart__gte=date.today()).order_by('month_year')
        monthes = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        mnths = {}

        for i in tmp:
            mnths[f"{monthes[i['month_year'].month - 1]} {i['month_year'].year}"] = Tour.objects.filter(
                dateId__dateStart__gte=i['month_year'],
                dateId__dateStart__lt=i['month_year'] + timedelta(days=30)
            )

        # print(mnths)
        context['mnths'] = mnths

        return dict(list(context.items()) + list(c_def.items()))

def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources
    """
    result = finders.find(uri)
    if result:
        if not isinstance(result, (list, tuple)):
            result = [result]
        result = list(os.path.realpath(path) for path in result)
        path = result[0]
    else:
        sUrl = settings.STATIC_URL  # Typically /static/
        sRoot = settings.STATIC_ROOT  # Typically /home/userX/project_static/
        mUrl = settings.MEDIA_URL  # Typically /media/
        mRoot = settings.MEDIA_ROOT  # Typically /home/userX/project_static/media/

        if uri.startswith(mUrl):
            path = os.path.join(mRoot, uri.replace(mUrl, ""))
        elif uri.startswith(sUrl):
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else:
            return uri

    # make sure that file exists
    if not os.path.isfile(path):
        raise RuntimeError(
            'media URI must start with %s or %s' % (sUrl, mUrl)
        )
    return path


class Statistics(View, DataMixin):
    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            today = date.today()
            context = {}

            context['all_trip_sum_booked'] = Tour.objects.all().aggregate(Sum('booked'))
            context['all_trip_sum_available'] = Tour.objects.all().aggregate(Sum('available'))
            context['all_trip_sums_byName'] = Tour.objects.values('tripId__name').annotate(total_b=Sum('booked'), total_a=Sum('available')).order_by('tripId__name')
            context['trip_sums_byName_byMonth'] = Reservation.objects.values('tourId__tripId__name').filter(time__year=today.year, time__month=today.month).order_by('tourId__tripId__name').annotate(Count('id'))
            context['trip_sums_byName_byYear'] = Reservation.objects.values('tourId__tripId__name').filter(time__year=today.year).order_by('tourId__tripId__name').annotate(Count('id'))

            # 2
            context['click_sums_byName_byDay'] = ToursStats.objects.values('tripId__name', 'count').filter(date__year=today.year, date__month=today.month, date__day=today.day).order_by('tripId__name')
            context['click_sums_byName_byMonth'] = ToursStats.objects.filter(date__year=today.year, date__month=today.month).values('tripId__name').annotate(total_count=Sum('count')).order_by('tripId__name')
            context['click_sums_byName_byYear'] = ToursStats.objects.filter(date__year=today.year).values('tripId__name').annotate(total_count=Sum('count')).order_by('tripId__name')

            # 3
            context['all_moto_sums_byName'] = MotoReservation.objects.filter(isPaid=True).values('motoId__name').annotate(total_count=Count('id')).order_by('motoId__name')
            context['moto_sums_byName_byMonth'] = MotoReservation.objects.filter(day__year=today.year, day__month=today.month, isPaid=True).values('motoId__name').annotate(total_count=Count('id')).order_by('motoId__name')
            context['moto_sums_byName_byYear'] = MotoReservation.objects.filter(day__year=today.year, isPaid=True).values('motoId__name').annotate(total_count=Count('id')).order_by('motoId__name')

            # 4
            context['all_moto_sums_byName_0'] = MotoReservation.objects.values('motoId__name').annotate(total_count=Count('id')).order_by('motoId__name')
            context['moto_sums_byName_byMonth_0'] = MotoReservation.objects.filter(day__year=today.year, day__month=today.month).values('motoId__name').annotate(total_count=Count('id')).order_by('motoId__name')
            context['moto_sums_byName_byYear_0'] = MotoReservation.objects.filter(day__year=today.year).values('motoId__name').annotate(total_count=Count('id')).order_by('motoId__name')


            return render(request, 'base/statistics.html', context=context)
        else:
            return HttpResponseNotFound('<h1>Страница не найдена</h1>')


def methodLoktya(x):
    import matplotlib.pyplot as plt
    wcss = []
    for i in range(1, 5):
        kmeans = KMeans(n_clusters=i, init='k-means++')
        kmeans.fit(x)
        wcss.append(kmeans.inertia_)

    plt.plot(range(1, 5), wcss)
    plt.title('Метод локтя')
    plt.xlabel('Количество кластеров')
    plt.ylabel('SSE')
    plt.show()


def getType(m):
    if m.type == "Маршруты выходного дня":
        return int(0)
    else:
        return int(1)


def getLvl(m):
    if m.lvl == "Начальный":
        return int(0)
    elif m.lvl == "Средний":
        return int(1)
    else:
        return int(2)


# Получаем выборку по всем турам
def getAllDataSet():
    dataSet = list()
    trips = Trip.objects.all()

    for trip in trips:
        dataSet.append([trip.pk, trip.duration, trip.length, getLvl(trip), getType(trip), trip.priceWMoto])

    return dataSet


def getModel():
    model = KMeans(n_clusters=2)
    model.fit(getAllDataSet())

    return model


def getAllRec(model):
    # methodLoktya(getAllDataSet())
    all_predictions = model.predict(getAllDataSet())
    # print(all_predictions)
    return all_predictions