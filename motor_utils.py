"""
Utility functions for motor control and data processing
"""

import numpy as np
import time
from typing import Dict, List, Tuple, Optional

def angle_to_encoder(angle_deg: float, encoder_resolution: int = 4096) -> int:
    """
    Convert angle in degrees to encoder position
    Using 2048 as the zero point (middle of encoder range)
    
    Args:
        angle_deg: Angle in degrees (can be beyond ±180° for multi-turn)
        encoder_resolution: Encoder resolution (default: 4096)
        
    Returns:
        Encoder position (2048 = 0°, 0 = -180°, 4096 = +180°, can go beyond 4096)
    """
    # Convert angle to encoder position
    # 2048 = 0°, 0 = -180°, 4096 = +180°
    encoder_pos = int(2048 + (angle_deg * 2048) / 180.0)
    
    # Ensure encoder position is within valid range
    # encoder_pos = max(0, min(encoder_pos, encoder_resolution - 1))
    
    return encoder_pos

def encoder_to_angle(encoder_pos: int, encoder_resolution: int = 4096) -> float:
    """
    Convert encoder position to accumulated angle in degrees
    Using 2048 as the zero point (middle of encoder range)
    Encoder values can go beyond 4096 for multi-turn scenarios
    
    Args:
        encoder_pos: Encoder position (can be beyond 0-4095 for multi-turn)
        encoder_resolution: Encoder resolution (default: 4096)
        
    Returns:
        Accumulated angle in degrees (2048 = 0°, can be beyond ±180°)
    """
    # Convert encoder position to accumulated angle
    # 2048 = 0°, 0 = -180°, 4096 = +180°, 6144 = +360°, etc.
    accumulated_angle = ((encoder_pos - 2048) * 180.0) / 2048
    
    return accumulated_angle

def normalize_angle(angle_deg: float) -> float:
    """
    Normalize angle to 0-360 degree range
    
    Args:
        angle_deg: Input angle in degrees
        
    Returns:
        Normalized angle in degrees (0-360)
    """
    return angle_deg % 360.0

def angle_difference(angle1_deg: float, angle2_deg: float) -> float:
    """
    Calculate the smallest difference between two angles
    
    Args:
        angle1_deg: First angle in degrees
        angle2_deg: Second angle in degrees
        
    Returns:
        Angle difference in degrees (-180 to 180)
    """
    diff = normalize_angle(angle2_deg - angle1_deg)
    if diff > 180:
        diff -= 360
    return diff

def smooth_angle_transition(current_angle: float, target_angle: float, 
                          max_step: float = 5.0) -> float:
    """
    Smoothly transition from current angle to target angle
    
    Args:
        current_angle: Current angle in degrees
        target_angle: Target angle in degrees
        max_step: Maximum step size in degrees
        
    Returns:
        Next angle in the smooth transition
    """
    diff = angle_difference(current_angle, target_angle)
    
    if abs(diff) <= max_step:
        return target_angle
    else:
        step = max_step if diff > 0 else -max_step
        return normalize_angle(current_angle + step)

def calculate_motor_velocity(current_angle: float, previous_angle: float, 
                           dt: float) -> float:
    """
    Calculate motor angular velocity
    
    Args:
        current_angle: Current angle in degrees
        previous_angle: Previous angle in degrees
        dt: Time step in seconds
        
    Returns:
        Angular velocity in degrees/second
    """
    if dt <= 0:
        return 0.0
    
    # Handle angle wrapping
    diff = angle_difference(previous_angle, current_angle)
    velocity = diff / dt
    
    return velocity

def filter_motor_data(motor_data: Dict, alpha: float = 0.8) -> Dict:
    """
    Apply low-pass filter to motor data
    
    Args:
        motor_data: Dictionary of motor data
        alpha: Filter coefficient (0-1, higher = more smoothing)
        
    Returns:
        Filtered motor data
    """
    filtered_data = {}
    
    for motor_id, data in motor_data.items():
        filtered_data[motor_id] = {
            'angle': data['angle'],  # Keep angle as is for now
            'speed': data['speed'],
            'load': data['load'],
            'position': data['position']
        }
    
    return filtered_data

def detect_motor_anomalies(motor_data: Dict, 
                          angle_threshold: float = 10.0,
                          speed_threshold: float = 1000.0,
                          load_threshold: float = 1000.0) -> List[Dict]:
    """
    Detect anomalies in motor data
    
    Args:
        motor_data: Dictionary of motor data
        angle_threshold: Maximum angle change threshold
        speed_threshold: Maximum speed threshold
        load_threshold: Maximum load threshold
        
    Returns:
        List of detected anomalies
    """
    anomalies = []
    
    for motor_id, data in motor_data.items():
        # Check for extreme values
        if abs(data['angle']) > 360:
            anomalies.append({
                'motor_id': motor_id,
                'type': 'invalid_angle',
                'value': data['angle'],
                'message': f"Motor {motor_id}: Invalid angle value {data['angle']:.2f}°"
            })
        
        if abs(data['speed']) > speed_threshold:
            anomalies.append({
                'motor_id': motor_id,
                'type': 'high_speed',
                'value': data['speed'],
                'message': f"Motor {motor_id}: High speed {data['speed']}"
            })
        
        if abs(data['load']) > load_threshold:
            anomalies.append({
                'motor_id': motor_id,
                'type': 'high_load',
                'value': data['load'],
                'message': f"Motor {motor_id}: High load {data['load']}"
            })
    
    return anomalies

def calculate_motor_statistics(motor_data: Dict) -> Dict:
    """
    Calculate statistics for motor data
    
    Args:
        motor_data: Dictionary of motor data
        
    Returns:
        Dictionary of statistics
    """
    if not motor_data:
        return {}
    
    angles = [data['angle'] for data in motor_data.values()]
    speeds = [data['speed'] for data in motor_data.values()]
    loads = [data['load'] for data in motor_data.values()]
    
    stats = {
        'angle': {
            'mean': np.mean(angles),
            'std': np.std(angles),
            'min': np.min(angles),
            'max': np.max(angles)
        },
        'speed': {
            'mean': np.mean(speeds),
            'std': np.std(speeds),
            'min': np.min(speeds),
            'max': np.max(speeds)
        },
        'load': {
            'mean': np.mean(loads),
            'std': np.std(loads),
            'min': np.min(loads),
            'max': np.max(loads)
        }
    }
    
    return stats

def validate_motor_commands(commands: Dict, 
                          min_angle: float = 0.0,
                          max_angle: float = 360.0) -> Tuple[bool, List[str]]:
    """
    Validate motor commands before sending
    
    Args:
        commands: Dictionary of motor_id: angle_deg pairs
        min_angle: Minimum allowed angle
        max_angle: Maximum allowed angle
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    for motor_id, angle in commands.items():
        if not isinstance(motor_id, int) or motor_id < 0:
            errors.append(f"Invalid motor ID: {motor_id}")
        
        if not isinstance(angle, (int, float)):
            errors.append(f"Invalid angle type for motor {motor_id}: {type(angle)}")
        elif angle < min_angle or angle > max_angle:
            errors.append(f"Angle {angle}° for motor {motor_id} outside valid range [{min_angle}, {max_angle}]")
    
    return len(errors) == 0, errors

def format_motor_data_for_logging(motor_data: Dict) -> str:
    """
    Format motor data for logging
    
    Args:
        motor_data: Dictionary of motor data
        
    Returns:
        Formatted string for logging
    """
    if not motor_data:
        return "No motor data"
    
    lines = []
    for motor_id, data in motor_data.items():
        line = f"Motor {motor_id}: {data['angle']:.1f}° | Speed: {data['speed']} | Load: {data['load']}"
        lines.append(line)
    
    return " | ".join(lines)

def create_motor_sequence(sequence_data: List[Dict], 
                         duration: float = 1.0,
                         interpolation: str = 'linear') -> List[Dict]:
    """
    Create interpolated motor sequence
    
    Args:
        sequence_data: List of target positions with timestamps
        duration: Total duration in seconds
        interpolation: Interpolation method ('linear', 'cubic', 'step')
        
    Returns:
        List of interpolated motor positions
    """
    if not sequence_data or len(sequence_data) < 2:
        return sequence_data
    
    # Sort by timestamp
    sequence_data = sorted(sequence_data, key=lambda x: x.get('timestamp', 0))
    
    # Extract timestamps and motor positions
    timestamps = [data.get('timestamp', i * duration / (len(sequence_data) - 1)) 
                 for i, data in enumerate(sequence_data)]
    
    motor_ids = list(sequence_data[0].get('motors', {}).keys())
    
    # Create interpolated sequence
    interpolated_sequence = []
    num_steps = max(10, int(duration * 10))  # At least 10 steps
    
    for step in range(num_steps):
        t = step * duration / (num_steps - 1)
        
        # Find interpolation interval
        for i in range(len(timestamps) - 1):
            if timestamps[i] <= t <= timestamps[i + 1]:
                # Linear interpolation
                alpha = (t - timestamps[i]) / (timestamps[i + 1] - timestamps[i])
                
                motors = {}
                for motor_id in motor_ids:
                    angle1 = sequence_data[i].get('motors', {}).get(motor_id, 0)
                    angle2 = sequence_data[i + 1].get('motors', {}).get(motor_id, 0)
                    
                    # Interpolate angle
                    interpolated_angle = angle1 + alpha * (angle2 - angle1)
                    motors[motor_id] = normalize_angle(interpolated_angle)
                
                interpolated_sequence.append({
                    'timestamp': t,
                    'motors': motors
                })
                break
    
    return interpolated_sequence 