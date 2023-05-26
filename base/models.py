from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from phonenumber_field.modelfields import PhoneNumberField

from base.enums import *


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = PhoneNumberField(verbose_name='Номер телефона', blank=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


@receiver(post_save, sender=User)
def addNewProfile(sender, instance, created, **kwargs):
    if created:
        profile = Profile()
        profile.user = instance
        profile.save()


class Moto(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название')
    weight = models.IntegerField(verbose_name='Вес')
    launch = models.CharField(max_length=255, choices=LaunchType.choices(), verbose_name='Тип запуска')
    seatHeight = models.FloatField(verbose_name='Высота сиденья')
    tankCapacity = models.FloatField(verbose_name='Емкость топливного бака')
    engineCapacity = models.IntegerField(verbose_name='Объем двигателя')
    enginePower = models.FloatField(verbose_name='Мощность двигателя')
    image = models.ImageField(upload_to='images/moto', blank=True)
    description = models.TextField(verbose_name='Описание', default=None, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Мотоцикл'
        verbose_name_plural = 'Мотоциклы'
        ordering = ['name']


class Trip(models.Model):
    name = models.CharField(max_length=150, verbose_name='Название')
    description = models.TextField(verbose_name='Описание', default=None)
    date = models.ManyToManyField('Dates', verbose_name='Даты', default=None, blank=True)
    duration = models.IntegerField(verbose_name='Длительность', default=None)
    length = models.IntegerField(verbose_name='Протяженность маршрута', default=None)
    lvl = models.CharField(max_length=255, choices=LvlType.choices(), verbose_name='Уровень сложности', default=None)
    priceWOMoto = models.IntegerField(verbose_name='Цена на воем мотоцикле', default=None)
    priceWMoto = models.IntegerField(verbose_name='Цена с арендтой мотоцикла', default=None)
    type = models.CharField(max_length=255, choices=TripType.choices(), verbose_name='Тип путешествия', default=None)
    image = models.ImageField(upload_to='images/trip', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Путешествие'
        verbose_name_plural = 'Путешествия'


class Dates(models.Model):
    dateStart = models.DateField(verbose_name='Начало')
    dateFinish = models.DateField(verbose_name='Конец')

    def __str__(self):
        return f'{str(self.dateStart.strftime("%d.%m.%Y"))} - {str(self.dateFinish.strftime("%d.%m.%Y"))}'

    class Meta:
        verbose_name = 'Дата'
        verbose_name_plural = 'Даты'


class Tour(models.Model):
    tripId = models.ForeignKey(Trip, on_delete=models.CASCADE, verbose_name="Путешествие")
    dateId = models.ForeignKey(Dates, on_delete=models.CASCADE, verbose_name="Дата тура")
    available = models.IntegerField(verbose_name='Вего мест')
    booked = models.IntegerField(verbose_name='Занято мест', default=0)

    def __str__(self):
        return str(self.tripId)

    class Meta:
        verbose_name = 'Тур'
        verbose_name_plural = 'Туры'


@receiver(post_save, sender=Tour)
def addNewDate(sender, instance, created, **kwargs):
    if created:
        tour = instance.dateId
        trip = Trip.objects.get(pk=instance.tripId.pk)
        trip.date.add(tour)
        trip.save()


class Reservation(models.Model):
    tourId = models.ForeignKey(Tour, on_delete=models.CASCADE, verbose_name="Тур")
    userId = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    price = models.IntegerField(verbose_name='Цена', blank=True)
    isRentMoto = models.BooleanField(verbose_name='Аренда', default=True)
    motoId = models.ForeignKey(Moto, on_delete=models.CASCADE, verbose_name="Мотоцикл", blank=True, null=True)
    time = models.DateTimeField(auto_now_add=True, verbose_name="Время бронирования")
    moreInfo = models.TextField(verbose_name='Дополнительная информация', blank=True)

    def __str__(self):
        return str(self.tourId)

    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'


@receiver(post_save, sender=Reservation)
def addOneBooking(sender, instance, created, **kwargs):
    if created:
        tour = Tour.objects.get(pk=instance.tourId.pk)
        tour.booked += 1
        tour.save()


class Comments(models.Model):
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name="Автор")
    content = models.TextField(verbose_name='Информация', default=None, max_length=200)
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return self.content

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'


class News(models.Model):
    title = models.CharField(max_length=150, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Информация', default=None)
    image = models.ImageField(upload_to='images/news', blank=True)
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    comments = models.ManyToManyField(Comments, verbose_name="Коментарий", blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
