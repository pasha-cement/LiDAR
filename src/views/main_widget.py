from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QPushButton, QComboBox, QGroupBox,
                           QFormLayout, QMessageBox, QSplitter,
                           QRadioButton, QButtonGroup, QLCDNumber,
                           QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
import time
import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from ..config.settings import PLOT_SETTINGS

class PlotCanvas(FigureCanvas):
    """Класс для встраивания графика Matplotlib в PyQt."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                  QSizePolicy.Expanding,
                                  QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.axes.set_xlabel("Номер измерения")
        self.axes.set_ylabel("Расстояние (м)")
        self.axes.grid(True)

class MainWidget(QWidget):
    def __init__(self, sensor_controller, data_controller):
        super().__init__()

        self.sensor_controller = sensor_controller
        self.data_controller = data_controller

        self.main_layout = QVBoxLayout(self)

        self.splitter = QSplitter(Qt.Vertical)
        self.main_layout.addWidget(self.splitter)

        self.connection_info_widget = QWidget()
        self.connection_info_layout = QHBoxLayout(self.connection_info_widget)
        self.connection_info_layout.setContentsMargins(0,0,0,0)

        self.connection_group = QGroupBox("Подключение")
        self.connection_box_layout = QVBoxLayout()
        self.connection_group.setLayout(self.connection_box_layout)

        self.port_layout = QHBoxLayout()
        self.port_label = QLabel("COM-порт:")
        self.port_combo = QComboBox()
        self.refresh_ports_button = QPushButton("Обновить")

        self.port_layout.addWidget(self.port_label)
        self.port_layout.addWidget(self.port_combo)
        self.port_layout.addWidget(self.refresh_ports_button)
        self.connection_box_layout.addLayout(self.port_layout)

        self.conn_buttons_layout = QHBoxLayout()
        self.connect_button = QPushButton("Подключить")
        self.disconnect_button = QPushButton("Отключить")
        self.disconnect_button.setEnabled(False)

        self.conn_buttons_layout.addWidget(self.connect_button)
        self.conn_buttons_layout.addWidget(self.disconnect_button)
        self.conn_buttons_layout.addStretch(1)
        self.connection_box_layout.addLayout(self.conn_buttons_layout)

        self.laser_button_layout = QHBoxLayout()
        self.laser_button = QPushButton("Включить лазер")
        self.laser_button.setEnabled(False)
        self.laser_button.setCheckable(True)
        self.laser_button_layout.addWidget(self.laser_button)
        self.laser_button_layout.addStretch(1)
        self.connection_box_layout.addLayout(self.laser_button_layout)

        self.connection_info_layout.addWidget(self.connection_group)

        self.info_group = QGroupBox("Информация")
        self.info_layout = QFormLayout()
        self.info_group.setLayout(self.info_layout)

        self.connection_status_label = QLabel("Не подключено")
        self.temperature_label = QLabel("Н/Д")
        self.voltage_label = QLabel("Н/Д")

        self.info_layout.addRow("Статус:", self.connection_status_label)
        self.info_layout.addRow("Температура:", self.temperature_label)
        self.info_layout.addRow("Напряжение:", self.voltage_label)

        self.connection_info_layout.addWidget(self.info_group)

        self.splitter.addWidget(self.connection_info_widget)

        self.measurement_widget = QWidget()
        self.measurement_layout = QVBoxLayout(self.measurement_widget)

        self.control_group = QGroupBox("Настройка")
        self.control_layout = QVBoxLayout()
        self.control_group.setLayout(self.control_layout)

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

        self.rate_layout = QHBoxLayout()
        self.rate_label = QLabel("Скорость измерений:")
        self.rate_combo = QComboBox()
        self.rate_combo.addItems(["Авто", "Быстро", "Медленно"])
        self.rate_combo.setEnabled(False)

        self.rate_layout.addWidget(self.rate_label)
        self.rate_layout.addWidget(self.rate_combo)
        self.rate_layout.addStretch(1)
        self.control_layout.addLayout(self.rate_layout)

        self.measure_buttons_layout = QHBoxLayout()
        self.measure_button = QPushButton("Измерить")
        self.stop_button = QPushButton("Остановить")
        self.stop_button.setEnabled(False)
        self.reset_button = QPushButton("Очистить данные")
        self.measure_button.setEnabled(False)
        self.reset_button.setEnabled(False)

        self.measure_buttons_layout.addWidget(self.measure_button)
        self.measure_buttons_layout.addWidget(self.stop_button)
        self.measure_buttons_layout.addWidget(self.reset_button)
        self.control_layout.addLayout(self.measure_buttons_layout)

        self.measurement_layout.addWidget(self.control_group)

        self.display_group = QGroupBox("Измерение")
        self.display_layout = QHBoxLayout()
        self.display_group.setLayout(self.display_layout)

        self.distance_lcd_layout = QVBoxLayout()
        self.distance_lcd = QLCDNumber()
        self.distance_lcd.setDigitCount(6)
        self.distance_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.distance_lcd.setStyleSheet("background-color: #f0f0f0;")
        self.distance_lcd_label = QLabel("Расстояние (м)")
        self.distance_lcd_label.setAlignment(Qt.AlignCenter)

        self.distance_lcd_layout.addWidget(self.distance_lcd)
        self.distance_lcd_layout.addWidget(self.distance_lcd_label)

        self.quality_lcd_layout = QVBoxLayout()
        self.quality_lcd = QLCDNumber()
        self.quality_lcd.setDigitCount(3)
        self.quality_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.quality_lcd.setStyleSheet("background-color: #f0f0f0;")
        self.quality_lcd_label = QLabel("Качество сигнала (%)")
        self.quality_lcd_label.setAlignment(Qt.AlignCenter)

        self.quality_lcd_layout.addWidget(self.quality_lcd)
        self.quality_lcd_layout.addWidget(self.quality_lcd_label)

        self.count_lcd_layout = QVBoxLayout()
        self.count_lcd = QLCDNumber()
        self.count_lcd.setDigitCount(4)
        self.count_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.count_lcd.setStyleSheet("background-color: #f0f0f0;")
        self.count_lcd_label = QLabel("Кол-во измерений")
        self.count_lcd_label.setAlignment(Qt.AlignCenter)

        self.count_lcd_layout.addWidget(self.count_lcd)
        self.count_lcd_layout.addWidget(self.count_lcd_label)

        self.display_layout.addLayout(self.distance_lcd_layout)
        self.display_layout.addLayout(self.quality_lcd_layout)
        self.display_layout.addLayout(self.count_lcd_layout)

        self.measurement_layout.addWidget(self.display_group)

        self.data_display_layout = QHBoxLayout()

        self.plot_group = QGroupBox("График расстояния")
        self.plot_layout = QVBoxLayout()
        self.plot_group.setLayout(self.plot_layout)

        self.plot_canvas = PlotCanvas(self)
        self.plot_layout.addWidget(self.plot_canvas)

        self.data_display_layout.addWidget(self.plot_group)

        self.results_group = QGroupBox("История")
        self.results_layout = QVBoxLayout()
        self.results_group.setLayout(self.results_layout)

        self.results_table = QTableWidget(0, 3)
        self.results_table.setHorizontalHeaderLabels(["Время", "Расстояние (м)", "Качество (%)"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.results_layout.addWidget(self.results_table)

        self.data_display_layout.addWidget(self.results_group)

        self.measurement_layout.addLayout(self.data_display_layout)

        self.splitter.addWidget(self.measurement_widget)

        self.splitter.setSizes([150, 650])

        self.connection_status_timer = QTimer()
        self.connection_status_timer.setInterval(5000)

        self.refresh_ports()

        self.connect_signals()

    def connect_signals(self):
        """Подключение сигналов"""
        self.refresh_ports_button.clicked.connect(self.refresh_ports)
        self.connect_button.clicked.connect(self.on_connect)
        self.disconnect_button.clicked.connect(self.on_disconnect)
        self.laser_button.clicked.connect(self.on_toggle_laser)

        self.sensor_controller.connection_changed.connect(self.on_connection_changed)
        self.sensor_controller.status_updated.connect(self.on_status_updated)
        if hasattr(self.sensor_controller, 'laser_state_changed'):
            self.sensor_controller.laser_state_changed.connect(self.on_laser_state_changed)
        else:
            print("Warning: SensorController does not have 'laser_state_changed' signal.")


        self.connection_status_timer.timeout.connect(self.update_sensor_status)

        self.single_mode_radio.toggled.connect(self.on_mode_changed)
        self.continuous_mode_radio.toggled.connect(self.on_mode_changed)

        self.measure_button.clicked.connect(self.on_measure)
        self.stop_button.clicked.connect(self.on_stop_measurement)
        self.reset_button.clicked.connect(self.on_reset_data)

        self.sensor_controller.measurement_taken.connect(self.on_measurement_taken)

        self.data_controller.data_updated.connect(self.on_data_updated)

    def refresh_ports(self):
        """Обновление списка доступных портов"""
        current_port = self.port_combo.currentText()
        ports = self.sensor_controller.get_available_ports()

        self.port_combo.clear()
        self.port_combo.addItems(ports)

        if current_port in ports:
            self.port_combo.setCurrentText(current_port)

    @pyqtSlot()
    def on_connect(self):
        """Обработчик нажатия кнопки подключения"""
        port = self.port_combo.currentText()
        if not port:
            QMessageBox.warning(self, "Ошибка", "Не выбран COM-порт")
            return

        success = self.sensor_controller.connect_sensor(port)
        if success:
            if hasattr(self.sensor_controller, 'get_laser_state'):
                self.sensor_controller.get_laser_state()
            self.connection_status_timer.start()

    @pyqtSlot()
    def on_disconnect(self):
        """Обработчик нажатия кнопки отключения"""
        self.connection_status_timer.stop()
        if self.stop_button.isEnabled():
            self.on_stop_measurement()
        success = self.sensor_controller.disconnect_sensor()
        if not success:
            QMessageBox.warning(self, "Ошибка", "Не удалось отключиться от датчика")

    @pyqtSlot(bool)
    def on_connection_changed(self, connected):
        """Обработчик изменения статуса подключения"""
        self.connect_button.setEnabled(not connected)
        self.disconnect_button.setEnabled(connected)
        self.connection_status_label.setText("Подключено" if connected else "Не подключено")

        self.laser_button.setEnabled(connected)
        if not connected:
            self.laser_button.setChecked(False)
            self.laser_button.setText("Включить лазер")

        self.measure_button.setEnabled(connected)
        self.reset_button.setEnabled(connected and not self.stop_button.isEnabled())

        if not connected:
            self.temperature_label.setText("Н/Д")
            self.voltage_label.setText("Н/Д")
            self.connection_status_timer.stop()
            if self.stop_button.isEnabled():
                 self.on_stop_measurement()
            else:
                 self.reset_button.setEnabled(False)
            self.measure_button.setEnabled(False)
            self.stop_button.setEnabled(False)

    @pyqtSlot(float, float)
    def on_status_updated(self, temperature, voltage):
        """Обработчик обновления статуса датчика"""
        self.temperature_label.setText(f"{temperature:.1f}°C")
        self.voltage_label.setText(f"{voltage:.2f} В")

    @pyqtSlot()
    def update_sensor_status(self):
        """Запрос обновления статуса датчика"""
        if self.sensor_controller.serial_handler.is_connected:
            self.sensor_controller.get_sensor_status()
            if hasattr(self.sensor_controller, 'get_laser_state'):
                self.sensor_controller.get_laser_state()

    @pyqtSlot(bool)
    def on_laser_state_changed(self, is_on):
        """Обработчик изменения состояния лазера"""
        self.laser_button.setChecked(is_on)
        self.laser_button.setText("Выключить лазер" if is_on else "Включить лазер")

    @pyqtSlot()
    def on_toggle_laser(self):
        """Обработчик нажатия кнопки управления лазером"""
        if not self.sensor_controller.serial_handler.is_connected:
            QMessageBox.warning(self, "Ошибка", "Датчик не подключен.")
            self.laser_button.setChecked(not self.laser_button.isChecked())
            return

        if hasattr(self.sensor_controller, 'toggle_laser'):
            self.sensor_controller.toggle_laser()
        else:
            QMessageBox.warning(self, "Ошибка", "Функция управления лазером не поддерживается.")
            self.laser_button.setChecked(not self.laser_button.isChecked())

    @pyqtSlot(bool)
    def on_mode_changed(self, checked):
        """Обработчик изменения режима измерения"""
        if checked:
            is_continuous = self.continuous_mode_radio.isChecked()
            self.rate_combo.setEnabled(is_continuous)
            is_measuring = self.stop_button.isEnabled()
            self.single_mode_radio.setEnabled(not is_measuring)
            self.continuous_mode_radio.setEnabled(not is_measuring)
            self.rate_combo.setEnabled(is_continuous and not is_measuring)

    @pyqtSlot()
    def on_measure(self):
        """Обработчик нажатия кнопки измерения"""
        if not self.sensor_controller.serial_handler.is_connected:
            QMessageBox.warning(self, "Ошибка", "Датчик не подключен.")
            return

        self.connection_status_timer.stop()
        self.reset_button.setEnabled(False)
        self.single_mode_radio.setEnabled(False)
        self.continuous_mode_radio.setEnabled(False)
        self.rate_combo.setEnabled(False)
        self.laser_button.setEnabled(False)

        if self.single_mode_radio.isChecked():
            self.measure_button.setEnabled(False)
            result = self.sensor_controller.get_single_measurement()
            self.measure_button.setEnabled(True)
            self.reset_button.setEnabled(True)
            self.single_mode_radio.setEnabled(True)
            self.continuous_mode_radio.setEnabled(True)
            self.rate_combo.setEnabled(self.continuous_mode_radio.isChecked())
            self.laser_button.setEnabled(True)

            self.connection_status_timer.start()

            if not result or result[0] is None:
                QMessageBox.warning(self, "Ошибка", "Не удалось выполнить измерение.")
        else:
            rate_mode = self.rate_combo.currentText()
            if rate_mode == "Быстро":
                measurement_type = "fast"
            elif rate_mode == "Медленно":
                measurement_type = "slow"
            else:
                measurement_type = "auto"

            self.sensor_controller.start_continuous_measurement(measurement_type)

            self.measure_button.setEnabled(False)
            self.stop_button.setEnabled(True)

    @pyqtSlot()
    def on_stop_measurement(self):
        """Обработчик нажатия кнопки остановки измерения"""
        self.sensor_controller.stop_continuous_measurement()

        self.measure_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.reset_button.setEnabled(True)
        self.single_mode_radio.setEnabled(True)
        self.continuous_mode_radio.setEnabled(True)
        self.rate_combo.setEnabled(self.continuous_mode_radio.isChecked())
        self.laser_button.setEnabled(True)

        if self.sensor_controller.serial_handler.is_connected:
            self.connection_status_timer.start()

    @pyqtSlot()
    def on_reset_data(self):
        """Обработчик нажатия кнопки сброса данных"""
        if self.stop_button.isEnabled():
             QMessageBox.warning(self, "Внимание", "Нельзя очистить данные во время измерения.")
             return

        reply = QMessageBox.question(self, 'Очистка данных',
                                     "Вы уверены, что хотите очистить историю измерений?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.data_controller.clear_data()
            self.results_table.setRowCount(0)
            self.count_lcd.display(0)
            self.distance_lcd.display(0.0)
            self.quality_lcd.display(0)

            self.plot_canvas.axes.clear()
            self.plot_canvas.axes.set_xlabel("Время (отн. сек)")
            self.plot_canvas.axes.set_ylabel("Расстояние (м)")
            self.plot_canvas.axes.grid(True)
            self.plot_canvas.draw()

    @pyqtSlot(float, int)
    def on_measurement_taken(self, distance, quality):
        """Обработчик получения нового измерения"""
        self.distance_lcd.display(distance)
        self.quality_lcd.display(quality)

    @pyqtSlot()
    def on_data_updated(self):
        """Обработчик обновления данных"""
        measurements = self.data_controller.model.measurements

        count = len(measurements)
        self.count_lcd.display(count)

        self.results_table.setRowCount(count)

        for i, (timestamp, distance, quality) in enumerate(reversed(measurements)):
            row_index = count - 1 - i
            if row_index < 0: continue

            try:
                time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
            except OSError:
                time_str = "Invalid Time"

            time_item = QTableWidgetItem(time_str)
            distance_item = QTableWidgetItem(f"{distance:.3f}")
            quality_item = QTableWidgetItem(f"{quality}")

            self.results_table.setItem(row_index, 0, time_item)
            self.results_table.setItem(row_index, 1, distance_item)
            self.results_table.setItem(row_index, 2, quality_item)

        if count > 0:
            self.results_table.scrollToBottom()

        self.plot_canvas.axes.clear()

        history_length = PLOT_SETTINGS.get('history_length', 100)
        plot_data = measurements[-history_length:] if len(measurements) > 0 else []

        if plot_data:
            timestamps = [m[0] for m in plot_data]
            distances = [m[1] for m in plot_data]

            if len(timestamps) > 1:
                first_timestamp = timestamps[0]
                rel_timestamps = [t - first_timestamp for t in timestamps]
                self.plot_canvas.axes.plot(rel_timestamps, distances, marker='.', linestyle='-')
                self.plot_canvas.axes.set_title(f"Последние {len(distances)} измерений")
            elif len(timestamps) == 1:
                self.plot_canvas.axes.plot(0, distances[0], marker='o')
                self.plot_canvas.axes.set_title("Одиночное измерение")
        else:
            self.plot_canvas.axes.set_title("Нет данных")

        min_y = PLOT_SETTINGS.get('distance_min_y', 0)
        max_y = PLOT_SETTINGS.get('distance_max_y', 10)
        self.plot_canvas.axes.set_ylim(min_y, max_y)
        self.plot_canvas.axes.set_xlabel("Время")
        self.plot_canvas.axes.set_ylabel("Расстояние (м)")
        self.plot_canvas.axes.grid(True)

        self.plot_canvas.draw()
