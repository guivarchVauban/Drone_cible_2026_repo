import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import serial
import struct


class BridgeDrone(Node):
    def __init__(self):
        super().__init__('bridge_drone')

        # Paramètres
        self.declare_parameter("port", "/dev/ttyUSB0")
        self.declare_parameter("baudrate", 9600)

        port = self.get_parameter("port").get_parameter_value().string_value
        baud = self.get_parameter("baudrate").get_parameter_value().integer_value

        # Subscription /imu/data
        self.subscription_imu = self.create_subscription(
            Imu,
            '/imu/data',
            self.imu_callback,
            10
        )

        # UART
        try:
            self.ser = serial.Serial(port, baud, timeout=0.1)
            self.get_logger().info(f"UART ouvert : {port} @ {baud}")
        except serial.SerialException as e:
            self.get_logger().error(f"Erreur ouverture UART : {e}")
            self.ser = None

    def imu_callback(self, msg: Imu):
        """
        Structure de la trame (31 octets) :
          [0x52] [0x02] [0x1C] [ox·4] [oy·4] [oz·4] [ow·4] [avx·4] [avy·4] [avz·4]
           start   type  len=28  orientation quaternion      angular velocity

        Payload = 7 × float32 little-endian = 28 octets (0x1C)
        """
        ox  = msg.orientation.x
        oy  = msg.orientation.y
        oz  = msg.orientation.z
        ow  = msg.orientation.w
        avx = msg.angular_velocity.x
        avy = msg.angular_velocity.y
        avz = msg.angular_velocity.z

        payload = struct.pack('<fffffff', ox, oy, oz, ow, avx, avy, avz)

        trame = bytearray([0x52, 0x02, 0x1C]) + bytearray(payload)

        self.get_logger().info(
            f"IMU → orientation=({ox:.3f},{oy:.3f},{oz:.3f},{ow:.3f}) "
            f"angular_vel=({avx:.3f},{avy:.3f},{avz:.3f})"
        )
        self.get_logger().info(f"Trame: {[hex(b) for b in trame]}")

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
