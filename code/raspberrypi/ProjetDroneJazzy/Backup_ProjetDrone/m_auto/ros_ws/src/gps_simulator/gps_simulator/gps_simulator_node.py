import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus

class GPSSimulator(Node):

    def __init__(self):
        super().__init__('gps_simulator')

        self.publisher_ = self.create_publisher(
            NavSatFix,
            '/gps/fix',
            10
        )

        self.timer = self.create_timer(1.0, self.publish_position)

        # Point de référence (ex : Rennes)
        self.lat0 = 48.1173
        self.lon0 = -1.6778

        self.radius = 20.0  # mètres
        self.angle = 0.0
        self.angular_speed = 0.1  # rad/s

        self.get_logger().info("GPS Simulator node started")

    def publish_position(self):
        msg = NavSatFix()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "gps"

        dlat = (self.radius * math.cos(self.angle)) / 111320.0
        dlon = (self.radius * math.sin(self.angle)) / (
            111320.0 * math.cos(math.radians(self.lat0))
        )

        msg.latitude = self.lat0 + dlat
        msg.longitude = self.lon0 + dlon
        msg.altitude = 50.0

        msg.status.status = NavSatStatus.STATUS_FIX
        msg.status.service = NavSatStatus.SERVICE_GPS

        self.publisher_.publish(msg)
        self.angle += self.angular_speed

def main():
    rclpy.init()
    node = GPSSimulator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
