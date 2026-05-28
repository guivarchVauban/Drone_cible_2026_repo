import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, String
from datetime import datetime

class WatchdogMonitorNode(Node):
    def __init__(self):
        super().__init__('watchdog_radio')
        
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

        # --- NOUVEAU : Drapeau pour suivre l'état de l'envoi ---
        self.mode_sent = False

        self.get_logger().info("Watchdog Radio Node started")

    def watchdog_callback(self, msg):
        # On reçoit un signe de vie : on met à jour le temps
        self.last_msg_time = datetime.now()
        
        # Si on était en état de "timeout" (mode_sent = True), on réinitialise 
        # pour permettre un futur renvoi si la connexion reperd à nouveau.
        if self.mode_sent:
            self.get_logger().info("Watchdog recovered: resetting trigger flag.")
            self.mode_sent = False

    def check_watchdog(self):
        delta = (datetime.now() - self.last_msg_time).total_seconds()
        
        # On ne publie que si le délai est dépassé ET que le message n'a pas encore été envoyé
        if delta > 5.0 and not self.mode_sent:
            self.get_logger().warn(f"No message for {delta:.2f}s → sending mode 3 once.")
            
            msg = String()
            msg.data = "3"
            self.mode_publisher.publish(msg)
            
            # On verrouille l'envoi
            self.mode_sent = True

def main(args=None):
    rclpy.init(args=args)
    node = WatchdogMonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
