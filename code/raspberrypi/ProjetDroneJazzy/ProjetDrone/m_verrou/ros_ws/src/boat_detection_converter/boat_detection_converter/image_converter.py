#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class ImageConverter(Node):
    def __init__(self):
        super().__init__('image_converter')
        self.bridge = CvBridge()
        # Subscriber sur le topic raw
        self.sub = self.create_subscription(
            Image,
            '/boat_detection',
            self.callback,
            10
        )
        # Publisher sur un nouveau topic pour JPEG
        self.pub = self.create_publisher(Image, '/boat_detection_jpeg', 10)

    def callback(self, msg):
        # Convertir ROS Image en OpenCV
        cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        # Encoder en JPEG
        success, jpeg = cv2.imencode('.jpg', cv_img)
        if success:
            jpeg_msg = Image()
            jpeg_msg.height = 0
            jpeg_msg.width = 0
            jpeg_msg.encoding = "jpeg"
            jpeg_msg.is_bigendian = 0
            jpeg_msg.step = len(jpeg.tobytes())
            jpeg_msg.data = jpeg.tobytes()
            # Publier le JPEG
            self.pub.publish(jpeg_msg)

def main(args=None):
    rclpy.init(args=args)
    node = ImageConverter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
