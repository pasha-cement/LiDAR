from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QCheckBox, QGroupBox, QComboBox,
                           QSpinBox, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSlot

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

class VisualizationWidget(QWidget):
    def __init__(self, data_controller):
        super().__init__()
        
        self.data_controller = data_controller
        
        # Set up the layout
        self.main_layout = QVBoxLayout(self)
        
        # Create visualization controls group
        self.controls_group = QGroupBox("Visualization Controls")
        self.controls_layout = QHBoxLayout()
        self.controls_group.setLayout(self.controls_layout)
        
        # Plot type selection
        self.plot_form = QFormLayout()
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["Distance", "Signal Quality", "Moving Average"])
        self.plot_form.addRow("Plot Type:", self.plot_type_combo)
        
        # History length control
        self.history_spin = QSpinBox()
        self.history_spin.setRange(10, 1000)
        self.history_spin.setSingleStep(10)
        self.history_spin.setValue(100)
        self.plot_form.addRow("History Length:", self.history_spin)
        
        self.controls_layout.addLayout(self.plot_form)
        
        # Plot options
        self.options_form = QFormLayout()
        self.autoscale_check = QCheckBox("Enable")
        self.autoscale_check.setChecked(True)
        self.options_form.addRow("Auto Scale:", self.autoscale_check)
        
        self.grid_check = QCheckBox("Show Grid")
        self.grid_check.setChecked(True)
        self.options_form.addRow("Grid:", self.grid_check)
        
        self.markers_check = QCheckBox("Show Markers")
        self.options_form.addRow("Markers:", self.markers_check)
        
        self.controls_layout.addLayout(self.options_form)
        
        # Plot buttons
        self.buttons_layout = QVBoxLayout()
        self.update_button = QPushButton("Update Plot")
        self.clear_button = QPushButton("Clear Plot")
        
        self.buttons_layout.addWidget(self.update_button)
        self.buttons_layout.addWidget(self.clear_button)
        self.buttons_layout.addStretch(1)
        
        self.controls_layout.addLayout(self.buttons_layout)
        
        self.main_layout.addWidget(self.controls_group)
        
        # Create matplotlib figure
        self.create_figure()
        
        # Connect signals
        self.connect_signals()
    
    def create_figure(self):
        # Create the figure and canvas for matplotlib
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Create initial plot
        self.axis = self.figure.add_subplot(111)
        self.axis.set_title('Distance Measurement')
        self.axis.set_xlabel('Time (seconds)')
        self.axis.set_ylabel('Distance (m)')
        self.axis.grid(True)
        
        # Add to layout
        self.main_layout.addWidget(self.toolbar)
        self.main_layout.addWidget(self.canvas)
    
    def connect_signals(self):
        self.update_button.clicked.connect(self.update_plots)
        self.clear_button.clicked.connect(self.clear_plot)
        self.plot_type_combo.currentIndexChanged.connect(self.update_plots)
        self.grid_check.stateChanged.connect(self.update_grid)
        self.autoscale_check.stateChanged.connect(self.update_plots)
    
    @pyqtSlot()
    def update_plots(self):
        # Clear the previous plot
        self.axis.clear()
        
        # Get plot type
        plot_type = self.plot_type_combo.currentText().lower().replace(' ', '_')
        
        # Get data from controller
        x_data, y_data = self.data_controller.get_plot_data(plot_type)
        
        # Limit data to the specified history length
        history_length = self.history_spin.value()
        if len(x_data) > history_length:
            x_data = x_data[-history_length:]
            y_data = y_data[-history_length:]
        
        # If there's no data, just update and return
        if not x_data:
            self.canvas.draw()
            return
        
        # Plot the data
        marker = 'o' if self.markers_check.isChecked() else None
        self.axis.plot(x_data, y_data, marker=marker, linestyle='-', color='blue')
        
        # Set title and labels based on plot type
        if plot_type == 'distance':
            self.axis.set_title('Distance Measurement')
            self.axis.set_ylabel('Distance (m)')
        elif plot_type == 'quality':
            self.axis.set_title('Signal Quality')
            self.axis.set_ylabel('Quality')
        elif plot_type == 'moving_avg':
            self.axis.set_title('Moving Average Distance')
            self.axis.set_ylabel('Distance (m)')
        
        self.axis.set_xlabel('Time (seconds)')
        
        # Apply grid setting
        self.axis.grid(self.grid_check.isChecked())
        
        # Apply autoscale if checked, otherwise use fixed y range for distance
        if not self.autoscale_check.isChecked() and plot_type in ['distance', 'moving_avg']:
            self.axis.set_ylim(0, 40)  # 0-40m is the sensor range
        
        # Refresh the canvas
        self.canvas.draw()
    
    @pyqtSlot()
    def clear_plot(self):
        self.axis.clear()
        
        # Reset labels
        plot_type = self.plot_type_combo.currentText().lower().replace(' ', '_')
        if plot_type == 'distance':
            self.axis.set_title('Distance Measurement')
            self.axis.set_ylabel('Distance (m)')
        elif plot_type == 'quality':
            self.axis.set_title('Signal Quality')
            self.axis.set_ylabel('Quality')
        elif plot_type == 'moving_avg':
            self.axis.set_title('Moving Average Distance')
            self.axis.set_ylabel('Distance (m)')
            
        self.axis.set_xlabel('Time (seconds)')
        
        # Apply grid setting
        self.axis.grid(self.grid_check.isChecked())
        
        # Refresh the canvas
        self.canvas.draw()
    
    @pyqtSlot(int)
    def update_grid(self, state):
        self.axis.grid(state != 0)
        self.canvas.draw()