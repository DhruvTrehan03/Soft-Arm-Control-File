#!/usr/bin/env python3

import json
import sys
import time
from pathlib import Path

from dynio import dxl

from xl330 import XL330


DEVICE_NAME = "/dev/ttyUSB0"
BAUD_RATE = 57600
MOTOR_IDS = [2, 11, 12, 13, 21, 22, 23, 31, 32, 33, 14]
POSITION_MODE_IDS = [14]
READ_ONLY_IDS = [2]
CURRENT_LIMIT_MA = 500
CURRENT_COMMANDS_MA = {
    11: 100,
    12: 100,
    13: 100,
    21: 200,
    22: 200,
    23: 200,
    31: 500,
    32: 500,
    33: 500,
}
STATUS_INTERVAL = 0.3
CALIBRATION_FILE = Path(__file__).with_name("xl330_calibration.json")


def load_calibration():
    if not CALIBRATION_FILE.exists():
        raise FileNotFoundError(
            f"Calibration file not found: {CALIBRATION_FILE}. "
            "Run calibrate_xl330_pose.py first."
        )
    payload = json.loads(CALIBRATION_FILE.read_text(encoding="utf-8"))
    zero_positions = payload.get("zero_positions", {})
    return {int(motor_id): int(position) for motor_id, position in zero_positions.items()}


def format_motor_status(motor, zero_positions):
    position = motor.get_extended_position()
    zero_position = zero_positions.get(motor.id, 0)
    relative_position = position - zero_position
    return f"ID {motor.id}: {relative_position}"


def main():
    if not XL330.CONTROL_TABLE_PATH.exists():
        print(f"[ERR] Missing control table file: {XL330.CONTROL_TABLE_PATH}")
        sys.exit(1)
    try:
        zero_positions = load_calibration()
    except Exception as exc:
        print(f"[ERR] {exc}")
        sys.exit(1)

    try:
        dxl_io = dxl.DynamixelIO(DEVICE_NAME, BAUD_RATE)
    except Exception as exc:
        print(f"[ERR] Failed to initialize DynamixelIO: {exc}")
        sys.exit(1)

    motors = [XL330(dxl_io, dxl_id) for dxl_id in MOTOR_IDS]

    print(f"[OK] Port opened: {DEVICE_NAME}")
    print(f"[OK] Baudrate set: {BAUD_RATE}")
    print(f"[OK] Calibration loaded: {CALIBRATION_FILE}")

    try:
        for motor in motors:
            model_number = motor.ping()
            print(f"[OK] ID {motor.id} online, model number: {model_number}")

        for motor in motors:
            if motor.id in READ_ONLY_IDS:
                continue
            if motor.id in POSITION_MODE_IDS:
                if motor.id not in zero_positions:
                    raise KeyError(
                        f"Calibration zero position missing for ID {motor.id}"
                    )
                motor.enable_extended_position_mode()
                motor.set_extended_position(zero_positions[motor.id])
                continue

            motor.enable_current_mode()
            motor.set_current_limit(CURRENT_LIMIT_MA)
            motor.set_current(CURRENT_COMMANDS_MA.get(motor.id, 0))

        print("[INFO] Mixed mode enabled: current mode for most motors, extended position mode for selected IDs")
        print("[INFO] Read-only IDs are monitored only and not controlled")
        print("[INFO] ID 14 is commanded to its calibration zero position")
        print("[INFO] Output is relative to calibration zero positions")
        print("[INFO] Press Ctrl+C to stop")

        while True:
            for motor in motors:
                print(format_motor_status(motor, zero_positions))
            print()
            time.sleep(STATUS_INTERVAL)

    except KeyboardInterrupt:
        print("\n[INFO] Stopping")
    except Exception as exc:
        print(f"[ERR] {exc}")
        sys.exit(1)
    finally:
        for motor in motors:
            try:
                if motor.id in READ_ONLY_IDS:
                    continue
                if motor.id in POSITION_MODE_IDS:
                    motor.torque_disable()
                else:
                    motor.set_current(0)
            except Exception:
                pass
            try:
                motor.torque_disable()
            except Exception:
                pass
        try:
            dxl_io.port_handler.closePort()
        except Exception:
            pass
        print("[INFO] Port closed")


if __name__ == "__main__":
    main()
