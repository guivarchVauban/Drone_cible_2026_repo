import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import torch

class BoatDetector(Node):
    def __init__(self):
        super().__init__('boat_detector')
        self.bridge = CvBridge()
        self.subscription = self.create_subscription(
            Image,
            '/image_raw',
            self.image_callback,
            10
        )
        self.publisher_ = self.create_publisher(Image, '/boat_detection', 10)

        self.get_logger().info("Loading YOLOv5 model...")
        # Charger YOLOv5 et filtrer uniquement la classe 8 (boat)
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        self.model.eval()
        self.model.classes = [8]
        self.get_logger().info("YOLOv5 loaded (boat-only).")

    def image_callback(self, msg):
        # Convertir le message ROS en image OpenCV
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import torch

class BoatDetector(Node):
    def __init__(self):
        super().__init__('boat_detector')
        self.bridge = CvBridge()
        self.subscription = self.create_subscription(
            Image,
            '/image_raw',
            self.image_callback,import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import torch

class BoatDetector(Node):
    def __init__(self):
        super().__init__('boat_detector')
        self.bridge = CvBridge()
        self.subscription = self.create_subscription(
            Image,
            '/image_raw',
            self.image_callback,
            10
        )
        self.publisher_ = self.create_publisher(Image, '/boat_detection', 10)

        self.get_logger().info("Loading YOLOv5 model...")
        # Charger YOLOv5 et filtrer uniquement la classe 8 (boat)
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        self.model.eval()
        self.model.classes = [8]
        self.get_logger().info("YOLOv5 loaded (boat-only).")

    def image_callback(self, msg):
        # Convertir le message ROS en image OpenCV
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import torch

class BoatDetector(Node):
    def __init__(self):
        super().__init__('boat_detector')
        self.bridge = CvBridge()
        self.subscription = self.create_subscription(
            Image,
            10
        )
        self.publisher_ = self.create_publisher(Image, '/boat_detection', 10)

        self.get_logger().info("Loading YOLOv5 model...")
        # Charger YOLOv5 et filtrer uniquement la classe 8 (boat)
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        self.model.eval()
        self.model.classes = [8]
        self.get_logger().info("YOLOv5 loaded (boat-only).")

    def image_callback(self, msg):
        # Convertir le message ROS en image OpenCV
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # Exécuter la détection YOLOv5
        results = self.model(frame)

        # Annoter l'image uniquement avec les bateaux détectés
        annotated_frame = results.render()[0]

        # Publier le résultat sur le topic ROS
        annotated_msg = self.bridge.cv2_to_imgmsg(annotated_frame, encoding='bgr8')
        self.publisher_.publish(annotated_msg)

def main(args=None):
    rclpy.init(args=args)
    node = BoatDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
