import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix
import serial
import struct


class BridgeDrone(Node):
    def __init__(self):
        super().__init__('bridge_drone')

        # Paramètres
        self.declare_parameter("port", "/dev/ttyUSB1")
        self.declare_parameter("baudrate", 9600)

        port = self.get_parameter("port").get_parameter_value().string_value
        baud = self.get_parameter("baudrate").get_parameter_value().integer_value

        # Subscription /fix (GPS)
        self.subscription_gps = self.create_subscription(
            NavSatFix,
            '/fix',
            self.gps_callback,
            10
        )

        # UART
        try:
            self.ser = serial.Serial(port, baud, timeout=0.1)
            self.get_logger().info(f"UART ouvert : {port} @ {baud}")
        except serial.SerialException as e:
            self.get_logger().error(f"Erreur ouverture UART : {e}")
            self.ser = None

    def gps_callback(self, msg: NavSatFix):
        """
        Structure de la trame (10 octets) :
          [0x52] [0x01] [0x08] [lat b0 b1 b2 b3] [lon b0 b1 b2 b3]
           start   type  len    float32 LE          float32 LE
        """
        lat = msg.latitude
        lon = msg.longitude

        lat_bytes = struct.pack('<f', lat)
        lon_bytes = struct.pack('<f', lon)

        trame = bytearray([0x52, 0x01, 0x08]) + bytearray(lat_bytes) + bytearray(lon_bytes)

        self.get_logger().info(
            f"GPS → lat={lat:.6f} lon={lon:.6f} | Trame: {[hex(b) for b in trame]}"
        )

        if self.ser and self.ser.is_open:
            payload_hex = trame.hex()
            cmd = f"AT+SEND=0,{payload_hex},0,0\r\n"
            self.get_logger().info(f"Commande LoRa: {cmd.strip()}")
            self.ser.write(cmd.encode())

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
