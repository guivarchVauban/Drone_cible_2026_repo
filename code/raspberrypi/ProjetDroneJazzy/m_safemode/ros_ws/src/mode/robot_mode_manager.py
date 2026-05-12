#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ModeManager(Node):

    def __init__(self):
        super().__init__('mode_manager')

        self.mode = "0"
        self.external_mode = False

        # Publisher
        self.publisher = self.create_publisher(String, '/robot_mode', 10)

        # Subscriber (écoute si un autre node change le mode)
        self.subscription = self.create_subscription(
            String,
            '/robot_mode',
            self.mode_callback,
            10
        )

        # Timer publication
        self.timer = self.create_timer(1.0, self.publish_mode)

        print("Mode manager started")

    def mode_callback(self, msg):

        # Si le mode reçu est différent
        if msg.data != self.mode:
            self.mode = msg.data
            self.external_mode = True
            print(f"Nouveau mode détecté : {self.mode}")

    def publish_mode(self):

        msg = String()

        # Si aucun mode externe → publier 0
        if not self.external_mode:
            msg.data = "0"
        else:
            msg.data = self.mode

        self.publisher.publish(msg)


def main():
    rclpy.init()
    node = ModeManager()
    rclpy.spin(node)


if __name__ == '__main__':
    main()
