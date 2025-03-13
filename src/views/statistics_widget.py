from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QGroupBox, QTableWidget, 
                            QTableWidgetItem, QHeaderView, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSlot

import numpy as np

class StatisticsWidget(QWidget):
    def __init__(self, data_controller):
        super().__init__()
        
        self.data_controller = data_controller
        
        # Set up the layout
        self.main_layout = QVBoxLayout(self)
        
        # Create basic statistics group
        self.basic_stats_group = QGroupBox("Basic Statistics")
        self.basic_layout = QGridLayout()
        self.basic_stats_group.setLayout(self.basic_layout)
        
        # Create statistics labels
        self.count_label = QLabel("Count: 0")
        self.min_label = QLabel("Min: N/A")
        self.max_label = QLabel("Max: N/A")
        self.mean_label = QLabel("Mean: N/A")
        self.median_label = QLabel("Median: N/A")
        self.std_dev_label = QLabel("Std Dev: N/A")
        self.last_val_label = QLabel("Last Value: N/A")
        self.range_label = QLabel("Range: N/A")
        
        # Add labels to grid layout
        self.basic_layout.addWidget(self.count_label, 0, 0)
        self.basic_layout.addWidget(self.min_label, 0, 1)
        self.basic_layout.addWidget(self.max_label, 0, 2)
        self.basic_layout.addWidget(self.mean_label, 1, 0)
        self.basic_layout.addWidget(self.median_label, 1, 1)
        self.basic_layout.addWidget(self.std_dev_label, 1, 2)
        self.basic_layout.addWidget(self.last_val_label, 2, 0)
        self.basic_layout.addWidget(self.range_label, 2, 1)
        
        self.main_layout.addWidget(self.basic_stats_group)
        
        # Create advanced statistics group
        self.advanced_stats_group = QGroupBox("Advanced Statistics")
        self.advanced_layout = QVBoxLayout()
        self.advanced_stats_group.setLayout(self.advanced_layout)
        
        # Outlier information
        self.outlier_layout = QHBoxLayout()
        self.outliers_count_label = QLabel("Outliers: 0")
        self.outliers_percent_label = QLabel("Outlier %: 0%")
        self.outlier_layout.addWidget(self.outliers_count_label)
        self.outlier_layout.addWidget(self.outliers_percent_label)
        self.outlier_layout.addStretch(1)
        
        # Rate of change information
        self.rate_layout = QHBoxLayout()
        self.avg_rate_label = QLabel("Avg. Rate of Change: N/A m/s")
        self.max_rate_label = QLabel("Max Rate of Change: N/A m/s")
        self.rate_layout.addWidget(self.avg_rate_label)
        self.rate_layout.addWidget(self.max_rate_label)
        self.rate_layout.addStretch(1)
        
        self.advanced_layout.addLayout(self.outlier_layout)
        self.advanced_layout.addLayout(self.rate_layout)
        
        self.main_layout.addWidget(self.advanced_stats_group)
        
        # Create statistics table
        self.table_group = QGroupBox("Measurement Statistics")
        self.table_layout = QVBoxLayout()
        self.table_group.setLayout(self.table_layout)
        
        self.stats_table = QTableWidget(0, 2)  # 0 rows, 2 columns initially
        headers = ["Statistic", "Value"]
        self.stats_table.setHorizontalHeaderLabels(headers)
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Add a refresh button
        self.refresh_button = QPushButton("Refresh Statistics")
        
        self.table_layout.addWidget(self.stats_table)
        self.table_layout.addWidget(self.refresh_button)
        
        self.main_layout.addWidget(self.table_group)
        
        # Connect signals
        self.connect_signals()
    
    def connect_signals(self):
        self.refresh_button.clicked.connect(self.data_controller.update_statistics)
        self.data_controller.statistics_updated.connect(self.update_statistics)
    
    @pyqtSlot(dict)
    def update_statistics(self, stats):
        """Update statistics display with new values"""
        # Update basic statistics labels
        self.count_label.setText(f"Count: {stats.get('count', 0)}")
        
        if stats.get('min') is not None:
            self.min_label.setText(f"Min: {stats.get('min'):.3f} m")
        
        if stats.get('max') is not None:
            self.max_label.setText(f"Max: {stats.get('max'):.3f} m")
        
        if stats.get('mean') is not None:
            self.mean_label.setText(f"Mean: {stats.get('mean'):.3f} m")
        
        if stats.get('median') is not None:
            self.median_label.setText(f"Median: {stats.get('median'):.3f} m")
        
        if stats.get('std_dev') is not None:
            self.std_dev_label.setText(f"Std Dev: {stats.get('std_dev'):.3f} m")
        
        if stats.get('last_value') is not None:
            self.last_val_label.setText(f"Last Value: {stats.get('last_value'):.3f} m")
        
        # Calculate range
        if stats.get('min') is not None and stats.get('max') is not None:
            range_val = stats.get('max') - stats.get('min')
            self.range_label.setText(f"Range: {range_val:.3f} m")
        
        # Update advanced statistics
        self.outliers_count_label.setText(f"Outliers: {stats.get('outliers_count', 0)}")
        self.outliers_percent_label.setText(f"Outlier %: {stats.get('outliers_percent', 0):.1f}%")
        
        if stats.get('avg_rate_of_change') is not None:
            self.avg_rate_label.setText(f"Avg. Rate: {stats.get('avg_rate_of_change'):.3f} m/s")
        
        if stats.get('max_rate_of_change') is not None:
            self.max_rate_label.setText(f"Max Rate: {stats.get('max_rate_of_change'):.3f} m/s")
        
        # Update statistics table
        self.update_stats_table(stats)
    
    def update_stats_table(self, stats):
        """Update the statistics table with all available statistics"""
        # Clear the table
        self.stats_table.setRowCount(0)
        
        # Add all statistics to the table
        row = 0
        for key, value in stats.items():
            # Format the key name for display
            display_name = key.replace('_', ' ').title()
            
            # Format the value based on its type
            if isinstance(value, (int, float, np.number)):
                if 'percent' in key:
                    display_value = f"{value:.1f}%"
                elif 'rate' in key:
                    display_value = f"{value:.3f} m/s"
                else:
                    display_value = f"{value:.3f}" if isinstance(value, float) else str(value)
            else:
                display_value = str(value)
            
            # Add a new row to the table
            self.stats_table.insertRow(row)
            self.stats_table.setItem(row, 0, QTableWidgetItem(display_name))
            self.stats_table.setItem(row, 1, QTableWidgetItem(display_value))
            row += 1