import os
import csv
import time
import pandas as pd
import numpy as np
from datetime import datetime
from ..config.settings import DATA_SETTINGS

class MeasurementModel:
    def __init__(self):
        self.measurements = []  # List of (timestamp, distance, quality) tuples
        self.current_session_id = None
        
        # Ensure measurement directory exists
        os.makedirs(DATA_SETTINGS['measurement_dir'], exist_ok=True)
        
    def start_new_session(self):
        """Start a new measurement session with a unique ID"""
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.measurements = []
        return self.current_session_id
        
    def add_measurement(self, distance, quality):
        """Add a new measurement with current timestamp"""
        timestamp = time.time()
        self.measurements.append((timestamp, distance, quality))
        return len(self.measurements)
    
    def get_measurements(self, count=None):
        """Get the most recent measurements"""
        if count is None:
            return self.measurements
        return self.measurements[-count:]
        
    def get_distances(self, count=None):
        """Get only the distance values from measurements"""
        measurements = self.get_measurements(count)
        return [m[1] for m in measurements]
        
    def get_timestamps(self, count=None, relative=False):
        """Get timestamps, optionally relative to the first measurement"""
        measurements = self.get_measurements(count)
        timestamps = [m[0] for m in measurements]
        
        if relative and timestamps:
            first_timestamp = timestamps[0]
            timestamps = [t - first_timestamp for t in timestamps]
            
        return timestamps
    
    def get_quality_values(self, count=None):
        """Get signal quality values from measurements"""
        measurements = self.get_measurements(count)
        return [m[2] for m in measurements]
    
    def clear_measurements(self):
        """Clear all measurements in current session"""
        self.measurements = []
    
    def save_to_csv(self, filename=None):
        """Save measurements to a CSV file"""
        if not self.measurements:
            return False
            
        if filename is None:
            if self.current_session_id is None:
                self.start_new_session()
            filename = f"{DATA_SETTINGS['default_filename']}_{self.current_session_id}.{DATA_SETTINGS['file_extension']}"
            
        filepath = os.path.join(DATA_SETTINGS['measurement_dir'], filename)
        
        try:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Timestamp', 'Distance (m)', 'Signal Quality'])
                writer.writerows(self.measurements)
            return True
        except Exception as e:
            print(f"Error saving measurements: {e}")
            return False
    
    def load_from_csv(self, filepath):
        """Load measurements from a CSV file"""
        try:
            df = pd.read_csv(filepath)
            self.measurements = list(zip(df['Timestamp'], df['Distance (m)'], df['Signal Quality']))
            return True
        except Exception as e:
            print(f"Error loading measurements: {e}")
            return False