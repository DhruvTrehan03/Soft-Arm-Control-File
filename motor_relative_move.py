#!/usr/bin/env python3
"""Interactive helper for relative motor moves.

This script enables selected motors, reads the latest feedback, and sends a T1
position command using absolute target angles computed from relative deltas.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
import time
from typing import List

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String

import rt_config as rt_cfg


def parse_number_list(text: str) -> List[float]:
    """Parse a list entered as JSON/Python literal or comma-separated values."""
    text = text.strip()
    if not text:
        return []

    if text.startswith("["):
        values = ast.literal_eval(text)
        if not isinstance(values, (list, tuple)):
            raise ValueError("Expected a list of numbers")
        return [float(value) for value in values]

    parts = [part.strip() for part in text.replace(" ", ",").split(",") if part.strip()]
    return [float(part) for part in parts]


class RelativeMoveClient(Node):
    def __init__(self, prefix: str = ""):
        node_name = f"{prefix}_relative_move_client" if prefix else "relative_move_client"
        super().__init__(node_name)

        self.prefix = prefix
        self.command_topic = f"/{prefix}_motor_commands" if prefix else "/motor_commands"
        self.feedback_topic = f"/{prefix}_motor_controller/feedback" if prefix else "/motor_controller/feedback"

        self.feedback_msg = None
        self.feedback_subscription = self.create_subscription(
            JointState,
            self.feedback_topic,
            self.feedback_callback,
            10,
        )
        self.command_publisher = self.create_publisher(String, self.command_topic, 10)

    def feedback_callback(self, msg: JointState) -> None:
        self.feedback_msg = msg

    def wait_for_feedback(self, timeout_sec: float) -> JointState | None:
        deadline = time.time() + timeout_sec
        while rclpy.ok() and time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.feedback_msg and self.feedback_msg.position:
                return self.feedback_msg
        return None

    def send_command(self, function_type: str, parameters: dict) -> None:
        msg = String()
        msg.data = json.dumps([function_type, parameters])
        self.command_publisher.publish(msg)


def prompt_list(prompt: str) -> List[float]:
    while True:
        try:
            return parse_number_list(input(prompt))
        except (ValueError, SyntaxError) as exc:
            print(f"Invalid input: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Enable motors and move them relative to current position.")
    parser.add_argument("motors", nargs="?", help="Motor indices, e.g. 1,2,3 or [1,2,3]")
    parser.add_argument("deltas", nargs="?", help="Relative deltas in degrees, e.g. 10,10,5 or [10,10,5]")
    parser.add_argument("--prefix", default="", help="Topic prefix, e.g. master for /master_motor_commands")
    parser.add_argument("--speed", type=float, default=rt_cfg.DEFAULT_SPEED, help="Position move speed for T1")
    parser.add_argument("--acceleration", type=float, default=rt_cfg.DEFAULT_ACCELERATION, help="Position move acceleration for T1")
    parser.add_argument("--torque", type=float, default=rt_cfg.DEFAULT_TORQUE_LIMIT, help="Torque limit for T1")
    parser.add_argument("--feedback-timeout", type=float, default=5.0, help="Seconds to wait for feedback")
    args = parser.parse_args()

    if args.motors is None:
        motors = prompt_list("Motor indices (example: 1,2,3): ")
    else:
        motors = parse_number_list(args.motors)

    if args.deltas is None:
        deltas = prompt_list("Relative deltas in degrees (example: 10,10,5): ")
    else:
        deltas = parse_number_list(args.deltas)

    motors = [int(motor) for motor in motors]
    if len(motors) != len(deltas):
        print("Motor count and delta count must match.")
        return 1

    if any(motor < 1 for motor in motors):
        print("Motor indices must start at 1.")
        return 1

    rclpy.init(args=None)
    node = RelativeMoveClient(prefix=args.prefix)

    try:
        print(f"Waiting for feedback on {node.feedback_topic} ...")
        feedback = node.wait_for_feedback(args.feedback_timeout)
        if feedback is None:
            print("No feedback received. Make sure the motor controller node is running.")
            return 1

        positions = list(feedback.position)
        if len(positions) < max(motors):
            print(f"Feedback only contains {len(positions)} positions, but motor {max(motors)} was requested.")
            return 1

        node.send_command("T0", {"motors": motors, "enable": True})
        time.sleep(0.2)

        absolute_positions = []
        for motor, delta in zip(motors, deltas):
            current_position = float(positions[motor - 1])
            target_position = current_position + float(delta)
            absolute_positions.append(target_position)
            print(f"Motor {motor}: current {current_position:.2f}° + {delta:.2f}° -> {target_position:.2f}°")

        node.send_command(
            "T1",
            {
                "motors": motors,
                "positions": absolute_positions,
                "speed": [args.speed] * len(motors),
                "acc": [args.acceleration] * len(motors),
                "torque": [args.torque] * len(motors),
            },
        )

        time.sleep(0.2)

        print(f"Sent relative move on {node.command_topic}")
        return 0
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    sys.exit(main())