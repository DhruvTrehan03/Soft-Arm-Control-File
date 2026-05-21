#!/usr/bin/env python3
"""
Test script for SMS_STS Controller
Demonstrates basic functionality of the SMS_STS servo controller
"""

import sys
import time
import os

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from sms_sts_controller import SMS_STSController


def test_basic_functionality():
    """Test basic SMS_STS controller functionality"""
    print("=" * 60)
    print("SMS_STS Controller Test")
    print("=" * 60)
    
    # Create controller instance
    controller = SMS_STSController()
    
    try:
        # Connect to servos
        print("Connecting to servos...")
        if not controller.connect():
            print("❌ Failed to connect!")
            return False
        
        print("✅ Connected successfully!")
        
        # Scan for servos
        print("\nScanning for servos...")
        found_servos = controller.ping_servos()
        
        if not found_servos:
            print("❌ No servos found!")
            return False
        
        print(f"✅ Found {len(found_servos)} servo(s): {found_servos}")
        
        # Test individual servo operations
        test_servo = found_servos[0]
        print(f"\nTesting individual servo operations on servo {test_servo}...")
        
        # Enable torque
        if controller.enable_torque(test_servo):
            print("✅ Torque enabled")
        else:
            print("❌ Failed to enable torque")
            return False
        
        # Read current state
        state = controller.read_servo_state(test_servo)
        if state:
            position, speed, load = state
            print(f"✅ Current state - Position: {position}, Speed: {speed}, Load: {load}")
        else:
            print("❌ Failed to read servo state")
        
        # Set position to center
        center_position = 2048
        print(f"\nMoving servo {test_servo} to center position ({center_position})...")
        if controller.set_position(test_servo, center_position):
            print("✅ Position command sent")
            time.sleep(2)  # Wait for movement
            
            # Read new state
            state = controller.read_servo_state(test_servo)
            if state:
                position, speed, load = state
                print(f"✅ New state - Position: {position}, Speed: {speed}, Load: {load}")
        else:
            print("❌ Failed to set position")
        
        # Test multiple servo operations
        if len(found_servos) > 1:
            print(f"\nTesting multiple servo operations on {len(found_servos)} servos...")
            
            # Enable torque for all servos
            if controller.enable_torque(found_servos):
                print("✅ Torque enabled for all servos")
            else:
                print("❌ Failed to enable torque for all servos")
            
            # Set all servos to different positions
            positions = {}
            for i, servo_id in enumerate(found_servos):
                # Spread servos across different positions
                pos = 1500 + (i * 200)  # 1500, 1700, 1900, etc.
                positions[servo_id] = pos
            
            print(f"Setting positions: {positions}")
            if controller.sync_write_positions(positions, speed=100, acc=50):
                print("✅ Sync position command sent")
                time.sleep(3)  # Wait for movement
                
                # Read all servo states
                states = controller.read_servo_state(found_servos)
                if states:
                    print("✅ All servo states:")
                    for servo_id, (pos, spd, ld) in states.items():
                        print(f"   Servo {servo_id}: Position={pos}, Speed={spd}, Load={ld}")
                else:
                    print("❌ Failed to read all servo states")
            else:
                print("❌ Failed to sync write positions")
        
        # Test mode reading
        print(f"\nTesting mode reading...")
        mode = controller.read_mode(test_servo)
        if mode is not None:
            mode_names = {
                0: "Position servo mode",
                1: "Constant speed mode", 
                2: "Constant current mode",
                3: "PWM open-loop speed control mode"
            }
            print(f"✅ Servo {test_servo} mode: {mode} ({mode_names.get(mode, 'Unknown')})")
        else:
            print("❌ Failed to read mode")
        
        # Print final controller status
        print("\n" + "=" * 40)
        controller.print_status()
        print("=" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    
    finally:
        # Always disconnect
        print("\nDisconnecting...")
        controller.disconnect()
        print("✅ Disconnected")


def test_advanced_features():
    """Test advanced SMS_STS controller features"""
    print("\n" + "=" * 60)
    print("Advanced SMS_STS Controller Test")
    print("=" * 60)
    
    controller = SMS_STSController()
    
    try:
        if not controller.connect():
            print("❌ Failed to connect!")
            return False
        
        found_servos = controller.ping_servos()
        if not found_servos:
            print("❌ No servos found!")
            return False
        
        test_servo = found_servos[0]
        print(f"Testing advanced features on servo {test_servo}...")
        
        # Test acceleration setting
        print("\nTesting acceleration setting...")
        if controller.set_acceleration(test_servo, 100):
            print("✅ Acceleration set to 100")
        else:
            print("❌ Failed to set acceleration")
        
        # Test speed setting
        print("\nTesting speed setting...")
        if controller.set_speed(test_servo, 200):
            print("✅ Speed set to 200")
        else:
            print("❌ Failed to set speed")
        
        # Test zero offset calibration
        print("\nTesting zero offset calibration...")
        if controller.set_zero_offset(test_servo, 1024):
            print("✅ Zero offset calibration completed")
        else:
            print("❌ Failed zero offset calibration")
        
        return True
        
    except Exception as e:
        print(f"❌ Advanced test failed with exception: {e}")
        return False
    
    finally:
        controller.disconnect()


def main():
    """Main test function"""
    print("SMS_STS Controller Test Suite")
    print("This script tests the SMS_STS servo controller functionality")
    print("Make sure your SMS_STS servos are connected and powered on!")
    
    # Ask user if they want to proceed
    response = input("\nDo you want to proceed with the test? (y/n): ").lower().strip()
    if response != 'y':
        print("Test cancelled.")
        return
    
    # Run basic functionality test
    basic_success = test_basic_functionality()
    
    if basic_success:
        # Ask if user wants to run advanced tests
        response = input("\nBasic test completed successfully! Run advanced tests? (y/n): ").lower().strip()
        if response == 'y':
            test_advanced_features()
    
    print("\n" + "=" * 60)
    print("Test Suite Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
