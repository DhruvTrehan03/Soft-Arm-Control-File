#!/bin/bash
# Desktop launcher for Motor Controller
# This script handles launching from desktop shortcuts

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the HardwareControl directory
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  Motor Controller Node Launcher"
echo "=========================================="
echo "Working directory: $(pwd)"
echo "Starting motor controller node..."
echo "Press Ctrl+C to stop"
echo ""

# Check if ROS2 environment needs to be sourced
if command -v ros2 &> /dev/null; then
    # Source ROS2 environment
    source /opt/ros/humble/setup.bash
    echo "✓ ROS2 environment sourced"
else
    echo "⚠ ROS2 not found - make sure it's installed"
fi

# Run the motor controller
python3 motor_controller_node.py

# Keep terminal open if there's an error
echo ""
echo "Motor controller stopped. Press Enter to close..."
read
