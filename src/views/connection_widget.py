from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QGroupBox, 
                            QTextEdit, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSlot

class ConnectionWidget(QWidget):
    def __init__(self, sensor_controller):
        super().__init__()
        
        self.sensor_controller = sensor_controller
        
        # Set up the layout
        self.main_layout = QVBoxLayout(self)
        
        # Create connection controls group
        self.connection_group = QGroupBox("Sensor Connection")
        self.connection_layout = QVBoxLayout()
        self.connection_group.setLayout(self.connection_layout)
        
        # Port selection
        self.port_layout = QHBoxLayout()
        self.port_label = QLabel("Serial Port:")
        self.port_combo = QComboBox()
        self.refresh_button = QPushButton("Refresh")
        self.port_layout.addWidget(self.port_label)
        self.port_layout.addWidget(self.port_combo)
        self.port_layout.addWidget(self.refresh_button)
        self.connection_layout.addLayout(self.port_layout)
        
        # Connect/Disconnect buttons
        self.btn_layout = QHBoxLayout()
        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setEnabled(False)
        self.btn_layout.addWidget(self.connect_button)
        self.btn_layout.addWidget(self.disconnect_button)
        self.connection_layout.addLayout(self.btn_layout)
        
        self.main_layout.addWidget(self.connection_group)
        
        # Create sensor info group
        self.info_group = QGroupBox("Sensor Information")
        self.info_layout = QFormLayout()
        self.info_group.setLayout(self.info_layout)
        
        self.connection_status_label = QLabel("Not Connected")
        self.version_label = QLabel("Unknown")
        self.temperature_label = QLabel("Unknown")
        self.voltage_label = QLabel("Unknown")
        
        self.info_layout.addRow("Connection Status:", self.connection_status_label)
        self.info_layout.addRow("Sensor Version:", self.version_label)
        self.info_layout.addRow("Temperature:", self.temperature_label)
        self.info_layout.addRow("Voltage:", self.voltage_label)
        
        self.main_layout.addWidget(self.info_group)
        
        # Create log area
        self.log_group = QGroupBox("Connection Log")
        self.log_layout = QVBoxLayout()
        self.log_group.setLayout(self.log_layout)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_layout.addWidget(self.log_text)
        
        self.main_layout.addWidget(self.log_group)
        
        # Connect signals
        self.connect_signals()
        
        # Initialize the port list
        self.refresh_ports()
    
    def connect_signals(self):
        # Button connections
        self.refresh_button.clicked.connect(self.refresh_ports)
        self.connect_button.clicked.connect(self.connect_to_sensor)
        self.disconnect_button.clicked.connect(self.disconnect_from_sensor)
        
        # Sensor controller connections
        self.sensor_controller.connection_changed.connect(self.update_connection_status)
        self.sensor_controller.error_occurred.connect(self.log_message)
        self.sensor_controller.status_updated.connect(self.update_sensor_status)
    
    @pyqtSlot()
    def refresh_ports(self):
        self.port_combo.clear()
        ports = self.sensor_controller.get_available_ports()
        self.port_combo.addItems(ports)
        self.log_message(f"Found {len(ports)} serial ports")
    
    @pyqtSlot()
    def connect_to_sensor(self):
        if self.port_combo.currentText():
            port = self.port_combo.currentText()
            self.log_message(f"Connecting to sensor on port {port}...")
            success = self.sensor_controller.connect_sensor(port)
            if success:
                self.get_sensor_info()
            else:
                self.log_message("Failed to connect to sensor")
        else:
            self.log_message("No port selected")
    
    @pyqtSlot()
    def disconnect_from_sensor(self):
        self.log_message("Disconnecting from sensor...")
        self.sensor_controller.disconnect_sensor()
    
    @pyqtSlot(bool)
    def update_connection_status(self, connected):
        if connected:
            self.connection_status_label.setText("Connected")
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.log_message("Sensor connected successfully")
        else:
            self.connection_status_label.setText("Not Connected")
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.version_label.setText("Unknown")
            self.temperature_label.setText("Unknown")
            self.voltage_label.setText("Unknown")
            self.log_message("Sensor disconnected")
    
    def get_sensor_info(self):
        # Get sensor version
        version = self.sensor_controller.get_sensor_version()
        if version:
            self.version_label.setText(version)
            self.log_message(f"Sensor version: {version}")
        
        # Get sensor status (temperature and voltage)
        status = self.sensor_controller.get_sensor_status()
        if status:
            temp, voltage = status
            self.update_sensor_status(temp, voltage)
    
    @pyqtSlot(float, float)
    def update_sensor_status(self, temp, voltage):
        self.temperature_label.setText(f"{temp}°C")
        self.voltage_label.setText(f"{voltage}V")
    
    def log_message(self, message):
        self.log_text.append(f"> {message}")
        # Scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )