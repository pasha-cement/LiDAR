from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QGroupBox, 
                            QFormLayout, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer

class ConnectionWidget(QWidget):
    def __init__(self, sensor_controller):
        super().__init__()
        
        self.sensor_controller = sensor_controller
        
        # Настройка макета
        self.main_layout = QVBoxLayout(self)
        
        # Группа подключения к устройству
        self.connection_group = QGroupBox("Подключение к LiDAR")
        self.connection_layout = QVBoxLayout()
        self.connection_group.setLayout(self.connection_layout)
        
        # Выбор порта
        self.port_layout = QHBoxLayout()
        self.port_label = QLabel("COM-порт:")
        self.port_combo = QComboBox()
        self.refresh_ports_button = QPushButton("Обновить")
        
        self.port_layout.addWidget(self.port_label)
        self.port_layout.addWidget(self.port_combo)
        self.port_layout.addWidget(self.refresh_ports_button)
        self.connection_layout.addLayout(self.port_layout)
        
        # Кнопки управления подключением
        self.buttons_layout = QHBoxLayout()
        self.connect_button = QPushButton("Подключить")
        self.disconnect_button = QPushButton("Отключить")
        self.disconnect_button.setEnabled(False)
        
        self.buttons_layout.addWidget(self.connect_button)
        self.buttons_layout.addWidget(self.disconnect_button)
        self.buttons_layout.addStretch(1)
        self.connection_layout.addLayout(self.buttons_layout)
        
        # Добавляем группу подключения в основной макет
        self.main_layout.addWidget(self.connection_group)
        
        # Группа информации о датчике
        self.info_group = QGroupBox("Информация о датчике")
        self.info_layout = QFormLayout()
        self.info_group.setLayout(self.info_layout)
        
        # Метки состояния
        self.connection_status_label = QLabel("Не подключено")
        self.device_info_label = QLabel("Н/Д")
        self.temperature_label = QLabel("Н/Д")
        self.voltage_label = QLabel("Н/Д")
        
        self.info_layout.addRow("Статус:", self.connection_status_label)
        self.info_layout.addRow("Устройство:", self.device_info_label)
        self.info_layout.addRow("Температура:", self.temperature_label)
        self.info_layout.addRow("Напряжение:", self.voltage_label)
        
        # Добавляем группу информации в основной макет
        self.main_layout.addWidget(self.info_group)
        
        # Добавляем растягиваемый элемент для заполнения оставшегося пространства
        self.main_layout.addStretch(1)
        
        # Таймер для обновления информации о датчике
        self.status_timer = QTimer()
        self.status_timer.setInterval(5000)  # 5 секунд
        
        # Подключаем сигналы
        self.connect_signals()
        
        # Инициализация списка портов
        self.refresh_ports()
    
    def connect_signals(self):
        """Подключение сигналов"""
        # Кнопки
        self.refresh_ports_button.clicked.connect(self.refresh_ports)
        self.connect_button.clicked.connect(self.on_connect)
        self.disconnect_button.clicked.connect(self.on_disconnect)
        
        # Сигналы от контроллера датчика
        self.sensor_controller.connection_changed.connect(self.on_connection_changed)
        self.sensor_controller.status_updated.connect(self.on_status_updated)
        self.sensor_controller.error_occurred.connect(self.on_error)
        
        # Таймер обновления статуса
        self.status_timer.timeout.connect(self.update_sensor_status)
    
    def refresh_ports(self):
        """Обновление списка доступных портов"""
        current_port = self.port_combo.currentText()
        ports = self.sensor_controller.get_available_ports()
        
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        
        # Восстанавливаем ранее выбранный порт, если он доступен
        if current_port in ports:
            self.port_combo.setCurrentText(current_port)
    
    @pyqtSlot()
    def on_connect(self):
        """Обработчик нажатия кнопки подключения"""
        port = self.port_combo.currentText()
        if not port:
            QMessageBox.warning(self, "Ошибка", "Не выбран COM-порт")
            return
        
        # Пытаемся подключиться к датчику
        success = self.sensor_controller.connect_sensor(port)
        if success:
            # Получаем версию устройства
            self.sensor_controller.get_sensor_version()
            # Запускаем таймер обновления статуса
            self.status_timer.start()
    
    @pyqtSlot()
    def on_disconnect(self):
        """Обработчик нажатия кнопки отключения"""
        self.status_timer.stop()
        success = self.sensor_controller.disconnect_sensor()
        if not success:
            QMessageBox.warning(self, "Ошибка", "Не удалось отключиться от датчика")
    
    @pyqtSlot(bool)
    def on_connection_changed(self, connected):
        """Обработчик изменения статуса подключения"""
        self.connect_button.setEnabled(not connected)
        self.disconnect_button.setEnabled(connected)
        self.connection_status_label.setText("Подключено" if connected else "Не подключено")
        
        if not connected:
            self.device_info_label.setText("Н/Д")
            self.temperature_label.setText("Н/Д")
            self.voltage_label.setText("Н/Д")
            self.status_timer.stop()
    
    @pyqtSlot(float, float)
    def on_status_updated(self, temperature, voltage):
        """Обработчик обновления статуса датчика"""
        self.temperature_label.setText(f"{temperature:.1f}°C")
        self.voltage_label.setText(f"{voltage:.2f} В")
    
    @pyqtSlot(str)
    def on_error(self, error_message):
        """Обработчик ошибок"""
        QMessageBox.warning(self, "Ошибка", error_message)
    
    @pyqtSlot()
    def update_sensor_status(self):
        """Запрос обновления статуса датчика"""
        if self.sensor_controller.serial_handler.is_connected:
            self.sensor_controller.get_sensor_status()