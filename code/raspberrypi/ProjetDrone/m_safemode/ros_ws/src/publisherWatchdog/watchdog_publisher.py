#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
import time


class WatchdogPublisher(Node):

    def __init__(self):
        super().__init__('watchdog_node')

        self.publisher = self.create_publisher(Int32, '/WatchdogPublisher', 10)
        self.timer = self.create_timer(1.0, self.timer_callback)

        self.counter = 0
        self.pause_triggered = False

        self.get_logger().info("Watchdog publisher started")

    def timer_callback(self):

        # Simuler une erreur : pause 5 secondes une seule fois
        if self.counter == 40 and not self.pause_triggered:
            self.get_logger().warn("Simulating freeze for 5 seconds...")
            time.sleep(5)
            self.pause_triggered = True

        msg = Int32()
        msg.data = self.counter

        self.publisher.publish(msg)
        self.get_logger().info(f"Publishing: {self.counter}")

        self.counter += 1


def main(args=None):
    rclpy.init(args=args)

    node = WatchdogPublisher()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
