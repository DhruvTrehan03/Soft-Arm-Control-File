#!/bin/bash

# Check if Ethernet (eth0) is connected
if ip addr show eth0 | grep -q "inet "; then
    echo "Ethernet detected. Using eth0 for ROS2 communication."
    export ROS2_NETWORK_INTERFACE=eth0
    export ROS_IP=$(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
else
  echo "Ethernet detected. Using wifi for ROS2 communication."
fi

source /opt/ros/rolling/setup.bash
export ROS_DOMAIN_ID=0
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
#ros2 run dynamixel_controller dynamixel_controller_node --ros-args -p port:=/dev/ttyUSB0 -p baudrate:=1000000
ros2 launch dynamixel_controller dynamixel_controller.launch.py name:=base port:=/dev/ttyUSB1 budrate:=1000000



