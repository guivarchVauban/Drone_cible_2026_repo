#!/opt/venv/bin/python3

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge

from ultralytics import YOLO

import cv2
import json
import time


class BoatDetector(Node):

    def __init__(self):
        super().__init__('boat_detector')

        self.bridge = CvBridge()
        self.latest_frame = None

        self.subscription = self.create_subscription(
            Image,
            '/image_raw',
            self.image_callback,
            10
        )

        self.publisher_ = self.create_publisher(
            String,
            '/boat_detection_json',
            10
        )

        self.timer = self.create_timer(0.2, self.process_frame)

        self.get_logger().info("Loading YOLOv8n...")
        self.model = YOLO("yolov8n.pt")
        self.get_logger().info("YOLOv8 READY")

    def image_callback(self, msg):
        self.latest_frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')

    def process_frame(self):

        if self.latest_frame is None:
            return

        start = time.time()

        #image originale
        frame = self.latest_frame.copy()
        original_h, original_w = frame.shape[:2]

        #amélioration image
        frame_enhanced = cv2.convertScaleAbs(frame, alpha=1.2, beta=10)

        #resize pour YOLO
        resized = cv2.resize(frame_enhanced, (320, 320))

        #scale factors
        scale_x = original_w / 320
        scale_y = original_h / 320

        #inference
        results = self.model(resized, conf=0.4, iou=0.45, verbose=False)

        end = time.time()
        self.get_logger().info(f"YOLOv8: {end - start:.3f}s")

        detections = []

        for r in results:
            if r.boxes is None:
                continue

            for box in r.boxes:

                cls = int(box.cls[0])
                if cls != 8:
                    continue

                x1, y1, x2, y2 = box.xyxy[0].tolist()

                #RE-SCALE vers image originale
                x1 *= scale_x
                y1 *= scale_y
                x2 *= scale_x
                y2 *= scale_y

                width = x2 - x1
                height = y2 - y1

                # filtre
                if width < 20 or height < 20:
                    continue

                #FORMAT DEMANDÉ
                detections.append({
                    "x": int(x1),
                    "y": int(y1),
                    "width": int(width),
                    "height": int(height)
                })

        #FORMAT FINAL = LISTE SIMPLE
        msg_out = String()
        msg_out.data = json.dumps(detections)

        self.publisher_.publish(msg_out)

        self.get_logger().info(f"{len(detections)} bateaux")


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


if __name__ == '__main__':
    main()
