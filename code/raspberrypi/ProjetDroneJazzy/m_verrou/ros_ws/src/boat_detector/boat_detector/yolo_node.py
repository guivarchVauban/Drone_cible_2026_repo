#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge

import torch
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

        torch.set_num_threads(4)

        self.get_logger().info("🚀 Loading YOLOv5n...")

        self.model = torch.hub.load(
            'ultralytics/yolov5',
            'yolov5n',
            pretrained=True,
            trust_repo=True,
            verbose=False
        )

        self.model.eval()
        self.model.classes = [8]

        # 🔥 réglages améliorés
        self.model.conf = 0.4       # plus sensible
        self.model.iou = 0.45
        self.model.max_det = 5

        self.get_logger().info("✅ YOLO READY (IMPROVED)")

    def image_callback(self, msg):
        self.latest_frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')

    def process_frame(self):

        if self.latest_frame is None:
            return

        start = time.time()

        frame = self.latest_frame.copy()

        # 🔥 amélioration image (important en extérieur / mer)
        frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=10)

        # 🔥 resize plus grand = meilleure détection
        frame = cv2.resize(frame, (320, 320))

        results = self.model(frame)

        end = time.time()

        self.get_logger().info(
            f"🧠 YOLO: {end - start:.3f}s"
        )

        detections = []

        if results.xyxy[0] is not None:
            for *box, conf, cls in results.xyxy[0].tolist():

                x_min, y_min, x_max, y_max = box
                width = x_max - x_min
                height = y_max - y_min

                # 🔥 filtre anti faux positifs
                if conf < 0.4:
                    continue

                if width < 20 or height < 20:
                    continue

                detections.append({
                    "x_min": float(x_min),
                    "y_min": float(y_min),
                    "width": float(width),
                    "height": float(height),
                    "confidence": float(conf)
                })

        output = {
            "timestamp": end,
            "num_boats": len(detections),
            "boats": detections
        }

        msg_out = String()
        msg_out.data = json.dumps(output)

        self.publisher_.publish(msg_out)

        self.get_logger().info(f"📤 {len(detections)} bateaux")


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
