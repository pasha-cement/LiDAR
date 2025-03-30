from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QGroupBox, 
                            QRadioButton, QButtonGroup, QSpacerItem,
                            QSizePolicy, QLCDNumber, QTableWidget,
                            QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
import time

class MeasurementWidget(QWidget):
    def __init__(self, sensor_controller, data_controller, aod_controller=None):
        super().__init__()
        
        self.sensor_controller = sensor_controller
        self.data_controller = data_controller
        self.aod_controller = aod_controller  # Добавляем контроллер АОЯ
        
        # Create timer for sensor status updates
        self.status_timer = QTimer()
        self.status_timer.setInterval(5000)  # 5 seconds
        
        # Set up the layout
        self.main_layout = QVBoxLayout(self)
        
        # Create measurement control group
        self.control_group = QGroupBox("Настройка измерений")
        self.control_layout = QVBoxLayout()
        self.control_group.setLayout(self.control_layout)
        
        # Measurement mode selection
        self.mode_layout = QHBoxLayout()
        self.mode_label = QLabel("Режим измерений:")
        
        self.mode_group = QButtonGroup(self)
        self.single_mode_radio = QRadioButton("Единичное")
        self.continuous_mode_radio = QRadioButton("Непрерывное")
        self.single_mode_radio.setChecked(True)
        
        self.mode_group.addButton(self.single_mode_radio)
        self.mode_group.addButton(self.continuous_mode_radio)
        
        self.mode_layout.addWidget(self.mode_label)
        self.mode_layout.addWidget(self.single_mode_radio)
        self.mode_layout.addWidget(self.continuous_mode_radio)
        self.mode_layout.addStretch(1)
        self.control_layout.addLayout(self.mode_layout)
        
        # Measurement rate selection (for continuous mode)
        self.rate_layout = QHBoxLayout()
        self.rate_label = QLabel("Скорость измерений:")
        self.rate_combo = QComboBox()
        self.rate_combo.addItems(["Авто", "Быстро", "Медленно"])
        self.rate_combo.setEnabled(False)  # Disabled initially
        
        self.rate_layout.addWidget(self.rate_label)
        self.rate_layout.addWidget(self.rate_combo)
        self.rate_layout.addStretch(1)
        self.control_layout.addLayout(self.rate_layout)
        
        # Measurement buttons
        self.buttons_layout = QHBoxLayout()
        self.measure_button = QPushButton("Измерить")
        self.stop_button = QPushButton("Остановить")
        self.stop_button.setEnabled(False)
        self.reset_button = QPushButton("Очистить данные")
        
        self.buttons_layout.addWidget(self.measure_button)
        self.buttons_layout.addWidget(self.stop_button)
        self.buttons_layout.addWidget(self.reset_button)
        self.control_layout.addLayout(self.buttons_layout)
        
        # Add the control group to the main layout
        self.main_layout.addWidget(self.control_group)
        
        # Create current measurement display group
        self.display_group = QGroupBox("Текущее измерение")
        self.display_layout = QHBoxLayout()
        self.display_group.setLayout(self.display_layout)
        
        # Distance LCD
        self.distance_lcd_layout = QVBoxLayout()
        self.distance_lcd = QLCDNumber()
        self.distance_lcd.setDigitCount(6)
        self.distance_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.distance_lcd.setStyleSheet("background-color: #f0f0f0;")
        self.distance_lcd_label = QLabel("Расстояние (м)")
        self.distance_lcd_label.setAlignment(Qt.AlignCenter)
        
        self.distance_lcd_layout.addWidget(self.distance_lcd)
        self.distance_lcd_layout.addWidget(self.distance_lcd_label)
        
        # Quality LCD
        self.quality_lcd_layout = QVBoxLayout()
        self.quality_lcd = QLCDNumber()
        self.quality_lcd.setDigitCount(3)
        self.quality_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.quality_lcd.setStyleSheet("background-color: #f0f0f0;")
        self.quality_lcd_label = QLabel("Качество сигнала (%)")
        self.quality_lcd_label.setAlignment(Qt.AlignCenter)
        
        self.quality_lcd_layout.addWidget(self.quality_lcd)
        self.quality_lcd_layout.addWidget(self.quality_lcd_label)
        
        # Status display
        self.status_layout = QVBoxLayout()
        self.laser_status_label = QLabel("Лазер: Выкл")
        self.measurement_status_label = QLabel("Измерение: Остановлено")
        self.data_count_label = QLabel("Кол-во измерений: 0")
        
        self.status_layout.addWidget(self.laser_status_label)
        self.status_layout.addWidget(self.measurement_status_label)
        self.status_layout.addWidget(self.data_count_label)
        self.status_layout.addStretch(1)
        
        # Add layouts to display group
        self.display_layout.addLayout(self.distance_lcd_layout)
        self.display_layout.addLayout(self.quality_lcd_layout)
        self.display_layout.addLayout(self.status_layout)
        
        # Add display group to main layout
        self.main_layout.addWidget(self.display_group)
        
        # Create results table group
        self.results_group = QGroupBox("История измерений")
        self.results_layout = QVBoxLayout()
        self.results_group.setLayout(self.results_layout)
        
        # Results table
        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Время", "Расстояние (м)", "Качество (%)"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.results_layout.addWidget(self.results_table)
        
        # Add results group to main layout
        self.main_layout.addWidget(self.results_group)
        
        # Добавляем интеграцию с АОЯ, если контроллер предоставлен
        if self.aod_controller:
            self.setup_aod_integration()
        
        # Connect signals
        self.connect_signals()
    
    def setup_aod_integration(self):
        """Настройка интеграции с акустооптической ячейкой"""
        # Создаем группу для АОЯ
        self.aod_group = QGroupBox("Сканирование с АОЯ")
        self.aod_layout = QVBoxLayout()
        self.aod_group.setLayout(self.aod_layout)
        
        # Информация о состоянии АОЯ
        self.aod_status_label = QLabel("Статус АОЯ: Не подключено")
        self.aod_layout.addWidget(self.aod_status_label)
        
        # Создаем элементы управления для АОЯ
        pattern_layout = QHBoxLayout()
        pattern_label = QLabel("Шаблон сканирования:")
        self.pattern_combo = QComboBox()
        
        # Заполняем список шаблонов
        patterns = self.aod_controller.get_available_patterns()
        for pattern_id, pattern_data in patterns.items():
            self.pattern_combo.addItem(pattern_data['name'], pattern_id)
        
        pattern_layout.addWidget(pattern_label)
        pattern_layout.addWidget(self.pattern_combo)
        
        # Кнопки управления сканированием
        button_layout = QHBoxLayout()
        self.scan_aod_button = QPushButton("Запустить сканирование с АОЯ")
        self.stop_aod_button = QPushButton("Остановить сканирование АОЯ")
        self.stop_aod_button.setEnabled(False)
        
        button_layout.addWidget(self.scan_aod_button)
        button_layout.addWidget(self.stop_aod_button)
        
        # Добавляем макеты в группу
        self.aod_layout.addLayout(pattern_layout)
        self.aod_layout.addLayout(button_layout)
        
        # Добавляем группу в основной макет
        self.main_layout.addWidget(self.aod_group)
        
        # Подключаем сигналы
        self.scan_aod_button.clicked.connect(self.start_aod_scanning)
        self.stop_aod_button.clicked.connect(self.stop_aod_scanning)
        
        # Подключаем сигналы от контроллера АОЯ
        self.aod_controller.connection_changed.connect(self.on_aod_connection_changed)
        self.aod_controller.scan_started.connect(self.on_aod_scan_started)
        self.aod_controller.scan_stopped.connect(self.on_aod_scan_stopped)
        
        # Обновляем состояние подключения
        self.update_aod_status()
    
    def connect_signals(self):
        """Подключение сигналов"""
        # Mode selection
        self.single_mode_radio.toggled.connect(self.on_mode_changed)
        self.continuous_mode_radio.toggled.connect(self.on_mode_changed)
    
        # Button actions
        self.measure_button.clicked.connect(self.on_measure)
        self.stop_button.clicked.connect(self.on_stop_measurement)
        self.reset_button.clicked.connect(self.on_reset_data)
    
        # Sensor controller signals
        self.sensor_controller.measurement_taken.connect(self.on_measurement_taken)
    
        # Data controller signals
        self.data_controller.data_updated.connect(self.on_data_updated)
    
        # Status timer
        self.status_timer.timeout.connect(self.update_sensor_status)
    
    def start_aod_scanning(self):
        """Запускает сканирование с использованием АОЯ"""
        if not self.aod_controller or not self.aod_controller.is_connected():
            QMessageBox.warning(self, "Ошибка", "АОЯ не подключена.")
            return
        
        if not self.sensor_controller.serial_handler.is_connected:
            QMessageBox.warning(self, "Ошибка", "Датчик LiDAR не подключен.")
            return
        
        pattern_id = self.pattern_combo.currentData()
        if not pattern_id:
            return
        
        # Запускаем непрерывное измерение на лидаре
        if not self.continuous_mode_radio.isChecked():
            self.continuous_mode_radio.setChecked(True)
        
        # Если измерение уже запущено, продолжаем; если нет - запускаем
        if self.stop_button.isEnabled():
            # Уже запущено
            pass
        else:
            self.on_measure()
        
        # Запускаем сканирование на АОЯ
        self.aod_controller.start_pattern(pattern_id)
    
    def stop_aod_scanning(self):
        """Останавливает сканирование с использованием АОЯ"""
        # Останавливаем сканирование на АОЯ
        if self.aod_controller:
            self.aod_controller.stop_pattern()
        
        # Останавливаем измерение на лидаре
        self.on_stop_measurement()
    
    def update_aod_status(self):
        """Обновляет отображение статуса АОЯ"""
        if not self.aod_controller:
            return
        
        is_connected = self.aod_controller.is_connected()
        is_scanning = self.aod_controller.is_scanning()
        
        status_text = "Статус АОЯ: "
        if is_connected:
            if is_scanning:
                pattern_name = self.pattern_combo.currentText()
                status_text += f"Подключено, сканирование ({pattern_name})"
            else:
                status_text += "Подключено, ожидание"
        else:
            status_text += "Не подключено"
        
        self.aod_status_label.setText(status_text)
        self.scan_aod_button.setEnabled(is_connected and not is_scanning)
        self.stop_aod_button.setEnabled(is_connected and is_scanning)
    
    @pyqtSlot(bool)
    def on_aod_connection_changed(self, connected):
        """Обработчик изменения статуса подключения АОЯ"""
        self.update_aod_status()
    
    @pyqtSlot(str)
    def on_aod_scan_started(self, pattern_id):
        """Обработчик начала сканирования на АОЯ"""
        self.scan_aod_button.setEnabled(False)
        self.stop_aod_button.setEnabled(True)
        self.update_aod_status()
    
    @pyqtSlot()
    def on_aod_scan_stopped(self):
        """Обработчик окончания сканирования на АОЯ"""
        self.scan_aod_button.setEnabled(True)
        self.stop_aod_button.setEnabled(False)
        self.update_aod_status()
    
    @pyqtSlot(bool)
    def on_mode_changed(self, checked):
        """Обработчик изменения режима измерения"""
        if checked:
            # Enable/disable rate combo box based on mode
            self.rate_combo.setEnabled(self.continuous_mode_radio.isChecked())
    
    @pyqtSlot()
    def on_measure(self):
        """Обработчик нажатия кнопки измерения"""
        if not self.sensor_controller.serial_handler.is_connected:
            QMessageBox.warning(self, "Ошибка", "Датчик не подключен.")
            return
        
        if self.single_mode_radio.isChecked():
            # Single measurement
            self.measure_button.setEnabled(False)
            result = self.sensor_controller.get_single_measurement()
            self.measure_button.setEnabled(True)
            
            if not result:
                QMessageBox.warning(self, "Ошибка", "Не удалось выполнить измерение.")
        else:
            # Continuous measurement
            rate_mode = self.rate_combo.currentText()
            if rate_mode == "Быстро":
                measurement_type = "fast"
            elif rate_mode == "Медленно":
                measurement_type = "slow"
            else:
                measurement_type = "auto"
                
            self.sensor_controller.start_continuous_measurement(measurement_type)
            
            # Update UI
            self.measure_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_timer.start()
            self.laser_status_label.setText("Лазер: Вкл")
            self.measurement_status_label.setText("Измерение: Активно")
    
    @pyqtSlot()
    def on_stop_measurement(self):
        """Обработчик нажатия кнопки остановки измерения"""
        self.sensor_controller.stop_continuous_measurement()
        
        # Update UI
        self.measure_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_timer.stop()
        self.laser_status_label.setText("Лазер: Выкл")
        self.measurement_status_label.setText("Измерение: Остановлено")
    
    @pyqtSlot()
    def on_reset_data(self):
        """Обработчик нажатия кнопки сброса данных"""
        self.data_controller.clear_data()
        self.results_table.setRowCount(0)
        self.data_count_label.setText("Кол-во измерений: 0")
        self.distance_lcd.display(0.0)
        self.quality_lcd.display(0)
    
    @pyqtSlot(float, int)
    def on_measurement_taken(self, distance, quality):
        """Обработчик получения нового измерения"""
        # Add measurement to data controller
        self.data_controller.add_measurement(distance, quality)
        
        # Update LCD displays
        self.distance_lcd.display(distance)
        self.quality_lcd.display(quality)
    
    @pyqtSlot()
    def update_sensor_status(self):
        """Обновление статуса датчика"""
        # Запрашиваем обновление статуса у контроллера
        self.sensor_controller.get_sensor_status()
    
    @pyqtSlot()
    def on_data_updated(self):
        """Обработчик обновления данных"""
        # Get latest measurements
        measurements = self.data_controller.model.measurements
        
        # Update data count label
        count = len(measurements)
        self.data_count_label.setText(f"Кол-во измерений: {count}")
        
        # Update results table
        self.results_table.setRowCount(count)
        
        # Add new rows to table
        for i, (timestamp, distance, quality) in enumerate(reversed(measurements)):
            row = count - i - 1
            
            # Convert timestamp to readable time
            time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
            
            # Create table items
            time_item = QTableWidgetItem(time_str)
            distance_item = QTableWidgetItem(f"{distance:.3f}")
            quality_item = QTableWidgetItem(f"{quality}")
            
            # Set items to table
            self.results_table.setItem(row, 0, time_item)
            self.results_table.setItem(row, 1, distance_item)
            self.results_table.setItem(row, 2, quality_item)
        
        # Scroll to the latest measurement
        if count > 0:
            self.results_table.scrollToBottom()