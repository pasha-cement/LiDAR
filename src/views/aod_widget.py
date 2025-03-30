from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QComboBox, QGroupBox, QSlider,
                           QDoubleSpinBox, QFormLayout, QTabWidget,
                           QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer

class AODWidget(QWidget):
    def __init__(self, aod_controller):
        super().__init__()
        
        self.aod_controller = aod_controller
        
        # Инициализируем таймеры до их использования
        self.angle_update_timer = QTimer()
        self.angle_update_timer.setInterval(500)  # 500 мс
        
        # Настройка макета
        self.main_layout = QVBoxLayout(self)
        
        # Создаем табы для разных функций
        self.tab_widget = QTabWidget()
        
        # Создаем вкладки
        self.connection_tab = self.create_connection_tab()
        self.manual_control_tab = self.create_manual_control_tab()
        self.scan_patterns_tab = self.create_scan_patterns_tab()
        
        # Добавляем вкладки
        self.tab_widget.addTab(self.connection_tab, "Подключение")
        self.tab_widget.addTab(self.manual_control_tab, "Ручное управление")
        self.tab_widget.addTab(self.scan_patterns_tab, "Шаблоны сканирования")
        
        # Добавляем табы в основной макет
        self.main_layout.addWidget(self.tab_widget)
        
        # Подключаем сигналы таймера
        self.angle_update_timer.timeout.connect(self.update_current_angle)
        
        # Подключаем остальные сигналы
        self.connect_signals()
        
        # Инициализация портов
        self.refresh_ports()
        
        # Обновляем UI на основе состояния
        self.update_ui_state()
    
    def create_connection_tab(self):
        """Создает вкладку подключения к AOD"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Группа подключения
        connection_group = QGroupBox("Подключение AOD")
        connection_layout = QVBoxLayout()
        
        # Выбор порта
        port_layout = QHBoxLayout()
        port_label = QLabel("COM-порт:")
        self.port_combo = QComboBox()
        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.refresh_ports)
        
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_combo)
        port_layout.addWidget(refresh_button)
        
        # Кнопки подключения/отключения
        buttons_layout = QHBoxLayout()
        self.connect_button = QPushButton("Подключить")
        self.disconnect_button = QPushButton("Отключить")
        self.disconnect_button.setEnabled(False)
        
        buttons_layout.addWidget(self.connect_button)
        buttons_layout.addWidget(self.disconnect_button)
        
        connection_layout.addLayout(port_layout)
        connection_layout.addLayout(buttons_layout)
        connection_group.setLayout(connection_layout)
        
        # Состояние устройства
        status_group = QGroupBox("Состояние устройства")
        status_layout = QFormLayout()
        
        self.connection_status_label = QLabel("Не подключено")
        self.current_angle_label = QLabel("0.0°")
        self.scanning_status_label = QLabel("Нет")
        
        status_layout.addRow("Статус подключения:", self.connection_status_label)
        status_layout.addRow("Текущий угол:", self.current_angle_label)
        status_layout.addRow("Сканирование:", self.scanning_status_label)
        
        status_group.setLayout(status_layout)
        
        # Добавляем группы в макет вкладки
        layout.addWidget(connection_group)
        layout.addWidget(status_group)
        layout.addStretch(1)
        
        return widget
    
    def create_manual_control_tab(self):
        """Создает вкладку для ручного управления AOD"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Группа управления углом
        angle_group = QGroupBox("Угол отклонения")
        angle_layout = QVBoxLayout()
        
        # Слайдер угла
        slider_layout = QHBoxLayout()
        slider_min_label = QLabel("-0.8°")
        self.angle_slider = QSlider(Qt.Horizontal)
        self.angle_slider.setMinimum(-80)  # -0.8 градуса * 100
        self.angle_slider.setMaximum(80)   # 0.8 градуса * 100
        self.angle_slider.setValue(0)
        self.angle_slider.setTickPosition(QSlider.TicksBelow)
        self.angle_slider.setTickInterval(10)
        slider_max_label = QLabel("0.8°")
        
        slider_layout.addWidget(slider_min_label)
        slider_layout.addWidget(self.angle_slider)
        slider_layout.addWidget(slider_max_label)
        
        # SpinBox для точного ввода угла
        spinbox_layout = QHBoxLayout()
        self.angle_spinbox = QDoubleSpinBox()
        self.angle_spinbox.setMinimum(-0.8)
        self.angle_spinbox.setMaximum(0.8)
        self.angle_spinbox.setValue(0.0)
        self.angle_spinbox.setSingleStep(0.1)
        self.angle_spinbox.setDecimals(2)
        set_angle_button = QPushButton("Установить угол")
        
        spinbox_layout.addWidget(QLabel("Угол (градусы):"))
        spinbox_layout.addWidget(self.angle_spinbox)
        spinbox_layout.addWidget(set_angle_button)
        
        angle_layout.addLayout(slider_layout)
        angle_layout.addLayout(spinbox_layout)
        angle_group.setLayout(angle_layout)
        
        # Предустановленные углы
        preset_group = QGroupBox("Предустановленные углы")
        preset_layout = QHBoxLayout()
        
        for angle in [-0.8, -0.4, 0.0, 0.4, 0.8]:
            button = QPushButton(f"{angle}°")
            button.clicked.connect(lambda checked, a=angle: self.set_preset_angle(a))
            preset_layout.addWidget(button)
        
        preset_group.setLayout(preset_layout)
        
        # Добавляем группы в макет вкладки
        layout.addWidget(angle_group)
        layout.addWidget(preset_group)
        layout.addStretch(1)
        
        # Подключаем сигналы
        self.angle_slider.valueChanged.connect(self.on_slider_changed)
        self.angle_spinbox.valueChanged.connect(self.on_spinbox_changed)
        set_angle_button.clicked.connect(self.on_set_angle)
        
        return widget
    
    def create_scan_patterns_tab(self):
        """Создает вкладку для управления шаблонами сканирования"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Выбор шаблона
        pattern_group = QGroupBox("Шаблон сканирования")
        pattern_layout = QFormLayout()
        
        self.pattern_combo = QComboBox()
        self.update_pattern_combo()
        
        pattern_layout.addRow("Выбрать шаблон:", self.pattern_combo)
        pattern_group.setLayout(pattern_layout)
        
        # Параметры текущего шаблона
        params_group = QGroupBox("Параметры шаблона")
        self.params_layout = QFormLayout()
        params_group.setLayout(self.params_layout)
        
        # Кнопки управления сканированием
        buttons_layout = QHBoxLayout()
        self.start_scan_button = QPushButton("Запустить сканирование")
        self.stop_scan_button = QPushButton("Остановить сканирование")
        self.stop_scan_button.setEnabled(False)
        
        buttons_layout.addWidget(self.start_scan_button)
        buttons_layout.addWidget(self.stop_scan_button)
        
        # Добавляем группы в макет вкладки
        layout.addWidget(pattern_group)
        layout.addWidget(params_group)
        layout.addLayout(buttons_layout)
        layout.addStretch(1)
        
        # Подключаем сигналы
        self.pattern_combo.currentIndexChanged.connect(self.on_pattern_changed)
        self.start_scan_button.clicked.connect(self.on_start_scan)
        self.stop_scan_button.clicked.connect(self.on_stop_scan)
        
        return widget
    
    def connect_signals(self):
        """Подключение сигналов"""
        # Подключаем сигналы кнопок вкладки "Подключение"
        self.connect_button.clicked.connect(self.on_connect)
        self.disconnect_button.clicked.connect(self.on_disconnect)
        
        # Подключаем сигналы от контроллера AOD
        self.aod_controller.connection_changed.connect(self.on_connection_changed)
        self.aod_controller.angle_changed.connect(self.on_angle_changed)
        self.aod_controller.scan_started.connect(self.on_scan_started)
        self.aod_controller.scan_stopped.connect(self.on_scan_stopped)
        self.aod_controller.error_occurred.connect(self.on_error)
    
    def refresh_ports(self):
        """Обновляет список доступных COM-портов"""
        current_port = self.port_combo.currentText()
        self.port_combo.clear()
        ports = self.aod_controller.get_available_ports()
        self.port_combo.addItems(ports)
        
        # Восстанавливаем прежний выбранный порт, если он все еще доступен
        if current_port and current_port in ports:
            self.port_combo.setCurrentText(current_port)
    
    def update_pattern_combo(self):
        """Обновляет список доступных шаблонов сканирования"""
        self.pattern_combo.clear()
        patterns = self.aod_controller.get_available_patterns()
        
        for pattern_id, pattern_data in patterns.items():
            self.pattern_combo.addItem(pattern_data['name'], pattern_id)
    
    def update_ui_state(self):
        """Обновляет состояние UI в зависимости от состояния подключения"""
        is_connected = self.aod_controller.is_connected()
        is_scanning = self.aod_controller.is_scanning()
        
        # Обновляем кнопки подключения
        self.connect_button.setEnabled(not is_connected)
        self.disconnect_button.setEnabled(is_connected)
        
        # Обновляем доступность вкладок
        self.manual_control_tab.setEnabled(is_connected)
        self.scan_patterns_tab.setEnabled(is_connected)
        
        # Обновляем состояние кнопок сканирования
        self.start_scan_button.setEnabled(is_connected and not is_scanning)
        self.stop_scan_button.setEnabled(is_connected and is_scanning)
        
        # Обновляем метки состояния
        self.connection_status_label.setText("Подключено" if is_connected else "Не подключено")
        self.scanning_status_label.setText("Активно" if is_scanning else "Нет")
        
        # Обновляем таймер
        if is_connected:
            if not self.angle_update_timer.isActive():
                self.angle_update_timer.start()
        else:
            if self.angle_update_timer.isActive():
                self.angle_update_timer.stop()
    
    def update_pattern_params(self, pattern_id):
        """Обновляет форму параметров для выбранного шаблона"""
        # Очищаем текущие элементы макета параметров
        while self.params_layout.rowCount() > 0:
            self.params_layout.removeRow(0)
        
        pattern_data = self.aod_controller.get_available_patterns().get(pattern_id)
        if not pattern_data:
            return
            
        # Создаем спинбоксы для всех параметров шаблона
        self.param_widgets = {}
        for param_name, param_value in pattern_data['params'].items():
            spinbox = QDoubleSpinBox()
            spinbox.setMinimum(-5.0)  # Предельные значения для параметров
            spinbox.setMaximum(5.0)
            spinbox.setValue(param_value)
            spinbox.setSingleStep(0.1)
            spinbox.setDecimals(2)
            
            # Специальная настройка для разных параметров
            if 'angle' in param_name:
                spinbox.setMinimum(-0.8)
                spinbox.setMaximum(0.8)
            elif 'speed' in param_name:
                spinbox.setMinimum(0.01)
                spinbox.setMaximum(1.0)
            elif 'steps' in param_name:
                spinbox.setDecimals(0)
                spinbox.setMinimum(2)
                spinbox.setMaximum(100)
            
            # Преобразуем имя параметра для отображения
            display_name = param_name.replace('_', ' ').title()
            self.params_layout.addRow(f"{display_name}:", spinbox)
            self.param_widgets[param_name] = spinbox
    
    def update_current_angle(self):
        """Обновляет отображение текущего угла"""
        if self.aod_controller.is_connected():
            angle = self.aod_controller.get_current_angle()
            self.current_angle_label.setText(f"{angle:.2f}°")
    
    def set_preset_angle(self, angle):
        """Устанавливает предустановленный угол"""
        self.angle_spinbox.setValue(angle)
        self.on_set_angle()
    
    # Обработчики событий UI
    def on_slider_changed(self, value):
        """Обработчик изменения слайдера угла"""
        # Конвертируем значение слайдера (целое) в угол (с плавающей точкой)
        angle = value / 100.0
        # Обновляем спинбокс, не вызывая циклических изменений
        self.angle_spinbox.blockSignals(True)
        self.angle_spinbox.setValue(angle)
        self.angle_spinbox.blockSignals(False)
        
    def on_spinbox_changed(self, value):
        """Обработчик изменения спинбокса угла"""
        # Обновляем слайдер, не вызывая циклических изменений
        self.angle_slider.blockSignals(True)
        self.angle_slider.setValue(int(value * 100))
        self.angle_slider.blockSignals(False)
    
    def on_set_angle(self):
        """Обработчик нажатия кнопки установки угла"""
        angle = self.angle_spinbox.value()
        self.aod_controller.set_angle(angle)
    
    def on_connect(self):
        """Обработчик нажатия кнопки подключения"""
        port = self.port_combo.currentText()
        if not port:
            self.on_error("Не выбран COM-порт для подключения.")
            return
            
        self.aod_controller.connect_aod(port)
    
    def on_disconnect(self):
        """Обработчик нажатия кнопки отключения"""
        self.aod_controller.disconnect_aod()
    
    def on_pattern_changed(self, index):
        """Обработчик изменения выбранного шаблона сканирования"""
        pattern_id = self.pattern_combo.currentData()
        if pattern_id:
            self.update_pattern_params(pattern_id)
    
    def on_start_scan(self):
        """Обработчик нажатия кнопки запуска сканирования"""
        pattern_id = self.pattern_combo.currentData()
        if not pattern_id:
            return
            
        # Собираем текущие значения параметров
        params = {}
        for param_name, widget in self.param_widgets.items():
            params[param_name] = widget.value()
            
        self.aod_controller.start_pattern(pattern_id, params)
    
    def on_stop_scan(self):
        """Обработчик нажатия кнопки остановки сканирования"""
        self.aod_controller.stop_pattern()
    
    # Обработчики сигналов от контроллера AOD
    @pyqtSlot(bool)
    def on_connection_changed(self, connected):
        """Обработчик изменения статуса подключения"""
        self.update_ui_state()
    
    @pyqtSlot(float)
    def on_angle_changed(self, angle):
        """Обработчик изменения угла"""
        # Обновляем только если значение отличается от текущего
        current_angle = self.angle_spinbox.value()
        if abs(current_angle - angle) > 0.01:
            # Обновляем виджеты без вызова обратных сигналов
            self.angle_spinbox.blockSignals(True)
            self.angle_slider.blockSignals(True)
            
            self.angle_spinbox.setValue(angle)
            self.angle_slider.setValue(int(angle * 100))
            
            self.angle_spinbox.blockSignals(False)
            self.angle_slider.blockSignals(False)
        
        self.current_angle_label.setText(f"{angle:.2f}°")
    
    @pyqtSlot(str)
    def on_scan_started(self, pattern_id):
        """Обработчик начала сканирования"""
        self.scanning_status_label.setText(f"Активно ({self.pattern_combo.currentText()})")
        self.update_ui_state()
    
    @pyqtSlot()
    def on_scan_stopped(self):
        """Обработчик окончания сканирования"""
        self.scanning_status_label.setText("Нет")
        self.update_ui_state()
    
    @pyqtSlot(str)
    def on_error(self, error_message):
        """Обработчик ошибок"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Ошибка AOD", error_message)