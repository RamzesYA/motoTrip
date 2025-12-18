ymaps.ready(function () {
        var myMap = new ymaps.Map('map', {
            center: [55.751574, 37.573856],
            zoom: 9,
            controls: []
        });

        // Создание маршрута по трем точкам.
        // Вторая точка будет транзитной.
        var multiRoute = new ymaps.multiRouter.MultiRoute({
            referencePoints: [
                'Москва',
                'Суздаль',
                'Плёс',
                'Ярославль',
                'Москва'
            ],
            params: {
                // Установим вторую точку маршрута ('метро Смоленская')
                // в качестве транзитной.
                viaIndexes: [1]
            }
        }, {
            boundsAutoApply: true
        });

        // Добавление маршрута на карту.
        myMap.geoObjects.add(multiRoute);
    });