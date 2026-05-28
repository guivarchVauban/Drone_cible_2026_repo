import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial
import json

class BridgeDrone(Node):

    def __init__(self):

        super().__init__('bridge_drone')

        self.declare_parameter("port", "/dev/ttyUSB0")
        self.declare_parameter("baudrate", 9600)

        port = self.get_parameter("port").get_parameter_value().string_value
        baud = self.get_parameter("baudrate").get_parameter_value().integer_value

        self.subscription_detection = self.create_subscription(
            String,
            '/boat_detection_json',
            self.detection_callback,
            10
        )

        try:
            self.ser = serial.Serial(port, baud, timeout=0.1)
            self.get_logger().info(f"UART ouvert : {port} @ {baud}")
        except serial.SerialException as e:
            self.get_logger().error(f"Erreur ouverture UART : {e}")
            self.ser = None

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
