from pathlib import Path
import time


class XL330:
    TICKS_PER_TURN = 4096
    DEGREES_PER_TURN = 360.0
    MIN_POSITION = 0
    MAX_POSITION = 4095
    EXTENDED_MIN_POSITION = -1048575
    EXTENDED_MAX_POSITION = 1048575
    CONTROL_TABLE_PATH = Path(__file__).with_name("xl330_m288_t.json")

    def __init__(self, dxl_io, motor_id):
        self.motor = dxl_io.new_motor(
            motor_id,
            str(self.CONTROL_TABLE_PATH),
            protocol=2,
            control_table_protocol=2,
        )
        self.id = motor_id
        self.zero_position = 0
        self.last_target_position = None
        self.last_target_angle_deg = None

    def ping(self):
        return self.motor.read_control_table("Model_Number")

    def blink_led(self, duration=0.2):
        self.motor.write_control_table("LED", 1)
        time.sleep(duration)
        self.motor.write_control_table("LED", 0)

    def write_control_table(self, name, value):
        self.motor.write_control_table(name, value)

    def read_control_table(self, name):
        return self.motor.read_control_table(name)

    def torque_enable(self):
        self.motor.torque_enable()

    def enable_velocity_mode(self):
        self.motor.torque_disable()
        self.motor.set_velocity_mode()
        self.motor.torque_enable()

    def enable_position_mode(self):
        self.motor.torque_disable()
        self.motor.set_position_mode(
            min_limit=self.MIN_POSITION,
            max_limit=self.MAX_POSITION,
        )
        self.motor.torque_enable()

    def enable_extended_position_mode(self):
        self.motor.torque_disable()
        self.motor.set_extended_position_mode()
        self.motor.torque_enable()

    def enable_current_mode(self):
        self.motor.torque_disable()
        self.write_control_table("Operating_Mode", 0)
        self.motor.torque_enable()

    def enable_current_based_position_mode(self):
        self.motor.torque_disable()
        self.write_control_table("Operating_Mode", 5)
        self.motor.torque_enable()

    def set_velocity(self, velocity):
        self.motor.set_velocity(velocity)

    def set_position(self, position):
        clamped = max(self.MIN_POSITION, min(self.MAX_POSITION, int(position)))
        self.motor.set_position(clamped)
        self.last_target_position = clamped
        self.last_target_angle_deg = self.position_to_angle(clamped)
        return clamped

    def set_angle(self, angle_deg):
        position = self.angle_to_position(angle_deg)
        return self.set_position(position)

    def set_extended_position(self, position):
        clamped = max(
            self.EXTENDED_MIN_POSITION,
            min(self.EXTENDED_MAX_POSITION, int(position)),
        )
        self.motor.set_position(clamped)
        self.last_target_position = clamped
        self.last_target_angle_deg = self.total_position_to_angle(clamped)
        return clamped

    def set_multi_turn_angle(self, angle_deg):
        position = self.total_angle_to_position(angle_deg)
        return self.set_extended_position(position)

    def stop(self):
        self.set_velocity(0)

    def torque_disable(self):
        self.motor.torque_disable()

    def set_goal_current(self, current_ma):
        self.write_control_table("Goal_Current", int(current_ma))

    def set_current(self, current_ma):
        self.set_goal_current(current_ma)

    def set_current_limit(self, current_ma):
        self.write_control_table("Current_Limit", int(current_ma))

    def set_position_p_gain(self, gain):
        self.write_control_table("Position_P_Gain", int(gain))

    def get_position(self):
        return self.motor.get_position()

    def get_extended_position(self):
        position = self.get_position()
        if position >= 2**31:
            position -= 2**32
        return position

    def get_angle(self):
        return self.position_to_angle(self.get_position())

    def get_total_angle(self):
        return self.total_position_to_angle(self.get_position())

    def get_extended_total_angle(self):
        return self.total_position_to_angle(self.get_extended_position())

    def get_present_current(self):
        return self.read_control_table("Present_Current")

    def capture_zero(self):
        self.zero_position = self.get_position()
        return self.zero_position

    def get_relative_position(self):
        return self.get_position() - self.zero_position

    @classmethod
    def angle_to_position(cls, angle_deg):
        wrapped_angle = angle_deg % cls.DEGREES_PER_TURN
        return round(wrapped_angle * cls.MAX_POSITION / cls.DEGREES_PER_TURN)

    @classmethod
    def position_to_angle(cls, position):
        normalized = position % cls.TICKS_PER_TURN
        return normalized * cls.DEGREES_PER_TURN / cls.TICKS_PER_TURN

    @classmethod
    def total_angle_to_position(cls, angle_deg):
        return round(angle_deg * cls.TICKS_PER_TURN / cls.DEGREES_PER_TURN)

    @classmethod
    def total_position_to_angle(cls, position):
        return position * cls.DEGREES_PER_TURN / cls.TICKS_PER_TURN

    @classmethod
    def format_position(cls, position):
        turns = position / cls.TICKS_PER_TURN
        total_angle_deg = turns * cls.DEGREES_PER_TURN
        angle_in_turn_deg = (
            (position % cls.TICKS_PER_TURN)
            * cls.DEGREES_PER_TURN
            / cls.TICKS_PER_TURN
        )
        return (
            f"raw={position} "
            f"turns={turns:.3f} "
            f"total_angle_deg={total_angle_deg:.1f} "
            f"angle_in_turn_deg={angle_in_turn_deg:.1f}"
        )

    def describe_absolute_position(self):
        return self.format_position(self.get_position())

    def describe_relative_position(self):
        return self.format_position(self.get_relative_position())
