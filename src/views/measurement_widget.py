from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QGroupBox, 
                            QRadioButton, QButtonGroup, QSpacerItem,
                            QSizePolicy, QLCDNumber, QTableWidget,
                            QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer

class MeasurementWidget(QWidget):
    def __init__(self, sensor_controller, data_controller):
        super().__init__()
        
        self.sensor_controller = sensor_controller
        self.data_controller = data_controller
        
        # Create timer for sensor status updates
        self.status_timer = QTimer()
        self.status_timer.setInterval(5000)  # 5 seconds
        
        # Set up the layout
        self.main_layout = QVBoxLayout(self)
        
        # Create measurement control group
        self.control_group = QGroupBox("Measurement Control")
        self.control_layout = QVBoxLayout()
        self.control_group.setLayout(self.control_layout)
        
        # Measurement mode selection
        self.mode_layout = QHBoxLayout()
        self.mode_label = QLabel("Measurement Mode:")
        
        self.mode_group = QButtonGroup(self)
        self.single_mode_radio = QRadioButton("Single")
        self.continuous_mode_radio = QRadioButton("Continuous")
        self.single_mode_radio.setChecked(True)
        
        self.mode_group.addButton(self.single_mode_radio)
        self.mode_group.addButton(self.continuous_mode_radio)
        
        self.mode_layout.addWidget(self.mode_label)
        self.mode_layout.addWidget(self.single_mode_radio)
        self.mode_layout.addWidget(self.continuous_mode_radio)
        self.mode_layout.addStretch(1)
        
        self.control_layout.addLayout(self.mode_layout)
        
        # Measurement speed selection (for continuous mode)
        self.speed_layout = QHBoxLayout()
        self.speed_label = QLabel("Measurement Speed:")
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["Auto", "Fast", "Slow"])
        self.speed_layout.addWidget(self.speed_label)
        self.speed_layout.addWidget(self.speed_combo)
        self.speed_layout.addStretch(1)
        
        self.control_layout.addLayout(self.speed_layout)
        
        # Measurement buttons
        self.buttons_layout = QHBoxLayout()
        self.measure_button = QPushButton("Measure")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.clear_button = QPushButton("Clear Data")
        
        self.buttons_layout.addWidget(self.measure_button)
        self.buttons_layout.addWidget(self.stop_button)
        self.buttons_layout.addWidget(self.clear_button)
        
        self.control_layout.addLayout(self.buttons_layout)
        
        self.main_layout.addWidget(self.control_group)
        
        # Create current reading display group
        self.reading_group = QGroupBox("Current Reading")
        self.reading_layout = QHBoxLayout()
        self.reading_group.setLayout(self.reading_layout)
        
        # Distance LCD
        self.distance_layout = QVBoxLayout()
        self.distance_label = QLabel("Distance (m)")
        self.distance_lcd = QLCDNumber(6)  # 6 digits
        self.distance_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.distance_lcd.setMinimumHeight(60)
        self.distance_layout.addWidget(self.distance_label, alignment=Qt.AlignCenter)
        self.distance_layout.addWidget(self.distance_lcd)
        
        # Quality LCD
        self.quality_layout = QVBoxLayout()
        self.quality_label = QLabel("Signal Quality")
        self.quality_lcd = QLCDNumber(3)  # 3 digits
        self.quality_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.quality_lcd.setMinimumHeight(60)
        self.quality_layout.addWidget(self.quality_label, alignment=Qt.AlignCenter)
        self.quality_layout.addWidget(self.quality_lcd)
        
        # Sensor status
        self.status_layout = QVBoxLayout()
        self.status_label = QLabel("Sensor Status")
        self.temp_label = QLabel("Temp: N/A")
        self.voltage_label = QLabel("Voltage: N/A")
        self.status_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)
        self.status_layout.addWidget(self.temp_label)
        self.status_layout.addWidget(self.voltage_label)
        
        self.reading_layout.addLayout(self.distance_layout)
        self.reading_layout.addLayout(self.quality_layout)
        self.reading_layout.addLayout(self.status_layout)
        
        self.main_layout.addWidget(self.reading_group)
        
        # Create measurements table group
        self.table_group = QGroupBox("Measurement History")
        self.table_layout = QVBoxLayout()
        self.table_group.setLayout(self.table_layout)
        
        self.measurements_table = QTableWidget(0, 3)  # 0 rows, 3 columns initially
        headers = ["Time", "Distance (m)", "Quality"]
        self.measurements_table.setHorizontalHeaderLabels(headers)
        self.measurements_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.table_layout.addWidget(self.measurements_table)
        
        self.main_layout.addWidget(self.table_group)
        
        # Connect signals
        self.connect_signals()
        
    def connect_signals(self):
        # Button connections
        self.measure_button.clicked.connect(self.start_measurement)
        self.stop_button.clicked.connect(self.stop_measurement)
        self.clear_button.clicked.connect(self.clear_measurements)
        
        # Radio button connections
        self.single_mode_radio.toggled.connect(self.update_mode_ui)
        
        # Sensor controller connections
        self.sensor_controller.measurement_taken.connect(self.update_current_reading)
        self.sensor_controller.status_updated.connect(self.update_sensor_status)
        self.sensor_controller.connection_changed.connect(self.update_ui_on_connection)
        
        # Data controller connections
        self.data_controller.data_updated.connect(self.update_measurements_table)
        
        # Timer connection
        self.status_timer.timeout.connect(self.get_sensor_status)
    
    @pyqtSlot()
    def update_mode_ui(self):
        is_single = self.single_mode_radio.isChecked()
        self.speed_combo.setEnabled(not is_single)
    
    @pyqtSlot()
    def start_measurement(self):
        if not self.sensor_controller.serial_handler.is_connected:
            return
        
        if self.single_mode_radio.isChecked():
            # Single measurement
            self.sensor_controller.get_single_measurement()
        else:
            # Continuous measurement
            measurement_type = self.speed_combo.currentText().lower()
            success = self.sensor_controller.start_continuous_measurement(measurement_type)
            
            if success:
                self.measure_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.single_mode_radio.setEnabled(False)
                self.continuous_mode_radio.setEnabled(False)
                
                # Start timer for periodic status updates
                self.status_timer.start()
    
    @pyqtSlot()
    def stop_measurement(self):
        self.sensor_controller.stop_continuous_measurement()
        self.measure_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.single_mode_radio.setEnabled(True)
        self.continuous_mode_radio.setEnabled(True)
        
        # Stop status update timer
        self.status_timer.stop()
    
    @pyqtSlot()
    def clear_measurements(self):
        reply = QMessageBox.question(self, 'Clear Measurements', 
                                     'Are you sure you want to clear all measurements?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.data_controller.clear_data()
            self.measurements_table.setRowCount(0)
    
    @pyqtSlot(float, int)
    def update_current_reading(self, distance, quality):
        self.distance_lcd.display(f"{distance:.3f}")
        self.quality_lcd.display(quality)
    
    @pyqtSlot(float, float)
    def update_sensor_status(self, temp, voltage):
        self.temp_label.setText(f"Temp: {temp}°C")
        self.voltage_label.setText(f"Voltage: {voltage}V")

    @pyqtSlot()
    def update_measurements_table(self):
        # Get the last 100 measurements
        measurements = self.data_controller.model.get_measurements(100)
        
        # Update table
        self.measurements_table.setRowCount(len(measurements))
        
        # Add items in reverse order (newest at top)
        for i, (timestamp, distance, quality) in enumerate(reversed(measurements)):
            # Format timestamp as time
            from datetime import datetime
            time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S.%f')[:-3]
            
            time_item = QTableWidgetItem(time_str)
            distance_item = QTableWidgetItem(f"{distance:.3f}")
            quality_item = QTableWidgetItem(str(quality))
            
            self.measurements_table.setItem(i, 0, time_item)
            self.measurements_table.setItem(i, 1, distance_item)
            self.measurements_table.setItem(i, 2, quality_item)
    
    @pyqtSlot(bool)
    def update_ui_on_connection(self, connected):
        self.measure_button.setEnabled(connected)
        self.clear_button.setEnabled(connected)
        
        if not connected:
            self.stop_measurement()  # Make sure to stop any ongoing measurements
    
    @pyqtSlot()
    def get_sensor_status(self):
        """Get sensor status periodically during continuous measurements"""
        if self.sensor_controller.serial_handler.is_connected:
            self.sensor_controller.get_sensor_status()

from PyQt5.QtWidgets import QMessageBox