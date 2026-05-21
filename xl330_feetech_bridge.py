#!/usr/bin/env python3
"""
Bridge XL330 master motion to Feetech slave motion.

This adapts the MATLAB master/slave loop to Python:
- read XL330 master positions relative to their calibration zeroes
- apply per-joint scaling and a source->target motor map
- command the Feetech servos to their calibrated zero plus the delta

The script also puts the XL330 source arm into current-control mode for the
non-read-only joints, which matches the holding workflow from the calibration
and monitor scripts in the dynamixel folder.
"""

import argparse
import json
import sys
import time
from pathlib import Path

from dynio import dxl

ROOT_DIR = Path(__file__).resolve().parent
DYNAMIXEL_DIR = ROOT_DIR / "dynamixel"
if str(DYNAMIXEL_DIR) not in sys.path:
    sys.path.insert(0, str(DYNAMIXEL_DIR))

from xl330 import XL330
from feetech_controller import FeetechController
import rt_config as rt_cfg


SOURCE_DEVICE_NAME = "/dev/ttyUSB0"
SOURCE_BAUD_RATE = 1000000
SOURCE_MOTOR_IDS = [2, 11, 12, 13, 21, 22, 23, 31, 32, 33, 14]
SOURCE_READ_ONLY_IDS = [2]
SOURCE_POSITION_MODE_IDS = [14]
SOURCE_CURRENT_LIMIT_MA = 500
SOURCE_CURRENT_COMMANDS_MA = {
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
SOURCE_CALIBRATION_FILE = ROOT_DIR / "xl330_calibration.json"

TARGET_CALIBRATION_FILE = ROOT_DIR / "feetech_calibration.json"
DEFAULT_STATUS_INTERVAL = 0.02


def load_calibration(path: Path) -> tuple[list[int], dict[int, int]]:
    if not path.exists():
        raise FileNotFoundError(f"Calibration file not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    motor_ids = [int(motor_id) for motor_id in payload.get("motor_ids", [])]
    zero_positions = payload.get("zero_positions", {})
    return motor_ids, {int(motor_id): int(position) for motor_id, position in zero_positions.items()}


def parse_mapping(text: str) -> dict[int, int]:
    mapping: dict[int, int] = {}
    if not text:
        return mapping

    for chunk in text.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ":" not in chunk:
            raise ValueError(f"Invalid mapping entry '{chunk}'. Use source:target pairs.")
        source_text, target_text = chunk.split(":", 1)
        mapping[int(source_text.strip())] = int(target_text.strip())
    return mapping


def parse_scales(text: str) -> dict[int, float]:
    scales: dict[int, float] = {}
    if not text:
        return scales

    for chunk in text.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            raise ValueError(f"Invalid scale entry '{chunk}'. Use motor_id=scale pairs.")
        motor_text, scale_text = chunk.split("=", 1)
        scales[int(motor_text.strip())] = float(scale_text.strip())
    return scales


def clamp_position(position: int) -> int:
    return max(0, min(4095, int(position)))


def build_default_joint_pairs(source_ids: list[int], target_ids: list[int]) -> list[tuple[int, int]]:
    pair_count = min(len(source_ids), len(target_ids))
    return [(source_ids[index], target_ids[index]) for index in range(pair_count)]


def capture_source_positions(motors: list[XL330]) -> dict[int, int]:
    return {motor.id: motor.get_extended_position() for motor in motors}


def format_relative_status(source_id: int, source_relative: int, target_id: int, target_position: int) -> str:
    return (
        f"XL330 {source_id}: delta={source_relative:+d} -> "
        f"Feetech {target_id}: command={target_position}"
    )


def build_joint_pairs_from_mapping_text(mapping_text: str, source_order: list[int], target_order: list[int]) -> list[tuple[int, int]]:
    if mapping_text:
        explicit_pairs = parse_mapping(mapping_text)
        return [(source_id, target_id) for source_id, target_id in explicit_pairs.items()]

    return build_default_joint_pairs(source_order, target_order)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mirror XL330 master motion to Feetech slave motion"
    )
    parser.add_argument("--source-port", type=str, default=SOURCE_DEVICE_NAME, help="XL330 serial port")
    parser.add_argument("--source-baud", type=int, default=SOURCE_BAUD_RATE, help="XL330 baudrate")
    parser.add_argument(
        "--source-calibration",
        type=str,
        default=str(SOURCE_CALIBRATION_FILE),
        help="XL330 calibration JSON file",
    )
    parser.add_argument(
        "--target-port",
        type=str,
        default="/dev/ttyCH341USB0",
        help="Feetech serial port (default: auto-detect)",
    )
    parser.add_argument(
        "--target-baud",
        type=int,
        default=rt_cfg.BAUDRATE,
        help="Feetech baudrate",
    )
    parser.add_argument(
        "--target-calibration",
        type=str,
        default=str(TARGET_CALIBRATION_FILE),
        help="Feetech calibration JSON file",
    )
    parser.add_argument(
        "--mapping",
        type=str,
        default="32:1, 33:2, 31:3, 22:4, 23:5, 21:6, 11:7, 12:8, 13:9, 14:10, 2:11 ",
        help="Comma-separated source:target motor ID pairs, e.g. 11:1,12:2,13:3",
    )
    parser.add_argument(
        "--scale",
        type=str,
        default="",
        help="Comma-separated per-source scale overrides, e.g. 14=2,11=1.0",
    )
    parser.add_argument(
        "--status-interval",
        type=float,
        default=DEFAULT_STATUS_INTERVAL,
        help="Control loop interval in seconds",
    )
    parser.add_argument(
        "--no-source-current-hold",
        action="store_true",
        help="Do not switch the XL330 source motors into current-holding mode",
    )
    parser.add_argument(
        "--source-current-limit",
        type=int,
        default=SOURCE_CURRENT_LIMIT_MA,
        help="XL330 current limit in mA",
    )
    parser.add_argument(
        "--source-current",
        type=int,
        default=None,
        help="Override XL330 holding current for every non-excluded source motor; omit to use built-in defaults",
    )
    parser.add_argument(
        "--target-speed",
        type=int,
        default=rt_cfg.DEFAULT_SPEED,
        help="Feetech position command speed",
    )
    parser.add_argument(
        "--target-acc",
        type=int,
        default=rt_cfg.DEFAULT_ACCELERATION,
        help="Feetech position command acceleration",
    )
    parser.add_argument(
        "--target-torque",
        type=int,
        default=rt_cfg.DEFAULT_TORQUE_LIMIT,
        help="Feetech position command torque limit",
    )

    args = parser.parse_args()

    source_calibration_path = Path(args.source_calibration)
    target_calibration_path = Path(args.target_calibration)

    if not XL330.CONTROL_TABLE_PATH.exists():
        print(f"[ERR] Missing control table file: {XL330.CONTROL_TABLE_PATH}")
        sys.exit(1)

    try:
        source_motor_order, source_zero_positions = load_calibration(source_calibration_path)
        target_motor_order, target_zero_positions = load_calibration(target_calibration_path)
    except Exception as exc:
        print(f"[ERR] {exc}")
        sys.exit(1)

    try:
        scale_overrides = parse_scales(args.scale)
    except Exception as exc:
        print(f"[ERR] {exc}")
        sys.exit(1)

    source_order = source_motor_order if source_motor_order else list(source_zero_positions.keys())
    target_order = target_motor_order if target_motor_order else list(target_zero_positions.keys())

    joint_pairs = build_joint_pairs_from_mapping_text(args.mapping, source_order, target_order)

    if not joint_pairs:
        print("[ERR] No source->target mapping could be constructed")
        sys.exit(1)

    try:
        dxl_io = dxl.DynamixelIO(args.source_port, args.source_baud)
    except Exception as exc:
        print(f"[ERR] Failed to initialize XL330 DynamixelIO: {exc}")
        sys.exit(1)

    source_motors = [XL330(dxl_io, dxl_id) for dxl_id in source_order]
    source_motor_by_id = {motor.id: motor for motor in source_motors}

    target_controller = FeetechController(port_name=args.target_port, baudrate=args.target_baud)

    print(f"[OK] XL330 port opened: {args.source_port}")
    print(f"[OK] XL330 baudrate set: {args.source_baud}")
    print(f"[OK] XL330 calibration loaded: {source_calibration_path}")
    print(f"[OK] Feetech calibration loaded: {target_calibration_path}")

    if not target_controller.connect():
        print("[ERR] Failed to connect to Feetech controller")
        try:
            dxl_io.port_handler.closePort()
        except Exception:
            pass
        sys.exit(1)

    target_found = target_controller.ping_servos()
    target_motor_ids = [target_id for _, target_id in joint_pairs]
    missing_targets = [motor_id for motor_id in target_motor_ids if motor_id not in target_found]
    if missing_targets:
        print(f"[ERR] Missing Feetech target motor(s): {missing_targets}")
        target_controller.disconnect()
        try:
            dxl_io.port_handler.closePort()
        except Exception:
            pass
        sys.exit(1)

    try:
        for motor_id in [source_id for source_id, _ in joint_pairs]:
            if motor_id not in source_motor_by_id:
                raise KeyError(f"Source motor ID {motor_id} is not in the loaded XL330 calibration")

        for motor in source_motors:
            model_number = motor.ping()
            print(f"[OK] XL330 ID {motor.id} online, model number: {model_number}")

        if not args.no_source_current_hold:
            for motor in source_motors:
                if motor.id in SOURCE_READ_ONLY_IDS:
                    continue
                if motor.id in SOURCE_POSITION_MODE_IDS:
                    if motor.id not in source_zero_positions:
                        raise KeyError(f"Missing XL330 calibration zero for ID {motor.id}")
                    motor.enable_extended_position_mode()
                    motor.set_extended_position(source_zero_positions[motor.id])
                    continue

                motor.enable_current_mode()
                motor.set_current_limit(args.source_current_limit)
                current_command = args.source_current
                if current_command is None:
                    current_command = SOURCE_CURRENT_COMMANDS_MA.get(motor.id, 0)
                motor.set_current(current_command)

            print("[INFO] XL330 source arm placed in holding current mode")
        else:
            print("[INFO] XL330 source holding-current setup disabled by flag")

        print("[INFO] Feetech target motors online and ready")
        print("[INFO] Press Ctrl+C to stop")
        print("[INFO] Mapping:")
        for index, (source_id, target_id) in enumerate(joint_pairs, start=1):
            scale = scale_overrides.get(source_id, 2.0 if index == len(joint_pairs) else 1.0)
            print(f"  joint {index}: XL330 {source_id} -> Feetech {target_id} (scale={scale})")

        while True:
            loop_start = time.perf_counter()
            source_positions = capture_source_positions(source_motors)
            print(f"\r[INFO] Captured source positions: " + ", ".join(f"ID {motor_id}={position}" for motor_id, position in source_positions.items()), end="", flush=True)
            target_commands = {}
            status_lines = []
            for index, (source_id, target_id) in enumerate(joint_pairs, start=1):
                source_zero = source_zero_positions[source_id]
                target_zero = target_zero_positions[target_id]
                source_relative = source_positions[source_id] - source_zero
                scale = scale_overrides.get(source_id, 2.0 if index == len(joint_pairs) else 1.0)
                target_position = clamp_position(target_zero + round(source_relative * scale))
                target_commands[target_id] = target_position
                status_lines.append(
                    format_relative_status(source_id, source_relative, target_id, target_position)
                )

            if target_commands:
                target_controller.sync_write_positions(
                    target_commands,
                    speed=args.target_speed,
                    acc=args.target_acc,
                    torque=args.target_torque,
                )

            for line in status_lines:
                print(line)
            print()

            elapsed = time.perf_counter() - loop_start
            sleep_time = args.status_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n[INFO] Stopping")
    except Exception as exc:
        print(f"[ERR] {exc}")
        sys.exit(1)
    finally:
        for motor in source_motors:
            try:
                if motor.id in SOURCE_READ_ONLY_IDS:
                    continue
                if motor.id in SOURCE_POSITION_MODE_IDS:
                    motor.torque_disable()
                elif not args.no_source_current_hold:
                    motor.set_current(0)
            except Exception:
                pass
            try:
                motor.torque_disable()
            except Exception:
                pass

        try:
            target_controller.disconnect()
        except Exception:
            pass

        try:
            dxl_io.port_handler.closePort()
        except Exception:
            pass

        print("[INFO] Port closed")


if __name__ == "__main__":
    main()