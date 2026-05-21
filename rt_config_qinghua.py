"""
Configuration file for Real-Time Motor Control System
"""

# Serial communication settings
# Auto-detect port on Raspberry Pi, fallback to common ports
import os
import platform
import serial.tools.list_ports

# FT232H 的 VID/PID
FT232H_VID = 0x0403
FT232H_PID = 0x6014

def auto_detect_ft232h():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if p.vid == FT232H_VID and p.pid == FT232H_PID:
            print(f"Detected FT232H on {p.device}")
            return p.device

    print("FT232H not found, falling back to /dev/ttyUSB0")
    return "/dev/ttyUSB0"

# Auto-detect serial port based on platform
if platform.system() == 'Linux':
    SERIAL_PORT = auto_detect_ft232h()
else:
    SERIAL_PORT = 'COM4'  # Windows fallback

print("Using serial port:", SERIAL_PORT)

# Other settings
BAUDRATE = 1000000
# BAUDRATE = 115200
# Motor control settings
DEFAULT_SPEED = 800      # Default movement speed (1-255)
DEFAULT_ACCELERATION = 50  # Default acceleration (1-254)
DEFAULT_TORQUE_LIMIT = 500  # Default torque limit (0-1000)
DEFAULT_UPDATE_RATE = 200   # Default update rate in Hz

# Motor angle limits (in degrees)
MIN_ANGLE = -2520
MAX_ANGLE = 2520

# Gripper joint specific settings
GRIPPER_MOTOR_ID = 18  # Motor ID for gripper joint
GRIPPER_MIN_ANGLE = -360  # Gripper joint minimum angle (degrees)
GRIPPER_MAX_ANGLE = 360   # Gripper joint maximum angle (degrees)
GRIPPER_DEFAULT_SPEED = 100   # Slower speed for gripper safety
GRIPPER_DEFAULT_ACCELERATION = 100  # Lower acceleration for gripper safety
GRIPPER_DEFAULT_TORQUE = 1000  # Lower torque limit for gripper safety

# Encoder conversion settings
ENCODER_RESOLUTION = 4096  # Encoder counts per full rotation
ENCODER_ZERO_POINT = 2048  # Zero point (middle of encoder range)
DEFAULT_ZERO_OFFSET = 2048  # Default offset for T99 zero calibration (middle position, full turn = 4096)
ANGLE_PER_UNIT = 180.0 / 2048  # Degrees per encoder unit (180° = 2048 units)

# Plot settings
PLOT_HISTORY_LENGTH = 1000  # Number of data points to keep in plots
PLOT_UPDATE_INTERVAL = 0.1  # Plot update interval in seconds

# Motor IDs (will be auto-detected, but you can specify expected ones)
EXPECTED_MOTOR_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]

# Safety settings
MAX_TORQUE_LIMIT = 1000  # Maximum torque limit (0-1000)
EMERGENCY_STOP_ENABLED = True

# Logging settings
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = True
LOG_FILE = 'motor_control.log'

# GUI settings
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
PLOT_HEIGHT = 200  # Height of each plot in pixels

# Color scheme for different motors
MOTOR_COLORS = [
    '#FF0000',  # Red
    '#0000FF',  # Blue
    '#00FF00',  # Green
    '#FFA500',  # Orange
    '#800080',  # Purple
    '#A52A2A',  # Brown
    '#FFC0CB',  # Pink
    '#808080',  # Gray
    '#808000',  # Olive
    '#00FFFF',  # Cyan
    '#FF00FF',  # Magenta
    '#FFFF00',  # Yellow
    '#000000',  # Black
] 
