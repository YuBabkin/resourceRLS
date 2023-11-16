#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import pandas as pd
import random
import matplotlib
import matplotlib.pyplot as plt

from components import *
from potok_sattelite import *

deltaTime = 1                   # такт работы модели (секунды)

monitoring = Monitoring()
detection = Detection()
tracker = Tracker()
voko = Voko()

time_log = []
res_observ_log = []
res_detect_log = []
res_tracker_log = []
res_voko_log = []
res_pk_log = []
res_fk_log = []
sumObjTracker_log = []               # количество объектов на сопровождении
sumObjDetect_log = []               # количество обнаруженных объектов (кол-во в такт)
sumObjFault_log = []                # количество потерянных объектов

potokSAT = PotokSatellite("satellite_mask.csv")

for time in range(0, 3600, deltaTime):

    #########  получение от компонентов требуемое количество ресурса
    res_observ     = monitoring.get_resourse(deltaTime)
    res_detect     =  detection.get_resourse(deltaTime)
    res_tracker    =    tracker.get_resourse(deltaTime)
    res_voko       =       voko.get_resourse(deltaTime, time)
    res_pk = 0.03                                                   # помеховый канал
    res_fk = 0.03                                                   # функциональный контроль
    res_fault = 0.05                                                # для красоты задаём потери ресурса

    # # # # # # # # # # #      Р А Б О Т А    П Л А Н И Р О В Щ И К А       # # # # # # # # # # # # # #
    # главное условие: R_observ + R_traker + R_voko = 100%

    # if  (resourseTracker > deltaTime - resourseVoko - resoursePk * deltaTime - resourseFault * deltaTime):
    #     rTrackerOut = deltaTime - resourseVoko - resoursePk * deltaTime - resourseFault * deltaTime
    # else:
    #     rTrackerOut = resourseTracker

    res_observ_out = deltaTime - res_tracker - res_voko - res_pk * deltaTime - res_fault * deltaTime
    if  (res_observ_out < 0):
        res_observ_out = 0
    res_detect_out = res_detect
    res_tracker_out = res_tracker
    res_voko_out = res_voko
    res_pk_out = res_pk
    res_fk_out = res_fk

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    tracker.let_resourse(res_tracker_out)
    tracker.remove_object(time)

    n_obj = detection.let_resourse(res_detect_out, deltaTime)
    for i in range(n_obj):
        tracker.add_object(time)

    n_obn = monitoring.let_resourse(res_observ_out, deltaTime, potokSAT.inSector(time))
    detection.set_count_detection(n_obn)

    #########  логирование + случайности для красоты выдаваемых графиков
    res_observ_log.append(res_observ_out)
    res_detect_log.append(res_detect_out)
    res_tracker_log.append(res_tracker_out)
    res_voko_log.append(res_voko_out)
    res_pk_log.append(res_pk + random.uniform(-0.005, 0.005))
    time_log.append(time/60)
    sumObjTracker_log.append(tracker.get_sum_sat())


df = pd.DataFrame({'time':  time_log,
                   'resourseObserv': res_observ_log,
                   'resourseDetect': res_detect_log,
                   'resourseTracker': res_tracker_log,
                   'resourseVoko': res_voko_log,
                   'sumObjTracker':  sumObjTracker_log})
df.to_csv('result.csv', sep = ';')



fig, ax = plt.subplots()
my_colors = []
my_colors.append('green')
my_colors.append('blue')
my_colors.append('red')
my_colors.append('gray')
ax.stackplot(time_log,
             [res_pk_log] + [res_tracker_log] + [res_voko_log] + [res_observ_log],
             colors=my_colors, alpha=0.7)
plt.xlabel(r'Время')
plt.title('Распределение ресурса между решаемыми задачами РЛС')
plt.grid(True)
plt.show()



'''
dataSat['skip'] = 0
dataSat['skip'] = dataSat['flowSat'] - sumObjTracker

f = open('config.json')
config = json.load(f)


fig, ax = plt.subplots()
ax.plot(time_out, dataSat['inSector'], color = 'black')
plt.stackplot(time_out, dataSat['flowSat'], color = 'red')
plt.stackplot(time_out, sumObjTracker, color = 'blue', alpha = 1.0)
plt.stackplot([config['Consts for VOKO']['startTime']/60, config['Consts for VOKO']['stopTime']/60], [100, 100], color = 'red', alpha = 0.3)
plt.xlabel(r'Время')
plt.ylabel(r'Количество ИСЗ')
plt.title('Оценка количества ИСЗ в секторе, оценка количества обнаруженных и пропущенных объектов')
ax.legend(loc = 1)
plt.grid(True)
timeFmt = matplotlib.dates.DateFormatter('%H:%M')
ax.xaxis.set_major_formatter(timeFmt)
ax.legend(['количество объектов в секторе действия РЛС',
           'пропущенные объекты',
           'обнаруженных'], loc = 2)
plt.show()

'''