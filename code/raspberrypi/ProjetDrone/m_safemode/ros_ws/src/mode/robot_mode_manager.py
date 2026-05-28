#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ModeManager(Node):
    def __init__(self):
        super().__init__('mode_manager')
        self.mode = "0"
        self.publisher = self.create_publisher(String, '/robot_mode', 10)
        self.subscription = self.create_subscription(
            String,
            '/set_robot_mode',
            self.mode_callback,
            10
        )
        self.timer = self.create_timer(5.0, self.publish_mode)

    def mode_callback(self, msg):
        value = msg.data
        if value not in ["0", "1", "2", "3"]:
            self.get_logger().warn("Valeur invalide : " + value)
            return
        if value != self.mode:
            self.mode = value
            self.get_logger().info("Mode change : " + self.mode)
            if self.mode != "3":
                self.timer.reset()
            self.publish_mode()

    def publish_mode(self):
        msg = String()
        msg.data = self.mode
        self.publisher.publish(msg)
        self.get_logger().info("Mode publie : " + self.mode)
        if self.mode == "3":
            self.timer.cancel()


def main():
    rclpy.init()
    node = ModeManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
