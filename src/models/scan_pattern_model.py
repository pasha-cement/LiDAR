import json
import os
import logging

class ScanPatternModel:
    """Модель для управления шаблонами сканирования"""
    
    def __init__(self):
        self.patterns = {
            'point': {
                'name': 'Точка',
                'description': 'Фиксированное положение луча',
                'params': {
                    'angle': 0.0  # угол в градусах
                }
            },
            'line': {
                'name': 'Линия',
                'description': 'Сканирование по линии',
                'params': {
                    'start_angle': -0.5,  # начальный угол
                    'end_angle': 0.5,     # конечный угол
                    'speed': 0.1,         # скорость сканирования (град/с)
                    'steps': 20           # количество шагов
                }
            },
            'square': {
                'name': 'Квадрат',
                'description': 'Сканирование по квадрату',
                'params': {
                    'size': 0.5,          # размер в градусах
                    'speed': 0.1,         # скорость сканирования (град/с)
                    'steps': 10           # шагов на сторону
                }
            },
            'circle': {
                'name': 'Окружность',
                'description': 'Сканирование по окружности',
                'params': {
                    'radius': 0.5,        # радиус в градусах
                    'speed': 0.1,         # скорость сканирования (град/с)
                    'steps': 50           # количество точек
                }
            },
            'zigzag': {
                'name': 'Зигзаг',
                'description': 'Сканирование зигзагом',
                'params': {
                    'amplitude': 0.5,     # амплитуда в градусах
                    'frequency': 0.5,     # частота в Гц
                    'duration': 10        # длительность в секундах
                }
            }
        }
        
        self.custom_patterns = {}
        self.load_custom_patterns()
    
    def get_pattern(self, pattern_id):
        """Получить параметры шаблона по его идентификатору"""
        if pattern_id in self.patterns:
            return self.patterns[pattern_id]
        elif pattern_id in self.custom_patterns:
            return self.custom_patterns[pattern_id]
        return None
    
    def get_all_patterns(self):
        """Получить все доступные шаблоны"""
        all_patterns = {}
        all_patterns.update(self.patterns)
        all_patterns.update(self.custom_patterns)
        return all_patterns
    
    def save_custom_pattern(self, pattern_id, pattern_data):
        """Сохранить пользовательский шаблон"""
        self.custom_patterns[pattern_id] = pattern_data
        self.save_custom_patterns()
        return True
    
    def delete_custom_pattern(self, pattern_id):
        """Удалить пользовательский шаблон"""
        if pattern_id in self.custom_patterns:
            del self.custom_patterns[pattern_id]
            self.save_custom_patterns()
            return True
        return False
    
    def load_custom_patterns(self):
        """Загрузить пользовательские шаблоны из файла"""
        patterns_file = os.path.join('data', 'scan_patterns.json')
        try:
            if os.path.exists(patterns_file):
                with open(patterns_file, 'r') as f:
                    self.custom_patterns = json.load(f)
        except Exception as e:
            logging.error(f"Ошибка при загрузке пользовательских шаблонов: {e}")
            self.custom_patterns = {}
    
    def save_custom_patterns(self):
        """Сохранить пользовательские шаблоны в файл"""
        patterns_dir = 'data'
        patterns_file = os.path.join(patterns_dir, 'scan_patterns.json')
        try:
            os.makedirs(patterns_dir, exist_ok=True)
            with open(patterns_file, 'w') as f:
                json.dump(self.custom_patterns, f, indent=2)
        except Exception as e:
            logging.error(f"Ошибка при сохранении пользовательских шаблонов: {e}")