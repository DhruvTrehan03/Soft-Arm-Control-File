#!/bin/bash
# This script works when run from Desktop
# It finds the HardwareControl folder and runs the motor controller

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if Ethernet (eth0) is connected
if ip addr show eth0 | grep -q "inet "; then
    echo "Ethernet detected. Using eth0 for ROS2 communication."
    export ROS2_NETWORK_INTERFACE=eth0
    export ROS_IP=$(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
else
  echo "Ethernet detected. Using wifi for ROS2 communication."
fi

source /opt/ros/rolling/setup.bash
export ROS_DOMAIN_ID=30
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Go to the folder where this script lives
cd "$SCRIPT_DIR"

# Check if the folder exists
if [ ! -f "motor_controller_node.py" ]; then
  echo "Error: motor_controller_node.py not found in $SCRIPT_DIR"
  echo "Make sure this script is located in the Soft Arm Control File folder"
    echo "Press Enter to close..."
    read
    exit 1
fi

echo "Found motor_controller_node.py in $SCRIPT_DIR"
echo "Starting motor controller..."

# Run the motor controller
python3 motor_controller_node.py --prefix master

# Keep terminal open
echo ""
echo "Motor controller stopped. Press Enter to close..."
read
