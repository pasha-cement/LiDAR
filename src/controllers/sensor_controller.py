# src/controllers/sensor_controller.py

import logging
import time
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

# --- Импорты из вашего пакета src ---
try:
    from ..config import settings # Импорт настроек (COMMANDS, SENSOR_SETTINGS и т.д.)
    # SerialHandler не импортируем напрямую, он передается в __init__
except ImportError as e:
    print(f"Критическая ошибка импорта в sensor_controller.py: {e}")
    print("Убедитесь, что структура папок и файлы __init__.py корректны.")
    # В реальном приложении здесь может потребоваться более сложная обработка
    raise # Перевыбросить исключение, чтобы предотвратить дальнейшую работу

class SensorController(QObject):
    """
    Контроллер для управления LiDAR сенсором.

    Отвечает за взаимодействие с устройством через SerialHandler,
    отправляет команды, обрабатывает результаты измерений и статуса,
    управляет состоянием подключения и лазера.
    """

    # --- Сигналы для обновления UI ---
    connection_changed = pyqtSignal(bool)
    status_updated = pyqtSignal(float, float)
    measurement_taken = pyqtSignal(float, int)
    error_occurred = pyqtSignal(str)
    laser_state_changed = pyqtSignal(bool)

    def __init__(self, serial_handler):
        """
        Инициализирует SensorController.

        Args:
            serial_handler (SerialHandler): Экземпляр обработчика последовательного порта.
        """
        super().__init__()
        if serial_handler is None:
             raise ValueError("SerialHandler не может быть None при инициализации SensorController")

        self.serial_handler = serial_handler
        self._is_connected = False
        self._is_measuring_continuous = False
        self._laser_state = False
        self._current_continuous_mode = None

        self.logger = logging.getLogger(__name__)
        self.logger.info("SensorController инициализирован")

        self.read_timer = QTimer(self)
        self.read_timer.setInterval(100) # Интервал чтения для непрерывного режима
        self.read_timer.timeout.connect(self._read_continuous_data)

        self.consecutive_errors = 0
        self.max_consecutive_errors = settings.SENSOR_SETTINGS.get('max_consecutive_errors', 5)

    @property
    def is_connected(self):
        """Возвращает True, если есть активное подключение к датчику."""
        return self._is_connected and self.serial_handler.is_connected

    def get_available_ports(self):
        """Получение списка доступных COM-портов через SerialHandler."""
        self.logger.debug("Запрос списка доступных портов...")
        ports = self.serial_handler.get_available_ports()
        if not ports:
            self.error_occurred.emit(settings.UI_ERROR_MESSAGES["NO_PORTS_AVAILABLE"])
            self.logger.warning("Доступные COM-порты не найдены.")
        return ports

    def connect_sensor(self, port):
        """Подключение к сенсору по указанному порту."""
        if self.is_connected:
            self.logger.warning(f"Попытка подключения к {port}, но уже подключено.")
            return True

        self.logger.info(f"Попытка подключения к порту: {port}")
        success = self.serial_handler.connect(port)

        if success:
            self._is_connected = True
            self.logger.info(f"Успешное подключение к {port}")
            self.connection_changed.emit(True)
            # Запрашиваем статус и сбрасываем состояние лазера
            self.get_sensor_status()
            self._laser_state = False
            self.laser_state_changed.emit(False)
            return True
        else:
            self._is_connected = False
            self.logger.error(f"Ошибка подключения к порту {port}")
            self.error_occurred.emit(settings.UI_ERROR_MESSAGES["CONNECTION_FAILED"])
            self.connection_changed.emit(False)
            return False

    def disconnect_sensor(self):
        """Отключение от сенсора."""
        if not self.is_connected:
            self.logger.info("Нет активного подключения для отключения.")
            return True

        self.logger.info("Начало процесса отключения...")
        if self._is_measuring_continuous:
            self.logger.info("Остановка непрерывного измерения перед отключением...")
            self.stop_continuous_measurement()

        if self._laser_state and settings.SENSOR_SETTINGS.get('auto_laser_off', True):
            self.logger.info("Автоматическое выключение лазера перед отключением...")
            self._send_laser_command(False)

        port_name = self.serial_handler.serial_port.port if self.serial_handler.serial_port else "Неизвестный порт"
        self.logger.info(f"Отключение от порта {port_name}...")
        success = self.serial_handler.disconnect()

        was_connected = self._is_connected
        self._is_connected = False
        self._is_measuring_continuous = False
        self._laser_state = False

        if was_connected:
             self.connection_changed.emit(False)

        if success:
            self.logger.info(f"Успешно отключено от {port_name}")
            return True
        else:
            self.logger.error(f"Произошла ошибка при физическом отключении от порта {port_name}")
            self.error_occurred.emit(settings.UI_ERROR_MESSAGES["DISCONNECTION_FAILED"])
            return False

    def _send_laser_command(self, turn_on):
        """Внутренний метод для отправки команды управления лазером."""
        if not self.is_connected:
            self.logger.error("Попытка управления лазером без подключения.")
            return False

        command = settings.COMMANDS['LASER_ON'] if turn_on else settings.COMMANDS['LASER_OFF']
        action_str = "включения" if turn_on else "выключения"
        self.logger.debug(f"Отправка команды {action_str} лазера ({command!r})...")
        response = self.serial_handler.send_command(command, wait_for_response=True)

        if response and ",OK!" in response:
            self.logger.info(f"Команда {action_str} лазера успешно выполнена.")
            self._laser_state = turn_on
            self.laser_state_changed.emit(self._laser_state)
            return True
        else:
            self.logger.error(f"Ошибка выполнения команды {action_str} лазера. Ответ: '{response}'")
            self.error_occurred.emit(settings.UI_ERROR_MESSAGES["LASER_CONTROL_FAILED"] + f" (Ответ: {response})")
            return False

    def toggle_laser(self):
        """Переключает состояние лазера."""
        if not self.is_connected:
             self.error_occurred.emit("Невозможно управлять лазером: нет подключения.")
             self.logger.warning("Попытка переключить лазер без подключения.")
             self.laser_state_changed.emit(self._laser_state) # Отправляем текущее состояние
             return

        target_state = not self._laser_state
        self._send_laser_command(target_state)

    def get_sensor_status(self):
        """Запрашивает и обрабатывает статус датчика."""
        if not self.is_connected:
            self.logger.warning("Запрос статуса без подключения.")
            return

        self.logger.debug("Запрос статуса датчика (команда 'S')...")
        response = self.serial_handler.send_command(settings.COMMANDS['READ_STATUS'], wait_for_response=True)

        if response:
            temp, volt, err_msg = self.serial_handler.parse_status_response(response)
            if err_msg:
                self.logger.error(f"Ошибка разбора ответа статуса: {err_msg}")
                self.error_occurred.emit(err_msg)
            elif temp is not None and volt is not None:
                self.logger.info(f"Статус получен: Температура={temp}°C, Напряжение={volt}V")
                self.status_updated.emit(temp, volt)
            else:
                 self.logger.warning(f"Ответ на запрос статуса не распознан: '{response}'")
                 self.error_occurred.emit(settings.UI_ERROR_MESSAGES["INVALID_RESPONSE"] + f" (Статус: {response})")
        else:
            self.logger.error("Не получен ответ на запрос статуса.")
            self.error_occurred.emit(settings.UI_ERROR_MESSAGES["STATUS_READ_FAILED"])

    def get_single_measurement(self):
        """Выполняет ОДНОкратное измерение (команда 'D')."""
        if not self.is_connected:
            self.error_occurred.emit("Невозможно измерить: нет подключения.")
            self.logger.warning("Попытка единичного измерения без подключения.")
            return False

        if self._is_measuring_continuous:
             self.logger.warning("Попытка единичного измерения во время непрерывного. Сначала остановите.")
             self.error_occurred.emit("Сначала остановите непрерывное измерение.")
             return False

        self.logger.info("Запрос единичного измерения (команда 'D')...")
        response = self.serial_handler.send_command(settings.COMMANDS['AUTO_MEASURE'], wait_for_response=True)
        return self._process_measurement_response(response)

    def start_continuous_measurement(self, mode):
        """
        Запускает непрерывное измерение в указанном режиме ('fast', 'slow' или 'auto').

        Args:
            mode (str): Режим 'fast', 'slow' или 'auto'.
        """
        if not self.is_connected:
            self.error_occurred.emit("Невозможно начать измерение: нет подключения.")
            self.logger.warning("Попытка старта непрерывного измерения без подключения.")
            return False

        if self._is_measuring_continuous:
            self.logger.warning("Непрерывное измерение уже запущено.")
            return True # Уже запущено

        mode = mode.lower()
        command = None
        log_msg = ""

        # ---- ДОБАВЛЕНА ОБРАБОТКА 'auto' ----
        if mode == 'fast':
            command = settings.COMMANDS['FAST_MEASURE']
            log_msg = "Запуск непрерывного измерения в БЫСТРОМ режиме (команда 'F')..."
        elif mode == 'slow':
            command = settings.COMMANDS['SLOW_MEASURE']
            log_msg = "Запуск непрерывного измерения в МЕДЛЕННОМ режиме (команда 'M')..."
        elif mode == 'auto':
            # Режим "auto" из UI для непрерывного режима не имеет прямого аналога
            # в командах датчика ('F' или 'M'). Используем 'slow' как дефолт.
            mode = 'slow' # Фактически будем использовать медленный режим
            command = settings.COMMANDS['SLOW_MEASURE']
            log_msg = "Запуск непрерывного измерения в режиме 'Авто' (используется МЕДЛЕННЫЙ режим, команда 'M')..."
            self.logger.info("Режим 'Авто' для непрерывного измерения интерпретирован как 'slow'.")
        # ------------------------------------
        else:
            self.logger.error(f"Неизвестный режим непрерывного измерения: {mode}")
            self.error_occurred.emit(f"Неподдерживаемый режим: {mode}")
            return False

        self.logger.info(log_msg)
        self.serial_handler.send_command(command, wait_for_response=False)
        time.sleep(0.1)

        self._is_measuring_continuous = True
        self._current_continuous_mode = mode # Сохраняем фактический режим ('fast' или 'slow')
        self.consecutive_errors = 0
        self.read_timer.start()
        self.logger.info(f"Таймер чтения запущен (интервал {self.read_timer.interval()} мс).")
        return True

    def _read_continuous_data(self):
        """Слот, вызываемый таймером для чтения данных в непрерывном режиме."""
        if not self._is_measuring_continuous or not self.is_connected:
            self.logger.warning("_read_continuous_data вызван некорректно. Остановка.")
            self.stop_continuous_measurement()
            return

        self.logger.debug("Чтение данных из буфера в непрерывном режиме...")
        response = self.serial_handler.send_command(None, wait_for_response=True, timeout=0.05)
        success = self._process_measurement_response(response)

        if not success and response is not None:
             self.consecutive_errors += 1
             self.logger.warning(f"Ошибка чтения/разбора. Счетчик ошибок: {self.consecutive_errors}/{self.max_consecutive_errors}")
             if self.consecutive_errors >= self.max_consecutive_errors:
                 self.logger.error(f"Превышен лимит ошибок. Остановка.")
                 self.error_occurred.emit(f"Остановка из-за {self.max_consecutive_errors} ошибок подряд.")
                 self.stop_continuous_measurement()
        elif success:
             if self.consecutive_errors > 0:
                  self.logger.info("Счетчик ошибок сброшен.")
             self.consecutive_errors = 0

    def _process_measurement_response(self, response_str):
        """Общий метод для обработки ответа с измерением."""
        if response_str is None:
            self.logger.debug("Получен пустой ответ (таймаут).")
            return False

        dist, qual, err_msg = self.serial_handler.parse_distance_response(response_str)

        if err_msg:
            self.logger.warning(f"Ошибка измерения/разбора: {err_msg} (Ответ: '{response_str}')")
            self.error_occurred.emit(err_msg)
            return False
        elif dist is not None and qual is not None:
            self.logger.debug(f"Получено измерение: Расстояние={dist:.3f} м, Качество={qual}")
            self.measurement_taken.emit(dist, qual)
            return True
        else:
            self.logger.debug(f"Получен ответ, не являющийся измерением: '{response_str}'")
            return False # Не ошибка, но и не валидное измерение

    def stop_continuous_measurement(self):
        """Останавливает непрерывное измерение."""
        if not self._is_measuring_continuous:
            self.logger.debug("Непрерывное измерение не запущено.")
            return True

        self.logger.info("Остановка непрерывного измерения...")
        self.read_timer.stop()
        self._is_measuring_continuous = False
        self._current_continuous_mode = None

        if self.is_connected:
             self.logger.debug("Отправка команды остановки ('X')...")
             self.serial_handler.send_command(settings.COMMANDS['STOP_MEASURE'], wait_for_response=False)
             time.sleep(0.1)
             if self.serial_handler.serial_port:
                  try:
                      self.serial_handler.serial_port.reset_input_buffer()
                  except Exception as e:
                       self.logger.error(f"Ошибка при очистке буфера после остановки: {e}")
        else:
             self.logger.warning("Не удалось отправить команду 'X', т.к. нет подключения.")

        self.logger.info("Непрерывное измерение остановлено.")
        return True