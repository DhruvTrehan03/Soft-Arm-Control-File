#!/usr/bin/env python3

import json
import select
import sys
import time
from pathlib import Path

from dynio import dxl

from xl330 import XL330


DEVICE_NAME = "/dev/ttyUSB0"
BAUD_RATE = 1000000
MOTOR_IDS = [2, 11, 12, 13, 21, 22, 23, 31, 32, 33, 14]
EXCLUDED_FROM_CURRENT_MODE = [2, 14]
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
OUTPUT_FILE = Path(__file__).with_name("xl330_calibration.json")
STABILIZE_SECONDS = 1.0


def capture_positions(motors):
    positions = {}
    for motor in motors:
        positions[motor.id] = motor.get_extended_position()
    return positions


def print_positions(title, positions):
    print(title)
    for motor_id in sorted(positions):
        print(f"ID {motor_id}: {positions[motor_id]}")
    print()


def capture_id2_range(motors):
    id2_motor = next((motor for motor in motors if motor.id == 2), None)
    if id2_motor is None:
        return None

    print("[INFO] ID 2 range capture started")
    print("[INFO] Move ID 2 through its full range, then press Enter to stop")

    min_position = None
    max_position = None

    while True:
        position = id2_motor.get_extended_position()
        if min_position is None or position < min_position:
            min_position = position
        if max_position is None or position > max_position:
            max_position = position

        print(
            f"\r[INFO] ID 2 current={position} min={min_position} max={max_position}",
            end="",
            flush=True,
        )

        ready, _, _ = select.select([sys.stdin], [], [], 0.05)
        if ready:
            sys.stdin.readline()
            print()
            return {
                "min": min_position,
                "max": max_position,
            }


def main():
    if not XL330.CONTROL_TABLE_PATH.exists():
        print(f"[ERR] Missing control table file: {XL330.CONTROL_TABLE_PATH}")
        sys.exit(1)

    try:
        dxl_io = dxl.DynamixelIO(DEVICE_NAME, BAUD_RATE)
    except Exception as exc:
        print(f"[ERR] Failed to initialize DynamixelIO: {exc}")
        sys.exit(1)

    motors = [XL330(dxl_io, dxl_id) for dxl_id in MOTOR_IDS]

    print(f"[OK] Port opened: {DEVICE_NAME}")
    print(f"[OK] Baudrate set: {BAUD_RATE}")

    try:
        for motor in motors:
            model_number = motor.ping()
            print(f"[OK] ID {motor.id} online, model number: {model_number}")

        for motor in motors:
            if motor.id in EXCLUDED_FROM_CURRENT_MODE:
                continue
            motor.enable_current_mode()
            motor.set_current_limit(CURRENT_LIMIT_MA)
            motor.set_current(CURRENT_COMMANDS_MA.get(motor.id, 0))

        print()
        print("[INFO] All motors except excluded IDs switched to Current Control Mode")
        print("[INFO] Move the mechanism to the calibration pose.")
        input("[INFO] Press Enter when the arm is ready...")
        time.sleep(STABILIZE_SECONDS)

        id2_range = capture_id2_range(motors)
        zero_positions = capture_positions(motors)
        print_positions("[INFO] Captured calibration positions:", zero_positions)
        if id2_range is not None:
            print(
                f"[INFO] ID 2 range: min={id2_range['min']} max={id2_range['max']}"
            )
            print()

        payload = {
            "device_name": DEVICE_NAME,
            "baud_rate": BAUD_RATE,
            "motor_ids": MOTOR_IDS,
            "captured_at_unix": time.time(),
            "zero_positions": zero_positions,
            "id2_range": id2_range,
        }

        OUTPUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"[OK] Calibration saved to {OUTPUT_FILE}")

    except KeyboardInterrupt:
        print("\n[INFO] Calibration cancelled")
    except Exception as exc:
        print(f"[ERR] {exc}")
        sys.exit(1)
    finally:
        for motor in motors:
            try:
                if motor.id not in EXCLUDED_FROM_CURRENT_MODE:
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
