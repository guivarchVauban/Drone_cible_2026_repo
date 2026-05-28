#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
import json
import time


class NavigationNode(Node):

    def __init__(self):
        super().__init__('navigation_verrou')

        # Subscribers
        self.create_subscription(String, '/robot_mode', self.mode_callback, 10)
        self.create_subscription(String, '/boat_detection_json', self.detection_callback, 10)

        # Publisher
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # State
        self.mode = 0
        self.locked = False
        self.last_detection = None
        self.last_detection_time = time.time()

        # Camera (adapter si besoin)
        self.image_center_x = 320.0

        # ===== PID =====
        self.kp = 0.0025
        self.kd = 0.0015
        self.ki = 0.0

        self.prev_error = 0.0
        self.integral = 0.0

        # ===== Lissage =====
        self.last_angular = 0.0
        self.smoothing = 0.7

        # ===== Paramètres =====
        self.dead_zone = 15.0
        self.max_angular = 1.0
        self.base_speed = 0.8

        # Timer (20 Hz)
        self.dt = 0.05
        self.timer = self.create_timer(self.dt, self.control_loop)

        self.get_logger().info("Navigation node started")

    # =========================
    # MODE CALLBACK
    # =========================
    def mode_callback(self, msg):
        try:
            self.mode = int(msg.data)
        except:
            self.mode = 0

        self.locked = (self.mode == 2)

    # =========================
    # DETECTION CALLBACK
    # =========================
    def detection_callback(self, msg):
        try:
            self.last_detection = json.loads(msg.data)
            self.last_detection_time = time.time()
        except Exception as e:
            self.get_logger().warn(f"JSON error: {e}")
            self.last_detection = None

    # =========================
    # MAIN LOOP
    # =========================
    def control_loop(self):

        twist = Twist()

        # 🔒 Mode OFF
        if not self.locked:
            self.cmd_pub.publish(twist)
            return

        # ⛔ Perte détection (>1s)
        if time.time() - self.last_detection_time > 1.0:
            self.cmd_pub.publish(twist)
            return

        # ❌ Pas de données
        if self.last_detection is None:
            self.cmd_pub.publish(twist)
            return

        # ===== NORMALISATION =====
        if isinstance(self.last_detection, dict):
            boats = self.last_detection.get("boats", [])
        elif isinstance(self.last_detection, list):
            boats = self.last_detection
        else:
            self.cmd_pub.publish(twist)
            return

        if len(boats) == 0:
            self.cmd_pub.publish(twist)
            return

        # ===== SELECTION =====
        boat = max(boats, key=lambda b: b.get("width", 0) * b.get("height", 0))

        try:
            x_min = float(boat.get("x_min", 0.0))
            width = float(boat.get("width", 0.0))
        except:
            self.cmd_pub.publish(twist)
            return

        center_x = x_min + width / 2.0
        error = center_x - self.image_center_x

        # ===== DEAD ZONE =====
        if abs(error) < self.dead_zone:
            error = 0.0

        # ===== PID =====
        p = self.kp * error

        self.integral += error * self.dt
        i = self.ki * self.integral

        d = self.kd * (error - self.prev_error) / self.dt

        output = p + i + d
        self.prev_error = error

        # ===== LISSAGE =====
        raw_angular = -output

        angular = (
            self.smoothing * self.last_angular +
            (1 - self.smoothing) * raw_angular
        )

        self.last_angular = angular

        # Clamp sécurité
        angular = max(min(angular, self.max_angular), -self.max_angular)

        # ===== VITESSE ADAPTATIVE =====
        speed = self.base_speed - min(abs(error) / 300.0, 0.5)

        # ===== APPLY =====
        twist.linear.x = float(speed)
        twist.angular.z = float(angular)

        self.cmd_pub.publish(twist)

        # Debug
        self.get_logger().info(
            f"mode={self.mode} error={error:.1f} "
            f"speed={speed:.2f} ang={angular:.2f}"
        )


def main(args=None):
    rclpy.init(args=args)
    node = NavigationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
