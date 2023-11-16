#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import random
import pandas as pd


from math import e
from math import factorial


class PotokSatellite:
    """ Поток Ко через сектор ответственности
    """

    def __init__(self, file_name):
        """
        """

        self.dataSat = pd.read_csv(file_name, sep = ',')


    #todo найти ближайшее сверху время в DF и вернуть поток КО для этого времени!!!

    def inSector(self, time):
        """ Количество объектов в сеторе на данным момент времени
        """
        return self.dataSat['inSector'].iloc[time]


    def flowSat(self, time):
        """
        """
        return self.dataSat['flowSat'].iloc[time]
