import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus
from gps import gps, WATCH_ENABLE, WATCH_NEWSTYLE

class GPSReal(Node):

    def __init__(self):
        super().__init__('gps_real')

        self.publisher_ = self.create_publisher(
            NavSatFix,
            '/gps/fix',
            10
        )

        self.gpsd = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
        self.timer = self.create_timer(1.0, self.read_gps)

        self.get_logger().info("GPS real node started")

    def read_gps(self):
        report = self.gpsd.next()

        if report['class'] == 'TPV' and hasattr(report, 'lat'):
            msg = NavSatFix()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = "gps"

            msg.latitude = report.lat
            msg.longitude = report.lon
            msg.altitude = getattr(report, 'alt', 0.0)

            msg.status.status = NavSatStatus.STATUS_FIX
            msg.status.service = NavSatStatus.SERVICE_GPS

            self.publisher_.publish(msg)

def main():
    rclpy.init()
    node = GPSReal()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
