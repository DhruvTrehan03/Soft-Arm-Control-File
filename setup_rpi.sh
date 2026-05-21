#!/bin/bash
# Setup script for HardwareControl package on Raspberry Pi
# Run with: sudo bash setup_rpi.sh

echo "Setting up HardwareControl package for Raspberry Pi..."
echo "=================================================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "Warning: This script is designed for Raspberry Pi"
    echo "Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update package list
echo "Updating package list..."
sudo apt update

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y python3-pip python3-dev python3-serial python3-numpy

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Extract scservo_sdk if it exists
if [ -f "scservo_sdk.zip" ]; then
    echo "Extracting scservo_sdk..."
    unzip -o scservo_sdk.zip
    echo "scservo_sdk extracted successfully"
else
    echo "Warning: scservo_sdk.zip not found"
fi

# Set proper permissions for USB devices
echo "Setting USB device permissions..."
sudo usermod -a -G dialout $USER

# Create udev rules for USB-to-serial devices
echo "Creating udev rules for USB devices..."
sudo tee /etc/udev/rules.d/99-usb-serial.rules > /dev/null <<EOF
# USB-to-Serial devices
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="067b", ATTRS{idProduct}=="2303", MODE="0666"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

echo ""
echo "Setup completed!"
echo ""
echo "Next steps:"
echo "1. Reboot your Raspberry Pi or log out and back in"
echo "2. Test the port scanner: python3 port_scanner.py"
echo "3. Run your motor control scripts"
echo ""
echo "Note: You may need to reboot for USB permissions to take effect"
