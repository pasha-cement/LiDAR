from PyQt5.QtCore import QObject, pyqtSignal
from ..models.measurement_model import MeasurementModel

class DataController(QObject):
    """
    Контроллер для управления данными измерений.
    Обеспечивает функции добавления, очистки и получения данных измерений.
    """
    # Сигналы для обновления данных
    data_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.model = MeasurementModel()

    def add_measurement(self, distance, quality):
        """Добавить новое измерение в текущую сессию."""
        self.model.add_measurement(distance, quality)
        self.data_updated.emit()

    def clear_data(self):
        """Очистить все измерения в текущей сессии."""
        self.model.clear_measurements()
        self.data_updated.emit()