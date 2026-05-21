#!/usr/bin/env python3

import sys
import time

from dynio import dxl

from xl330 import XL330


DEVICE_NAME = "/dev/ttyUSB0"
BAUD_RATE = 57600
MOTOR_ID = 8

# Single-turn position mode target: 0 ~ 4095
TARGET_POSITION = 2048

# If you want to use angle instead of raw position, set this to a number
# and leave TARGET_POSITION as-is.
TARGET_ANGLE_DEG = None

SETTLE_TIME = 1.0


def main():
    if not XL330.CONTROL_TABLE_PATH.exists():
        print(f"[ERR] Missing control table file: {XL330.CONTROL_TABLE_PATH}")
        sys.exit(1)

    try:
        dxl_io = dxl.DynamixelIO(DEVICE_NAME, BAUD_RATE)
    except Exception as exc:
        print(f"[ERR] Failed to initialize DynamixelIO: {exc}")
        sys.exit(1)

    motor = XL330(dxl_io, MOTOR_ID)

    print(f"[OK] Port opened: {DEVICE_NAME}")
    print(f"[OK] Baudrate set: {BAUD_RATE}")

    try:
        model_number = motor.ping()
        print(f"[OK] ID {motor.id} online, model number: {model_number}")

        motor.enable_position_mode()
        current_position = motor.get_position()
        print(f"[INFO] Current position: {current_position}")

        if TARGET_ANGLE_DEG is not None:
            goal_position = motor.set_angle(TARGET_ANGLE_DEG)
            print(
                f"[INFO] Move ID {motor.id} to angle={TARGET_ANGLE_DEG:.1f} deg "
                f"(goal_position={goal_position})"
            )
        else:
            goal_position = motor.set_position(TARGET_POSITION)
            print(
                f"[INFO] Move ID {motor.id} to target_position={goal_position}"
            )

        time.sleep(SETTLE_TIME)

        final_position = motor.get_position()
        print(f"[OK] Final position: {final_position}")

    except KeyboardInterrupt:
        print("\n[INFO] Stopping")
    except Exception as exc:
        print(f"[ERR] {exc}")
        sys.exit(1)
    finally:
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
