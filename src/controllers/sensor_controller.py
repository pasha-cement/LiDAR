import time
import threading
from PyQt5.QtCore import QObject, pyqtSignal
from ..config.settings import COMMANDS
from ..utils.serial_handler import SerialHandler

class SensorController(QObject):
    # Signals
    measurement_taken = pyqtSignal(float, int)  # distance, quality
    connection_changed = pyqtSignal(bool)  # connected status
    error_occurred = pyqtSignal(str)  # error message
    status_updated = pyqtSignal(float, float)  # temperature, voltage - FIX: Changed from (str, float) to (float, float)
    
    def __init__(self, serial_handler=None):
        super().__init__()
        self.serial_handler = serial_handler or SerialHandler()
        self.is_measuring = False
        self.continuous_thread = None
        self.stop_flag = False
    
    def connect_sensor(self, port):
        """Connect to the LiDAR sensor"""
        success = self.serial_handler.connect(port)
        if success:
            # Turn on the laser after connection
            response = self.serial_handler.send_command(COMMANDS['LASER_ON'])
            if response and ',OK!' in response:
                self.connection_changed.emit(True)
                return True
            else:
                self.serial_handler.disconnect()
                self.error_occurred.emit("Failed to turn on laser")
                self.connection_changed.emit(False)
                return False
        else:
            self.connection_changed.emit(False)
            return False
    
    def disconnect_sensor(self):
        """Disconnect from the LiDAR sensor"""
        self.stop_continuous_measurement()
        success = self.serial_handler.disconnect()
        self.connection_changed.emit(not success)
        return success
    
    def get_single_measurement(self):
        """Get a single distance measurement"""
        if not self.serial_handler.is_connected:
            self.error_occurred.emit("Sensor not connected")
            return None, None

        try:
            response = self.serial_handler.send_command(COMMANDS['AUTO_MEASURE'])
            distance, quality, error = self.serial_handler.parse_distance_response(response)

            if error:
                self.error_occurred.emit(error)
                return None, None

            if distance is not None:
                print(f"Debug - Successful measurement: {distance}m, quality: {quality}")
                self.measurement_taken.emit(distance, quality)
                return distance, quality
            else:
                self.error_occurred.emit("Invalid measurement result")
                return None, None
        except Exception as e:
            self.error_occurred.emit(f"Measurement error: {str(e)}")
            return None, None
    
    def start_continuous_measurement(self, measure_type='auto'):
        """Start continuous measurement in a separate thread"""
        if self.is_measuring:
            return False
            
        if not self.serial_handler.is_connected:
            self.error_occurred.emit("Sensor not connected")
            return False
        
        # Set the command based on measurement type
        if measure_type == 'slow':
            command = COMMANDS['SLOW_MEASURE']
        elif measure_type == 'fast':
            command = COMMANDS['FAST_MEASURE']
        else:  # auto
            command = COMMANDS['AUTO_MEASURE']
        
        self.stop_flag = False
        self.is_measuring = True
        
        # Start measurement thread
        self.continuous_thread = threading.Thread(
            target=self._continuous_measurement_worker,
            args=(command,),
            daemon=True
        )
        self.continuous_thread.start()
        return True
    
    def stop_continuous_measurement(self):
        """Stop continuous measurement"""
        self.stop_flag = True
        if self.continuous_thread and self.continuous_thread.is_alive():
            self.continuous_thread.join(timeout=1.0)
        self.is_measuring = False
        return True
    
    def _continuous_measurement_worker(self, command):
        """Worker function for continuous measurement thread"""
        # Make sure laser is on
        self.serial_handler.send_command(COMMANDS['LASER_ON'])
        time.sleep(0.2)

        consecutive_errors = 0
        max_consecutive_errors = 5

        while not self.stop_flag:
            try:
                response = self.serial_handler.send_command(command)

                # Check if response looks like a status message
                if "'C" in response and "V" in response:
                    # Get proper temperature and voltage instead of treating as distance
                    temp, voltage, _ = self.serial_handler.parse_status_response(response)
                    if temp is not None and voltage is not None:
                        self.status_updated.emit(temp, voltage)
                        print(f"Debug - Updated sensor status: {temp}°C, {voltage}V")
                        consecutive_errors = 0  # Reset error counter
                        time.sleep(0.3)
                        continue

                # Try to parse as distance measurement
                distance, quality, error = self.serial_handler.parse_distance_response(response)

                if error:
                    print(f"Debug - Error in continuous mode: {error}")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        self.error_occurred.emit(f"Multiple measurement errors: {error}")
                        consecutive_errors = 0  # Reset after reporting
                        time.sleep(1.0)  # Longer wait after multiple errors
                elif distance is not None:
                    print(f"Debug - Continuous measurement: {distance}m, quality: {quality}")
                    self.measurement_taken.emit(distance, quality)
                    consecutive_errors = 0  # Reset error counter
                else:
                    print("Debug - No valid distance in continuous mode")
                    consecutive_errors += 1

                # Small delay between measurements
                time.sleep(0.3)

            except Exception as e:
                print(f"Debug - Exception in continuous mode: {e}")
                consecutive_errors += 1
                time.sleep(0.5)
    
    def get_sensor_status(self):
        """Get sensor status (temperature and voltage)"""
        if not self.serial_handler.is_connected:
            self.error_occurred.emit("Sensor not connected")
            return None
            
        response = self.serial_handler.send_command(COMMANDS['READ_STATUS'])
        if response:
            temp, voltage, error = self.serial_handler.parse_status_response(response)
            
            if error:
                self.error_occurred.emit(error)
                return None
                
            self.status_updated.emit(temp, voltage)
            return temp, voltage
        
        self.error_occurred.emit("No status response")
        return None
    
    def get_sensor_version(self):
        """Get sensor firmware version"""
        if not self.serial_handler.is_connected:
            self.error_occurred.emit("Sensor not connected")
            return None
            
        response = self.serial_handler.send_command(COMMANDS['VERSION'])
        return response.strip() if response else None
    
    def get_available_ports(self):
        """Get list of available serial ports"""
        return self.serial_handler.get_available_ports()