#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import pandas as pd
import random
import matplotlib
import matplotlib.pyplot as plt

from components import *
from potok_satellite import *
from scheduler import scheduler_simple
from scheduler import scheduler_second

potokSAT = PotokSatellite("satellite.csv")

config_file = 'config.json'
with open(config_file, 'r') as f:
    config = json.load(f)
    time_start = config['time_start']
    time_finish = config['time_finish']
    time_step = config['time_step']                  # такт работы модели (секунды)
    win_length = config['win_length']                # величина скользящего окна для графика захваченных и пропущенных целей В СЕКУНДАХ

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

for time in range(time_start, time_finish, time_step):

    #########  получение от компонентов требуемого количества ресурса
    res_observ     = monitoring.get_resourse(time_step)             # обзор
    res_detect     =  detection.get_resourse(time_step)             # обнаружение
    res_tracker    =    tracker.get_resourse(time_step)             # сопровождение
    res_voko       =       voko.get_resourse(time_step, time)       # ВОКО
    res_pk         = 0.03 * time_step                               # помеховый канал
    res_fk         = 0.03 * time_step                               # функциональный контроль
    res_fault      = 0.05 * time_step                               # для красоты задаём потери ресурса

    # # # # # # # # # # #      Р А Б О Т А    П Л А Н И Р О В Щ И К А       # # # # # # # # # # # # # #
    # главное условие: R_observ + R_traker + R_voko = 100%

    # res_observ_out, res_detect_out, res_tracker_out, res_voko_out, res_pk_out, res_fk_out = scheduler_simple(time_step, res_observ, res_detect, res_tracker, res_voko, res_pk, res_fk, res_fault)

    res_observ_out, res_detect_out, res_tracker_out, res_voko_out, res_pk_out, res_fk_out = scheduler_second(time_step, res_observ, res_detect, res_tracker, res_voko, res_pk, res_fk, res_fault)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    # сколько ресурса было выделено на сопровождению, вернуть сколько объектов потеряно
    sumObjFault = tracker.let_resourse(res_tracker_out)
    # потеря обектов на сопровождении из-за нехватки ресурса
    tracker.remove_object(time)

    # сколько ресурса было веделено на подтверждение
    n_obj = detection.let_resourse(res_detect_out, time_step)
    # добавление объектов на сопровождение
    for i in range(n_obj):
        tracker.add_object(time)

    # количество обнаруженных при поиске
    n_obn = monitoring.let_resourse(res_observ_out, time_step, potokSAT.inBarrier(time))
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
# ax.legend(loc = 1)
plt.grid(True)
ax.legend(['количество объектов в секторе действия РЛС',
           'пропущенные объекты',
           'обнаруженных'], loc = 2)
plt.show()


# # # График по скользящему окну для кол-ва захваченных, вошедших в сектор и потерянных объектов

time_win = []
sumObjTracker_win   = []
sumObjDetect_win    = []
sumObjFault_win     = []
sumObjInBarrier_win = []
for i in range(int(time_finish / win_length / time_step)):

    ii_start = int(i * win_length / time_step)
    ii_stop = int((i+1) * win_length / time_step)

    time_win.append(i * win_length)
    sumObjTracker_win.append(sum(sumObjTracker_log[ii_start: ii_stop]))
    sumObjDetect_win.append(sum(sumObjDetect_log[ii_start: ii_stop]))
    sumObjFault_win.append(sum(sumObjFault_log[ii_start: ii_stop]))
    sumObjInBarrier_win.append(sum(sumObjInBarrier_log[ii_start: ii_stop]))

fig, ax = plt.subplots()
plt.step(time_win, sumObjInBarrier_win, color = 'blue', linewidth = 5, alpha = 0.5)
plt.step(time_win, sumObjTracker_win, color = 'green', linewidth = 5, alpha = 0.5)
plt.step(time_win, sumObjDetect_win, color = 'black', linewidth = 5, alpha = 0.5)
plt.step(time_win, sumObjFault_win, color = 'red', linewidth = 5, alpha = 0.5)
plt.xlabel(r'Время')
plt.ylabel(r'Количество объектов')
plt.title(r'Количество объектов')
plt.grid(True)
ax.legend()
plt.show()

