#!/usr/bin/env python
#
# *********     Feetech HLS Controller      *********
#
# A comprehensive controller for Feetech HLS servos with the following features:
# - Ping/scan servos
# - Change servo IDs
# - Sync read position, speed, load
# - Sync write position commands
# - Individual servo control
# - Real-time monitoring
#

import sys
import time
import threading
from typing import List, Dict, Tuple, Optional, Union
import os

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from scservo_sdk import *                      # Uses FTServo SDK library
try:
    from port_scanner import PortScanner
    PORT_SCANNER_AVAILABLE = True
except Exception:
    PortScanner = None
    PORT_SCANNER_AVAILABLE = False


class FeetechController:
    def __init__(self, port_name: str = None, baudrate: int = 1000000):
        """
        Initialize the Feetech controller
        
        Args:
            port_name: Serial port name (Windows: COM1, Linux: /dev/ttyUSB0)
                      If None, will auto-detect on Raspberry Pi
            baudrate: Communication baudrate (default: 1000000)
        """
        self.port_name = port_name
        self.baudrate = baudrate
        
        # Auto-detect port if not specified
        if self.port_name is None:
            self._auto_detect_port()
        self.portHandler = None
        self.packetHandler = None
        self.connected = False
        self.monitoring = False
        self.monitor_thread = None
        self.found_servos = []
        
        # Position conversion factor (can be calibrated)
        # For 0-4096 encoder range: 360° / 4096 = 0.087890625° per unit
        self.position_conversion_factor = 0.087890625  # degrees per unit
        
        # Track sync write parameters to avoid redundant operations
        self.last_sync_write = {
            'servo_ids': [],
            'address': None,
            'value': None,
            'data_length': None
        }
    
    def _auto_detect_port(self):
        """Auto-detect the best available serial port"""
        if not PORT_SCANNER_AVAILABLE:
            print("Port scanner not available, using default port")
            return
        
        try:
            scanner = PortScanner()
            best_port = scanner.suggest_best_port()
            
            if best_port:
                self.port_name = best_port
                print(f"Auto-detected port: {self.port_name}")
            else:
                print("No working ports found, using default")
                # Fallback to common ports
                import platform
                if platform.system() == 'Linux':
                    self.port_name = '/dev/ttyCH341USB0'
                else:
                    self.port_name = 'COM4'
        except Exception as e:
            print(f"Error during auto-detection: {e}")
            # Fallback to common ports
            import platform
            if platform.system() == 'Linux':
                self.port_name = '/dev/ttyCH341USB0'
            else:
                self.port_name = 'COM4'
    
    def _check_sync_write_params(self, servo_ids: List[int], address: int, value: int, data_length: int) -> bool:
        """
        Check if sync write parameters have changed and update tracking
        
        Args:
            servo_ids: List of servo IDs
            address: Register address
            value: Value to write
            data_length: Data length (1 or 2 bytes)
            
        Returns:
            True if parameters changed (need to clear and add new params), False if same
        """
        # Check if parameters are the same
        if (self.last_sync_write['servo_ids'] == servo_ids and 
            self.last_sync_write['address'] == address and 
            self.last_sync_write['value'] == value and
            self.last_sync_write['data_length'] == data_length):
            return False
        
        # Parameters changed, update tracking
        self.last_sync_write = {
            'servo_ids': servo_ids.copy(),
            'address': address,
            'value': value,
            'data_length': data_length
        }
        return True
    
    def _create_sync_write_group(self, address: int, data_length: int):
        """
        Create a sync write group for the specified address and data length
        
        Args:
            address: Register address to write to
            data_length: Data length (1 or 2 bytes)
            
        Returns:
            GroupSyncWrite instance
        """
        return GroupSyncWrite(self.packetHandler, address, data_length)
    
    def _create_sync_read_group(self, address: int, data_length: int):
        """
        Create a sync read group for the specified address and data length
        
        Args:
            address: Register address to read from
            data_length: Data length to read
            
        Returns:
            GroupSyncRead instance
        """
        return GroupSyncRead(self.packetHandler, address, data_length)
    
    def connect(self) -> bool:
        """Connect to the serial port and initialize the controller"""
        try:
            # Initialize PortHandler and PacketHandler
            self.portHandler = PortHandler(self.port_name)
            self.packetHandler = hls(self.portHandler)
            
            # Open port
            if not self.portHandler.openPort():
                print(f"Failed to open port {self.port_name}")
                return False
            
            # Set baudrate
            if not self.portHandler.setBaudRate(self.baudrate):
                print(f"Failed to set baudrate to {self.baudrate}")
                self.portHandler.closePort()
                return False
            

            
            self.connected = True
            return True
            
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the serial port"""
        if self.portHandler:
            self.portHandler.closePort()
            self.connected = False
    
    def ping_servos(self) -> List[int]:
        """
        Ping servos to find which ones are connected (scans IDs 0-30)
        
        Returns:
            List of found servo IDs
        """
        if not self.connected:
            print("Not connected. Call connect() first.")
            return []
        
        print(f"Scanning for servos from ID 0 to 30...")
        found_servos = []
        
        for servo_id in range(0, 31):
            scs_model_number, scs_comm_result, scs_error = self.packetHandler.ping(servo_id)
            
            if scs_comm_result == COMM_SUCCESS:
                print(f"[ID:{servo_id:03d}] Found servo. Model: {scs_model_number}")
                found_servos.append(servo_id)
            elif scs_error != 0:
                print(f"[ID:{servo_id:03d}] Error: {self.packetHandler.getRxPacketError(scs_error)}")
        
        self.found_servos = found_servos
        print(f"Found {len(found_servos)} servo(s): {found_servos}")
        return found_servos
    
    def change_id(self, current_id: int, new_id: int) -> bool:
        """
        Change the ID of a servo
        
        Args:
            current_id: Current ID of the servo
            new_id: New ID to assign
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("Not connected. Call connect() first.")
            return False
        
        if new_id < 0 or new_id > 253:
            print("Invalid new ID. Must be between 0 and 253.")
            return False
        
        print(f"Changing servo ID from {current_id} to {new_id}...")
        
        # Step 1: Unlock EEPROM
        scs_comm_result, scs_error = self.packetHandler.unLockEprom(current_id)
        if scs_comm_result != COMM_SUCCESS:
            print(f"Failed to unlock EEPROM: {self.packetHandler.getTxRxResult(scs_comm_result)}")
            return False
        
        # Step 2: Write new ID
        scs_comm_result, scs_error = self.packetHandler.write1ByteTxRx(current_id, HLS_ID, new_id)
        if scs_comm_result != COMM_SUCCESS:
            print(f"Failed to write new ID: {self.packetHandler.getTxRxResult(scs_comm_result)}")
            return False
        
        # Step 3: Lock EEPROM
        scs_comm_result, scs_error = self.packetHandler.LockEprom(new_id)
        if scs_comm_result != COMM_SUCCESS:
            print(f"Failed to lock EEPROM: {self.packetHandler.getTxRxResult(scs_comm_result)}")
            return False
        
        # Step 4: Verify the change
        time.sleep(0.1)
        scs_model_number, scs_comm_result, scs_error = self.packetHandler.ping(new_id)
        if scs_comm_result == COMM_SUCCESS:
            # Update found_servos list
            if current_id in self.found_servos:
                self.found_servos.remove(current_id)
            self.found_servos.append(new_id)
            return True
        else:
            print(f"Failed to verify ID change")
            return False
    
    def set_zero(self, servo_id) -> bool:
        """
        Set the current position as zero (calibration). No offset value.
        HLS: disable torque, unlock EEPROM, then Recal (INST_CAL with no params).
        
        Args:
            servo_id: ID of the servo (int) or list of servo IDs
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("Not connected. Call connect() first.")
            return False
        
        if isinstance(servo_id, int):
            servo_ids = [servo_id]
        else:
            servo_ids = servo_id
        
        success_count = 0
        for sid in servo_ids:
            self.disable_torque(sid)
            scs_comm_result, scs_error = self.packetHandler.unLockEprom(sid)
            if scs_comm_result != COMM_SUCCESS:
                print(f"Failed to unlock EEPROM for servo {sid}: {self.packetHandler.getTxRxResult(scs_comm_result)}")
            else:
                scs_comm_result, scs_error = self.packetHandler.reCal(sid)
                if scs_comm_result != COMM_SUCCESS:
                    print(f"Failed to set zero for servo {sid}: {self.packetHandler.getTxRxResult(scs_comm_result)}")
                elif scs_error != 0:
                    print(f"Error setting zero for servo {sid}: {self.packetHandler.getRxPacketError(scs_error)}")
                else:
                    print(f"[ID:{sid:03d}] Set zero succeeded (HLS Recal)")
                    success_count += 1
        
        return success_count == len(servo_ids)

    def add_encoder_offset(self, servo_id, offset: int = 2048) -> bool:
        """
        Add an encoder position offset. Sends reOfsCal (INST_OFSCAL) with the 2-byte offset value.
        Effect on reported position and angle control is protocol-dependent; see servo manual
        (e.g. position offset register at address 31-32, encoding 0~8191 for -4095~+4095).
        
        Args:
            servo_id: ID of the servo (int) or list of servo IDs
            offset: Encoder position offset value to add (default 2048; range/encoding per protocol)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("Not connected. Call connect() first.")
            return False
        
        if isinstance(servo_id, int):
            servo_ids = [servo_id]
        else:
            servo_ids = servo_id
        
        success_count = 0
        for sid in servo_ids:
            scs_comm_result, scs_error = self.packetHandler.reOfsCal(sid, offset)
            if scs_comm_result != COMM_SUCCESS:
                print(f"Failed to add encoder offset for servo {sid}: {self.packetHandler.getTxRxResult(scs_comm_result)}")
            elif scs_error != 0:
                print(f"Error adding encoder offset for servo {sid}: {self.packetHandler.getRxPacketError(scs_error)}")
            else:
                print(f"[ID:{sid:03d}] Add encoder offset succeeded (offset={offset})")
                success_count += 1
        
        return success_count == len(servo_ids)
    
    def change_mode(self, servo_id, mode: int) -> bool:
        """
        Change the servo mode
        
        Args:
            servo_id: ID of the servo (int) or list of servo IDs
            mode: Mode to set (0-3)
                0: Position servo mode (位置伺服模式)
                1: Constant speed mode (电机恒速模式)
                2: Constant current mode (电机恒流模式)
                3: PWM open-loop speed control mode (PWM开环调速度模式)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("Not connected. Call connect() first.")
            return False
        
        if mode < 0 or mode > 3:
            print("Invalid mode. Must be between 0 and 3.")
            return False
        
        mode_names = {
            0: "Position servo mode (位置伺服模式)",
            1: "Constant speed mode (电机恒速模式)", 
            2: "Constant current mode (电机恒流模式)",
            3: "PWM open-loop speed control mode (PWM开环调速度模式)"
        }
        
        # Handle single ID or list of IDs
        if isinstance(servo_id, int):
            servo_ids = [servo_id]
        else:
            servo_ids = servo_id
        
        # Use sync write for multiple servos, individual write for single servo
        if len(servo_ids) == 1:
            # Single servo - use individual write
            sid = servo_ids[0]
            scs_comm_result, scs_error = self.packetHandler.write1ByteTxRx(sid, HLS_MODE, mode)
            if scs_comm_result != COMM_SUCCESS:
                print(f"Failed to change mode for servo {sid}: {self.packetHandler.getTxRxResult(scs_comm_result)}")
                return False
            elif scs_error != 0:
                print(f"Error changing mode for servo {sid}: {self.packetHandler.getRxPacketError(scs_error)}")
                return False
            else:
                return True
        else:
            # Multiple servos - use sync write
            # Check if parameters have changed
            if self._check_sync_write_params(servo_id, HLS_MODE, mode, 1):
                # Create sync write group for mode change (1 byte at address 33)
                groupSyncWrite = self._create_sync_write_group(HLS_MODE, 1)
                
                # Add parameters for all servos
                for sid in servo_id:
                    result = groupSyncWrite.addParam(sid, [mode])
                    if not result:
                        print(f"Failed to add parameter for servo {sid}")
                        return False
            
            # Execute sync write
            comm_result = groupSyncWrite.txPacket()
            if comm_result != COMM_SUCCESS:
                print(f"Sync write failed: {self.packetHandler.getTxRxResult(comm_result)}")
                return False
            
            return True
    
    def read_mode(self, servo_id) -> Optional[Union[int, Dict[int, int]]]:
        """
        Read the current mode of a servo
        
        Args:
            servo_id: ID of the servo (int) or list of servo IDs
            
        Returns:
            For single servo: Current mode (0-3) or None if failed
            For multiple servos: Dictionary mapping servo ID to mode, or None if failed
        """
        if not self.connected:
            print("Not connected. Call connect() first.")
            return None
        
        mode_names = {
            0: "Position servo mode (位置伺服模式)",
            1: "Constant speed mode (电机恒速模式)",
            2: "Constant current mode (电机恒流模式)", 
            3: "PWM open-loop speed control mode (PWM开环调速度模式)"
        }
        
        # Handle single ID or list of IDs
        if isinstance(servo_id, int):
            servo_ids = [servo_id]
        else:
            servo_ids = servo_id
        
        # Use sync read for multiple servos, individual read for single servo
        if len(servo_ids) == 1:
            # Single servo - use individual read
            sid = servo_ids[0]
            mode, scs_comm_result, scs_error = self.packetHandler.read1ByteTxRx(sid, HLS_MODE)
            if scs_comm_result != COMM_SUCCESS:
                print(f"Failed to read mode for servo {sid}: {self.packetHandler.getTxRxResult(scs_comm_result)}")
                return None
            elif scs_error != 0:
                print(f"Error reading mode for servo {sid}: {self.packetHandler.getRxPacketError(scs_error)}")
                return None
            else:
                return mode
        else:
            # Multiple servos - use sync read
            results = self.sync_read_parameters(servo_ids, HLS_MODE, 1, "mode")
            
            return results if results else None
    
    def enable_torque(self, servo_id) -> bool:
        """
        Enable torque output for a servo
        
        Args:
            servo_id: ID of the servo (int) or list of servo IDs
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("Not connected. Call connect() first.")
            return False
        
        # Handle single ID or list of IDs
        if isinstance(servo_id, int):
            # Single servo - use individual write
            sid = servo_id
            scs_comm_result, scs_error = self.packetHandler.write1ByteTxRx(sid, HLS_TORQUE_ENABLE, 1)
            if scs_comm_result != COMM_SUCCESS:
                print(f"Failed to enable torque for servo {sid}: {self.packetHandler.getTxRxResult(scs_comm_result)}")
                return False
            elif scs_error != 0:
                print(f"Error enabling torque for servo {sid}: {self.packetHandler.getRxPacketError(scs_error)}")
                return False
            else:
                return True
        else:
            # Multiple servos - use sync write
            # Check if parameters have changed
            if self._check_sync_write_params(servo_id, HLS_TORQUE_ENABLE, 1, 1):
                # Create sync write group for torque enable (1 byte at address 40)
                groupSyncWrite = self._create_sync_write_group(HLS_TORQUE_ENABLE, 1)
                
                # Add parameters for all servos (write 1 to enable torque)
                for sid in servo_id:
                    result = groupSyncWrite.addParam(sid, [1])
                    if not result:
                        print(f"Failed to add parameter for servo {sid}")
                        return False
            
            # Execute sync write
            comm_result = groupSyncWrite.txPacket()
            if comm_result != COMM_SUCCESS:
                print(f"Sync write failed: {self.packetHandler.getTxRxResult(comm_result)}")
                return False
            
            return True
    
    def disable_torque(self, servo_id) -> bool:
        """
        Disable torque output for a servo
        
        Args:
            servo_id: ID of the servo (int) or list of servo IDs
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("Not connected. Call connect() first.")
            return False
        
        # Handle single ID or list of IDs
        if isinstance(servo_id, int):
            # Single servo - use individual write
            sid = servo_id
            scs_comm_result, scs_error = self.packetHandler.write1ByteTxRx(sid, HLS_TORQUE_ENABLE, 0)
            if scs_comm_result != COMM_SUCCESS:
                print(f"Failed to disable torque for servo {sid}: {self.packetHandler.getTxRxResult(scs_comm_result)}")
                return False
            elif scs_error != 0:
                print(f"Error disabling torque for servo {sid}: {self.packetHandler.getRxPacketError(scs_error)}")
                return False
            else:
                return True
        else:
            # Multiple servos - use sync write
            # Check if parameters have changed
            if self._check_sync_write_params(servo_id, HLS_TORQUE_ENABLE, 0, 1):
                # Create sync write group for torque disable (1 byte at address 40)
                groupSyncWrite = self._create_sync_write_group(HLS_TORQUE_ENABLE, 1)
                
                # Add parameters for all servos (write 0 to disable torque)
                for sid in servo_id:
                    result = groupSyncWrite.addParam(sid, [0])
                    if not result:
                        print(f"Failed to add parameter for servo {sid}")
                        return False
            
            # Execute sync write
            comm_result = groupSyncWrite.txPacket()
            if comm_result != COMM_SUCCESS:
                print(f"Sync write failed: {self.packetHandler.getTxRxResult(comm_result)}")
                return False
            
            return True
    
    def set_acceleration(self, servo_id, acceleration: int) -> bool:
        """
        Set acceleration for a servo
        
        Args:
            servo_id: ID of the servo (int) or list of servo IDs
            acceleration: Acceleration value (0-254, 0 = max acceleration)
                         Unit: 8.7 degrees/second²
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("Not connected. Call connect() first.")
            return False
        
        if acceleration < 0 or acceleration > 254:
            print("Invalid acceleration. Must be between 0 and 254.")
            return False
        
        # Handle single ID or list of IDs
        if isinstance(servo_id, int):
            servo_ids = [servo_id]
        else:
            servo_ids = servo_id
        
        # Use sync write for multiple servos, individual write for single servo
        if len(servo_ids) == 1:
            # Single servo - use individual write
            sid = servo_ids[0]
            scs_comm_result, scs_error = self.packetHandler.write1ByteTxRx(sid, HLS_ACC, acceleration)
            if scs_comm_result != COMM_SUCCESS:
                print(f"Failed to set acceleration for servo {sid}: {self.packetHandler.getTxRxResult(scs_comm_result)}")
                return False
            elif scs_error != 0:
                print(f"Error setting acceleration for servo {sid}: {self.packetHandler.getRxPacketError(scs_error)}")
                return False
            else:
                return True
        else:
            # Multiple servos - use sync write
            # Check if parameters have changed
            if self._check_sync_write_params(servo_ids, HLS_ACC, acceleration, 1):
                # Create sync write group for acceleration (1 byte at address 41)
                groupSyncWrite = self._create_sync_write_group(HLS_ACC, 1)
                
                # Add parameters for all servos
                for sid in servo_ids:
                    result = groupSyncWrite.addParam(sid, [acceleration])
                    if not result:
                        print(f"Failed to add parameter for servo {sid}")
                        return False
            
            # Execute sync write
            comm_result = groupSyncWrite.txPacket()
            if comm_result != COMM_SUCCESS:
                print(f"Sync write failed: {self.packetHandler.getTxRxResult(comm_result)}")
                return False
            
            return True
    
    def set_position(self, servo_id, position: int) -> bool:
        """
        Set target position for a servo
        
        Args:
            servo_id: ID of the servo (int) or list of servo IDs
            position: Target position (0-4095 for full rotation)
                     Unit: 0.087890625 degrees per unit (360°/4096)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("Not connected. Call connect() first.")
            return False
        
        if position < 0 or position > 4095:
            print("Invalid position. Must be between 0 and 4095 for full rotation.")
            return False
        
        # Handle single ID or list of IDs
        if isinstance(servo_id, int):
            servo_ids = [servo_id]
        else:
            servo_ids = servo_id
        
        # Use sync write for multiple servos, individual write for single servo
        if len(servo_ids) == 1:
            # Single servo - use individual write
            sid = servo_ids[0]
            scs_comm_result, scs_error = self.packetHandler.write2ByteTxRx(sid, HLS_GOAL_POSITION_L, position)
            if scs_comm_result != COMM_SUCCESS:
                print(f"Failed to set position for servo {sid}: {self.packetHandler.getTxRxResult(scs_comm_result)}")
                return False
            elif scs_error != 0:
                print(f"Error setting position for servo {sid}: {self.packetHandler.getRxPacketError(scs_error)}")
                return False
            else:
                return True
        else:
            # Multiple servos - use sync write
            # Check if parameters have changed
            if self._check_sync_write_params(servo_ids, HLS_GOAL_POSITION_L, position, 2):
                # Create sync write group for position (2 bytes at address 42)
                groupSyncWrite = self._create_sync_write_group(HLS_GOAL_POSITION_L, 2)
                
                # Add parameters for all servos
                for sid in servo_ids:
                    # Convert position to proper byte format for 2-byte value
                    servo_value = self.packetHandler.scs_toscs(position, 15)
                    pos_bytes = [self.packetHandler.scs_lobyte(servo_value), self.packetHandler.scs_hibyte(servo_value)]
                    result = groupSyncWrite.addParam(sid, pos_bytes)
                    if not result:
                        print(f"Failed to add parameter for servo {sid}")
                        return False
            
            # Execute sync write
            comm_result = groupSyncWrite.txPacket()
            if comm_result != COMM_SUCCESS:
                print(f"Sync write failed: {self.packetHandler.getTxRxResult(comm_result)}")
                return False
            
            return True
    
    def set_torque(self, servo_id, torque) -> bool:
        """
        Set target torque for a servo
        
        Args:
            servo_id: ID of the servo (int) or list of servo IDs
            torque: Target torque value(s)
                   - Single int: Same torque for all servos (-2047 to 2047)
                   - List of ints: Individual torque for each servo
                   Unit: 6.5mA
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("Not connected. Call connect() first.")
            return False
        
        # Handle single ID or list of IDs
        if isinstance(servo_id, int):
            servo_ids = [servo_id]
        else:
            servo_ids = servo_id
        
        # Handle single torque value or list of torque values
        if isinstance(torque, int):
            # Single torque value for all servos
            torque_values = [torque] * len(servo_ids)
        elif isinstance(torque, list) and len(torque) == len(servo_ids):
            # List of torque values for each servo
            torque_values = torque
        else:
            print("Invalid torque input. Must be single int or list matching servo count.")
            return False
        
        # Convert negative values: convert to abs(value) + 32768
        converted_torque_values = []
        for t in torque_values:
            if t < 0:
                converted_torque_values.append(abs(t) + 32768)
            else:
                converted_torque_values.append(t)
        
        # Use sync write for multiple servos, individual write for single servo
        if len(servo_ids) == 1:
            # Single servo - use individual write
            sid = servo_ids[0]
            converted_torque = converted_torque_values[0]
            scs_comm_result, scs_error = self.packetHandler.write2ByteTxRx(sid, HLS_GOAL_TORQUE_L, converted_torque)
            if scs_comm_result != COMM_SUCCESS:
                print(f"Failed to set torque for servo {sid}: {self.packetHandler.getTxRxResult(scs_comm_result)}")
                return False
            elif scs_error != 0:
                print(f"Error setting torque for servo {sid}: {self.packetHandler.getRxPacketError(scs_error)}")
                return False
            else:
                return True
        else:
            # Multiple servos - use sync write
            # For multiple servos with different values, we need to handle each individually
            # since sync write requires same value for all servos
            if len(set(converted_torque_values)) == 1:
                # All servos have the same converted torque value - can use sync write
                converted_torque = converted_torque_values[0]
                # Check if parameters have changed
                if self._check_sync_write_params(servo_ids, HLS_GOAL_TORQUE_L, converted_torque, 2):
                    # Create sync write group for torque (2 bytes at address 44)
                    groupSyncWrite = self._create_sync_write_group(HLS_GOAL_TORQUE_L, 2)
                    
                    # Add parameters for all servos
                    for sid in servo_ids:
                        # Convert torque to proper byte format for 2-byte value
                        servo_value = self.packetHandler.scs_toscs(converted_torque, 15)
                        torque_bytes = [self.packetHandler.scs_lobyte(servo_value), self.packetHandler.scs_hibyte(servo_value)]
                        result = groupSyncWrite.addParam(sid, torque_bytes)
                        if not result:
                            print(f"Failed to add parameter for servo {sid}")
                            return False
                
                # Execute sync write
                comm_result = groupSyncWrite.txPacket()
                if comm_result != COMM_SUCCESS:
                    print(f"Sync write failed: {self.packetHandler.getTxRxResult(comm_result)}")
                    return False
            else:
                # Different torque values for different servos - use individual writes
                for i, sid in enumerate(servo_ids):
                    converted_torque = converted_torque_values[i]
                    scs_comm_result, scs_error = self.packetHandler.write2ByteTxRx(sid, HLS_GOAL_TORQUE_L, converted_torque)
                    if scs_comm_result != COMM_SUCCESS:
                        print(f"Failed to set torque for servo {sid}: {self.packetHandler.getTxRxResult(scs_comm_result)}")
                        return False
                    elif scs_error != 0:
                        print(f"Error setting torque for servo {sid}: {self.packetHandler.getRxPacketError(scs_error)}")
                        return False
            
            return True
    
    def set_speed(self, servo_id, speed) -> bool:
        """
        Set running speed for a servo
        
        Args:
            servo_id: ID of the servo (int) or list of servo IDs
            speed: Running speed value(s)
                   - Single int: Same speed for all servos (-32767 to 32767)
                   - List of ints: Individual speed for each servo
                   Unit: 0.732 RPM
        
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("Not connected. Call connect() first.")
            return False
        
        # Handle single ID or list of IDs
        if isinstance(servo_id, int):
            servo_ids = [servo_id]
        else:
            servo_ids = servo_id
        
        # Handle single speed value or list of speed values
        if isinstance(speed, int):
            # Single speed value for all servos
            speed_values = [speed] * len(servo_ids)
        elif isinstance(speed, list) and len(speed) == len(servo_ids):
            # List of speed values for each servo
            speed_values = speed
        else:
            print("Invalid speed input. Must be single int or list matching servo count.")
            return False
        
        # Convert negative values: convert to abs(value) + 32768
        converted_speed_values = []
        for s in speed_values:
            if s < 0:
                converted_speed_values.append(abs(s) + 32768)
            else:
                converted_speed_values.append(s)
        
        # Use sync write for multiple servos, individual write for single servo
        if len(servo_ids) == 1:
            # Single servo - use individual write
            sid = servo_ids[0]
            converted_speed = converted_speed_values[0]
            scs_comm_result, scs_error = self.packetHandler.write2ByteTxRx(sid, HLS_GOAL_SPEED_L, converted_speed)
            if scs_comm_result != COMM_SUCCESS:
                print(f"Failed to set speed for servo {sid}: {self.packetHandler.getTxRxResult(scs_comm_result)}")
                return False
            elif scs_error != 0:
                print(f"Error setting speed for servo {sid}: {self.packetHandler.getRxPacketError(scs_error)}")
                return False
            else:
                return True
        else:
            # Multiple servos - use sync write
            # For multiple servos with different values, we need to handle each individually
            # since sync write requires same value for all servos
            if len(set(converted_speed_values)) == 1:
                # All servos have the same converted speed value - can use sync write
                converted_speed = converted_speed_values[0]
                # Check if parameters have changed
                if self._check_sync_write_params(servo_ids, HLS_GOAL_SPEED_L, converted_speed, 2):
                    # Create sync write group for speed (2 bytes at address 46)
                    groupSyncWrite = self._create_sync_write_group(HLS_GOAL_SPEED_L, 2)
                    
                    # Add parameters for all servos
                    for sid in servo_ids:
                        # Convert speed to proper byte format for 2-byte value
                        servo_value = self.packetHandler.scs_toscs(converted_speed, 15)
                        speed_bytes = [self.packetHandler.scs_lobyte(servo_value), self.packetHandler.scs_hibyte(servo_value)]
                        result = groupSyncWrite.addParam(sid, speed_bytes)
                        if not result:
                            print(f"Failed to add parameter for servo {sid}")
                            return False
                
                # Execute sync write
                comm_result = groupSyncWrite.txPacket()
                if comm_result != COMM_SUCCESS:
                    print(f"Sync write failed: {self.packetHandler.getTxRxResult(comm_result)}")
                    return False
            else:
                # Different speed values for different servos - use individual writes
                for i, sid in enumerate(servo_ids):
                    converted_speed = converted_speed_values[i]
                    scs_comm_result, scs_error = self.packetHandler.write2ByteTxRx(sid, HLS_GOAL_SPEED_L, converted_speed)
                    if scs_comm_result != COMM_SUCCESS:
                        print(f"Failed to set speed for servo {sid}: {self.packetHandler.getTxRxResult(scs_comm_result)}")
                        return False
                    elif scs_error != 0:
                        print(f"Error setting speed for servo {sid}: {self.packetHandler.getRxPacketError(scs_error)}")
                        return False
            
            return True
    
    def set_torque_limit(self, servo_id, torque_limit: int) -> bool:
        """
        Set torque limit for a servo
        
        Args:
            servo_id: ID of the servo (int) or list of servo IDs
            torque_limit: Torque limit (0 to 1000)
                         Unit: 0.1%
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("Not connected. Call connect() first.")
            return False
        
        if torque_limit < 0 or torque_limit > 1000:
            print("Invalid torque limit. Must be between 0 and 1000.")
            return False
        
        # Handle single ID or list of IDs
        if isinstance(servo_id, int):
            servo_ids = [servo_id]
        else:
            servo_ids = servo_id
        
        # Use sync write for multiple servos, individual write for single servo
        if len(servo_ids) == 1:
            # Single servo - use individual write
            sid = servo_ids[0]
            scs_comm_result, scs_error = self.packetHandler.write2ByteTxRx(sid, 48, torque_limit)
            if scs_comm_result != COMM_SUCCESS:
                print(f"Failed to set torque limit for servo {sid}: {self.packetHandler.getTxRxResult(scs_comm_result)}")
                return False
            elif scs_error != 0:
                print(f"Error setting torque limit for servo {sid}: {self.packetHandler.getRxPacketError(scs_error)}")
                return False
            else:
                return True
        else:
            # Multiple servos - use sync write
            # Check if parameters have changed
            if self._check_sync_write_params(servo_ids, 48, torque_limit, 2):  # Torque limit address
                # Create sync write group for torque limit (2 bytes at address 48)
                groupSyncWrite = self._create_sync_write_group(48, 2)
                
                # Add parameters for all servos
                for sid in servo_ids:
                    # Convert torque limit to proper byte format for 2-byte value
                    servo_value = self.packetHandler.scs_toscs(torque_limit, 15)
                    limit_bytes = [self.packetHandler.scs_lobyte(servo_value), self.packetHandler.scs_hibyte(servo_value)]
                    result = groupSyncWrite.addParam(sid, limit_bytes)
                    if not result:
                        print(f"Failed to add parameter for servo {sid}")
                        return False
            
            # Execute sync write
            comm_result = groupSyncWrite.txPacket()
            if comm_result != COMM_SUCCESS:
                print(f"Sync write failed: {self.packetHandler.getTxRxResult(comm_result)}")
                return False
            
            return True
    
    def sync_read_posspeedload(self, servo_ids: List[int]) -> Dict[int, Tuple[int, int, int]]:
        """
        Synchronously read position, speed, and load from multiple servos
        
        Args:
            servo_ids: List of servo IDs to read from
            
        Returns:
            Dictionary mapping servo ID to (position, speed, load) tuple
        """
        return self.sync_read_parameters(servo_ids, HLS_PRESENT_POSITION_L, 6, "position/speed/load")
    
    def sync_read_parameters(self, servo_ids: List[int], address: int, data_length: int, 
                           description: str = "parameters") -> Dict[int, Union[int, List[int]]]:
        """
        Synchronously read parameters from multiple servos
        
        Args:
            servo_ids: List of servo IDs to read from
            address: Starting register address to read from
            data_length: Number of bytes to read
            description: Description of what's being read (for logging)
            
        Returns:
            Dictionary mapping servo ID to read data
        """
        if not self.connected:
            print("Not connected. Call connect() first.")
            return {}
        
        if not servo_ids:
            return {}
        
        # Create sync read group for the specific address and data length
        groupSyncRead = self._create_sync_read_group(address, data_length)
        
        # Add parameters for all servos
        for servo_id in servo_ids:
            result = groupSyncRead.addParam(servo_id)
            if not result:
                print(f"Failed to add parameter for servo {servo_id}")
        
        # Execute sync read
        comm_result = groupSyncRead.txRxPacket()
        if comm_result != COMM_SUCCESS:
            print(f"Sync read failed: {self.packetHandler.getTxRxResult(comm_result)}")
            return {}
        
        # Process results
        results = {}
        for servo_id in servo_ids:
            data_result, error = groupSyncRead.isAvailable(servo_id, address, data_length)
            if data_result:
                if data_length == 1:
                    # Single byte read
                    value = groupSyncRead.getData(servo_id, address, 1)
                    results[servo_id] = value
                elif data_length == 2:
                    # Two byte read
                    value = groupSyncRead.getData(servo_id, address, 2)
                    results[servo_id] = self.packetHandler.scs_tohost(value, 15)
                elif data_length == 6:
                    # Six byte read (position, speed, load)
                    position = groupSyncRead.getData(servo_id, HLS_PRESENT_POSITION_L, 2)
                    speed = groupSyncRead.getData(servo_id, HLS_PRESENT_SPEED_L, 2)
                    load = groupSyncRead.getData(servo_id, HLS_PRESENT_LOAD_L, 2)
                    
                    # Convert values
                    position_value = self.packetHandler.scs_tohost(position, 15)
                    speed_value = self.packetHandler.scs_tohost(speed, 15)
                    load_value = self.packetHandler.scs_tohost(load, 15)
                    
                    results[servo_id] = (position_value, speed_value, load_value)
                else:
                    # Multiple bytes read as list
                    values = []
                    for i in range(0, data_length, 2):
                        if i + 1 < data_length:
                            value = groupSyncRead.getData(servo_id, address + i, 2)
                            values.append(self.packetHandler.scs_tohost(value, 15))
                        else:
                            value = groupSyncRead.getData(servo_id, address + i, 1)
                            values.append(value)
                    results[servo_id] = values
            else:
                print(f"Failed to read data from servo {servo_id}")
                if error != 0:
                    print(f"   Error: {self.packetHandler.getRxPacketError(error)}")
        
        return results
    
    def sync_write_positions(self, servo_positions: Dict[int, int], 
                           speed: Union[int, List[int]] = 100, 
                           acc: Union[int, List[int]] = 50, 
                           torque: Union[int, List[int]] = 500) -> bool:
        """
        Synchronously write position commands to multiple servos
        
        Args:
            servo_positions: Dictionary mapping servo ID to target position
            speed: Movement speed (-32767 to 32767) - can be scalar or list per servo
            acc: Acceleration (0-255) - can be scalar or list per servo
            torque: Torque limit (0-1000) - can be scalar or list per servo
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("Not connected. Call connect() first.")
            return False
        
        if not servo_positions:
            return False
        
        # Convert scalar inputs to lists if needed
        servo_ids = list(servo_positions.keys())
        num_servos = len(servo_ids)
        
        if isinstance(speed, int):
            speed = [speed] * num_servos
        if isinstance(acc, int):
            acc = [acc] * num_servos
        if isinstance(torque, int):
            torque = [torque] * num_servos
        
        # Validate array lengths
        if len(speed) != num_servos or len(acc) != num_servos or len(torque) != num_servos:
            print(f"Parameter array lengths must match number of servos. Got: speed={len(speed)}, acc={len(acc)}, torque={len(torque)}, servos={num_servos}")
            return False
        
        # Clear previous parameters
        self.packetHandler.groupSyncWrite.clearParam()
        
        # Add parameters for all servos using SDK's SyncWritePosEx
        for i, (servo_id, position) in enumerate(servo_positions.items()):
            result = self.packetHandler.SyncWritePosEx(servo_id, position, speed[i], acc[i], torque[i])
            if not result:
                print(f"Failed to add parameter for servo {servo_id}")
                return False
        
        # Execute sync write
        comm_result = self.packetHandler.groupSyncWrite.txPacket()
        if comm_result != COMM_SUCCESS:
            print(f"Sync write failed: {self.packetHandler.getTxRxResult(comm_result)}")
            return False
        
        return True
    
    def individual_write_position(self, servo_id: int, position: int, 
                                speed: int = 100, acc: int = 50, torque: int = 500) -> bool:
        """
        Write position command to a single servo
        
        Args:
            servo_id: ID of the servo
            position: Target position (0-4095)
            speed: Movement speed (-32767 to 32767)
            acc: Acceleration (0-255)
            torque: Torque limit (0-1000)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connected:
            print("Not connected. Call connect() first.")
            return False
        
        scs_comm_result, scs_error = self.packetHandler.WritePosEx(servo_id, position, speed, acc, torque)
        if scs_comm_result != COMM_SUCCESS:
            print(f"Failed to write position to servo {servo_id}: {self.packetHandler.getTxRxResult(scs_comm_result)}")
            return False
        elif scs_error != 0:
            print(f"Error writing to servo {servo_id}: {self.packetHandler.getRxPacketError(scs_error)}")
            return False
        
        return True
    
    def read_servo_state(self, servo_id) -> Optional[Union[Tuple[int, int, int, int], Dict[int, Tuple[int, int, int, int]]]]:
        """
        Read position, speed, load, and current from a servo
        
        Args:
            servo_id: ID of the servo (int) or list of servo IDs
            
        Returns:
            For single servo: Tuple of (position, speed, load, current) or None if failed
            For multiple servos: Dictionary mapping servo ID to (position, speed, load, current) tuple, or None if failed
        """
        if not self.connected:
            print("Not connected. Call connect() first.")
            return None
        
        # Handle single ID or list of IDs
        if isinstance(servo_id, int):
            # Single servo - use individual read
            sid = servo_id
            position, speed, load, comm_result, error = self.packetHandler.ReadPosSpeedLoad(sid)
            if comm_result != COMM_SUCCESS:
                print(f"Failed to read from servo {sid}: {self.packetHandler.getTxRxResult(comm_result)}")
                return None
            elif error != 0:
                print(f"Error reading from servo {sid}: {self.packetHandler.getRxPacketError(error)}")
                return None
            
            # Read current from address 69 (right after load read)
            current_results = self.sync_read_parameters([sid], HLS_PRESENT_CURRENT_L, 2, "current")
            if sid not in current_results:
                print(f"Failed to read current from servo {sid}")
                current = 0  # Default to 0 if read fails
            else:
                current = current_results[sid]
            
            return (position, speed, load, current)
        else:
            # Multiple servos - use sync read (reuse existing function)
            results = self.sync_read_posspeedload(servo_id)
            # Also read current for all servos
            current_results = self.sync_read_parameters(servo_id, HLS_PRESENT_CURRENT_L, 2, "current")
            # Combine results
            combined_results = {}
            for sid in servo_id:
                if sid in results and sid in current_results:
                    pos, spd, ld = results[sid]
                    current = current_results[sid]
                    combined_results[sid] = (pos, spd, ld, current)
                elif sid in results:
                    # If current read failed, use 0
                    pos, spd, ld = results[sid]
                    combined_results[sid] = (pos, spd, ld, 0)
            return combined_results if combined_results else None
    
   
    def print_status(self):
        """Print current controller status"""
        print(f"\nFeetech Controller Status:")
        print(f"   Port: {self.port_name}")
        print(f"   Baudrate: {self.baudrate}")
        print(f"   Connected: {self.connected}")
        print(f"   Monitoring: {self.monitoring}")
        print(f"   Found servos: {self.found_servos}")


 