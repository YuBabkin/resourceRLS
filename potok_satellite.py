#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd

class PotokSatellite:
    """ Поток КО через сектор ответственности
    """

    def __init__(self, file_name):
        self.data = pd.read_csv(file_name, sep = ',')
        self.data.sort_values(by='time')
        # return self

    def inBarrier(self, time):
        """ Количество объектов в барьере на данным момент времени
        """
        data = self.data[self.data['time'] <= time]
        return data['inBarrier'].iloc[-1]
