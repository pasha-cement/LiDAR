import os
import csv
import time
import pandas as pd
import numpy as np
from datetime import datetime

class MeasurementModel:
    def __init__(self):
        """
        Инициализирует модель измерений.

        Создает пустой список для хранения измерений и устанавливает идентификатор текущей сессии в None.
        """
        self.measurements = []
        self.current_session_id = None
        
    def add_measurement(self, distance, quality):
        """
        Добавляет новое измерение.

        Добавляет измерение с текущей временной меткой, дистанцией и качеством сигнала в список измерений.

        Args:
            distance (float): Значение дистанции.
            quality (float): Значение качества сигнала.

        Returns:
            int: Количество измерений в списке после добавления нового измерения.
        """
        timestamp = time.time()
        self.measurements.append((timestamp, distance, quality))
        return len(self.measurements)
    
    def get_measurements(self, count=None):
        """
        Возвращает измерения.

        Возвращает все измерения или указанное количество последних измерений.

        Args:
            count (int, optional): Количество последних измерений для возврата. Если None, возвращаются все измерения.

        Returns:
            list: Список измерений.
        """
        if count is None:
            return self.measurements
        return self.measurements[-count:]
        
    def get_distances(self, count=None):
        """
        Возвращает значения дистанций из измерений.

        Args:
            count (int, optional): Количество последних измерений для извлечения дистанций. Если None, используются все измерения.

        Returns:
            list: Список значений дистанций.
        """
        measurements = self.get_measurements(count)
        return [m[1] for m in measurements]
    
    def get_quality_values(self, count=None):
        """
        Возвращает значения качества сигнала из измерений.

        Args:
            count (int, optional): Количество последних измерений для извлечения значений качества. Если None, используются все измерения.

        Returns:
            list: Список значений качества сигнала.
        """
        measurements = self.get_measurements(count)
        return [m[2] for m in measurements]
    
    def clear_measurements(self):
        """Очищает все измерения в текущей сессии."""
        self.measurements = []