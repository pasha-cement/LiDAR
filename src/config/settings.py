# Serial connection settings
SERIAL_SETTINGS = {
    'baudrate': 19200,
    'bytesize': 8,
    'parity': 'N',
    'stopbits': 1,
    'timeout': 2,     # Increased timeout
    'write_timeout': 1,
    'inter_byte_timeout': 0.1  # Add delay between bytes
}

# Command codes for the LiDAR sensor
COMMANDS = {
    'LASER_ON': 'O',       # (0x4F) Turn laser on
    'LASER_OFF': 'C',      # (0x43) Turn laser off
    'READ_STATUS': 'S',    # (0x53) Read sensor status
    'AUTO_MEASURE': 'D',   # (0x44) Start automatic measurement
    'SLOW_MEASURE': 'M',   # (0x4D) Start slow measurement
    'FAST_MEASURE': 'F',   # (0x46) Start fast measurement
    'VERSION': 'V',        # (0x56) Get version information
    'POWER_OFF': 'X'       # (0x58) Turn off module
}

# Error codes and their meanings
ERROR_CODES = {
    'Er01': 'Battery voltage too low (must be >= 2.0V)',
    'Er02': 'Internal error',
    'Er03': 'Module temperature too low (< -20°C)',
    'Er04': 'Module temperature too high (> +40°C)',
    'Er05': 'Target out of measurement range',
    'Er06': 'Invalid measurement result',
    'Er07': 'Background light too strong',
    'Er08': 'Laser signal too weak',
    'Er09': 'Laser signal too strong',
    'Er10': 'Hardware malfunction 1',
    'Er11': 'Hardware malfunction 2',
    'Er12': 'Hardware malfunction 3',
    'Er13': 'Hardware malfunction 4',
    'Er14': 'Hardware malfunction 5',
    'Er15': 'Laser signal unstable'
}

# Visualization settings
PLOT_SETTINGS = {
    'update_interval_ms': 500,
    'history_length': 100,
    'distance_min_y': 0,
    'distance_max_y': 40,  # 40m is the max range of the sensor
}

# Statistics settings
STATISTICS_SETTINGS = {
    'moving_avg_window': 5,
    'outlier_threshold': 2.0,  # standard deviations
}

# Data storage settings
DATA_SETTINGS = {
    'measurement_dir': 'data/measurements/',
    'default_filename': 'lidar_measurement',
    'file_extension': 'csv'
}