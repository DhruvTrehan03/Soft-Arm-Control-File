#!/usr/bin/env python3
"""
Motor Controller Node for ROS2 - Snake Robot Control

This node provides a unified interface for controlling Feetech servo motors in a snake robot.
All motor operations are handled through JSON commands via the motor commands topic.

Topic names are dynamic based on the prefix parameter:
- Without prefix: /motor_commands
- With prefix (e.g., "master"): /master_motor_commands
- With prefix (e.g., "tongue"): /tongue_motor_commands

================================================================================
USAGE EXAMPLES
================================================================================

Note: All examples use /motor_commands as the topic name. If you're using a prefix
(e.g., --prefix master), replace /motor_commands with /master_motor_commands in
all commands below.

1. POSITION CONTROL (T1)
   Move specific motors to target positions:
   ```bash
   # Move motors 1,2,3 to positions 10°, 20°, 30° (uses default speed)
   ros2 topic pub /motor_commands std_msgs/msg/String '["T1", {"motors": [1,2,3], "positions": [10,20,30]}]'
   
   # Move with custom speed (how fast to reach target position)
   ros2 topic pub /motor_commands std_msgs/msg/String '["T1", {"motors": [1,2,3], "positions": [10,20,30], "speed": [100,150,200]}]'
   
   # Move all 18 motors to different positions
   ros2 topic pub /motor_commands std_msgs/msg/String '["T1", {"motors": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18], "positions": [0,10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170]}]'
   ```
   Note: The "speed" parameter controls how fast the motor moves to reach the target position (used in position mode).

2. TORQUE CONTROL (T4)
   Apply specific torques to motors:
   ```bash
   # Apply torques 100, 200, 300 to motors 1,2,3
   ros2 topic pub /motor_commands std_msgs/msg/String '["T4", {"motors": [1,2,3], "torques": [100,200,300]}]'
   
   # Apply same torque (500) to all motors
   ros2 topic pub /motor_commands std_msgs/msg/String '["T4", {"motors": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18], "torques": [500,500,500,500,500,500,500,500,500,500,500,500,500,500,500,500,500,500]}]'
   ```

3. VELOCITY CONTROL (T2)
   Set constant velocity (velocity mode - motor maintains constant speed):
   ```bash
   # Set constant velocities 50, 75, 100 to motors 1,2,3 (velocity mode)
   ros2 topic pub /motor_commands std_msgs/msg/String '["T2", {"motors": [1,2,3], "speeds": [50,75,100]}]'
   ```
   Note: This sets the motor to constant velocity mode. The motor will maintain the specified speed continuously.
   This is different from position mode's "speed" parameter which only controls how fast to reach a target position.

4. ENABLE/DISABLE MOTORS (T0)
   Enable or disable motor torque:
   ```bash
   # Enable motors 1,2,3
   ros2 topic pub /motor_commands std_msgs/msg/String '["T0", {"motors": [1,2,3], "enable": true}]'
   
   # Disable all motors (emergency stop)
   ros2 topic pub /motor_commands std_msgs/msg/String '["T0", {"motors": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18], "enable": false}]'
   ```

5. TORQUE LIMITS (T5)
   Set torque limits for motors:
   ```bash
   # Set torque limits 800, 600, 400 for motors 1,2,3
   ros2 topic pub /motor_commands std_msgs/msg/String '["T5", {"motors": [1,2,3], "torque_limits": [800,600,400]}]'
   ```

6. ACCELERATION SETTINGS (T3)
   Set motor acceleration:
   ```bash
   # Set acceleration 100 for motors 1,2,3
   ros2 topic pub /motor_commands std_msgs/msg/String '["T3", {"motors": [1,2,3], "accelerations": [100,100,100]}]'
   ```

7. MODE CHANGES (T10)
   Change motor operating modes:
   ```bash
   # Change motors 1,2,3 to position mode (0)
   ros2 topic pub /motor_commands std_msgs/msg/String '["T10", {"motors": [1,2,3], "modes": [0,0,0]}]'
   
   # Change motors 1,2,3 to velocity mode (1) - constant speed mode
   ros2 topic pub /motor_commands std_msgs/msg/String '["T10", {"motors": [1,2,3], "modes": [1,1,1]}]'
   
   # Change motors 1,2,3 to torque mode (2) - constant current mode
   ros2 topic pub /motor_commands std_msgs/msg/String '["T10", {"motors": [1,2,3], "modes": [2,2,2]}]'
   ```
   Modes: 0=Position, 1=Velocity (constant speed), 2=Torque (constant current)
   
   READ MOTOR MODES (T10 with action="read"):
   Query the current operating mode of motors:
   ```bash
   # Read mode for motors 1,2,3
   ros2 topic pub /motor_commands std_msgs/msg/String '["T10", {"motors": [1,2,3], "action": "read"}]'
   
   # Read mode for a single motor
   ros2 topic pub /motor_commands std_msgs/msg/String '["T10", {"motors": [1], "action": "read"}]'
   ```
   The mode results will be published to /motor_controller/motor_modes topic and logged to console.

8. SERVO ID CHANGES (T11)
   Change servo IDs (use with caution):
   ```bash
   # Change servo ID from 1 to 5
   ros2 topic pub /motor_commands std_msgs/msg/String '["T11", {"current_id": 1, "new_id": 5}]'
   ```

9. SET ZERO (T99) - Calibrate current position as zero (no offset value)
   ```bash
   ros2 topic pub /motor_commands std_msgs/msg/String '["T99", {"motors": [1]}]'
   ros2 topic pub /motor_commands std_msgs/msg/String '["T99", {"motors": [1, 2, 3]}]'
   ```

10. ADD ENCODER OFFSET (T98) - Add encoder position offset (current position reads as given value)
   ```bash
   ros2 topic pub /motor_commands std_msgs/msg/String '["T98", {"motors": [1, 2], "offsets": [2048, 2048]}]'
   ```

================================================================================
MONITORING
================================================================================

Monitor motor feedback:
```bash
# View motor feedback data (position, speed, load)
ros2 topic echo /motor_controller/feedback

# View system status
ros2 topic echo /motor_controller/status

# Check hardware connection status
ros2 topic echo /motor_controller/hardware_connected

# View motor modes (published when reading modes via T10 with action="read")
ros2 topic echo /motor_controller/motor_modes
```

================================================================================
SERVICES
================================================================================

Available services:
```bash
# Connect to hardware
ros2 service call /motor_controller/connect_hardware std_srvs/srv/Trigger

# Disconnect from hardware
ros2 service call /motor_controller/disconnect_hardware std_srvs/srv/Trigger

# Emergency stop
ros2 service call /emergency_stop std_srvs/srv/Trigger

# Clear emergency stop
ros2 service call /clear_emergency_stop std_srvs/srv/Trigger

# Enable all motors
ros2 service call /enable_motor std_srvs/srv/Trigger

# Disable all motors
ros2 service call /disable_motor std_srvs/srv/Trigger

# Ping servos to check connection
ros2 service call /ping_servos std_srvs/srv/Trigger
```

================================================================================
NOTES
================================================================================

- Commands are executed immediately when received
- Stored commands are sent once more in the next control loop (100 Hz)
- Emergency stop is enabled by default (safe mode)
- All motors are disabled by default - enable before use
- Feedback is published continuously at 100 Hz
- Individual read with retry mechanism for reliable feedback
- Last known good data used as fallback when reads fail

================================================================================
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String, Bool, Int32MultiArray
from std_srvs.srv import Trigger
import numpy as np
import sys
import os
import time
import traceback
import json
import argparse

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from feetech_controller import FeetechController
import rt_config as rt_cfg
from motor_utils import angle_to_encoder, encoder_to_angle

os.environ['ROS_DOMAIN_ID'] = '30'
os.environ['ROS_LOCALHOST_ONLY'] = '0'
os.environ['RMW_IMPLEMENTATION'] = 'rmw_cyclonedds_cpp'

class MotorControllerNode(Node):
    def __init__(self, name_prefix: str = '', debug_mode: bool = False, serial_port: str = None):
        """
        Initialize MotorControllerNode
        
        Args:
            name_prefix: Prefix for node name and topics (e.g., 'master' -> 'master_motor_controller_node')
                        If empty, uses default names without prefix
            debug_mode: If True, enables debug features like encoder value publishing (default: False)
            serial_port: Serial port name (e.g., 'COM9' or '/dev/ttyUSB0'). If None, uses rt_config.SERIAL_PORT
        """
        # Build node name with prefix
        if name_prefix:
            node_name = f'{name_prefix}_motor_controller_node'
        else:
            node_name = 'motor_controller_node'
        
        super().__init__(node_name)
        
        # Store prefix for building topic/service names
        self.name_prefix = name_prefix
        self.debug_mode = debug_mode
        self.serial_port = serial_port if serial_port else rt_cfg.SERIAL_PORT
        
        # Motor control parameters - simple and focused
        self.motor_ids = []
        self.hardware_connected = False
        
        # Emergency stop state
        self.emergency_stop = True  # Start with emergency stop enabled (safe default)
        
        # Simple command storage - just store the latest commands
        self.latest_commands = {}  # motor_id -> command_data
        
        # Command tracking flag
        self.new_commands_received = False
        
        # Last known good feedback storage (for fallback when reading fails)
        self.last_motor_feedback = {}
        self.last_good_feedback = {
            'positions': np.array([]),
            'speeds': np.array([]),
            'loads': np.array([]),
            'currents': np.array([]),  # Add currents array
            'timestamp': 0.0,
            'valid': False
        }
        
        # Dynamic motor tracking (will be set when motors are discovered)
        self.num_motors = 0
        self.expected_motor_ids = []
        
        # Motor control state - will be set when motors are discovered
        self.motor_enabled = np.array([])
        self.motor_modes = np.array([])
        self.position_commands = np.array([])
        self.torque_commands = np.array([])
        self.velocity_commands = np.array([])  # Target constant velocity (used in velocity mode)
        self.torque_limits = np.array([])
        self.position_move_speed = np.array([])  # Speed at which to move to target position (used in position mode)
        self.acceleration_commands = np.array([])  # Acceleration for position commands
        self.position_torque_commands = np.array([])  # Torque for position commands
        
        # Hardware controller
        self.controller = None
        
        # Debug: Log motor control parameters
        self.get_logger().info(f"Motor control parameters:")
        self.get_logger().info(f"  Focus: ROS2 messaging and motor commands only")
        self.get_logger().info(f"  Default torque limit: {rt_cfg.DEFAULT_TORQUE_LIMIT}")
        self.get_logger().info(f"  Default speed: {rt_cfg.DEFAULT_SPEED}")
        self.get_logger().info(f"  Default acceleration: {rt_cfg.DEFAULT_ACCELERATION}")
        
        try:
            self.controller = FeetechController(self.serial_port, 1000000)
            self.get_logger().info(f"Hardware controller initialized for {self.serial_port}")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize hardware: {str(e)}")
        
        # Build topic/service names with prefix
        if self.name_prefix:
            motor_cmd_topic = f'/{self.name_prefix}_motor_commands'
            motor_controller_ns = f'/{self.name_prefix}_motor_controller'
            service_ns = f'/{self.name_prefix}'
        else:
            motor_cmd_topic = '/motor_commands'
            motor_controller_ns = '/motor_controller'
            service_ns = ''
        
        # JSON command subscriber for all motor operations
        self.create_subscription(
            String,
            motor_cmd_topic,
            self.json_commands_callback,
            10
        )
        
        # Publishers for status updates
        self.hardware_status_pub = self.create_publisher(
            Bool,
            f'{motor_controller_ns}/hardware_connected',
            10
        )
        
        self.status_pub = self.create_publisher(
            String,
            f'{motor_controller_ns}/status',
            10
        )
        
        # Publisher for motor feedback data
        self.motor_feedback_pub = self.create_publisher(
            JointState,
            f'{motor_controller_ns}/feedback',
            10
        )
        
        # Publisher for motor modes (published when reading modes)
        self.motor_modes_pub = self.create_publisher(
            String,
            f'{motor_controller_ns}/motor_modes',
            10
        )
        
        # Publisher for motor currents (published with feedback)
        self.motor_currents_pub = self.create_publisher(
            String,
            f'{motor_controller_ns}/motor_currents',
            10
        )
        
        # Publisher for encoder values (debug mode only)
        self.motor_encoders_pub = None
        if self.debug_mode:
            self.motor_encoders_pub = self.create_publisher(
                String,
                f'{motor_controller_ns}/motor_encoders',
                10
            )
            self.get_logger().info("Debug mode enabled: Encoder values will be published to /motor_controller/motor_encoders")
        
        # Services
        self.connect_hardware_srv = self.create_service(
            Trigger,
            f'{motor_controller_ns}/connect_hardware',
            self.connect_hardware_service
        )
        
        self.disconnect_hardware_srv = self.create_service(
            Trigger,
            f'{motor_controller_ns}/disconnect_hardware',
            self.disconnect_hardware_service
        )
        
        enable_motor_svc = f'{service_ns}_enable_motor' if service_ns else 'enable_motor'
        disable_motor_svc = f'{service_ns}_disable_motor' if service_ns else 'disable_motor'
        emergency_stop_svc = f'{service_ns}_emergency_stop' if service_ns else 'emergency_stop'
        clear_emergency_stop_svc = f'{service_ns}_clear_emergency_stop' if service_ns else 'clear_emergency_stop'
        ping_servos_svc = f'{service_ns}_ping_servos' if service_ns else 'ping_servos'
        
        self.enable_motor_service = self.create_service(
            Trigger, enable_motor_svc, self.enable_motor_callback)
        self.disable_motor_service = self.create_service(
            Trigger, disable_motor_svc, self.disable_motor_callback)
        self.emergency_stop_service = self.create_service(
            Trigger, emergency_stop_svc, self.emergency_stop_callback)
        self.clear_emergency_stop_service = self.create_service(
            Trigger, clear_emergency_stop_svc, self.clear_emergency_stop_callback)
        
        # Ping servos service
        self.ping_servos_service = self.create_service(
            Trigger, ping_servos_svc, self.ping_servos_callback)
        
        # Log the topic/service names being used
        self.get_logger().info(f"Node name: {self.get_name()}")
        self.get_logger().info(f"Command topic: {motor_cmd_topic}")
        self.get_logger().info(f"Controller namespace: {motor_controller_ns}")
        self.get_logger().info(f"Service namespace: {service_ns if service_ns else '<root>'}")
        
        # Motor control timer
        self.motor_timer = self.create_timer(0.01, self.motor_control_loop)  # 100 Hz
        
        # Status publishing timer
        self.status_timer = self.create_timer(0.2, self.publish_status)  # 5 Hz (every 200ms)
        
        # Motor modes publishing timer - publish every 0.5 seconds
        self.modes_timer = self.create_timer(0.5, self.publish_modes_periodic)
        

        
        self.get_logger().info('Motor Controller Node started')
    
    def json_commands_callback(self, msg):
        """Handle JSON commands for motor operations"""
        try:
            # Debug: Log the raw message data
            self.get_logger().debug(f"Received message data: '{msg.data}'")
            
            # Parse the JSON string from msg.data
            command_data = json.loads(msg.data)
            
            # Debug: Log the parsed command data
            self.get_logger().debug(f"Parsed command data: {command_data}")
            
            if not isinstance(command_data, list) or len(command_data) < 2:
                self.get_logger().warn("Invalid JSON command format. Expected: [\"T:X\", {parameters}]")
                return
            
            function_type = command_data[0]
            parameters = command_data[1]
            
            # Parse function type (e.g., "T0", "T1", "T10", etc.)
            if not function_type.startswith("T"):
                self.get_logger().warn(f"Invalid function type: {function_type}. Expected format: T0, T1, T10, etc.")
                return
            
            try:
                function_number = int(function_type[1:])
            except ValueError:
                self.get_logger().warn(f"Invalid function number in {function_type}")
                return
            
            # Handle different function types
            if function_number == 0:  # T0: Enable/Disable torque
                self.handle_enable_disable_command(parameters)
            elif function_number == 1:  # T1: Position commands (sync write)
                self.handle_position_command(parameters)
            elif function_number == 2:  # T2: Speed commands (sync write)
                self.handle_speed_command(parameters)
            elif function_number == 3:  # T3: Acceleration commands
                self.handle_acceleration_command(parameters)
            elif function_number == 4:  # T4: Torque commands (sync write)
                self.handle_torque_command(parameters)
            elif function_number == 5:  # T5: Torque limit commands
                self.handle_torque_limit_command(parameters)
            elif function_number == 10:  # T10: Mode commands
                self.handle_mode_command(parameters)
            elif function_number == 11:  # T11: Change servo ID
                self.handle_change_id_command(parameters)
            elif function_number == 98:  # T98: Add encoder offset
                self.handle_add_encoder_offset_command(parameters)
            elif function_number == 99:  # T99: Set zero (calibrate current position as zero)
                self.handle_set_zero_command(parameters)
            else:
                self.get_logger().warn(f"Unknown function type: {function_type}")
                
        except json.JSONDecodeError as e:
            self.get_logger().warn(f"Invalid JSON format: {e}")
        except Exception as e:
            self.get_logger().error(f"Error processing JSON command: {str(e)}")

    def handle_enable_disable_command(self, parameters):
        """Handle T0: Enable/Disable torque commands"""
        if not self.hardware_connected or not self.controller:
            self.get_logger().warn("Hardware not connected")
            return
        
        motors = parameters.get("motors", [])
        enable = parameters.get("enable", False)
        
        # Debug: Log what we received
        self.get_logger().info(f"T0: Received motors: {motors} (type: {type(motors)})")
        self.get_logger().info(f"T0: Received enable: {enable} (type: {type(enable)})")
        
        # Handle both single values and arrays for motors
        if not isinstance(motors, list):
            motors = [motors]
        
        # Debug: Log after conversion
        self.get_logger().info(f"T0: After conversion - motors: {motors}")
        
        for motor_id in motors:
            if motor_id in self.motor_ids:
                # Find motor index and update the motor_enabled array
                motor_index = self.motor_ids.index(motor_id)
                if motor_index < len(self.motor_enabled):
                    # Update hardware
                    if enable:
                        self.controller.enable_torque(motor_id)
                    else:
                        self.controller.disable_torque(motor_id)
                    
                    # Update software state
                    self.motor_enabled[motor_index] = enable
                    self.get_logger().info(f"{'Enabled' if enable else 'Disabled'} motor {motor_id}")
                else:
                    self.get_logger().warn(f"Motor index {motor_index} out of range for motor {motor_id}")
            else:
                self.get_logger().warn(f"Motor {motor_id} not found in connected motors")
        
        self.get_logger().info(f"{'Enabled' if enable else 'Disabled'} {len(motors)} motors: {motors}")
        
        # Force immediate status update to reflect changes
        self.publish_status()

    def handle_position_command(self, parameters):
        """Handle T1: Position commands (sync write)"""
        if not self.hardware_connected or not self.controller:
            self.get_logger().warn("Hardware not connected")
            return
        
        motors = parameters.get("motors", [])
        positions = parameters.get("positions", [])
        speed = parameters.get("speed", rt_cfg.DEFAULT_SPEED)
        acc = parameters.get("acc", rt_cfg.DEFAULT_ACCELERATION)
        torque = parameters.get("torque", rt_cfg.DEFAULT_TORQUE_LIMIT)
        
        # Handle both single values and arrays for motors and positions
        if not isinstance(motors, list):
            motors = [motors]
        if not isinstance(positions, list):
            positions = [positions]
        
        # Handle both single values and arrays for speed, acceleration, and torque
        if not isinstance(speed, list):
            speed = [speed] * len(motors)
        if not isinstance(acc, list):
            acc = [acc] * len(motors)
        if not isinstance(torque, list):
            torque = [torque] * len(motors)
        
        # Validate array lengths
        if len(motors) != len(positions):
            self.get_logger().warn("Number of motors and positions must match")
            return
        
        if len(speed) != len(motors) or len(acc) != len(motors) or len(torque) != len(motors):
            self.get_logger().warn("Speed, acceleration, and torque arrays must match the number of motors")
            return
        
        # Store position commands for immediate execution
        for idx, (motor_id, position_deg) in enumerate(zip(motors, positions)):
            if motor_id in self.motor_ids:
                # Find motor index in motor_ids (same as expected_motor_ids)
                motor_index = self.motor_ids.index(motor_id)
                # Store command in the appropriate array
                self.position_commands[motor_index] = position_deg
                self.motor_modes[motor_index] = 0  # Position servo mode (位置伺服模式)
                # Store speed, acceleration, and torque for this position command
                self.position_move_speed[motor_index] = speed[idx]
                self.acceleration_commands[motor_index] = acc[idx]
                self.position_torque_commands[motor_index] = torque[idx]
                # self.get_logger().debug(f"Stored position command for motor {motor_id}: {position_deg}°")
            else:
                # self.get_logger().warn(f"Motor {motor_id} not found in connected motors")
                pass
        
        # Set flag that new commands were received
        self.new_commands_received = True
        
        # self.get_logger().info(f"Position commands for {len(motors)} motors: {list(zip(motors, positions))}")
        
        # Force immediate status update to reflect mode changes
        self.publish_status()
        
        # Also execute immediately for immediate response
        servo_positions = {}
        for motor_id, position_deg in zip(motors, positions):
            if motor_id in self.motor_ids:
                encoder_value = angle_to_encoder(position_deg)
                servo_positions[motor_id] = encoder_value
                # Debug: Log angle command and encoder value
                self.get_logger().info(f"Motor {motor_id}: Command angle={position_deg:.2f}° → Encoder={encoder_value}")
        
        if servo_positions:
            # Use individual values for each motor
            motor_indices = [motors.index(motor_id) for motor_id in servo_positions.keys()]
            individual_speeds = [speed[i] for i in motor_indices]
            individual_accs = [acc[i] for i in motor_indices]
            individual_torques = [torque[i] for i in motor_indices]
            
            result = self.controller.sync_write_positions(servo_positions, individual_speeds, individual_accs, individual_torques)
            if result:
                self.get_logger().info(f"JSON T1: Position command stored and executed for {len(servo_positions)} motors")
                pass
            else:
                self.get_logger().error("JSON T1: Position command failed")

    def handle_speed_command(self, parameters):
        """Handle T2: Speed commands (sync write)"""
        if not self.hardware_connected or not self.controller:
            self.get_logger().warn("Hardware not connected")
            return
        
        motors = parameters.get("motors", [])
        speeds = parameters.get("speeds", [])
        
        # Handle both single values and arrays for motors and speeds
        if not isinstance(motors, list):
            motors = [motors]
        if not isinstance(speeds, list):
            speeds = [speeds]
        
        if len(motors) != len(speeds):
            self.get_logger().warn("Number of motors and speeds must match")
            return
        
        # Store velocity commands for continuous execution
        for motor_id, speed in zip(motors, speeds):
            if motor_id in self.motor_ids:
                # Find motor index and store command in the appropriate array
                motor_index = self.motor_ids.index(motor_id)
                self.velocity_commands[motor_index] = speed
                self.motor_modes[motor_index] = 1  # Constant speed mode (电机恒速模式)
                self.motor_enabled[motor_index] = True  # Enable this motor
                self.get_logger().debug(f"Stored velocity command for motor {motor_id}: {speed}")
            else:
                self.get_logger().warn(f"Motor {motor_id} not found in connected motors")
        
        # Set flag to indicate new commands received
        self.new_commands_received = True
        
        # Also execute immediately for immediate response
        for motor_id, speed in zip(motors, speeds):
            if motor_id in self.motor_ids:
                self.controller.set_speed(motor_id, speed)
        
        self.get_logger().info(f"Velocity commands for {len(motors)} motors: {list(zip(motors, speeds))}")

    def handle_acceleration_command(self, parameters):
        """Handle T3: Acceleration commands"""
        if not self.hardware_connected or not self.controller:
            self.get_logger().warn("Hardware not connected")
            return
        
        motors = parameters.get("motors", [])
        accelerations = parameters.get("accelerations", [])
        
        # Debug: Log what we received
        self.get_logger().info(f"T3: Received motors: {motors} (type: {type(motors)})")
        self.get_logger().info(f"T3: Received accelerations: {accelerations} (type: {type(accelerations)})")
        
        # Handle both single values and arrays for motors and accelerations
        if not isinstance(motors, list):
            motors = [motors]
        if not isinstance(accelerations, list):
            accelerations = [accelerations]
        
        # Debug: Log after conversion
        self.get_logger().info(f"T3: After conversion - motors: {motors}, accelerations: {accelerations}")
        
        if len(motors) != len(accelerations):
            self.get_logger().warn("Number of motors and accelerations must match")
            return
        
        for motor_id, acc in zip(motors, accelerations):
            if motor_id in self.motor_ids:
                self.controller.set_acceleration(motor_id, acc)
                self.get_logger().info(f"Set motor {motor_id} acceleration to {acc}")
            else:
                self.get_logger().warn(f"Motor {motor_id} not found in connected motors")
        
        self.get_logger().info(f"Set accelerations for {len(motors)} motors: {list(zip(motors, accelerations))}")

    def handle_torque_command(self, parameters):
        """Handle T4: Torque commands (sync write)"""
        if not self.hardware_connected or not self.controller:
            self.get_logger().warn("Hardware not connected")
            return
        
        motors = parameters.get("motors", [])
        torques = parameters.get("torques", [])
        
        # Handle both single values and arrays for motors and torques
        if not isinstance(motors, list):
            motors = [motors]
        if not isinstance(torques, list):
            torques = [torques]
        
        if len(motors) != len(torques):
            self.get_logger().warn("Number of motors and torques must match")
            return
        
        # Store torque commands for continuous execution
        for motor_id, torque in zip(motors, torques):
            if motor_id in self.motor_ids:
                # Find motor index and store command in the appropriate array
                motor_index = self.motor_ids.index(motor_id)
                self.torque_commands[motor_index] = torque
                self.motor_modes[motor_index] = 2  # Constant current mode (电机恒流模式)
                self.motor_enabled[motor_index] = True  # Enable this motor
                self.get_logger().debug(f"Stored torque command for motor {motor_id}: {torque}")
            else:
                self.get_logger().warn(f"Motor {motor_id} not found in connected motors")
        
        # Set flag to indicate new commands received
        self.new_commands_received = True
        
        # Also execute immediately for immediate response
        for motor_id, torque in zip(motors, torques):
            if motor_id in self.motor_ids:
                self.controller.set_torque(motor_id, torque)
        
        self.get_logger().info(f"Torque commands for {len(motors)} motors: {list(zip(motors, torques))}")

    def handle_torque_limit_command(self, parameters):
        """Handle T5: Torque limit commands"""
        if not self.hardware_connected or not self.controller:
            self.get_logger().warn("Hardware not connected")
            return
        
        motors = parameters.get("motors", [])
        torque_limits = parameters.get("torque_limits", [])
        
        # Debug: Log what we received
        self.get_logger().info(f"T5: Received motors: {motors} (type: {type(motors)})")
        self.get_logger().info(f"T5: Received torque_limits: {torque_limits} (type: {type(torque_limits)})")
        
        # Handle both single values and arrays for motors and torque_limits
        if not isinstance(motors, list):
            motors = [motors]
        if not isinstance(torque_limits, list):
            torque_limits = [torque_limits]
        
        # Debug: Log after conversion
        self.get_logger().info(f"T5: After conversion - motors: {motors}, torque_limits: {torque_limits}")
        
        if len(motors) != len(torque_limits):
            self.get_logger().warn("Number of motors and torque limits must match")
            return
        
        for motor_id, limit in zip(motors, torque_limits):
            if motor_id in self.motor_ids:
                self.controller.set_torque_limit(motor_id, limit)
                self.get_logger().info(f"Set motor {motor_id} torque limit to {limit}")
            else:
                self.get_logger().warn(f"Motor {motor_id} not found in connected motors")
        
        self.get_logger().info(f"Set torque limits for {len(motors)} motors: {list(zip(motors, torque_limits))}")

    def handle_mode_command(self, parameters):
        """Handle T10: Mode commands"""
        if not self.hardware_connected or not self.controller:
            self.get_logger().warn("Hardware not connected")
            return
        
        motors = parameters.get("motors", [])
        modes = parameters.get("modes", [])
        action = parameters.get("action", "change")
        
        # Debug: Log what we received
        self.get_logger().info(f"T10: Received motors: {motors} (type: {type(motors)})")
        self.get_logger().info(f"T10: Received modes: {modes} (type: {type(modes)})")
        
        # Handle both single values and arrays for motors and modes
        if not isinstance(motors, list):
            motors = [motors]
        if not isinstance(modes, list):
            modes = [modes]
        
        # Debug: Log after conversion
        self.get_logger().info(f"T10: After conversion - motors: {motors}, modes: {modes}")
        
        if action == "read":
            # Read modes
            mode_results = {}
            mode_names = {
                0: "Position servo mode",
                1: "Constant speed mode",
                2: "Constant current mode",
                3: "PWM open-loop speed control mode"
            }
            
            for motor_id in motors:
                if motor_id in self.motor_ids:
                    mode = self.controller.read_mode(motor_id)
                    if mode is not None:
                        mode_results[motor_id] = int(mode)
                        self.get_logger().info(f"Motor {motor_id} mode: {mode} ({mode_names.get(mode, 'Unknown')})")
                    else:
                        mode_results[motor_id] = None
                        self.get_logger().warn(f"Failed to read mode for motor {motor_id}")
                else:
                    self.get_logger().warn(f"Motor {motor_id} not found in connected motors")
            
            # Publish mode results as JSON array with motor_id and mode fields
            if mode_results:
                modes_list = []
                for motor_id, mode in mode_results.items():
                    modes_list.append({"motor_id": motor_id, "mode": mode})
                
                modes_msg = String()
                modes_msg.data = json.dumps(modes_list)
                self.motor_modes_pub.publish(modes_msg)
                # self.get_logger().info(f"Published mode results for {len(mode_results)} motors")
        else:
            # Change modes
            if len(motors) != len(modes):
                self.get_logger().warn("Number of motors and modes must match")
                return
            
            # Change modes one by one (individual writes)
            for motor_id, mode in zip(motors, modes):
                if motor_id in self.motor_ids:
                    # Update hardware - individual write for each motor
                    self.controller.change_mode(motor_id, mode)
                    
                    # Update software state - find motor index and update mode
                    motor_index = self.motor_ids.index(motor_id)
                    if motor_index < len(self.motor_modes):
                        self.motor_modes[motor_index] = mode
                        
                        # Immediately set velocity and torque to 0 when switching modes to prevent unwanted movement
                        if mode == 0:  # Position mode
                            pass  # Position mode doesn't need immediate zeroing
                        elif mode == 1:  # Speed mode
                            # Immediately set speed to 0 on the hardware
                            self.controller.set_speed(motor_id, 0)
                            self.velocity_commands[motor_index] = 0.0
                        elif mode == 2:  # Torque mode
                            # Immediately set torque to 0 on the hardware
                            self.controller.set_torque(motor_id, 0)
                            self.torque_commands[motor_index] = 0.0
                        
                        self.get_logger().info(f"Changed motor {motor_id} to mode {mode}")
                    else:
                        self.get_logger().warn(f"Motor index {motor_index} out of range for motor {motor_id}")
                else:
                    self.get_logger().warn(f"Motor {motor_id} not found in connected motors")
            
            # After mode changes, read actual modes from hardware and publish to topic
            # This ensures we publish the actual hardware state, not just what we commanded
            self._read_and_publish_modes(motors)
            
            # Force immediate status update to reflect mode changes
            self.publish_status()

    def handle_change_id_command(self, parameters):
        """Handle T11: Change servo ID"""
        if not self.hardware_connected or not self.controller:
            self.get_logger().warn("Hardware not connected")
            return
        
        current_id = parameters.get("current_id")
        new_id = parameters.get("new_id")
        
        if current_id is None or new_id is None:
            self.get_logger().warn("current_id and new_id required")
            return
        
        result = self.controller.change_id(current_id, new_id)
        if result:
            self.get_logger().info(f"Changed motor ID from {current_id} to {new_id}")
        else:
            self.get_logger().error(f"Failed to change motor ID from {current_id} to {new_id}")

    def handle_set_zero_command(self, parameters):
        """Handle T99: Set zero (calibrate current position as zero; no offset value)"""
        if not self.hardware_connected or not self.controller:
            self.get_logger().warn("Hardware not connected")
            return
        
        motors = parameters.get("motors", [])
        if not isinstance(motors, list):
            motors = [motors]
        
        for motor_id in motors:
            if motor_id in self.motor_ids:
                result = self.controller.set_zero(motor_id)
                if result:
                    self.get_logger().info(f"Set zero for motor {motor_id}")
                else:
                    self.get_logger().error(f"Failed to set zero for motor {motor_id}")

    def handle_add_encoder_offset_command(self, parameters):
        """Handle T98: Add encoder offset (motors + offsets required)"""
        if not self.hardware_connected or not self.controller:
            self.get_logger().warn("Hardware not connected")
            return
        
        motors = parameters.get("motors", [])
        offsets = parameters.get("offsets", [])
        
        if not isinstance(motors, list):
            motors = [motors]
        if not isinstance(offsets, list):
            offsets = [offsets]
        
        if not offsets or len(offsets) != len(motors):
            self.get_logger().warn("T98 (add encoder offset) requires motors and offsets arrays of same length")
            return
        
        for motor_id, offset in zip(motors, offsets):
            if motor_id in self.motor_ids:
                result = self.controller.add_encoder_offset(motor_id, offset)
                if result:
                    self.get_logger().info(f"Add encoder offset for motor {motor_id} to {offset}")
                else:
                    self.get_logger().error(f"Failed to add encoder offset for motor {motor_id}")

    def connect_hardware_service(self, request, response):
        """Service callback for connecting to hardware"""
        try:
            if self.connect_hardware():
                response.success = True
                response.message = f"Connected to {len(self.motor_ids)} motors"
                self.get_logger().info("Hardware connection service successful")
            else:
                response.success = False
                response.message = "Failed to connect to hardware"
                self.get_logger().error("Hardware connection service failed")
        except Exception as e:
            response.success = False
            response.message = f"Connection error: {str(e)}"
            self.get_logger().error(f"Hardware connection service error: {str(e)}")
        
        # Publish status update
        status_msg = Bool()
        status_msg.data = self.hardware_connected
        self.hardware_status_pub.publish(status_msg)
        
        return response
    
    def disconnect_hardware_service(self, request, response):
        """Service callback for disconnecting from hardware"""
        try:
            self.disconnect_hardware()
            response.success = True
            response.message = "Disconnected from hardware"
            self.get_logger().info("Hardware disconnection service successful")
        except Exception as e:
            response.success = False
            response.message = f"Disconnection error: {str(e)}"
            self.get_logger().error(f"Hardware disconnection service error: {str(e)}")
        
        # Publish status update
        status_msg = Bool()
        status_msg.data = self.hardware_connected
        self.hardware_status_pub.publish(status_msg)
        
        return response
    
    def emergency_stop_callback(self, request, response):
        """Enable emergency stop - stops all motor commands"""
        try:
            self.emergency_stop = True
            self.get_logger().warn("EMERGENCY STOP ACTIVATED - All motor commands blocked")
            response.success = True
            response.message = "Emergency stop activated"
        except Exception as e:
            response.success = False
            response.message = f"Failed to activate emergency stop: {str(e)}"
        return response

    def clear_emergency_stop_callback(self, request, response):
        """Clear emergency stop - allows motor commands again"""
        try:
            self.emergency_stop = False
            self.get_logger().info("Emergency stop cleared - Motor commands allowed")
            response.success = True
            response.message = "Emergency stop cleared"
        except Exception as e:
            response.success = False
            response.message = f"Failed to clear emergency stop: {str(e)}"
        return response

    def enable_motor_callback(self, request, response):
        """Enable all motors"""
        try:
            if self.hardware_connected:
                for motor_id in self.motor_ids:
                    self.controller.enable_torque(motor_id)
                self.motor_enabled.fill(True)
                self.get_logger().info("All motors enabled")
                response.success = True
                response.message = "All motors enabled"
            else:
                response.success = False
                response.message = "Hardware not connected"
        except Exception as e:
            response.success = False
            response.message = f"Failed to enable motors: {str(e)}"
        return response

    def disable_motor_callback(self, request, response):
        """Disable all motors"""
        try:
            if self.hardware_connected:
                for motor_id in self.motor_ids:
                    self.controller.disable_torque(motor_id)
                self.motor_enabled.fill(False)
                self.get_logger().info("All motors disabled")
                response.success = True
                response.message = "All motors disabled"
            else:
                response.success = False
                response.message = "Hardware not connected"
        except Exception as e:
            response.success = False
            response.message = f"Failed to disable motors: {str(e)}"
        return response

    def ping_servos_callback(self, request, response):
        """Service callback for pinging servos"""
        if not self.hardware_connected or not self.controller:
            response.success = False
            response.message = "Hardware not connected"
            self.get_logger().warn("Ping servos service called, but hardware not connected.")
            return response
        
        try:
            found_servos = self.controller.ping_servos()
            if found_servos:
                # Update motor tracking with new discovery
                self.motor_ids = sorted(found_servos)
                self.expected_motor_ids = sorted(found_servos)
                self.num_motors = len(found_servos)
                
                response.success = True
                response.message = f"Pinged servos: {found_servos} (Total: {self.num_motors})"
                self.get_logger().info(f"Ping servos service successful. Found {self.num_motors} motors: {found_servos}")
                
                # Automatically read modes for all discovered motors and publish to topic
                self._read_and_publish_modes(found_servos)
            else:
                response.success = False
                response.message = "No motors found"
                self.get_logger().warn("Ping servos service: No motors found")
        except Exception as e:
            response.success = False
            response.message = f"Ping servos error: {str(e)}"
            self.get_logger().error(f"Ping servos service error: {str(e)}")
        return response
    
    def _read_and_publish_modes(self, motor_ids):
        """Helper method to read modes from hardware and publish to topic"""
        if not self.hardware_connected or not self.controller:
            return
        
        if not motor_ids:
            motor_ids = self.motor_ids
        
        if not motor_ids:
            return
        
        try:
            # Read modes for specified motors
            modes_list = []
            for motor_id in motor_ids:
                if motor_id in self.motor_ids:
                    mode = self.controller.read_mode(motor_id)
                    if mode is not None:
                        modes_list.append({"motor_id": motor_id, "mode": int(mode)})
                    else:
                        modes_list.append({"motor_id": motor_id, "mode": -1})
            
            # Publish to topic
            if modes_list:
                modes_msg = String()
                modes_msg.data = json.dumps(modes_list)
                self.motor_modes_pub.publish(modes_msg)
                # self.get_logger().info(f"Published mode results for {len(modes_list)} motors")
        except Exception as e:
            self.get_logger().error(f"Error reading and publishing modes: {str(e)}")
    
    def publish_modes_periodic(self):
        """Periodic callback to publish motor modes every 0.5 seconds"""
        if self.hardware_connected and self.controller and self.motor_ids:
            # Read and publish modes for all connected motors
            self._read_and_publish_modes(None)  # None means read all motors

    def connect_hardware(self):
        """Connect to hardware motors"""
        if not self.controller:
            self.get_logger().warn("Hardware controller not available")
            return False
        
        try:
            # Reset last good feedback before connecting
            self.reset_last_good_feedback()
            
            # Connect to hardware
            self.controller.connect()
            
            # Ping servos to check connection and discover motors
            pinged_servos = self.controller.ping_servos()
            if pinged_servos:
                self.hardware_connected = True
                self.motor_ids = sorted(pinged_servos)
                
                self.get_logger().info(f"Motor discovery: Found {len(pinged_servos)} motors: {pinged_servos}")
                
                # Only ping motors - no commands sent during initialization
                self.get_logger().info(f"Motor discovery successful - {len(pinged_servos)} motors found")
                
                # Set the expected motor IDs based on what we found
                self.expected_motor_ids = sorted(pinged_servos)
                self.num_motors = len(self.expected_motor_ids)
                
                # Initialize last good feedback arrays for discovered motors
                self.last_good_feedback['positions'] = np.zeros(self.num_motors)
                self.last_good_feedback['speeds'] = np.zeros(self.num_motors)
                self.last_good_feedback['loads'] = np.zeros(self.num_motors)
                self.last_good_feedback['valid'] = False
                
                # Initialize motor control state arrays
                self.motor_enabled = np.zeros(self.num_motors, dtype=bool)  # All disabled by default
                self.motor_modes = np.zeros(self.num_motors, dtype=int)     # All in position mode (0)
                self.position_commands = np.zeros(self.num_motors)          # Position commands in degrees
                self.torque_commands = np.zeros(self.num_motors)            # Torque commands
                self.velocity_commands = np.zeros(self.num_motors)  # Target constant velocity (used in velocity mode)
                self.torque_limits = np.full(self.num_motors, rt_cfg.DEFAULT_TORQUE_LIMIT)  # Default torque limits
                self.position_move_speed = np.full(self.num_motors, rt_cfg.DEFAULT_SPEED)  # Speed at which to move to target position (used in position mode)
                self.acceleration_commands = np.full(self.num_motors, rt_cfg.DEFAULT_ACCELERATION)  # Acceleration for position commands
                self.position_torque_commands = np.full(self.num_motors, rt_cfg.DEFAULT_TORQUE_LIMIT)  # Torque for position commands
                
                # Motors are DISABLED by default - user must explicitly enable them
                self.get_logger().debug(f"All {self.num_motors} motors DISABLED by default - use GUI to enable")
                
                return True
            else:
                self.get_logger().error("No servos found. Check connection.")
                return False
                
        except Exception as e:
            self.get_logger().error(f"Connection failed: {str(e)}")
            return False
    
    def disconnect_hardware(self):
        """Disconnect from hardware motors"""
        if self.hardware_connected and self.controller:
            try:
                self.controller.disconnect()
                self.hardware_connected = False
                self.motor_ids = []
                # Reset motor tracking when disconnecting
                self.num_motors = 0
                self.expected_motor_ids = []
                self.get_logger().info("Disconnected from hardware")
            except Exception as e:
                self.get_logger().error(f"Disconnect error: {str(e)}")
    
    # Removed resize_arrays_for_motors - not needed for simple approach
    
    def reset_last_good_feedback(self):
        """Reset the last good feedback (useful when reconnecting or after errors)"""
        # Clear the last motor feedback
        self.last_motor_feedback = {}
        self.last_good_feedback = {
            'positions': np.array([]),
            'speeds': np.array([]),
            'loads': np.array([]),
            'currents': np.array([]),  # Add currents array
            'timestamp': 0.0,
            'valid': False
        }
        self.get_logger().info("Last good feedback reset")
    
    def get_last_feedback_age(self):
        """Get the age of the last good feedback in seconds"""
        if not self.last_good_feedback['valid']:
            return float('inf')  # No valid feedback
        return time.time() - self.last_good_feedback['timestamp']
    

    
    def motor_control_loop(self):
        """Main motor control loop - runs continuously at 100 Hz"""
        # Always read and publish feedback first (regardless of emergency stop or commands)
        if self.hardware_connected:
            self.read_motor_feedback()
            self.publish_motor_feedback()
        
        # Check emergency stop - if active, only read feedback, no commands
        if self.emergency_stop:
            return
        
                # Emergency stop is FALSE - send stored commands only if new commands were received
        if self.hardware_connected and np.any(self.motor_enabled) and self.new_commands_received:
            self.send_stored_commands()
            self.new_commands_received = False  # Reset flag after sending
    
    def send_stored_commands(self):
        """Send stored commands to motors continuously"""
        if not self.hardware_connected or not self.controller:
            return
        
        # Group motors by mode for efficient sync operations
        position_motors = []
        position_values = []
        position_speeds = []
        position_accs = []
        position_torques = []
        torque_motors = []
        torque_values = []
        velocity_motors = []
        velocity_values = []
        
        # Check each motor's mode and collect commands
        for i in range(self.num_motors):
            if self.motor_enabled[i]:
                motor_id = self.expected_motor_ids[i] if i < len(self.expected_motor_ids) else i + 1
                
                if motor_id in self.motor_ids:
                    if self.motor_modes[i] == 0:  # Position mode
                        position_motors.append(motor_id)
                        position_values.append(self.position_commands[i])
                        position_speeds.append(self.position_move_speed[i])
                        position_accs.append(self.acceleration_commands[i])
                        position_torques.append(self.position_torque_commands[i])
                    elif self.motor_modes[i] == 1:  # Velocity mode (Constant speed mode)
                        velocity_motors.append(motor_id)
                        velocity_values.append(self.velocity_commands[i])
                    elif self.motor_modes[i] == 2:  # Torque mode (Constant current mode)
                        torque_motors.append(motor_id)
                        torque_values.append(self.torque_commands[i])
        
        # Execute sync commands for each mode
        if position_motors:
            self.execute_position_commands(position_motors, position_values, position_speeds, position_accs, position_torques)
        
        if torque_motors:
            self.execute_torque_commands(torque_motors, torque_values)
        
        if velocity_motors:
            self.execute_velocity_commands(velocity_motors, velocity_values)
    
    def execute_position_commands(self, motors, positions, speeds=None, accelerations=None, torques=None):
        """Execute position commands using sync write
        
        Args:
            motors: List of motor IDs
            positions: List of position values (in degrees)
            speeds: List of speed values (optional, uses stored values if None)
            accelerations: List of acceleration values (optional, uses stored values if None)
            torques: List of torque values (optional, uses stored values if None)
        """
        servo_positions = {}
        for motor_id, position_deg in zip(motors, positions):
            encoder_value = angle_to_encoder(position_deg)
            servo_positions[motor_id] = encoder_value
        
        if servo_positions:
            # Use provided values or defaults
            if speeds is None:
                speeds = [rt_cfg.DEFAULT_SPEED] * len(motors)
            if accelerations is None:
                accelerations = [rt_cfg.DEFAULT_ACCELERATION] * len(motors)
            if torques is None:
                default_torque = self.torque_limits[0] if len(self.torque_limits) > 0 else 800
                torques = [default_torque] * len(motors)
            
            # Use individual values for each motor
            motor_indices = [motors.index(motor_id) for motor_id in servo_positions.keys()]
            individual_speeds = [speeds[i] for i in motor_indices]
            individual_accs = [accelerations[i] for i in motor_indices]
            individual_torques = [torques[i] for i in motor_indices]
            
            result = self.controller.sync_write_positions(
                servo_positions,
                individual_speeds,
                individual_accs,
                individual_torques
            )
            if result:
                self.get_logger().debug(f"Continuous position commands sent to {len(motors)} motors")
            else:
                self.get_logger().error("Continuous position commands failed")

    def execute_torque_commands(self, motors, torques):
        """Execute torque commands using sync write"""
        # Use sync write for torques if all values are the same
        if len(set(torques)) == 1:
            torque = torques[0]
            result = self.controller.set_torque(motors, torque)
            if result:
                self.get_logger().debug(f"Continuous torque commands sent to {len(motors)} motors")
            else:
                self.get_logger().error("Continuous torque commands failed")
        else:
            # Individual writes for different torque values
            for motor_id, torque in zip(motors, torques):
                self.controller.set_torque(motor_id, torque)

    def execute_velocity_commands(self, motors, velocities):
        """Execute velocity commands using sync write"""
        # Use sync write for velocities if all values are the same
        if len(set(velocities)) == 1:
            velocity = velocities[0]
            result = self.controller.set_speed(motors, velocity)
            if result:
                self.get_logger().debug(f"Continuous velocity commands sent to {len(motors)} motors")
            else:
                self.get_logger().error("Continuous velocity commands failed")
        else:
            # Individual writes for different velocity values
            for motor_id, velocity in zip(motors, velocities):
                self.controller.set_speed(motor_id, velocity)
        


    def read_motor_feedback(self):
        """Read motor feedback using individual reads with retry mechanism"""
        if not self.hardware_connected or not self.controller:
            return
        
        try:
            # Read from each motor individually with retry
            feedback_data = {}
            max_retries = 2
            
            for motor_id in self.expected_motor_ids:
                if motor_id in self.motor_ids:
                    # Try to read from this motor with retries
                    for attempt in range(max_retries):
                        try:
                            # Use individual read for each motor
                            data = self.controller.read_servo_state(motor_id)
                            if data and len(data) == 4:
                                position, speed, load, current = data
                                # Debug: Log current encoder value and angle
                                current_angle = encoder_to_angle(position)
                                self.get_logger().debug(f"Motor {motor_id}: Current Encoder={position} → Current Angle={current_angle:.2f}°")
                                feedback_data[motor_id] = (position, speed, load, current)
                                break
                            elif data and len(data) == 3:
                                # Backward compatibility: if only 3 values, add current as 0
                                position, speed, load = data
                                feedback_data[motor_id] = (position, speed, load, 0)
                                break
                            else:
                                self.get_logger().debug(f"Motor {motor_id} returned invalid data on attempt {attempt + 1}")
                        except Exception as e:
                            if attempt == max_retries - 1:
                                self.get_logger().debug(f"Failed to read motor {motor_id} after {max_retries} attempts: {str(e)}")
                                # Use last known good data for this motor
                                motor_index = self.expected_motor_ids.index(motor_id)
                                if self.last_good_feedback['valid']:
                                    # Use last known good data (already in degrees, convert to encoder for storage)
                                    position_deg = self.last_good_feedback['positions'][motor_index]
                                    position_encoder = angle_to_encoder(position_deg)
                                    # Get current from last good feedback if available, otherwise 0
                                    current = self.last_good_feedback.get('currents', [0] * len(self.expected_motor_ids))[motor_index] if 'currents' in self.last_good_feedback else 0
                                    feedback_data[motor_id] = [
                                        position_encoder,  # Store as encoder value
                                        self.last_good_feedback['speeds'][motor_index],
                                        self.last_good_feedback['loads'][motor_index],
                                        current
                                    ]
                                else:
                                    feedback_data[motor_id] = [2048, 0, 0, 0]  # Default to center position (2048 encoder units)
            
            # Store feedback for potential use
            if feedback_data:
                self.last_motor_feedback = feedback_data
            else:
                self.get_logger().warn("No feedback data received from any motors")
                
        except Exception as e:
            self.get_logger().debug(f"Failed to read motor feedback: {str(e)}")


    
    def publish_status(self):
        """Publish detailed status updates including motor states"""
        # Publish hardware connection status
        status_msg = Bool()
        status_msg.data = self.hardware_connected
        self.hardware_status_pub.publish(status_msg)
        
        # Publish detailed status with motor information
        status_text = String()
        if self.hardware_connected:
            # Create compact status for terminal display
            status_lines = []
            status_lines.append(f"Connected: {self.num_motors} motors (IDs: {self.motor_ids})")
            status_lines.append(f"Emergency Stop: {'ON' if self.emergency_stop else 'OFF'}")
            
            # Add motor summary with specific IDs
            if len(self.motor_enabled) > 0:
                enabled_motors = []
                disabled_motors = []
                for i, motor_id in enumerate(self.expected_motor_ids):
                    if i < len(self.motor_enabled):
                        if self.motor_enabled[i]:
                            enabled_motors.append(str(motor_id))
                        else:
                            disabled_motors.append(str(motor_id))
                
                if enabled_motors:
                    status_lines.append(f"Motors Enabled: {','.join(enabled_motors)}")
                else:
                    status_lines.append("Motors Enabled: none")
                
                if disabled_motors:
                    status_lines.append(f"Motors Disabled: {','.join(disabled_motors)}")
            
            # Add mode summary with specific motor IDs
            if len(self.motor_modes) > 0:
                position_motors = []
                torque_motors = []
                velocity_motors = []
                
                for i, motor_id in enumerate(self.expected_motor_ids):
                    if i < len(self.motor_modes):
                        if self.motor_modes[i] == 0:
                            position_motors.append(str(motor_id))
                        elif self.motor_modes[i] == 1:
                            velocity_motors.append(str(motor_id))
                        elif self.motor_modes[i] == 2:
                            torque_motors.append(str(motor_id))
                
                if position_motors:
                    status_lines.append(f"Position Mode: {','.join(position_motors)}")
                else:
                    status_lines.append("Position Mode: none")
                
                if torque_motors:
                    status_lines.append(f"Torque Mode: {','.join(torque_motors)}")
                else:
                    status_lines.append("Torque Mode: none")
                
                if velocity_motors:
                    status_lines.append(f"Velocity Mode: {','.join(velocity_motors)}")
                else:
                    status_lines.append("Velocity Mode: none")
            
            # Add current information if available
            if 'currents' in self.last_good_feedback and self.last_good_feedback['valid']:
                current_info = []
                for i, motor_id in enumerate(self.expected_motor_ids):
                    if i < len(self.last_good_feedback['currents']):
                        current_val = self.last_good_feedback['currents'][i]
                        current_info.append(f"M{motor_id}:{current_val:.0f}")
                if current_info:
                    status_lines.append(f"Current: {','.join(current_info)}")

            
            status_text.data = " | ".join(status_lines)
        else:
            status_text.data = "Hardware disconnected"
        
        self.status_pub.publish(status_text)
    
    def _get_mode_name(self, mode):
        """Convert mode number to readable name"""
        mode_names = {
            0: "position_servo",
            1: "constant_speed", 
            2: "constant_current",
            3: "pwm_open_loop"
        }
        return mode_names.get(mode, f"unknown_{mode}")
    
    def publish_motor_feedback(self):
        """Publish motor feedback data (position, speed, load)"""
        if not self.hardware_connected or not self.controller:
            self.get_logger().debug("Cannot publish feedback: hardware not connected or controller not available")
            return
        
        try:
            # Use the feedback data that was already read in read_motor_feedback()
            if not hasattr(self, 'last_motor_feedback') or not self.last_motor_feedback:
                self.get_logger().debug("No motor feedback data available to publish")
                return
            
            # Prepare feedback message
            feedback_msg = JointState()
            feedback_msg.header.stamp = self.get_clock().now().to_msg()
            
            # Extract data for each motor with proper validation
            positions = []
            speeds = []
            loads = []
            
            def validate_value(value, name, motor_id):
                """Validate and convert value to safe float"""
                try:
                    # Convert to float and check for valid range
                    float_val = float(value)
                    
                    # Check for NaN or infinite values only
                    if not np.isfinite(float_val):
                        self.get_logger().warn(f"Motor {motor_id} {name} is not finite: {value}, using 0.0")
                        return 0.0
                    
                    # Only check for extremely large values that are clearly corrupted
                    if abs(float_val) > 1e10:
                        self.get_logger().warn(f"Motor {motor_id} {name} value extremely large (likely corrupted): {value}, using 0.0")
                        return 0.0
                    
                    return float_val
                except (ValueError, TypeError) as e:
                    self.get_logger().warn(f"Motor {motor_id} {name} invalid value: {value}, using 0.0")
                    return 0.0
            
            currents = []  # Add current list
            
            for motor_id in self.expected_motor_ids:
                if motor_id in self.last_motor_feedback:
                    try:
                        feedback_tuple = self.last_motor_feedback[motor_id]
                        if len(feedback_tuple) == 4:
                            position, speed, load, current = feedback_tuple
                        else:
                            # Backward compatibility
                            position, speed, load = feedback_tuple
                            current = 0
                        
                        # Validate each value
                        valid_position = validate_value(position, "position", motor_id)
                        valid_speed = validate_value(speed, "speed", motor_id)
                        valid_load = validate_value(load, "load", motor_id)
                        valid_current = validate_value(current, "current", motor_id)
                        
                        # Convert encoder position to degrees for publishing
                        position_deg = encoder_to_angle(valid_position)
                        
                        positions.append(position_deg)  # Publish in degrees
                        speeds.append(valid_speed)
                        loads.append(valid_load)
                        currents.append(valid_current)
                    except Exception as e:
                        self.get_logger().warn(f"Error processing motor {motor_id} data: {e}")
                        # Use last good feedback for this motor if available
                        motor_index = self.expected_motor_ids.index(motor_id)
                        if self.last_good_feedback['valid']:
                            positions.append(self.last_good_feedback['positions'][motor_index])
                            speeds.append(self.last_good_feedback['speeds'][motor_index])
                            loads.append(self.last_good_feedback['loads'][motor_index])
                            current_val = self.last_good_feedback.get('currents', [0] * len(self.expected_motor_ids))[motor_index] if 'currents' in self.last_good_feedback else 0
                            currents.append(current_val)
                            self.get_logger().info(f"Motor {motor_id}: Using last known good feedback")
                        else:
                            positions.append(0.0)
                            speeds.append(0.0)
                            loads.append(0.0)
                            currents.append(0.0)
                else:
                    # Motor not in data - use last good feedback if available
                    motor_index = self.expected_motor_ids.index(motor_id)
                    if self.last_good_feedback['valid']:
                        positions.append(self.last_good_feedback['positions'][motor_index])
                        speeds.append(self.last_good_feedback['speeds'][motor_index])
                        loads.append(self.last_good_feedback['loads'][motor_index])
                        current_val = self.last_good_feedback.get('currents', [0] * len(self.expected_motor_ids))[motor_index] if 'currents' in self.last_good_feedback else 0
                        currents.append(current_val)
                        self.get_logger().info(f"Motor {motor_id}: No data available, using last known good feedback")
                    else:
                        positions.append(0.0)
                        speeds.append(0.0)
                        loads.append(0.0)
                        currents.append(0.0)
                        self.get_logger().warn(f"Motor {motor_id}: No data available and no last good feedback")
            
            # Store data in JointState message
            feedback_msg.name = [f"motor_{i+1}" for i in range(len(self.expected_motor_ids))]
            feedback_msg.position = positions  # Motor positions (now in degrees)
            feedback_msg.velocity = speeds     # Motor speeds
            feedback_msg.effort = loads        # Motor loads (torque)
            
            # Store this as last good feedback for future fallback
            self.last_good_feedback['positions'] = np.array(positions)
            self.last_good_feedback['speeds'] = np.array(speeds)
            self.last_good_feedback['loads'] = np.array(loads)
            self.last_good_feedback['currents'] = np.array(currents)  # Store currents
            self.last_good_feedback['timestamp'] = time.time()
            self.last_good_feedback['valid'] = True
            
            # Debug: Log current state summary for all motors
            if len(positions) > 0:
                debug_lines = []
                for i, motor_id in enumerate(self.expected_motor_ids):
                    if i < len(positions):
                        # Get current encoder value from feedback
                        current_encoder = self.last_motor_feedback.get(motor_id, [0, 0, 0])[0] if motor_id in self.last_motor_feedback else 0
                        current_angle = positions[i]
                        # Get command angle if available
                        motor_index = self.motor_ids.index(motor_id) if motor_id in self.motor_ids else -1
                        command_angle = self.position_commands[motor_index] if motor_index >= 0 and motor_index < len(self.position_commands) else None
                        command_encoder = angle_to_encoder(command_angle) if command_angle is not None else None
                        
                        if command_angle is not None:
                            debug_lines.append(f"M{motor_id}: Cmd={command_angle:.1f}°(enc:{command_encoder}) | Curr={current_angle:.1f}°(enc:{int(current_encoder)})")
                        else:
                            debug_lines.append(f"M{motor_id}: Curr={current_angle:.1f}°(enc:{int(current_encoder)})")
                self.get_logger().debug(" | ".join(debug_lines))
            
            # Publish feedback
            self.motor_feedback_pub.publish(feedback_msg)
            
            # Publish current values as JSON array (similar to motor_modes format)
            if currents:
                currents_list = []
                for i, motor_id in enumerate(self.expected_motor_ids):
                    if i < len(currents):
                        currents_list.append({"motor_id": motor_id, "current": float(currents[i])})
                
                if currents_list:
                    currents_msg = String()
                    currents_msg.data = json.dumps(currents_list)
                    self.motor_currents_pub.publish(currents_msg)
            
            # Publish encoder values in debug mode
            if self.debug_mode and self.motor_encoders_pub:
                encoders_list = []
                for i, motor_id in enumerate(self.expected_motor_ids):
                    if motor_id in self.last_motor_feedback:
                        feedback_tuple = self.last_motor_feedback[motor_id]
                        encoder_value = feedback_tuple[0] if len(feedback_tuple) > 0 else 0
                        encoders_list.append({"motor_id": motor_id, "encoder": int(encoder_value)})
                
                if encoders_list:
                    encoders_msg = String()
                    encoders_msg.data = json.dumps(encoders_list)
                    self.motor_encoders_pub.publish(encoders_msg)
            
        except Exception as e:
            self.get_logger().error(f"Error publishing motor feedback: {str(e)}")
            self.get_logger().error(f"Traceback: {traceback.format_exc()}")

def main(args=None):
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Motor Controller Node for ROS2')
    parser.add_argument('--prefix', type=str, default='',
                        help='Prefix for node name and topics (e.g., "master" -> "/master_motor_commands", "tongue" -> "/tongue_motor_commands")')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Enable debug mode (publishes encoder values to /motor_controller/motor_encoders)')
    parser.add_argument('--port', type=str, default=None,
                        help='Serial port name (e.g., "COM9" on Windows or "/dev/ttyUSB0" on Linux). If not provided, uses value from rt_config.py')
    parser.add_argument('--ros-args', action='store_true', help='ROS2 argument (ignored)')
    parser.add_argument('--ros-args-remap', nargs='*', help='ROS2 remap arguments (ignored)')
    
    # Parse known args (ignore unknown ROS2 args)
    parsed_args, unknown = parser.parse_known_args(args)
    
    name_prefix = parsed_args.prefix.strip() if parsed_args.prefix else ''
    debug_mode = parsed_args.debug
    serial_port = parsed_args.port.strip() if parsed_args.port else None
    
    rclpy.init(args=args)
    node = MotorControllerNode(name_prefix=name_prefix, debug_mode=debug_mode, serial_port=serial_port)
    
    # Try to connect to hardware and ping motors automatically
    if not node.connect_hardware():
        node.get_logger().warn("Running in simulation mode - no hardware connected")
    else:
        node.get_logger().info(f"Node started successfully with {node.num_motors} motors discovered")
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.disconnect_hardware()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
