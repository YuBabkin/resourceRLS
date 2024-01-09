#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import pandas as pd
import random
import matplotlib
import matplotlib.pyplot as plt

from components import *
from potok_satellite import *

deltaTime = 1                   # такт работы модели (секунды)

config_file = 'config.json'

potokSAT = PotokSatellite("satellite.csv")


monitoring = Monitoring(config_file)
detection = Detection(config_file)
tracker = Tracker(config_file)
voko = Voko(config_file)

time_log = []
res_observ_log = []
res_detect_log = []
res_tracker_log = []
res_voko_log = []
res_pk_log = []
res_fk_log = []
sumObjTracker_log = []              # количество объектов на сопровождении
sumObjDetect_log = []               # количество взятых на сопровождение объектов (кол-во в такт)
sumObjFault_log = []                # количество потерянных объектов
sumObjInBarrier_log = []            # количество объектов в барьере

for time in range(0, 3600, deltaTime):

    #########  получение от компонентов требуемого количества ресурса
    res_observ     = monitoring.get_resourse(deltaTime)             # обзор
    res_detect     =  detection.get_resourse(deltaTime)             # обнаружение
    res_tracker    =    tracker.get_resourse(deltaTime)             # сопровождение
    res_voko       =       voko.get_resourse(deltaTime, time)       # ВОКО
    res_pk = 0.03                                                   # помеховый канал
    res_fk = 0.03                                                   # функциональный контроль
    res_fault = 0.05                                                # для красоты задаём потери ресурса

    # # # # # # # # # # #      Р А Б О Т А    П Л А Н И Р О В Щ И К А       # # # # # # # # # # # # # #
    # главное условие: R_observ + R_traker + R_voko = 100%

    # временной ресурс на поиск рассчитывается как остаток ресурса после выполнения остальных задач
    res_observ_out = deltaTime \
                    - res_tracker \
                    - res_voko \
                    - res_pk * deltaTime \
                    - res_fk * deltaTime \
                    - res_fault * deltaTime
    if  (res_observ_out < 0):
        res_observ_out = 0

    # TODO на обнаружение и сопровождения ресурса тоже может не хватить. Доработать.
    res_detect_out = res_detect
    res_tracker_out = res_tracker
    res_voko_out = res_voko
    res_pk_out = res_pk
    res_fk_out = res_fk

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    # сколько ресурса было выделено на сопровождению, вернуть сколько объектов потеряно
    sumObjFault = tracker.let_resourse(res_tracker_out)
    # потеря обектов на сопровождении из-за нехватки ресурса
    tracker.remove_object(time)

    # сколько ресурса было веделено на подтверждение
    n_obj = detection.let_resourse(res_detect_out, deltaTime)
    # добавление объектов на сопровождение
    for i in range(n_obj):
        tracker.add_object(time)

    # количество обнаруженных при поиске
    n_obn = monitoring.let_resourse(res_observ_out, deltaTime, potokSAT.inBarrier(time))
    # сколько объектов требуется подтверлить (на след.такте работы модели)
    detection.set_count_detection(n_obn)

    #########  логирование + случайности для красоты графиков
    res_observ_log.append(res_observ_out)
    res_detect_log.append(res_detect_out)
    res_tracker_log.append(res_tracker_out)
    res_voko_log.append(res_voko_out)
    res_pk_log.append(res_pk + random.uniform(-0.005, 0.005))
    res_fk_log.append(res_fk + random.uniform(-0.002, 0.002))
    time_log.append(time/60)

    sumObjTracker_log.append(tracker.get_sum_sat())
    sumObjDetect_log.append(n_obj)
    sumObjFault_log.append(sumObjFault)
    sumObjInBarrier_log.append(potokSAT.inBarrier(time))


df = pd.DataFrame({'time':  time_log,
                   'resourseObserv': res_observ_log,
                   'resourseDetect': res_detect_log,
                   'resourseTracker': res_tracker_log,
                   'resourseVoko': res_voko_log,
                   'sumObjInBarrier': sumObjInBarrier_log,
                   'sumObjDetect': sumObjDetect_log,
                   'sumObjTracker':  sumObjTracker_log,
                   'sumObjFault': sumObjFault_log
                   })
df.to_csv('result.csv', sep = ';')


fig, ax = plt.subplots()
my_colors = []
my_colors.append('green')
my_colors.append('darkgreen')
my_colors.append('red')
my_colors.append('blue')
my_colors.append('orange')
my_colors.append('gray')
ax.stackplot(time_log,
             [res_pk_log] + [res_fk_log] + [res_detect_log] +
             [res_tracker_log] + [res_voko_log] + [res_observ_log],
             colors = ['green', 'darkgreen', 'red',
                       'blue', 'orange', 'gray'], alpha=1.0)
plt.xlabel(r'Время (минуты)')
plt.title('Распределение ресурса между решаемыми задачами РЛС')
plt.grid(True)
plt.show()


'''
TODO добавить данные о количестве:
-- обнаруженных объектов  (за период)
-- сопровождаемых в данный момент
-- потерянных объектов  (за период)
-- объектов в барьере
-- объектов в секторе (НЕ НАДО)
-- входящих в сектор  (за период)
'''
fig, ax = plt.subplots()
ax.plot(time_log, sumObjInBarrier_log, color = 'black')
ax.plot(time_log, sumObjFault_log, 'r*', alpha = 0.1)
plt.stackplot(time_log, sumObjDetect_log, color = 'green')
plt.stackplot(time_log, sumObjTracker_log, color = 'blue')
plt.xlabel(r'Время')
plt.ylabel(r'Количество ИСЗ')
plt.title('Оценка количества ИСЗ в секторе, оценка количества обнаруженных и пропущенных объектов')
ax.legend(loc = 1)
plt.grid(True)
ax.legend(['количество объектов в секторе действия РЛС',
           'пропущенные объекты',
           'обнаруженных'], loc = 2)
plt.show()
