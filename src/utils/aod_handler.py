import sys
import os
import time
import logging
import threading
import numpy as np
from scipy import interpolate

# Добавляем путь к исходному модулю АОЯ
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'AOD'))
from UTCDeflector import DevReader, Deflector

class AODHandler:
    """Класс для управления акустооптическим дефлектором в основном приложении"""
    
    def __init__(self, dev_filename=None, port=None):
        self.deflector = None
        self.dev_filename = dev_filename or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'AOD', 'AOD.dev')
        self.port = port
        self.connected = False
        self.scanning = False
        self.scan_thread = None
        self.stop_scan = False
        self.current_pattern = None
        self.last_angle = 0.0
        
        # Паттерны сканирования
        self.scan_patterns = {
            'point': self._point_scan,
            'line': self._line_scan,
            'square': self._square_scan,
            'circle': self._circle_scan,
            'zigzag': self._zigzag_scan
        }
    
    def connect(self, port):
        """Подключение к акустооптическому дефлектору"""
        try:
            self.port = port
            self.deflector = Deflector(self.dev_filename, port)
            self.connected = True
            logging.info(f"АОЯ подключена к порту {port}")
            return True
        except Exception as e:
            logging.error(f"Ошибка при подключении к АОЯ: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Отключение от акустооптического дефлектора"""
        if self.deflector:
            try:
                self.stop_scanning()
                self.deflector.stop()
                self.deflector.close()
                self.connected = False
                logging.info("АОЯ отключена")
                return True
            except Exception as e:
                logging.error(f"Ошибка при отключении от АОЯ: {e}")
                return False
        return True
    
    def start(self):
        """Запуск акустооптического дефлектора"""
        if not self.connected or not self.deflector:
            return False
        
        try:
            self.deflector.start()
            logging.info("АОЯ запущена")
            return True
        except Exception as e:
            logging.error(f"Ошибка при запуске АОЯ: {e}")
            return False
    
    def set_angle(self, angle):
        """Установка угла отклонения луча"""
        if not self.connected or not self.deflector:
            return False
        
        try:
            self.deflector.set_angle(angle)
            self.last_angle = angle
            logging.debug(f"АОЯ: установлен угол {angle} градусов")
            return True
        except Exception as e:
            logging.error(f"Ошибка при установке угла АОЯ: {e}")
            return False
    
    def set_amplitude(self, amplitude):
        """Установка амплитуды сигнала"""
        if not self.connected or not self.deflector:
            return False
        
        try:
            self.deflector.set_ampl(amplitude)
            logging.debug(f"АОЯ: установлена амплитуда {amplitude}%")
            return True
        except Exception as e:
            logging.error(f"Ошибка при установке амплитуды АОЯ: {e}")
            return False
    
    def start_scanning(self, pattern_name, params):
        """Запуск сканирования по заданному шаблону"""
        if self.scanning or not self.connected:
            return False
        
        if pattern_name not in self.scan_patterns:
            logging.error(f"Неизвестный шаблон сканирования: {pattern_name}")
            return False
        
        self.stop_scan = False
        self.current_pattern = pattern_name
        
        # Запускаем сканирование в отдельном потоке
        self.scan_thread = threading.Thread(
            target=self.scan_patterns[pattern_name],
            args=(params,),
            daemon=True
        )
        self.scanning = True
        self.scan_thread.start()
        logging.info(f"Запущено сканирование по шаблону '{pattern_name}'")
        return True
    
    def stop_scanning(self):
        """Остановка текущего сканирования"""
        if self.scanning and self.scan_thread and self.scan_thread.is_alive():
            self.stop_scan = True
            self.scan_thread.join(timeout=1.0)
            self.scanning = False
            self.current_pattern = None
            logging.info("Сканирование остановлено")
            return True
        return False
    
    # Методы реализации различных шаблонов сканирования
    def _point_scan(self, params):
        """Фиксированная точка (статический режим)"""
        angle = params.get('angle', 0.0)
        self.set_angle(angle)
    
    def _line_scan(self, params):
        """Линейное сканирование между двумя углами"""
        start_angle = params.get('start_angle', -0.5)
        end_angle = params.get('end_angle', 0.5)
        speed = params.get('speed', 0.1)  # градусов в секунду
        steps = params.get('steps', 20)
        
        angles = np.linspace(start_angle, end_angle, steps)
        step_delay = abs(end_angle - start_angle) / (steps * speed)
        
        while not self.stop_scan:
            for angle in angles:
                if self.stop_scan:
                    return
                self.set_angle(angle)
                time.sleep(step_delay)
            
            for angle in reversed(angles):
                if self.stop_scan:
                    return
                self.set_angle(angle)
                time.sleep(step_delay)
    
    def _square_scan(self, params):
        """Сканирование по квадрату"""
        # Для АОЯ с одним каналом реализуем "квадрат" как последовательность точек
        size = params.get('size', 0.5)  # размер половины стороны квадрата
        speed = params.get('speed', 0.1)
        steps_per_side = params.get('steps', 10)
        
        points = []
        # Верхняя сторона: слева направо
        for i in range(steps_per_side):
            points.append(-size + i * 2 * size / (steps_per_side - 1))
        
        step_delay = 2 * size / (steps_per_side * speed)
        
        while not self.stop_scan:
            # Проходим все точки
            for angle in points:
                if self.stop_scan:
                    return
                self.set_angle(angle)
                time.sleep(step_delay)
            
            # Проходим в обратном порядке
            for angle in reversed(points):
                if self.stop_scan:
                    return
                self.set_angle(angle)
                time.sleep(step_delay)
    
    def _circle_scan(self, params):
        """Сканирование по окружности (для одноканального АОЯ - синусоидальное)"""
        radius = params.get('radius', 0.5)
        speed = params.get('speed', 0.1)
        steps = params.get('steps', 50)
        
        angles = [radius * np.sin(2 * np.pi * i / steps) for i in range(steps)]
        step_delay = 2 * np.pi * radius / (steps * speed)
        
        while not self.stop_scan:
            for angle in angles:
                if self.stop_scan:
                    return
                self.set_angle(angle)
                time.sleep(step_delay)
    
    def _zigzag_scan(self, params):
        """Сканирование зигзагом"""
        amplitude = params.get('amplitude', 0.5)
        frequency = params.get('frequency', 0.5)  # Гц
        duration = params.get('duration', 10)  # секунд
        samples_per_sec = 20
        
        start_time = time.time()
        
        while not self.stop_scan and (time.time() - start_time < duration):
            current_time = time.time() - start_time
            angle = amplitude * np.sin(2 * np.pi * frequency * current_time)
            self.set_angle(angle)
            time.sleep(1.0 / samples_per_sec)