#!/usr/bin/env python3

import json
import sys
import time
from collections import deque
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RadioButtons
from dynio import dxl

from xl330 import XL330


DEVICE_NAME = "/dev/ttyUSB0"
BAUD_RATE = 1000000
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
CALIBRATION_FILE = Path(__file__).with_name("xl330_calibration.json")

# Sampling at 100 Hz
STATUS_INTERVAL = 0.01

# Plot the most recent N seconds
WINDOW_SECONDS = 10

# Refresh the GUI every sample
GUI_UPDATE_EVERY = 1


def load_calibration():
    if not CALIBRATION_FILE.exists():
        raise FileNotFoundError(
            f"Calibration file not found: {CALIBRATION_FILE}. "
            "Run calibrate_xl330_pose.py first."
        )
    payload = json.loads(CALIBRATION_FILE.read_text(encoding="utf-8"))
    zero_positions = payload.get("zero_positions", {})
    return {int(motor_id): int(position) for motor_id, position in zero_positions.items()}


def get_relative_position(motor, zero_positions):
    position = motor.get_extended_position()
    zero_position = zero_positions.get(motor.id, 0)
    return position - zero_position


def setup_plot():
    plt.ion()
    fig = plt.figure(figsize=(15, 8))
    ax = fig.add_axes([0.30, 0.12, 0.66, 0.80])
    fig.canvas.manager.set_window_title("XL330 Position Monitor")
    ax.set_title("XL330 Relative Position")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Relative Position")
    ax.grid(True, alpha=0.3)
    return fig, ax


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
    history_len = max(100, int(WINDOW_SECONDS / STATUS_INTERVAL))
    time_history = deque(maxlen=history_len)
    position_histories = {
        motor.id: deque(maxlen=history_len) for motor in motors
    }

    print(f"[OK] Port opened: {DEVICE_NAME}")
    print(f"[OK] Baudrate set: {BAUD_RATE}")
    print(f"[OK] Calibration loaded: {CALIBRATION_FILE}")

    fig, ax = setup_plot()
    nav_ax = fig.add_axes([0.03, 0.22, 0.22, 0.66])
    nav_ax.set_title("Motors", fontsize=11, pad=10)
    radio = RadioButtons(nav_ax, [f"ID {motor.id}" for motor in motors], active=0)
    for label in radio.labels:
        label.set_fontsize(12)

    prev_ax = fig.add_axes([0.03, 0.08, 0.10, 0.08])
    next_ax = fig.add_axes([0.15, 0.08, 0.10, 0.08])
    prev_button = Button(prev_ax, "Prev")
    next_button = Button(next_ax, "Next")
    prev_button.label.set_fontsize(12)
    next_button.label.set_fontsize(12)

    selected_motor_id = motors[0].id
    selected_index = 0
    line, = ax.plot([], [], linewidth=2.0, color="#b34b28")

    def set_selected_by_index(index):
        nonlocal selected_motor_id, selected_index
        selected_index = index % len(motors)
        selected_motor_id = motors[selected_index].id
        radio.set_active(selected_index)

    def on_radio_clicked(label):
        nonlocal selected_motor_id, selected_index
        motor_id = int(label.split()[-1])
        selected_motor_id = motor_id
        selected_index = [motor.id for motor in motors].index(motor_id)

    def on_prev(_event):
        set_selected_by_index(selected_index - 1)

    def on_next(_event):
        set_selected_by_index(selected_index + 1)

    radio.on_clicked(on_radio_clicked)
    prev_button.on_clicked(on_prev)
    next_button.on_clicked(on_next)

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
        print("[INFO] Plot shows one motor at a time relative to calibration zero positions")
        print("[INFO] Sampling and GUI refresh target are both 100 Hz. Close the plot window or press Ctrl+C to stop")

        sample_index = 0
        start_time = time.perf_counter()

        while plt.fignum_exists(fig.number):
            loop_start = time.perf_counter()
            elapsed = loop_start - start_time
            time_history.append(elapsed)

            for motor in motors:
                position_histories[motor.id].append(
                    get_relative_position(motor, zero_positions)
                )

            if sample_index % GUI_UPDATE_EVERY == 0:
                if time_history:
                    line.set_data(
                        list(time_history),
                        list(position_histories[selected_motor_id]),
                    )
                    x_min = max(0.0, time_history[-1] - WINDOW_SECONDS)
                    x_max = max(WINDOW_SECONDS, time_history[-1])
                    ax.set_xlim(x_min, x_max)

                    selected_values = list(position_histories[selected_motor_id])
                    if selected_values:
                        y_min = min(selected_values)
                        y_max = max(selected_values)
                        if y_min == y_max:
                            y_min -= 1
                            y_max += 1
                        margin = max(10, 0.05 * (y_max - y_min))
                        ax.set_ylim(y_min - margin, y_max + margin)
                    ax.set_title(f"ID {selected_motor_id} Relative Position")

                fig.canvas.draw_idle()
                fig.canvas.flush_events()
                plt.pause(0.001)

            sample_index += 1
            sleep_time = STATUS_INTERVAL - (time.perf_counter() - loop_start)
            if sleep_time > 0:
                time.sleep(sleep_time)

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
        plt.close("all")
        print("[INFO] Port closed")


if __name__ == "__main__":
    main()
