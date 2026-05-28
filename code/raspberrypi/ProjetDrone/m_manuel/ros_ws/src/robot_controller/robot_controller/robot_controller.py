#!/usr/bin/python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import re
from std_msgs.msg import String
# PCA9685 / Servo
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

# GPIO Raspberry Pi 5
import lgpio


class RobotController(Node):
    def __init__(self):
        super().__init__('robot_controller')
        self.robot_mode =  1 # Mode par defaut du robot
        # ================= GPIO (sens moteurs) =================
        self.M0_A, self.M0_B = 18, 17
        self.M1_A, self.M1_B = 22, 27
        self.pins = [self.M0_A, self.M0_B, self.M1_A, self.M1_B]

        self.gpio = lgpio.gpiochip_open(0)
        for pin in self.pins:
            lgpio.gpio_claim_output(self.gpio, pin, 0)

        # ================= PCA9685 =================
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(self.i2c)
        self.pca.frequency = 50  # servos + moteurs

        # Servo direction (CH0)
        self.steering = servo.Servo(self.pca.channels[0])

        # PWM moteurs (ENABLE)
        self.pwm_left = self.pca.channels[5]
        self.pwm_right = self.pca.channels[4]

        self.pwm_left.duty_cycle = 0
        self.pwm_right.duty_cycle = 0

        # ================= ROS =================
        self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.get_logger().info("Abonnement cmd_vel...OK")

        self.create_subscription(
            String,
            '/set_robot_mode',
            self.mode_callback,
            10
        )

        self.get_logger().info("Abonnement set_robot_mode...OK")
    # ================= MOTEURS DC =================
    def set_motors(self, speed: float):
        speed = max(-1.0, min(1.0, speed))

        # PWM correct PCA9685
        duty = int(abs(speed) * 65535)

        # seuil minimum moteur
        if 0 < duty < 20000:
            duty = 20000

        self.get_logger().info(f"Speed: {speed} Duty: {duty}")

        try:
            self.pwm_left.duty_cycle = duty
            self.pwm_right.duty_cycle = duty
        except OSError as e:
            self.get_logger().error(f"I2C error: {e}")
            return

        if speed > 0:
            lgpio.gpio_write(self.gpio, self.M0_A, 0)
            lgpio.gpio_write(self.gpio, self.M0_B, 1)
            lgpio.gpio_write(self.gpio, self.M1_A, 0)
            lgpio.gpio_write(self.gpio, self.M1_B, 1)

        elif speed < 0:
            lgpio.gpio_write(self.gpio, self.M0_A, 1)
            lgpio.gpio_write(self.gpio, self.M0_B, 0)
            lgpio.gpio_write(self.gpio, self.M1_A, 1)
            lgpio.gpio_write(self.gpio, self.M1_B, 0)

        else:
            self.stop_motors()

    def stop_motors(self):
        self.pwm_left.duty_cycle = 0
        self.pwm_right.duty_cycle = 0
        for pin in self.pins:
            lgpio.gpio_write(self.gpio, pin, 0)

    # ================= CALLBACK ROS =================
    def cmd_vel_callback(self, msg: Twist):
        if self.robot_mode != 3:

            # moteurs
            self.set_motors(msg.linear.x)

            # servo direction
            angle = 90.0 + msg.angular.z * 45.0
            angle = max(0.0, min(180.0, angle))
            self.steering.angle = angle

    # ================ CALLBACK MODE =============
    def mode_callback(self, msg):

        # récupère le nombre dans la string
        self.get_logger().info(f"Mode recu: {msg.data}")
        numbers = re.findall(r'\d+', msg.data)

        if not numbers:
            return

        mode_value = int(numbers[-1])

        if mode_value != self.robot_mode:

            self.robot_mode = mode_value
            self.get_logger().info(f"Mode robot détecté : {self.robot_mode}")

        if self.robot_mode == 3:

            self.get_logger().error("MODE 3 → ARRET ROBOT")

            self.stop_motors() 
    # ================= CLEANUP =================
    def destroy_node(self):
        self.get_logger().info("Arrêt du robot")
        self.stop_motors()
        self.steering.angle = 90.0
        lgpio.gpiochip_close(self.gpio)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = RobotController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
