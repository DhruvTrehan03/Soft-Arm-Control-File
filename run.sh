#!/bin/bash
# This script opens in a terminal and runs the motor controller
# Make sure to: chmod +x run.sh

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the directory where the controller file lives
cd "$SCRIPT_DIR"
export ROS_DOMAIN_ID=30
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source /opt/ros/rolling/setup.bash
# Run the motor controller
'/usr/bin/python3' motor_controller_node.py

# Keep terminal open
echo ""
echo "Motor controller stopped. Press Enter to close..."
read
