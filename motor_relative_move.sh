#!/bin/bash

# Relative motor move helper.
# Usage:
#   bash motor_relative_move.sh 1,2,3 10,10,5
#   bash motor_relative_move.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export ROS_DOMAIN_ID=30
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source /opt/ros/rolling/setup.bash
cd "$SCRIPT_DIR"

python3 "$SCRIPT_DIR/motor_relative_move.py" "$@"