# HardwareControl Package for Raspberry Pi

This package provides motor control capabilities for Feetech HLS servos on Raspberry Pi with automatic USB port detection.

## Features

- **Automatic USB Port Detection**: Automatically finds and tests available USB/Serial ports
- **Feetech HLS Controller**: Full control of Feetech HLS servos
- **Port Scanner**: Utility to scan and test serial port connectivity
- **Motor Utilities**: Helper functions for angle/encoder conversions
- **Raspberry Pi Optimized**: Configured for Linux/Raspberry Pi systems

## Files

- `feetech_controller.py` - Main servo controller class
- `port_scanner.py` - USB/Serial port detection utility
- `motor_utils.py` - Motor control utility functions
- `rt_config.py` - Configuration file with auto-port detection
- `requirements.txt` - Python dependencies
- `setup_rpi.sh` - Automated setup script for Raspberry Pi
- `test_setup.py` - Test script to verify installation

## Quick Setup

### 1. Copy Files to Raspberry Pi

Copy the entire `HardwareControl` folder to your Raspberry Pi.

### 2. Run Setup Script

```bash
cd HardwareControl
chmod +x setup_rpi.sh
sudo bash setup_rpi.sh
```

This script will:
- Install system dependencies
- Install Python packages
- Extract the scservo_sdk
- Set USB device permissions
- Create udev rules for USB devices

### 3. Reboot (Recommended)

```bash
sudo reboot
```

### 4. Test Installation

```bash
cd HardwareControl
python3 test_setup.py
```

## Manual Setup (Alternative)

If you prefer manual setup:

### Install Dependencies

```bash
sudo apt update
sudo apt install python3-pip python3-dev python3-serial python3-numpy
pip3 install -r requirements.txt
```

### Extract SDK

```bash
unzip scservo_sdk.zip
```

### Set Permissions

```bash
sudo usermod -a -G dialout $USER
```

## Usage Examples

### Basic Port Scanning

```python
from port_scanner import PortScanner

scanner = PortScanner()
working_ports = scanner.find_working_ports()
print(f"Working ports: {working_ports}")
```

### Auto-Detecting Controller

```python
from feetech_controller import FeetechController

# Port will be auto-detected
controller = FeetechController()
controller.connect()
```

### Manual Port Selection

```python
from feetech_controller import FeetechController

controller = FeetechController(port_name='/dev/ttyUSB0')
controller.connect()
```

## Port Detection Priority

The system automatically prioritizes ports in this order:

1. `/dev/ttyUSB*` - USB-to-Serial adapters (recommended)
2. `/dev/ttyACM*` - Arduino/Teensy devices
3. `/dev/ttyS*` - Hardware serial ports
4. `/dev/ttyAMA*` - Raspberry Pi hardware serial

## Troubleshooting

### No Ports Found

1. Check USB connections
2. Run `lsusb` to see USB devices
3. Check if device appears in `/dev/`
4. Verify user is in `dialout` group

### Permission Denied

```bash
sudo usermod -a -G dialout $USER
# Then log out and back in, or reboot
```

### Import Errors

1. Ensure all dependencies are installed: `pip3 install -r requirements.txt`
2. Check if scservo_sdk.zip was extracted
3. Verify Python path includes current directory

### Port Not Working

1. Test with `python3 port_scanner.py`
2. Check device manager/system logs
3. Try different USB ports
4. Verify baudrate compatibility

## Testing

Run the comprehensive test suite:

```bash
python3 test_setup.py
```

This will test:
- All module imports
- Port scanner functionality
- Controller initialization
- Motor utility functions

## Configuration

Edit `rt_config.py` to modify:
- Default baudrate
- Motor limits
- Safety settings
- Logging options

## Support

If you encounter issues:

1. Check the test output: `python3 test_setup.py`
2. Verify USB device detection: `lsusb`
3. Check port availability: `ls /dev/tty*`
4. Review system logs: `dmesg | tail`

## Requirements

- Raspberry Pi (any model)
- Python 3.7+
- USB-to-Serial adapter (recommended)
- Feetech HLS servos
- Internet connection for initial setup
