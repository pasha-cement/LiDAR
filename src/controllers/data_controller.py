from PyQt5.QtCore import QObject, pyqtSignal
from ..models.measurement_model import MeasurementModel
from ..utils.statistics import StatisticsCalculator

class DataController(QObject):
    # Signals
    data_updated = pyqtSignal()
    statistics_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.model = MeasurementModel()
        self.statistics = StatisticsCalculator()
    
    def start_new_session(self):
        """Start a new measurement session"""
        session_id = self.model.start_new_session()
        self.data_updated.emit()
        return session_id
    
    def add_measurement(self, distance, quality):
        """Add a new measurement to the current session"""
        self.model.add_measurement(distance, quality)
        self.update_statistics()
        self.data_updated.emit()
    
    def update_statistics(self):
        """Calculate and emit updated statistics"""
        distances = self.model.get_distances()
        if not distances:
            return
        
        stats = self.statistics.calculate_basic_stats(distances)
        outliers, cleaned_data = self.statistics.detect_outliers(distances)
        moving_avg = self.statistics.moving_average(distances)
        
        # Add additional statistics
        stats['outliers_count'] = len(outliers)
        stats['outliers_percent'] = (len(outliers) / len(distances)) * 100 if distances else 0
        stats['last_value'] = distances[-1] if distances else None
        stats['last_moving_avg'] = moving_avg[-1] if moving_avg else None
        
        # Calculate rates of change if we have timestamps
        timestamps = self.model.get_timestamps(relative=True)
        if len(timestamps) > 1:
            time_intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
            rates = self.statistics.calculate_rate_of_change(distances, time_intervals)
            if rates:
                stats['avg_rate_of_change'] = sum(rates) / len(rates)
                stats['max_rate_of_change'] = max(rates)
        
        self.statistics_updated.emit(stats)
    
    def get_plot_data(self, type='distance'):
        """Get data for plotting"""
        timestamps = self.model.get_timestamps(relative=True)
        
        if type == 'distance':
            return timestamps, self.model.get_distances()
        elif type == 'quality':
            return timestamps, self.model.get_quality_values()
        elif type == 'moving_avg':
            distances = self.model.get_distances()
            return timestamps, self.statistics.moving_average(distances)
        
        return [], []
    
    def clear_data(self):
        """Clear all measurements in current session"""
        self.model.clear_measurements()
        self.data_updated.emit()
    
    def save_data(self, filename=None):
        """Save current measurements to a CSV file"""
        success = self.model.save_to_csv(filename)
        return success
    
    def load_data(self, filepath):
        """Load measurements from a CSV file"""
        success = self.model.load_from_csv(filepath)
        if success:
            self.update_statistics()
            self.data_updated.emit()
        return success