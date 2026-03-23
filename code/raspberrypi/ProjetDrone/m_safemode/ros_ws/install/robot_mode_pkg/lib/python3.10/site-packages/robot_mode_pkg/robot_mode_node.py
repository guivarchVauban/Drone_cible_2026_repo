import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class RobotModeNode(Node):

    def __init__(self):
        super().__init__('robot_mode_node')

        self.mode = 1

        # Publisher debug
        self.publisher = self.create_publisher(
            String,
            '/debug_mode',
            10
        )

        # Subscriber pour changer le mode
        self.subscription = self.create_subscription(
            String,
            '/set_robot_mode',
            self.mode_callback,
            10
        )

        self.timer = self.create_timer(
            1.0,
            self.publish_mode
        )

        self.get_logger().info("Robot Mode Node started")

    def publish_mode(self):

        msg = String()
        msg.data = f"Robot en Mode = {self.mode}"

        self.publisher.publish(msg)

    def mode_callback(self, msg):

        try:
            self.mode = int(msg.data)
            self.get_logger().info(f"Nouveau mode : {self.mode}")

        except:
            self.get_logger().warn("Mode invalide")


def main(args=None):

    rclpy.init(args=args)

    node = RobotModeNode()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
