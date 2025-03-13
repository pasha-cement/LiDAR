import numpy as np
import pandas as pd
from ..config.settings import STATISTICS_SETTINGS

class StatisticsCalculator:
    @staticmethod
    def calculate_basic_stats(measurements):
        """Calculate basic statistics from a list of measurements"""
        if not measurements:
            return {
                "count": 0,
                "min": None,
                "max": None,
                "mean": None,
                "median": None,
                "std_dev": None
            }
        
        data = np.array(measurements)
        return {
            "count": len(data),
            "min": np.min(data),
            "max": np.max(data),
            "mean": np.mean(data),
            "median": np.median(data),
            "std_dev": np.std(data)
        }
    
    @staticmethod
    def detect_outliers(measurements):
        """Detect outliers using the standard deviation method"""
        if not measurements or len(measurements) < 3:
            return [], measurements
        
        data = np.array(measurements)
        mean = np.mean(data)
        std_dev = np.std(data)
        threshold = STATISTICS_SETTINGS['outlier_threshold'] * std_dev
        
        outliers_indices = np.where(np.abs(data - mean) > threshold)[0]
        outliers = data[outliers_indices]
        
        # Create cleaned data by excluding outliers
        cleaned_data = np.delete(data, outliers_indices)
        
        return outliers.tolist(), cleaned_data.tolist()
    
    @staticmethod
    def moving_average(measurements, window=None):
        """Calculate moving average of measurements"""
        if not measurements:
            return []
        
        if window is None:
            window = STATISTICS_SETTINGS['moving_avg_window']
        
        data = pd.Series(measurements)
        return data.rolling(window=window, min_periods=1).mean().tolist()
    
    @staticmethod
    def calculate_rate_of_change(measurements, time_intervals):
        """Calculate rate of change between consecutive measurements"""
        if len(measurements) < 2 or len(measurements) != len(time_intervals) + 1:
            return []
            
        rates = []
        for i in range(1, len(measurements)):
            delta_measurement = measurements[i] - measurements[i-1]
            delta_time = time_intervals[i-1]
            if delta_time > 0:
                rates.append(delta_measurement / delta_time)
            else:
                rates.append(0)
                
        return rates