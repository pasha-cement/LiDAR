from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout,
                           QHBoxLayout, QWidget, QMenuBar, QMenu,
                           QAction, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt

from .main_widget import MainWidget

class MainWindow(QMainWindow):
    """
    Главное окно приложения LiDAR Measurement.

    Обеспечивает пользовательский интерфейс для взаимодействия с LiDAR датчиком,
    включая отображение данных измерений, управление сессиями, сохранение и загрузку данных,
    а также отображение информации о приложении.
    """
    def __init__(self, sensor_controller, data_controller):
        """
        Инициализирует главное окно приложения.

        Args:
            sensor_controller: Контроллер для управления датчиком LiDAR.
                             Отвечает за подключение, отключение, запуск и остановку измерений.
            data_controller: Контроллер для управления данными измерений.
                           Отвечает за хранение, обработку, сохранение и загрузку данных измерений.
        """
        super().__init__()

        self.sensor_controller = sensor_controller
        self.data_controller = data_controller

        self.setWindowTitle("Measurement Application")
        self.resize(900, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)

        self.combined_widget = MainWidget(self.sensor_controller, self.data_controller)
        self.main_layout.addWidget(self.combined_widget)

        self.setup_connections()

    def setup_connections(self):
        """Устанавливает связи между сигналами и слотами для взаимодействия компонентов."""
        self.sensor_controller.measurement_taken.connect(self.data_controller.add_measurement)
        self.sensor_controller.error_occurred.connect(self.show_error)

    def show_error(self, message):
        """Отображает сообщение об ошибке."""
        QMessageBox.critical(self, "Ошибка", message)

    def closeEvent(self, event):
        """Обработчик события закрытия окна."""
        if self.sensor_controller and hasattr(self.sensor_controller, 'serial_handler') and self.sensor_controller.serial_handler.is_connected:
            self.sensor_controller.stop_continuous_measurement()
            self.sensor_controller.disconnect_sensor()
        event.accept()