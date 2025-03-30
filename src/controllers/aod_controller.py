from PyQt5.QtCore import QObject, pyqtSignal
import logging
import serial.tools.list_ports

from ..utils.aod_handler import AODHandler
from ..models.scan_pattern_model import ScanPatternModel

class AODController(QObject):
    # Сигналы
    connection_changed = pyqtSignal(bool)  # статус подключения
    angle_changed = pyqtSignal(float)      # текущий угол
    scan_started = pyqtSignal(str)         # запущенный шаблон сканирования
    scan_stopped = pyqtSignal()            # остановка сканирования
    error_occurred = pyqtSignal(str)       # ошибка
    
    def __init__(self):
        super().__init__()
        self.aod_handler = AODHandler()
        self.scan_model = ScanPatternModel()
    
    def connect_aod(self, port):
        """Подключение к акустооптическому дефлектору"""
        try:
            success = self.aod_handler.connect(port)
            if success:
                success = self.aod_handler.start()
                
            self.connection_changed.emit(success)
            return success
        except Exception as e:
            self.error_occurred.emit(f"Ошибка при подключении к АОЯ: {str(e)}")
            self.connection_changed.emit(False)
            return False
    
    def disconnect_aod(self):
        """Отключение от акустооптического дефлектора"""
        try:
            success = self.aod_handler.disconnect()
            self.connection_changed.emit(not success)
            return success
        except Exception as e:
            self.error_occurred.emit(f"Ошибка при отключении от АОЯ: {str(e)}")
            return False
    
    def set_angle(self, angle):
        """Установка угла отклонения луча"""
        try:
            success = self.aod_handler.set_angle(angle)
            if success:
                self.angle_changed.emit(angle)
            return success
        except Exception as e:
            self.error_occurred.emit(f"Ошибка при установке угла: {str(e)}")
            return False
    
    def start_pattern(self, pattern_id, params=None):
        """Запуск шаблона сканирования"""
        if not self.aod_handler.connected:
            self.error_occurred.emit("АОЯ не подключена")
            return False
            
        # Получаем параметры шаблона
        pattern_data = self.scan_model.get_pattern(pattern_id)
        if not pattern_data:
            self.error_occurred.emit(f"Шаблон {pattern_id} не найден")
            return False
            
        # Если переданы пользовательские параметры, используем их
        scan_params = pattern_data['params'].copy()
        if params:
            scan_params.update(params)
            
        try:
            success = self.aod_handler.start_scanning(pattern_id, scan_params)
            if success:
                self.scan_started.emit(pattern_id)
            return success
        except Exception as e:
            self.error_occurred.emit(f"Ошибка при запуске сканирования: {str(e)}")
            return False
    
    def stop_pattern(self):
        """Остановка текущего шаблона сканирования"""
        try:
            success = self.aod_handler.stop_scanning()
            if success:
                self.scan_stopped.emit()
            return success
        except Exception as e:
            self.error_occurred.emit(f"Ошибка при остановке сканирования: {str(e)}")
            return False
    
    def get_available_patterns(self):
        """Получить список доступных шаблонов сканирования"""
        return self.scan_model.get_all_patterns()
    
    def get_available_ports(self):
        """Получить список доступных последовательных портов"""
        return [port.device for port in serial.tools.list_ports.comports()]
    
    def is_connected(self):
        """Проверить, подключено ли устройство"""
        return self.aod_handler.connected
    
    def is_scanning(self):
        """Проверить, выполняется ли сканирование"""
        return self.aod_handler.scanning
    
    def get_current_angle(self):
        """Получить текущий угол отклонения"""
        return self.aod_handler.last_angle