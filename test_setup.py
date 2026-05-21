#!/usr/bin/env python3
"""
Test script to verify HardwareControl setup on Raspberry Pi
Run this after setup to ensure everything is working
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import numpy
        print("✓ numpy imported successfully")
    except ImportError as e:
        print(f"✗ numpy import failed: {e}")
        return False
    
    try:
        import serial
        print("✓ pyserial imported successfully")
    except ImportError as e:
        print(f"✗ pyserial import failed: {e}")
        return False
    
    try:
        from port_scanner import PortScanner
        print("✓ port_scanner imported successfully")
    except ImportError as e:
        print(f"✗ port_scanner import failed: {e}")
        return False
    
    try:
        from feetech_controller import FeetechController
        print("✓ feetech_controller imported successfully")
    except ImportError as e:
        print(f"✗ feetech_controller import failed: {e}")
        return False
    
    try:
        from motor_utils import angle_to_encoder, encoder_to_angle
        print("✓ motor_utils imported successfully")
    except ImportError as e:
        print(f"✗ motor_utils import failed: {e}")
        return False
    
    return True

def test_port_scanner():
    """Test the port scanner functionality"""
    print("\nTesting port scanner...")
    
    try:
        from port_scanner import PortScanner
        scanner = PortScanner()
        
        # Scan for available ports
        available_ports = scanner.scan_available_ports()
        print(f"Found {len(available_ports)} available ports: {available_ports}")
        
        if available_ports:
            # Test port connectivity
            working_ports = scanner.find_working_ports()
            print(f"Found {len(working_ports)} working ports: {working_ports}")
            
            if working_ports:
                best_port = scanner.suggest_best_port()
                print(f"Suggested best port: {best_port}")
                return True
            else:
                print("No working ports found")
                return False
        else:
            print("No ports found")
            return False
            
    except Exception as e:
        print(f"Port scanner test failed: {e}")
        return False

def test_feetech_controller():
    """Test the Feetech controller initialization"""
    print("\nTesting Feetech controller...")
    
    try:
        from feetech_controller import FeetechController
        
        # Test auto-port detection
        controller = FeetechController()  # This should auto-detect port
        print(f"Controller initialized with port: {controller.port_name}")
        
        # Test connection (without actually connecting)
        print("Controller initialization successful")
        return True
        
    except Exception as e:
        print(f"Feetech controller test failed: {e}")
        return False

def test_motor_utils():
    """Test motor utility functions"""
    print("\nTesting motor utilities...")
    
    try:
        from motor_utils import angle_to_encoder, encoder_to_angle
        
        # Test angle conversions
        test_angle = 90.0
        encoder_pos = angle_to_encoder(test_angle)
        converted_angle = encoder_to_angle(encoder_pos)
        
        print(f"Test angle: {test_angle}°")
        print(f"Encoder position: {encoder_pos}")
        print(f"Converted back: {converted_angle}°")
        
        # Check if conversion is reasonable (within 1 degree)
        if abs(test_angle - converted_angle) < 1.0:
            print("✓ Angle conversion test passed")
            return True
        else:
            print(f"✗ Angle conversion test failed: {test_angle}° != {converted_angle}°")
            return False
            
    except Exception as e:
        print(f"Motor utilities test failed: {e}")
        return False

def main():
    """Main test function"""
    print("HardwareControl Setup Test for Raspberry Pi")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 4
    
    # Run all tests
    if test_imports():
        tests_passed += 1
    
    if test_port_scanner():
        tests_passed += 1
    
    if test_feetech_controller():
        tests_passed += 1
    
    if test_motor_utils():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"TEST SUMMARY: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✓ All tests passed! Setup is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
