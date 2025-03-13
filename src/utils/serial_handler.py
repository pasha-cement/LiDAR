import serial
import time
import re
from ..config.settings import SERIAL_SETTINGS, COMMANDS, ERROR_CODES

class SerialHandler:
    def __init__(self):
        self.serial = None
        self.port = None
        self.is_connected = False
    
    def connect(self, port):
        """Connect to the LiDAR sensor via serial port"""
        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=SERIAL_SETTINGS['baudrate'],
                bytesize=SERIAL_SETTINGS['bytesize'],
                parity=SERIAL_SETTINGS['parity'],
                stopbits=SERIAL_SETTINGS['stopbits'],
                timeout=SERIAL_SETTINGS['timeout']
            )
            self.port = port
            self.is_connected = True
            return True
        except Exception as e:
            print(f"Error connecting to port {port}: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the serial port"""
        if self.serial and self.is_connected:
            try:
                self.send_command(COMMANDS['LASER_OFF'])
                time.sleep(0.1)
                self.serial.close()
                self.is_connected = False
                return True
            except Exception as e:
                print(f"Error disconnecting: {e}")
                return False
        return True
    
    def send_command(self, command):
        """Send command to the LiDAR sensor"""
        if not self.is_connected:
            return None
        
        try:
            # Clear any existing data in buffer
            self.serial.reset_input_buffer()
            
            # Send command with carriage return and line feed
            self.serial.write((command + "\r\n").encode())
            
            # Give time for the sensor to process the command
            time.sleep(0.1)
            
            # Read initial response - might just be echo of command
            initial_response = self.serial.read_all().decode(errors='ignore')
            print(f"Debug - Initial response: {repr(initial_response)}")
            
            # For measurement commands, we need to wait more and read again
            if command in [COMMANDS['AUTO_MEASURE'], COMMANDS['FAST_MEASURE'], COMMANDS['SLOW_MEASURE']]:
                # Wait longer for the actual measurement data
                time.sleep(0.5)
                
                # Read the actual measurement response
                measurement_response = self.serial.read_all().decode(errors='ignore')
                print(f"Debug - Measurement response: {repr(measurement_response)}")
                
                if measurement_response:
                    return measurement_response
                else:
                    return initial_response
            else:
                return initial_response
                
        except Exception as e:
            print(f"Error sending command: {e}")
            return None
    
    def parse_distance_response(self, response):
        """Parse the response from a distance measurement command"""
        if not response:
            return None, None, "No response from sensor"

        # Check for error response
        for error_code, error_msg in ERROR_CODES.items():
            if error_code in response:
                return None, None, error_msg

        # Check if response is a status message instead of distance
        if "'C" in response and "V" in response:
            # This is a status response, not a distance measurement
            return None, None, "Received status response instead of distance"

        # Parse successful measurement response
        try:
            # Look for format ": X.XXXm,YYYY" where X.XXX is distance and YYYY is quality
            match = re.search(r': (\d+\.\d+)m,(\d+)', response)
            if match:
                distance = float(match.group(1))
                quality = int(match.group(2))
                return distance, quality, None

            # Alternative format without colon
            match = re.search(r'(\d+\.\d+)m,(\d+)', response)
            if match:
                distance = float(match.group(1))
                quality = int(match.group(2))
                return distance, quality, None

            return None, None, "Could not extract distance from response"
        except Exception as e:
            return None, None, f"Error parsing response: {e}"
    
    def parse_status_response(self, response):
        """Parse the status response from the sensor"""
        if not response:
            return None, None, "No status response"

        try:
            # Extract temperature and voltage using regex
            temp_match = re.search(r'S: (\d+\.\d*)[\'°]?C', response)
            if not temp_match:
                temp_match = re.search(r'(\d+\.\d*)[\'°]?C', response)

            voltage_match = re.search(r'(\d+\.\d*)V', response)

            temp = 25.0  # Default temperature
            voltage = 3.0  # Default voltage

            if temp_match:
                temp = float(temp_match.group(1))
            else:
                return None, None, "Could not extract temperature from response"

            if voltage_match:
                voltage = float(voltage_match.group(1))

            return temp, voltage, None
        except Exception as e:
            return None, None, f"Error parsing status: {e}"
    
    def get_available_ports(self):
        """Get list of available serial ports"""
        import serial.tools.list_ports
        return [port.device for port in serial.tools.list_ports.comports()]