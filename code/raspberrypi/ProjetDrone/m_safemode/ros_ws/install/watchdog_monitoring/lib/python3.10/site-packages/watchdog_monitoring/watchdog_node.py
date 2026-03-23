import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, String
from datetime import datetime, timedelta

class WatchdogMonitorNode(Node):
    def __init__(self):

        super().__init__('watchdog_monitor_node')
        # Subscriber vers le WatchdogPublisher
        self.subscription = self.create_subscription(
            Int32,
            '/WatchdogPublisher',
            self.watchdog_callback,
            10
        )

        # Publisher pour changer le mode du robot
        self.mode_publisher = self.create_publisher(
            String,
            '/set_robot_mode',
            10
        )

        self.last_msg_time = datetime.now()
        self.check_timer = self.create_timer(1.0, self.check_watchdog)

        self.get_logger().info("Watchdog Monitor Node started")

    def watchdog_callback(self, msg):
        # Met à jour le timestamp de la dernière publication reçue
        self.last_msg_time = datetime.now()
        self.get_logger().info(f"WatchdogPublisher received: {msg.data}")

    def check_watchdog(self):
        # Vérifie si plus de 3 secondes se sont écoulées depuis la dernière publication
        delta = (datetime.now() - self.last_msg_time).total_seconds()
        if delta > 3.0:
            self.get_logger().warn(f"No message from WatchdogPublisher for {delta:.2f}s → setting robot mode to 3")
            # Publie le mode 3
            msg = String()
            msg.data = "3"
            self.mode_publisher.publish(msg)
            # Réinitialise le timer pour éviter de republier toutes les secondes
            self.last_msg_time = datetime.now()

def main(args=None):
    rclpy.init(args=args)
    node = WatchdogMonitorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
