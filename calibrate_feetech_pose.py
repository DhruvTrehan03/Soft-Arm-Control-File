#!/usr/bin/env python3
"""
Calibration helper for Feetech servos using FeetechController.

This script mimics the workflow of the provided XL330 calibration tool
but uses the project's `FeetechController` API from `feetech_controller.py`.

Usage example:
  python calibrate_feetech_pose.py --port COM4 --baud 1000000 --motors 1,2,3,4 --output feetech_calibration.json

The script will optionally switch specified motors to current/torque mode,
apply small current/torque commands to hold the mechanism, prompt you to
move the arm into the calibration pose, capture encoder positions, and
optionally capture the travel range of ID 2 while you manually move it.
"""

import argparse
import json
import select
import sys
import time
from pathlib import Path

from feetech_controller import FeetechController
import rt_config as rt_cfg


def capture_positions(controller, motor_ids):
    positions = {}
    # Use read_servo_state for multiple servos
    try:
        results = controller.read_servo_state(motor_ids)
        if results is None:
            # fall back to per-servo reads
            for sid in motor_ids:
                res = controller.read_servo_state(sid)
                if res:
                    positions[sid] = res[0]
        else:
            # results may be dict mapping id->(pos,spd,load,current)
            for sid, vals in results.items():
                if isinstance(vals, (list, tuple)) and len(vals) >= 1:
                    positions[sid] = vals[0]
    except Exception as exc:
        print(f"[ERR] Failed to capture positions: {exc}")

    return positions


def print_positions(title, positions):
    print(title)
    for motor_id in sorted(positions):
        print(f"ID {motor_id}: {positions[motor_id]}")
    print()


def torque_for_motor(motor_id, default_torque):
    if motor_id in (10, 11):
        return 0
    if motor_id in (6,7,8,9):
        return  100
    return default_torque


def capture_id11_range(controller, motor_ids):
    if 11 not in motor_ids:
        return None

    print("[INFO] ID 11 range capture started")
    print("[INFO] Move ID 11 through its full range, then press Enter to stop")

    min_position = None
    max_position = None

    try:
        # Non-blocking wait loop until Enter pressed
        while True:
            res = controller.read_servo_state(11)
            if res:
                # single servo returns (pos, speed, load, current)
                pos = res[0] if isinstance(res, (list, tuple)) else None
                if pos is not None:
                    if min_position is None or pos < min_position:
                        min_position = pos
                    if max_position is None or pos > max_position:
                        max_position = pos

                print(f"\r[INFO] ID 11 current={pos} min={min_position} max={max_position}", end="", flush=True)

            ready, _, _ = select.select([sys.stdin], [], [], 0.05)
            if ready:
                sys.stdin.readline()
                print()
                return {"min": min_position, "max": max_position}
    except KeyboardInterrupt:
        print("\n[INFO] ID 11 range capture cancelled")
        return {"min": min_position, "max": max_position}


def main():
    parser = argparse.ArgumentParser(description="Calibrate Feetech servos and capture zero positions")
    parser.add_argument("--port", type=str, default=None, help="Serial port (e.g. COM4 or /dev/ttyUSB0). If omitted, controller may auto-detect")
    parser.add_argument("--baud", type=int, default=rt_cfg.BAUDRATE, help="Baudrate (default from rt_config)")
    parser.add_argument("--motors", type=str, default=','.join(map(str, rt_cfg.EXPECTED_MOTOR_IDS)), help="Comma-separated motor IDs to calibrate (default from rt_config.EXPECTED_MOTOR_IDS)")
    parser.add_argument("--exclude", type=str, default='', help="Comma-separated motor IDs to exclude from current mode (optional)")
    parser.add_argument("--torque", type=int, default=200, help="Holding torque/current command to apply in current mode (units per Feetech API)")
    parser.add_argument("--output", type=str, default="feetech_calibration.json", help="Output JSON file path")

    args = parser.parse_args()

    motor_ids = [int(x) for x in args.motors.split(',') if x.strip()]
    excluded = [int(x) for x in args.exclude.split(',') if x.strip()] if args.exclude else []

    controller = FeetechController(port_name=args.port if args.port else None, baudrate=args.baud)

    print(f"[INFO] Connecting to controller on port {controller.port_name} @ {args.baud}")
    if not controller.connect():
        print("[ERR] Failed to connect to controller")
        sys.exit(1)

    try:
        # Ping and list servos
        found = controller.ping_servos()

        # Filter motor_ids to ones we actually found (but keep requested list if ping failed)
        active_motor_ids = [m for m in motor_ids if m in found] if found else motor_ids

        print()
        print(f"[INFO] Using motor IDs for calibration: {active_motor_ids}")

        # Switch motors (except excluded) to current/torque mode (mode=2) and apply holding torque
        for mid in active_motor_ids:
            if mid in excluded:
                print(f"[INFO] Skipping mode/current setup for excluded motor {mid}")
                continue

            motor_torque = torque_for_motor(mid, args.torque)

            # Change mode to constant current (2)
            try:
                ok = controller.change_mode(mid, 2)
                if not ok:
                    print(f"[WARN] change_mode failed for {mid}")
            except Exception as exc:
                print(f"[WARN] Exception changing mode for {mid}: {exc}")

            # Set torque limit conservatively
            try:
                controller.set_torque_limit(mid, rt_cfg.DEFAULT_TORQUE_LIMIT)
            except Exception:
                pass

            # Apply small holding torque/current (best-effort)
            try:
                controller.set_torque(mid, motor_torque)
            except Exception as exc:
                print(f"[WARN] set_torque failed for {mid}: {exc}")

        print()
        print("[INFO] Move the mechanism to the calibration pose.")
        input("[INFO] Press Enter when the arm is ready...")
        time.sleep(0.5)

        # Optionally capture ID 11 range
        id11_range = None
        if 11 in active_motor_ids:
            print("[INFO] Will capture ID 11 range interactively. Move it now when prompted.")
            id11_range = capture_id11_range(controller, active_motor_ids)

        # Capture zero positions
        zero_positions = capture_positions(controller, active_motor_ids)
        print_positions("[INFO] Captured calibration positions:", zero_positions)

        payload = {
            "port_name": controller.port_name,
            "baud_rate": args.baud,
            "motor_ids": active_motor_ids,
            "captured_at_unix": time.time(),
            "zero_positions": zero_positions,
            "id11_range": id11_range,
        }

        out_file = Path(args.output)
        out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"[OK] Calibration saved to {out_file}")

    except KeyboardInterrupt:
        print("\n[INFO] Calibration cancelled")
    except Exception as exc:
        print(f"[ERR] {exc}")
        sys.exit(1)
    finally:
        # Try to tidy up: stop torques and disable torque where appropriate
        for mid in motor_ids:
            try:
                controller.set_torque(mid, 0)
            except Exception:
                pass
            try:
                controller.disable_torque(mid)
            except Exception:
                pass

        try:
            controller.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    main()
