import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String
import serial
import json

class BridgeDrone(Node):
    def __init__(self):
        super().__init__('bridge_drone')

        # Paramètres
        self.declare_parameter("port", "/dev/ttyUSB1")
        self.declare_parameter("baudrate", 9600)
        self.declare_parameter("max_linear_speed", 1.0)
        self.declare_parameter("max_angular_speed", 1.0)

        port = self.get_parameter("port").get_parameter_value().string_value
        baud = self.get_parameter("baudrate").get_parameter_value().integer_value

        self.max_linear = self.get_parameter("max_linear_speed").value
        self.max_angular = self.get_parameter("max_angular_speed").value

        # Publisher cmd_vel
        self.publisher_ = self.create_publisher(Twist, "/cmd_vel", 10)

        # Subscription /boat_detection_json
        self.subscription_detection = self.create_subscription(
            String,
            '/boat_detection_json',
            self.detection_callback,
            10
        )

        # UART
        try:
            self.ser = serial.Serial(port, baud, timeout=0.1)
            self.get_logger().info(f"UART ouvert : {port} @ {baud}")
        except serial.SerialException as e:
            self.get_logger().error(f"Erreur ouverture UART : {e}")
            self.ser = None

        # Timer lecture
        self.timer = self.create_timer(0.01, self.read_serial)

    def detection_callback(self, msg):
        try:
            detections = json.loads(msg.data)

            if not detections:
                return

            nb = len(detections)
            trame = bytearray([0x52, 0x03, nb])

            for d in detections:
                x = int(d['x'])
                y = int(d['y'])
                w = int(d['width'])
                h = int(d['height'])

                trame += bytearray([x & 0xFF, (x >> 8) & 0xFF])
                trame += bytearray([y & 0xFF, (y >> 8) & 0xFF])
                trame += bytearray([w & 0xFF, (w >> 8) & 0xFF])
                trame += bytearray([h & 0xFF, (h >> 8) & 0xFF])

            self.get_logger().info(f"Trame: {[hex(b) for b in trame]}")

            if self.ser and self.ser.is_open:
                payload_hex = trame.hex()
                cmd = f"AT+SEND=0,{payload_hex},0,0\r\n"
                self.get_logger().info(f"Commande LoRa: {cmd.strip()}")
                self.ser.write(cmd.encode())

        except Exception as e:
            self.get_logger().warn(f"Erreur detection_callback : {e}")

    def parse_frame(self, line):
        if "Data: (HEX:" not in line:
            return None

        try:
            hex_part = line.split("HEX:")[1]
            hex_part = hex_part.replace(")", "").strip()
            hex_values = hex_part.split()

            if len(hex_values) < 5:
                return None

            start = int(hex_values[0], 16)
            frame_type = int(hex_values[1], 16)
            length = int(hex_values[2], 16)

            if start != 0x52 or frame_type != 0x08 or length != 0x02:
                return None

            x0_mapped = int(hex_values[3], 16)
            x1_mapped = int(hex_values[4], 16)

            x0 = (x0_mapped / 127.5) - 1
            x1 = (x1_mapped - 10) / 10

            return x0, x1

        except Exception as e:
            self.get_logger().warn(f"Erreur parsing : {e}")
            return None

    def publish_cmd_vel(self, x0, x1):
        if abs(x0) < 0.02:
            x0 = 0.0

        if abs(x1) < 0.02:
            x1 = 0.0

        msg = Twist()
        msg.linear.x = x1 * self.max_linear
        msg.angular.z = x0 * self.max_angular

        if abs(msg.angular.z) < 0.001:
            msg.angular.z = 0.0

        self.publisher_.publish(msg)
        self.get_logger().info(
            f"cmd_vel -> linear.x={msg.linear.x:.2f} angular.z={msg.angular.z:.2f}"
        )

    def read_serial(self):
        if self.ser is None:
            return

        try:
            if self.ser.in_waiting == 0:
                return

            line = self.ser.readline().decode("utf-8", errors="ignore").strip()
            result = self.parse_frame(line)

            if result is None:
                return

            x0, x1 = result
            self.publish_cmd_vel(x0, x1)

        except serial.SerialException as e:
            self.get_logger().error(f"Erreur lecture UART : {e}")

    def destroy_node(self):
        if self.ser is not None and self.ser.is_open:
            self.ser.close()
            self.get_logger().info("UART fermé")
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = BridgeDrone()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
