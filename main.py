import sys
from PyQt5.QtWidgets import QApplication

from src.views.main_window import MainWindow
from src.controllers.sensor_controller import SensorController
from src.controllers.data_controller import DataController
from src.utils.serial_handler import SerialHandler

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LiDAR Distance Measurement")
    
    # Initialize components
    serial_handler = SerialHandler()
    sensor_controller = SensorController(serial_handler)
    data_controller = DataController()
    
    # Initialize main window
    window = MainWindow(sensor_controller, data_controller)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()