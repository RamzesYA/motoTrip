from enum import Enum


class LaunchType(Enum):

    KICKSTARTER = "Кикстартер"
    ELECTRIC = "Электрический"

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)


class LvlType(Enum):

    EASY = "Начальный"
    MEDIUM = "Средний"
    DIFFICULT = "Сложный"

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)


class TripType(Enum):

    WEEKEND = "Маршруты выходного дня"
    LONG = "Многодневные маршруты"

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)