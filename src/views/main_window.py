from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, 
                           QHBoxLayout, QWidget, QMenuBar, QMenu,
                           QAction, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt

from .connection_widget import ConnectionWidget
from .measurement_widget import MeasurementWidget
from .visualization_widget import VisualizationWidget
from .statistics_widget import StatisticsWidget
from .aod_widget import AODWidget  # Добавляем импорт нового виджета

class MainWindow(QMainWindow):
    def __init__(self, sensor_controller, data_controller, aod_controller=None):  # Добавляем аргумент
        super().__init__()
        
        self.sensor_controller = sensor_controller
        self.data_controller = data_controller
        self.aod_controller = aod_controller  # Сохраняем контроллер АОЯ
        
        self.setWindowTitle("LiDAR Measurement Application")
        self.resize(900, 600)
        
        # Set up the main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Initialize widgets
        self.connection_widget = ConnectionWidget(self.sensor_controller)
        self.measurement_widget = MeasurementWidget(self.sensor_controller, self.data_controller)
        self.visualization_widget = VisualizationWidget(self.data_controller)
        self.statistics_widget = StatisticsWidget(self.data_controller)
        
        # Добавляем виджет АОЯ, если контроллер предоставлен
        if self.aod_controller:
            self.aod_widget = AODWidget(self.aod_controller)
        
        # Add widgets to tabs
        self.tab_widget.addTab(self.connection_widget, "Подключение")
        self.tab_widget.addTab(self.measurement_widget, "Измерение")
        self.tab_widget.addTab(self.visualization_widget, "Визуализация")
        self.tab_widget.addTab(self.statistics_widget, "Статистика")
        
        # Добавляем вкладку АОЯ, если контроллер предоставлен
        if self.aod_controller:
            self.tab_widget.addTab(self.aod_widget, "Акустооптическая ячейка")
        
        # Set up menu
        self.create_menus()
        
        # Connect signals
        self.setup_connections()
    
    def create_menus(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_session_action = QAction("New Session", self)
        new_session_action.triggered.connect(self.start_new_session)
        file_menu.addAction(new_session_action)
        
        save_action = QAction("Save Data", self)
        save_action.triggered.connect(self.save_data)
        file_menu.addAction(save_action)
        
        load_action = QAction("Load Data", self)
        load_action.triggered.connect(self.load_data)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_connections(self):
        # Connect data controller signals to update visualization
        self.data_controller.data_updated.connect(self.visualization_widget.update_plots)
        self.data_controller.statistics_updated.connect(self.statistics_widget.update_statistics)
        
        # Connect sensor controller signals for measurements
        self.sensor_controller.measurement_taken.connect(self.data_controller.add_measurement)
        self.sensor_controller.error_occurred.connect(self.show_error)
    
    def start_new_session(self):
        reply = QMessageBox.question(self, 'New Session', 
                                     'Start a new measurement session? Current data will be cleared.',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.data_controller.start_new_session()
    
    def save_data(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Measurement Data", "", 
                                                "CSV Files (*.csv);;All Files (*)")
        if filename:
            success = self.data_controller.save_data(filename)
            if success:
                QMessageBox.information(self, "Success", "Data saved successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to save data")
    
    def load_data(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Measurement Data", "", 
                                                "CSV Files (*.csv);;All Files (*)")
        if filename:
            success = self.data_controller.load_data(filename)
            if success:
                QMessageBox.information(self, "Success", "Data loaded successfully")
                # Switch to visualization tab to show the loaded data
                self.tab_widget.setCurrentWidget(self.visualization_widget)
            else:
                QMessageBox.warning(self, "Error", "Failed to load data")
    
    def show_error(self, error_message):
        QMessageBox.warning(self, "Error", error_message)
    
    def show_about(self):
        QMessageBox.about(self, "About", 
                         "LiDAR Measurement Application\n\n"
                         "A Python application for measuring distance using LiDAR sensor JRT M703A.\n\n"
                         "Features:\n"
                         "- Serial connection to sensor\n"
                         "- Real-time distance measurement\n"
                         "- Data visualization\n"
                         "- Statistical analysis\n"
                         "- Data export and import")
    
    def closeEvent(self, event):
        # Make sure to disconnect from sensor when closing
        if self.sensor_controller and hasattr(self.sensor_controller, 'is_connected') and self.sensor_controller.serial_handler.is_connected:
            self.sensor_controller.stop_continuous_measurement()
            self.sensor_controller.disconnect_sensor()
        event.accept()