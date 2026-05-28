#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
import json


class NavigationNode(Node):

    def __init__(self):
        super().__init__('navigation_node')

        # Subscribers
        self.create_subscription(
            String,
            '/robot_mode',
            self.mode_callback,
            10
        )

        self.create_subscription(
            String,
            '/boat_detection_json',
            self.detection_callback,
            10
        )

        # Publisher
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # State
        self.mode = 0
        self.locked = False
        self.last_detection = None

        # Camera params (640x480 supposé)
        self.image_center_x = 320.0

        # Control loop
        self.timer = self.create_timer(0.05, self.control_loop)  # 20 Hz

        self.get_logger().info("Navigation node started")

    # -------------------------
    # MODE CALLBACK
    # -------------------------
    def mode_callback(self, msg):
        try:
            self.mode = int(msg.data)
        except:
            self.mode = 0

        self.locked = (self.mode == 2)

    # -------------------------
    # DETECTION CALLBACK
    # -------------------------
    def detection_callback(self, msg):
        try:
            self.last_detection = json.loads(msg.data)
        except Exception as e:
            self.get_logger().warn(f"JSON error: {e}")
            self.last_detection = None

    # -------------------------
    # MAIN LOOP
    # -------------------------
    def control_loop(self):

        twist = Twist()

        # 💤 MODE SLEEP
        if not self.locked:
            self.cmd_pub.publish(twist)
            return

        # ❌ NO DATA
        if not self.last_detection:
            self.cmd_pub.publish(twist)
            return

        if self.last_detection.get("num_boats", 0) == 0:
            self.cmd_pub.publish(twist)
            return

        # -------------------------
        # TAKE FIRST BOAT
        # -------------------------
        boat = self.last_detection["boats"][0]

        x_min = float(boat.get("x_min", 0.0))
        width = float(boat.get("width", 0.0))

        center_x = x_min + (width / 2.0)

        error = center_x - self.image_center_x

        # -------------------------
        # CONTROL PARAMS
        # -------------------------
        Kp = 0.002
        dead_zone = 20.0

        # Forward speed
        twist.linear.x = 0.6

        # Steering
        if abs(error) < dead_zone:
            twist.angular.z = 0.0
        else:
            twist.angular.z = float(-Kp * error)

        # Safety clamp
        twist.angular.z = float(max(min(twist.angular.z, 1.0), -1.0))

        # Publish
        self.cmd_pub.publish(twist)

        self.get_logger().info(
            f"mode={self.mode} error={error:.2f} "
            f"lin_x={twist.linear.x:.2f} ang_z={twist.angular.z:.2f}"
        )


def main(args=None):
    rclpy.init(args=args)
    node = NavigationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
