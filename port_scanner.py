#!/usr/bin/env python3
"""
USB/Serial Port Scanner for Raspberry Pi
Automatically detects available serial ports and tests connectivity
"""

import serial
import serial.tools.list_ports
import time
import os
import sys
from typing import List, Dict, Optional, Tuple

class PortScanner:
    def __init__(self):
        """Initialize the port scanner"""
        self.available_ports = []
        self.working_ports = []
        
    def scan_available_ports(self):
        ports = []
        # 1. pyserial detected ports
        for port in serial.tools.list_ports.comports():
            ports.append(port.device)
        # 2. fallback direct filesystem scan (IMPORTANT)
        import glob
        for pattern in ["/dev/ttyUSB*", "/dev/ttyACM*", "/dev/ttyCH341*", "/dev/ttyS*", "/dev/ttyAMA*"]:
            for p in glob.glob(pattern):
                if p not in ports:
                    ports.append(p)
        self.available_ports = ports
        return ports
    
    def test_port_connectivity(self, port_name: str, baudrate: int = 1000000, 
                              timeout: float = 1.0) -> bool:
        """
        Test if a port can be opened and closed successfully
        
        Args:
            port_name: Name of the port to test
            baudrate: Baudrate to test with
            timeout: Connection timeout in seconds
            
        Returns:
            True if port is accessible, False otherwise
        """
        try:
            # Try to open the port
            ser = serial.Serial(
                port=port_name,
                baudrate=baudrate,
                timeout=timeout,
                write_timeout=timeout
            )
            
            # Check if port is actually open
            if ser.is_open:
                ser.close()
                return True
            else:
                return False
                
        except (serial.SerialException, OSError, ValueError) as e:
            print(f"Error testing port {port_name}: {e}")
            return False
    
    def find_working_ports(self, baudrate: int = 1000000) -> List[str]:
        """
        Find all working serial ports at the specified baudrate
        
        Args:
            baudrate: Baudrate to test ports with
        Returns:
            List of working port names
        """
        working_ports = []
        
        # First scan for available ports
        available_ports = self.scan_available_ports()
        
        if not available_ports:
            print("No serial ports found!")
            return []
        
        print(f"Found {len(available_ports)} available ports:")
        for port in available_ports:
            print(f"  - {port}")
        
        print(f"\nTesting ports at {baudrate} baud...")
        
        # Test each port
        for port in available_ports:
            print(f"Testing {port}...", end=" ")
            if self.test_port_connectivity(port, baudrate):
                working_ports.append(port)
                print("✓ WORKING")
            else:
                print("✗ FAILED")
        
        self.working_ports = working_ports
        return working_ports
    
    def get_port_info(self, port_name: str) -> Optional[Dict]:
        """
        Get detailed information about a specific port
        
        Args:
            port_name: Name of the port
            
        Returns:
            Dictionary with port information or None if not found
        """
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            if port.device == port_name:
                return {
                    'device': port.device,
                    'name': port.name,
                    'description': port.description,
                    'hwid': port.hwid,
                    'vid': port.vid,
                    'pid': port.pid,
                    'serial_number': port.serial_number,
                    'manufacturer': port.manufacturer,
                    'product': port.product
                }
        
        return None
    
    def suggest_best_port(self, preferred_vendor: str = None) -> Optional[str]:
        """
        Suggest the best port to use based on available options
        
        Args:
            preferred_vendor: Preferred vendor name (e.g., 'FTDI', 'Silicon Labs')
            
        Returns:
            Suggested port name or None if no ports available
        """
        working_ports = self.find_working_ports()
        
        if not working_ports:
            return None
        
        # If we have a preferred vendor, prioritize it
        if preferred_vendor:
            for port in working_ports:
                info = self.get_port_info(port)
                if info and info.get('manufacturer'):
                    if preferred_vendor.lower() in info['manufacturer'].lower():
                        return port
        
        # Otherwise, prioritize common USB-to-serial devices
        priority_patterns = [
            '/dev/ttyUSB',  # USB-to-Serial adapters
            '/dev/ttyACM',  # Arduino/Teensy devices
            '/dev/ttyS',    # Hardware serial ports
            '/dev/ttyAMA',  # Raspberry Pi hardware serial
            '/dev/ttyCH341USB',   #CH341 Driver on Jetson 
        ]
        
        for pattern in priority_patterns:
            for port in working_ports:
                if pattern in port:
                    return port
        
        # Return first working port if no priority matches
        return working_ports[0] if working_ports else None
    
    def print_port_summary(self):
        """Print a summary of all available and working ports"""
        print("\n" + "="*60)
        print("PORT SCANNING SUMMARY")
        print("="*60)
        
        # Available ports
        print(f"Available ports: {len(self.available_ports)}")
        for port in self.available_ports:
            info = self.get_port_info(port)
            if info:
                print(f"  {port}: {info.get('description', 'Unknown')}")
                if info.get('manufacturer'):
                    print(f"    Manufacturer: {info['manufacturer']}")
                if info.get('product'):
                    print(f"    Product: {info['product']}")
        
        # Working ports
        print(f"\nWorking ports: {len(self.working_ports)}")
        for port in self.working_ports:
            print(f"  ✓ {port}")
        
        # Best suggestion
        best_port = self.suggest_best_port()
        if best_port:
            print(f"\nSuggested port: {best_port}")
        else:
            print("\nNo working ports found!")

def main():
    """Main function for command-line usage"""
    scanner = PortScanner()
    
    print("USB/Serial Port Scanner for Raspberry Pi")
    print("="*40)
    
    # Scan for working ports
    working_ports = scanner.find_working_ports()
    
    # Print summary
    scanner.print_port_summary()
    
    # Return exit code based on results
    if working_ports:
        print(f"\nSuccessfully found {len(working_ports)} working port(s)")
        return 0
    else:
        print("\nNo working ports found!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
