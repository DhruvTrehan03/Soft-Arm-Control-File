#!/bin/bash

# Check if Ethernet (eth0) is connected
if ip addr show eth0 | grep -q "inet "; then
    echo "Ethernet detected. Using eth0 for ROS2 communication."
    export ROS2_NETWORK_INTERFACE=eth0
    export ROS_IP=$(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
else
  echo "Ethernet detected. Using wifi for ROS2 communication."
fi

# -----------------------------
# Auto-detect dynamxiel FT232H serial port
# -----------------------------
# FT232H 的 VID/PID
#FT232H_VID = 0x0403
#FT232H_PID = 0x6014

FT232H_VID="0403"
FT232H_PID="6014"

SERIAL_PORT=""

for dev in /dev/ttyUSB*; do
    if udevadm info -a -n "$dev" | grep -q "idVendor.*$FT232H_VID"; then
        if udevadm info -a -n "$dev" | grep -q "idProduct.*$FT232H_PID"; then
            SERIAL_PORT="$dev"
            echo "Detected FT232H on $SERIAL_PORT"
            break
        fi
    fi
done

# fallback if not found
if [ -z "$SERIAL_PORT" ]; then
    SERIAL_PORT="/dev/ttyUSB1"
    echo "Dynamixel FT232H not found, falling back to $SERIAL_PORT"
fi



# -----------------------------
# ROS2 Environment Setup
# -----------------------------
source /opt/ros/rolling/setup.bash

export ROS_DOMAIN_ID=0
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp


# -----------------------------
# Launch Controller
# -----------------------------
ros2 launch dynamixel_controller dynamixel_controller.launch.py \
    name:=MastHand \
    port:=$SERIAL_PORT \
    baudrate:=1000000

