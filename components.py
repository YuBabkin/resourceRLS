#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import random

from math import e
from math import factorial

from scipy.stats import poisson


class Monitoring:
    """ Модель обзора барьерной области.

    Требует необходимое кол-во ресурса на задачу посика,
    разыгрывает количество обнаружений в зависимости от
    объема выделенного на поиск временного ресурса.
    """

    def __init__(self, config_file):
        with open(config_file) as f:
            config = json.load(f)
            self.tau = config['Consts for observ']['tau']                   # длительность используемых заявок
            self.delta_t = config['Consts for observ']['delta_t']           # заданное время осмотра барьерной зоны
            self.n_dir = config['Consts for observ']['n_dir']               # количество направлений (количество заявок, необходимое реализовать за период осмотра)
            self.k_loss = config['Consts for detection']['k_loss']          # крат ложный обнаруженй
            self.mean_potok = config['Consts for detection']['mean_potok']  # средний поток наблюдаемых КО в час

    def get_resourse(self, dT):
        """ Возвращает количество требуемого ресурса
        """
        return (self.tau * self.n_dir / self.delta_t )

    def let_resourse(self, resourse, dT, potok):
        """ Сообщить компоненту сколько ему выделили ресурса.
            Разыгрывает количество обнаружений за такт работы модели.
            На выходе кол-во обнаруженных объектов.

            Сколько спутников должны обнаружить за такт работы модели?
             -- при трате запланированного объёма ресурса на поиск
             -- при среднем потоке КО через сектор
             -- на отрезок времени dT
            должны получить средний поток КО. Ввели "коэффициент потерь"
            который будет обратно уменьшать поток на тапе захвата.
            При --изменении теального потока;
                --изменении кол-ва выделенного ресурса;
            наигранный поток обнаруженных КО пропорционально изменяется.
        """
        potok_in_dT = self.k_loss * resourse / self.get_resourse(dT)  *  potok / self.mean_potok  *  dT/(60*60)

        P_1 = poisson.pmf(k=1, mu=potok_in_dT)
        P_2 = poisson.pmf(k=2, mu=potok_in_dT)
        P_3 = poisson.pmf(k=3, mu=potok_in_dT)
        rand = random.random()
        if  (P_3 > rand):
            return 3
        elif (P_3+P_2 > rand):
            return 2
        elif (P_3+P_2+P_1 > rand):
            return 1
        else:
            return 0


class Detection:
    """ Подтверждение обнаруженных объектов на этапе поиска.

    Если обнаруженный объект подтвердился -- необходимо
    добавить новый объкт на сопровождение.
    """

    def __init__(self, config_file):
        self.counts_obj = 0
        self.resourse = 0

        with open(config_file) as f:
            config = json.load(f)
            self.tau = config['Consts for detection']['tau']
            self.k_loss = config['Consts for detection']['k_loss']

    def set_count_detection(self, count):
        """ установить сколько подтверждений необходимо произвести
           (по итогам работы поиска)
        """
        self.counts_obj = count

    def get_resourse(self, dT):
        """
        Требуемое количетво ресурса на подтверждение
        """
        self.resourse = self.counts_obj * self.tau / dT
        return self.resourse

    def let_resourse(self, resourse, dT):
        """ Сообщить компоненту сколько ему выделили ресурса.
        В зависимости от количество ресурса разыграть
        количество подтверждённых объектов. Если ресурса недостаточно,
        подтверждение объекта не происходит.
        """
        #TODO а как отследить сколько ресурса компоненту недодали?
        #TODO надо логировать количество недоподтверждённых объектов
        if resourse > self.resourse:
            resourse = self.resourse

        count_obj = 0
        for i in range(int(resourse // self.tau / dT)):
            if random.uniform(0.0, self.k_loss) < 1:
                count_obj += 1
        return count_obj


class Tracker:
    """ Модель компонента "сопровождение".

    Массив сопровождаемых объектов. Для сопровождения каждого объекта определены:
    -- длительность сопровождения;
    -- период сопровождения;
    -- дальность до объекта и используемый сигнал;
    -- TODO можно разыграть ещё радиальную скорость объекта.
    """
    def __init__(self, config_file):
        with open(config_file) as f:
            self.config = json.load(f)

        self.delta_t = self.config['Consts for Tracker']['delta t']
        self.p_sopr = self.config['Consts for Tracker']['p_sopr']
        self.tau1 = self.config['Consts for Tracker']['tau1']
        self.tau2 = self.config['Consts for Tracker']['tau2']

        self.lastNumberObject = 0

        self.trackingObjects = []

    def get_resourse(self, dT):
        """ Возвращает требуемый ресурс.
        """
        self.sum_resourse = 0
        for obj in self.trackingObjects:
            self.sum_resourse += obj.resourse(dT)
        return self.sum_resourse

    def let_resourse(self, resourse):
        """ Сообщить компоненту сколько ему выделили ресурса.
        Если выделенного ресурса недостаточно, сбросить объекты
        (аварийно прекратить сопровождение объектов).
        При сбросе объекта, по условию (длительность сопровождения)
        принимаем цель как отработанную, либо считаем как пропуск.
        """

        delta = abs(self.sum_resourse - resourse)

        if delta > self.sum_resourse * 0.1:
            self.trackingObjects.pop(random.randint(0, len(self.trackingObjects)))
            return 1
        return 0

    def add_object(self, time):
        """ Добавить новый объект
        """
        self.lastNumberObject += 1
        trObject = TrackingObject(time,
                                self.lastNumberObject,
                                self.p_sopr,
                                random.uniform(self.tau1, self.tau2),
                                self.delta_t)
        self.trackingObjects.append(trObject)

    def remove_object(self, time):
        """ Проверка не пора ли удалить объект по условию времени сопровождения
        """
        for index, obj in enumerate(self.trackingObjects):
            if obj.is_expired(time):
                self.trackingObjects.pop(index)
                return 1
        return 0

    def get_sum_sat(self):
        """ Возвращает количество объектов на сопровождении в данный момент
        """
        return (len(self.trackingObjects))


class TrackingObject:
    """ Сопровождаемый объект. Для каждого объекта определены:
        start_time -- начало сопровождения объекта
        number -- порядковый номер объекта
        p_sopr -- период сопровождения
        tau -- длительность заявки, используемоф для этого объекта
        delta_t -- период сопровождения
    """

    def __init__(self, time, number, p_sopr, tau, delta_t):
        self.startTime = time
        self.number = number
        self.p_sopr = p_sopr
        self.tau = tau
        self.delta_t = delta_t


    def resourse(self, dT):
        """ Ресурс требуемый для данного объекта (в долях от всего ресурса)
        """
        return (self.tau / self.delta_t)


    def is_expired(self, currentTime):
        """ Проверяет, не пора ли сбросить объект?
        """
        return  (self.startTime + self.p_sopr < currentTime)


class Voko:
    """ Модель работы компонента работы по ВОКО. Для ВОКО определены:
        startTime -- начало работы по ВОКО
        stopTime -- конец работы по ВОКО
        delta_t -- период выставления заявки по ВОКО
        tau -- длительность заявки
    """

    def __init__(self, config_file):
        with open(config_file) as f:
            config = json.load(f)
            self.startTime = config['Consts for VOKO']['startTime']
            self.stopTime = config['Consts for VOKO']['stopTime']
            self.delta_t = config['Consts for VOKO']['delta_t']
            self.tau = config['Consts for VOKO']['tau']


    def get_resourse(self, dT, currentTime):
        """ Возвращает долю требуемого ресурса.
        Либо работа по ВОКО идёт, либо не идёт.
        Всего за весь прогон 1 сеанс работы по ВОКО
        """
        if (self.startTime < currentTime and currentTime < self.stopTime):
            return  (self.tau / self.delta_t)
        else:
            return 0
